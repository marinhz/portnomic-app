"""Fill port coordinates for AIS (aisstream.io) berth lookups

Revision ID: 20260321_port_coords
Revises: 20260321_content_hash_idx
Create Date: 2026-03-21

Required for Sentinel Rule S-002: AIS client needs port lat/lon to build
bounding box for vessel position lookups. Ports without coordinates are skipped.
"""

from sqlalchemy import text

from alembic import op

revision = "20260321_port_coords"
down_revision = "20260321_content_hash_idx"
branch_labels = None
depends_on = None

# Approximate coordinates for major ports (harbor center / pilot station)
PORT_COORDINATES = [
    ("DEHAM", 53.5511, 9.9937),   # Hamburg
    ("GRPIR", 37.9436, 23.6469),  # Piraeus
    ("NLRTM", 51.9225, 4.4792),   # Rotterdam
    ("ROTTERDAM", 51.9225, 4.4792),  # Rotterdam (alternate code)
    ("CNSHA", 31.2304, 121.4737),  # Shanghai
    ("SGSIN", 1.2644, 103.8158),   # Singapore
]


def upgrade() -> None:
    conn = op.get_bind()
    for code, lat, lon in PORT_COORDINATES:
        conn.execute(
            text(
                "UPDATE ports SET latitude = :lat, longitude = :lon "
                "WHERE code = :code AND (latitude IS NULL OR longitude IS NULL)"
            ),
            {"code": code, "lat": lat, "lon": lon},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for code, _, _ in PORT_COORDINATES:
        conn.execute(
            text("UPDATE ports SET latitude = NULL, longitude = NULL WHERE code = :code"),
            {"code": code},
        )
