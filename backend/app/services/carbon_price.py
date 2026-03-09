"""
Carbon Price Service: fetch EUA (EU Allowance) market price for C-Engine cost projection.

Fetches from external API (EEX, ICE, aggregators), caches in Redis (1h TTL),
falls back to configurable default when API unavailable. Never blocks emission calculation.
"""

import logging
from typing import Any

import httpx

from app.config import settings
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

CACHE_KEY = "shipflow:carbon_price_eur"


def _extract_price_from_json(data: dict[str, Any], path: str) -> float | None:
    """Extract price from JSON using dot-separated path (e.g. 'price' or 'contracts.0.last_price')."""
    keys = path.split(".")
    obj: Any = data
    for key in keys:
        if obj is None:
            return None
        if key.isdigit():
            idx = int(key)
            obj = obj[idx] if isinstance(obj, list) and 0 <= idx < len(obj) else None
        else:
            obj = obj.get(key) if isinstance(obj, dict) else None
    if obj is None:
        return None
    try:
        return float(obj)
    except (TypeError, ValueError):
        return None


async def get_current_price_eur() -> float:
    """Get current EU carbon (EUA) price in EUR.

    Tries: cache -> API -> stale cache -> fallback. Never raises; always returns a price.
    """
    ttl = settings.carbon_price_cache_ttl_seconds
    fallback = settings.fallback_carbon_price_eur

    # 1. Try cache first
    try:
        cached = await redis_client.get(CACHE_KEY)
        if cached is not None:
            return float(cached)
    except Exception as e:
        logger.warning("Carbon price cache read failed: %s", e)

    # 2. Try API if configured
    if settings.carbon_price_api_url:
        price = await _fetch_from_api()
        if price is not None and price >= 0:
            try:
                await redis_client.set(CACHE_KEY, str(price), ex=ttl)
            except Exception as e:
                logger.warning("Carbon price cache write failed: %s", e)
            return price
        logger.warning(
            "Carbon price API unavailable or invalid; using cache/fallback",
            extra={"api_url": settings.carbon_price_api_url},
        )

    # 3. Try stale cache (any cached value is better than nothing)
    try:
        stale = await redis_client.get(CACHE_KEY)
        if stale is not None:
            return float(stale)
    except Exception:
        pass

    # 4. Fallback
    return fallback


async def _fetch_from_api() -> float | None:
    """Fetch price from configured API. Returns None on failure."""
    url = settings.carbon_price_api_url
    headers: dict[str, str] | None = None
    if settings.carbon_price_api_key:
        hdr = settings.carbon_price_api_header
        val = (
            f"Bearer {settings.carbon_price_api_key}"
            if hdr.lower() == "authorization"
            else settings.carbon_price_api_key
        )
        headers = {hdr: val}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.warning("Carbon price API request failed: %s", e)
        return None

    if not isinstance(data, dict):
        return None

    price = _extract_price_from_json(data, settings.carbon_price_json_path)
    if price is None:
        # Try common keys as fallback
        for key in ("price", "price_eur", "last_price"):
            price = _extract_price_from_json(data, key)
            if price is not None:
                break
        if price is None and "contracts" in data:
            contracts = data.get("contracts")
            if isinstance(contracts, list) and contracts:
                first = contracts[0]
                if isinstance(first, dict):
                    price = _extract_price_from_json(first, "last_price")

    return price if price is not None and price >= 0 else None


__all__ = ["get_current_price_eur"]
