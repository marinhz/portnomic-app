"""Run Sentinel audit on a port call (for testing AIS/aisstream.io).

Run: python -m app.run_sentinel_audit <port_call_id> <tenant_id>
Example: python -m app.run_sentinel_audit 7a66d078-3d84-429a-9752-9e2ef97e7df8 665e89e2-1a69-4b5c-ab43-c9469605d784
"""

import asyncio
import sys
import uuid

from app.database import async_session_factory
from app.services.sentinel import AuditEngine


async def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m app.run_sentinel_audit <port_call_id> <tenant_id>")
        sys.exit(1)
    port_call_id = uuid.UUID(sys.argv[1])
    tenant_id = uuid.UUID(sys.argv[2])

    async with async_session_factory() as db:
        engine = AuditEngine(db, tenant_id)
        report = await engine.compare_events(port_call_id)
        print(f"Audit completed: {report.total_count} discrepancy(ies)")
        print(f"Rules executed: {report.rules_executed}")
        print(f"By severity: {report.by_severity}")
        print(f"By rule: {report.by_rule}")
        for i, d in enumerate(report.discrepancies[:5], 1):
            print(f"  {i}. [{d.rule_id}] {d.description}")


if __name__ == "__main__":
    asyncio.run(main())
