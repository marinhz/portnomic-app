#!/usr/bin/env python3
"""Smoke test: verify aisstream.io connection and that we receive PositionReports.

Run: python -m app.test_aisstream_connection
In container: docker compose exec app python -m app.test_aisstream_connection

Requires: AISSTREAM_API_KEY in .env

This subscribes to Rotterdam port area (no MMSI filter) and waits up to 30s
for any PositionReport. If we get at least 1 message, the integration works.
"""

import asyncio
import json
import os
import sys
import time

import websockets


async def main() -> None:
    api_key = os.environ.get("AISSTREAM_API_KEY", "")
    if not api_key:
        print("ERROR: AISSTREAM_API_KEY not set. Get one at https://aisstream.io")
        sys.exit(1)

    # Rotterdam port area - busy shipping lane, we should get messages
    bbox = [[[51.77, 4.3], [52.0, 4.7]]]
    subscribe_msg = {
        "APIKey": api_key,
        "BoundingBoxes": bbox,
        "FilterMessageTypes": ["PositionReport"],
    }

    print("Connecting to wss://stream.aisstream.io/v0/stream ...")
    received = 0

    try:
        async with websockets.connect(
            "wss://stream.aisstream.io/v0/stream",
            open_timeout=10,
            close_timeout=5,
        ) as ws:
            await ws.send(json.dumps(subscribe_msg))
            print("Subscribed. Waiting up to 30s for PositionReports...")

            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                remaining = deadline - time.monotonic()
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=min(5, remaining))
                except asyncio.TimeoutError:
                    continue

                data = json.loads(msg)
                if "error" in data:
                    print(f"ERROR from aisstream: {data.get('error')}")
                    sys.exit(1)

                if data.get("MessageType") == "PositionReport":
                    received += 1
                    pr = data.get("Message", {}).get("PositionReport", {})
                    meta = data.get("MetaData") or data.get("Metadata", {})
                    mmsi = meta.get("MMSI", pr.get("UserID", "?"))
                    sog = pr.get("Sog", pr.get("sog", "?"))
                    lat = pr.get("Latitude", "?")
                    lon = pr.get("Longitude", "?")
                    print(f"  [{received}] MMSI {mmsi} @ ({lat}, {lon}) Sog={sog} kn")

                    if received >= 3:
                        print(f"\nSUCCESS: Received {received} PositionReports. AIS integration works.")
                        return

            if received > 0:
                print(f"\nSUCCESS: Received {received} PositionReport(s). AIS integration works.")
            else:
                print("\nNo PositionReports in 30s. Possible causes:")
                print("  - API key invalid or rate limited")
                print("  - No vessels in Rotterdam area right now (unlikely)")
                print("  - Network/firewall blocking wss://")
                sys.exit(1)

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Connection failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
