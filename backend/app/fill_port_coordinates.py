"""Fill port coordinates for AIS (aisstream.io) berth lookups.

Run: python -m app.fill_port_coordinates
In container: docker compose exec app python -m app.fill_port_coordinates

Alternative (direct SQL when app service unavailable):
  docker compose exec postgres psql -U shipflow -d shipflow -f - <<'SQL'
  UPDATE ports SET latitude = 53.5511, longitude = 9.9937 WHERE code = 'DEHAM';
  UPDATE ports SET latitude = 37.9436, longitude = 23.6469 WHERE code = 'GRPIR';
  UPDATE ports SET latitude = 51.9225, longitude = 4.4792 WHERE code IN ('NLRTM','ROTTERDAM');
  UPDATE ports SET latitude = 31.2304, longitude = 121.4737 WHERE code = 'CNSHA';
  UPDATE ports SET latitude = 1.2644, longitude = 103.8158 WHERE code = 'SGSIN';
  SQL

Required for Sentinel Rule S-002: AIS client needs port lat/lon to build
bounding box for vessel position lookups. Ports without coordinates are skipped.
"""

import asyncio

from sqlalchemy import select, update

from app.database import async_session_factory
from app.models.port import Port

# Approximate coordinates for major ports (harbor center / pilot station)
PORT_COORDINATES = [
    ("DEHAM", 53.5511, 9.9937),   # Hamburg
    ("GRPIR", 37.9436, 23.6469),  # Piraeus
    ("NLRTM", 51.9225, 4.4792),   # Rotterdam
    ("ROTTERDAM", 51.9225, 4.4792),  # Rotterdam (alternate code)
    ("CNSHA", 31.2304, 121.4737),  # Shanghai
    ("SGSIN", 1.2644, 103.8158),   # Singapore
]


async def main() -> None:
    async with async_session_factory() as db:
        updated = 0
        for code, lat, lon in PORT_COORDINATES:
            result = await db.execute(
                update(Port)
                .where(Port.code == code)
                .where((Port.latitude.is_(None)) | (Port.longitude.is_(None)))
                .values(latitude=lat, longitude=lon)
            )
            updated += result.rowcount or 0
        await db.commit()
        print(f"Updated coordinates for {updated} port(s).")
        if updated == 0:
            print("No ports were missing coordinates, or codes did not match.")


if __name__ == "__main__":
    asyncio.run(main())
