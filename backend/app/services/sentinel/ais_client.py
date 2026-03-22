"""
AIS client — connects to aisstream.io WebSocket API to fetch vessel position data.

Provides berth arrival/departure inference for Sentinel Rule S-002 (Berthage/Stay Verification).
When AIS is unavailable or vessel is not at berth, returns None; AuditEngine falls back to eta/etd.

API ref: https://aisstream.io/documentation
- Subscription message must be sent within 3 seconds of connection.
- Use asyncio.wait_for on recv() to avoid blocking indefinitely when vessel is not transmitting.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import websockets
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.vessel import Vessel
from app.services.cache import cache_get, cache_set

logger = logging.getLogger("shipflow.sentinel.ais")

CACHE_KEY_PREFIX = "ais_berth"
# ~0.1° ≈ 11 km; reasonable port area for berth detection
DEFAULT_PORT_BBOX_DEG = 0.15


@dataclass
class BerthData:
    """Inferred berth arrival and departure from AIS position reports."""

    berth_arrival: datetime
    berth_departure: datetime
    raw_positions_count: int


def _parse_ais_timestamp(ts_str: str | None) -> datetime | None:
    """Parse time_utc from AIS Metadata, e.g. '2022-12-29 18:22:32.318353 +0000 UTC'."""
    if not ts_str:
        return None
    try:
        # Strip timezone suffix; parse as UTC
        parts = ts_str.replace(" +0000 UTC", "").strip()
        return datetime.fromisoformat(parts.replace(" ", "T")).replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def _build_bounding_box(lat: float, lon: float, deg: float = DEFAULT_PORT_BBOX_DEG) -> list:
    """Build aisstream BoundingBoxes format: [[[lat1,lon1],[lat2,lon2]]]."""
    return [[[lat - deg, lon - deg], [lat + deg, lon + deg]]]


def _infer_berth_from_positions(
    positions: list[dict[str, Any]],
    speed_threshold_knots: float,
) -> BerthData | None:
    """
    Infer berth arrival and departure from position reports.

    Considers a vessel "at berth" when Sog < speed_threshold. Uses first and last such
    timestamp in the collected window as berth_arrival and berth_departure.
    """
    at_berth: list[datetime] = []
    for p in positions:
        sog = p.get("sog")
        if sog is None:
            continue
        try:
            speed = float(sog)
        except (TypeError, ValueError):
            continue
        if speed < speed_threshold_knots:
            ts = p.get("timestamp")
            if ts:
                at_berth.append(ts)

    if len(at_berth) < 2:
        return None

    at_berth.sort()
    return BerthData(
        berth_arrival=at_berth[0],
        berth_departure=at_berth[-1],
        raw_positions_count=len(positions),
    )


async def _load_port_call_context(
    db: AsyncSession, port_call_id: uuid.UUID, tenant_id: uuid.UUID
) -> tuple[str, float, float, uuid.UUID] | None:
    """Load vessel MMSI and port coords for AIS lookup. Returns (mmsi, lat, lon, port_id) or None."""
    pc_result = await db.execute(
        select(Vessel.mmsi, Port.latitude, Port.longitude, Port.id)
        .select_from(PortCall)
        .join(Vessel, PortCall.vessel_id == Vessel.id)
        .join(Port, PortCall.port_id == Port.id)
        .where(PortCall.id == port_call_id, PortCall.tenant_id == tenant_id)
    )
    row = pc_result.one_or_none()
    if not row:
        return None
    mmsi, lat, lon, port_id = row
    mmsi = (mmsi or "").strip()
    if not mmsi or lat is None or lon is None:
        return None
    return (mmsi, lat, lon, port_id)


async def _stream_and_infer(
    mmsi: str,
    port_lat: float,
    port_lon: float,
    port_id: uuid.UUID,
    cache_key: str,
) -> BerthData | None:
    """Open WebSocket, collect positions, infer berth, optionally cache. Returns None on failure."""
    positions: list[dict[str, Any]] = []
    bbox = _build_bounding_box(port_lat, port_lon)
    subscribe_msg = {
        "APIKey": settings.aisstream_api_key,
        "BoundingBoxes": bbox,
        "FiltersShipMMSI": [mmsi],
        "FilterMessageTypes": ["PositionReport"],
    }
    timeout = settings.aisstream_collect_timeout_seconds
    speed_threshold = settings.aisstream_berth_speed_threshold_knots
    ttl = settings.aisstream_cache_ttl_seconds

    # Per docs: subscription must be sent within 3 seconds of connection
    logger.debug("AIS connecting to %s for MMSI %s", settings.aisstream_url, mmsi)
    async with websockets.connect(
        settings.aisstream_url,
        open_timeout=10,
        close_timeout=5,
        ping_interval=20,
        ping_timeout=10,
    ) as ws:
        await ws.send(json.dumps(subscribe_msg))
        logger.debug("AIS subscribed, collecting for %ds", timeout)
        deadline_ts = datetime.now(timezone.utc).timestamp() + timeout
        recv_timeout = 5.0  # Per docs: must read promptly or connection may be closed

        while datetime.now(timezone.utc).timestamp() < deadline_ts:
            remaining = deadline_ts - datetime.now(timezone.utc).timestamp()
            if remaining <= 0:
                break
            try:
                msg = await asyncio.wait_for(
                    ws.recv(), timeout=min(recv_timeout, remaining)
                )
            except asyncio.TimeoutError:
                # No message; vessel may not be transmitting in this area
                continue
            except websockets.exceptions.ConnectionClosed:
                break

            data = json.loads(msg)
            if "error" in data:
                logger.warning("AIS stream error: %s", data.get("error"))
                return None

            if data.get("MessageType") != "PositionReport":
                continue

            pr = data.get("Message", {}).get("PositionReport", {})
            meta = data.get("MetaData") or data.get("Metadata", {})
            ts = _parse_ais_timestamp(meta.get("time_utc") or meta.get("TimeUTC"))
            if ts is None:
                ts = datetime.now(timezone.utc)

            positions.append({
                "timestamp": ts,
                "sog": pr.get("Sog", pr.get("sog")),
            })

            if len(positions) >= 3:
                result = _infer_berth_from_positions(positions, speed_threshold)
                if result:
                    await cache_set(
                        cache_key,
                        {
                            "berth_arrival": result.berth_arrival.isoformat(),
                            "berth_departure": result.berth_departure.isoformat(),
                            "raw_positions_count": result.raw_positions_count,
                        },
                        ttl,
                    )
                    return result
    return None


async def fetch_berth_data(
    db: AsyncSession,
    port_call_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> BerthData | None:
    """
    Fetch AIS berth data for a port call.

    Connects to aisstream.io WebSocket, subscribes to port bounding box and vessel MMSI,
    collects PositionReports for a short window, infers berth arrival/departure.

    Returns None on: no API key, no MMSI, no port coordinates, connection error,
    or when vessel is not detected at berth. Uses Redis cache to respect rate limits.
    """
    if not settings.aisstream_api_key:
        logger.debug("AIS client: no API key configured; skipping")
        return None

    ctx = await _load_port_call_context(db, port_call_id, tenant_id)
    if not ctx:
        return None

    mmsi, port_lat, port_lon, port_id = ctx
    cache_key = f"{CACHE_KEY_PREFIX}:{mmsi}:{port_id}"
    cached = await cache_get(cache_key)
    if cached:
        try:
            return BerthData(
                berth_arrival=datetime.fromisoformat(cached["berth_arrival"]),
                berth_departure=datetime.fromisoformat(cached["berth_departure"]),
                raw_positions_count=cached.get("raw_positions_count", 0),
            )
        except (KeyError, ValueError):
            pass

    try:
        return await _stream_and_infer(mmsi, port_lat, port_lon, port_id, cache_key)
    except websockets.exceptions.InvalidStatusCode as e:
        logger.warning("AIS connection failed (status %s): %s", getattr(e, "status_code", ""), e)
        return None
    except Exception as e:
        logger.warning("AIS fetch failed: %s", e, exc_info=True)
        return None
