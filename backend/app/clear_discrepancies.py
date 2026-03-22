"""Clear all Sentinel discrepancies. For dev/testing: reset before re-testing uploads.

Run: python -m app.clear_discrepancies
In container: docker compose exec app python -m app.clear_discrepancies
"""

import asyncio

from sqlalchemy import delete

from app.database import async_session_factory
from app.models.discrepancy import Discrepancy


async def main() -> None:
    async with async_session_factory() as db:
        result = await db.execute(delete(Discrepancy))
        count = result.rowcount or 0
        await db.commit()
        print(f"Cleared {count} Sentinel discrepancy(ies).")


if __name__ == "__main__":
    asyncio.run(main())
