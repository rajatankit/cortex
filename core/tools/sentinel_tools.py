"""
tools/sentinel_tools.py

SENTINEL security/monitoring tools for CORTEX.

read_security_logs and security_scan now read REAL data from Battle
Crown's "Alert" table in Neon Postgres - the same table your
monitoring system (/api/cortex/monitor/*) already writes to for
deposits, withdrawals, new users, tournament issues, errors, etc.

security_action is left untouched. Its risk level is CRITICAL, and
per core/decision.py, CRITICAL actions are always BLOCKED at the
decision layer - "blocked until a future explicit security workflow
is implemented." That's intentional: wiring a real handler here
would never actually run until that workflow is designed, so there's
nothing to build yet.
"""

from __future__ import annotations

from typing import Any

from .tool import Tool, ToolRisk
from core.db import fetch


_VALID_SEVERITIES = {"low", "medium", "high"}


# ============================================================
# READ SECURITY LOGS  (REAL DATA)
# ============================================================

async def read_security_logs(
    context: dict[str, Any],
) -> dict[str, Any]:

    severity = context.get("severity")
    alert_type = context.get("type") or context.get("alert_type")
    only_unacknowledged = context.get("unacknowledged")

    where_parts: list[str] = []
    params: list[Any] = []

    if severity:
        s = str(severity).strip().lower()
        if s in _VALID_SEVERITIES:
            params.append(s)
            where_parts.append(f'LOWER("severity") = ${len(params)}')

    if alert_type:
        params.append(str(alert_type).strip().lower())
        where_parts.append(f'LOWER("type") = ${len(params)}')

    if only_unacknowledged:
        where_parts.append('"notified" = false')

    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    rows = await fetch(
        f'''
        SELECT "id", "type", "severity", "title", "message", "refId", "notified", "createdAt"
        FROM "Alert"
        {where_clause}
        ORDER BY "createdAt" DESC
        LIMIT 20
        ''',
        *params,
    )

    return {
        "status": "ok",
        "operation": "read_security_logs",
        "alerts": [
            {
                "id": r["id"],
                "type": r["type"],
                "severity": r["severity"],
                "title": r["title"],
                "message": r["message"],
                "ref_id": r["refId"],
                "acknowledged": bool(r["notified"]),
                "created_at": r["createdAt"].isoformat() if r["createdAt"] else None,
            }
            for r in rows
        ],
    }


# ============================================================
# SECURITY SCAN  (REAL DATA - summary/aggregate over Alert table)
# ============================================================

async def security_scan(
    context: dict[str, Any],
) -> dict[str, Any]:

    rows = await fetch(
        '''
        SELECT "severity", "notified"
        FROM "Alert"
        WHERE "notified" = false
        '''
    )

    high = sum(1 for r in rows if str(r["severity"]).lower() == "high")
    medium = sum(1 for r in rows if str(r["severity"]).lower() == "medium")
    low = sum(1 for r in rows if str(r["severity"]).lower() == "low")
    total = len(rows)

    return {
        "status": "ok",
        "operation": "security_scan",
        "unacknowledged_total": total,
        "high": high,
        "medium": medium,
        "low": low,
        "clean": total == 0,
    }


# ============================================================
# SECURITY ACTION  (unchanged - see module docstring: CRITICAL
# risk is always BLOCKED at the decision layer, so this handler
# never actually runs until that workflow is designed)
# ============================================================

async def security_action(
    context: dict[str, Any],
) -> dict[str, Any]:

    return {
        "operation": "security_action",
        "status": "success",
        "message": "Authorized security action executed.",
        "context": context,
    }


# ============================================================
# REGISTRATION
# ============================================================

def register_sentinel_tools(tool_registry) -> None:

    if not tool_registry.exists("read_security_logs"):
        tool_registry.register(
            Tool(
                name="read_security_logs",
                description=(
                    "Reads real Battle Crown security/monitoring alerts "
                    "(deposits, withdrawals, errors, etc), optionally "
                    "filtered by severity or type."
                ),
                required_action="read_security_logs",
                risk=ToolRisk.LOW,
                handler=read_security_logs,
            )
        )

    if not tool_registry.exists("security_scan"):
        tool_registry.register(
            Tool(
                name="security_scan",
                description=(
                    "Summarizes unacknowledged security alerts by severity "
                    "(high/medium/low) - use for 'sab theek hai?' type checks."
                ),
                required_action="security_scan",
                risk=ToolRisk.MEDIUM,
                handler=security_scan,
            )
        )

    if not tool_registry.exists("security_action"):
        tool_registry.register(
            Tool(
                name="security_action",
                description=(
                    "Execute an explicitly authorized security action."
                ),
                required_action="security_action",
                risk=ToolRisk.CRITICAL,
                handler=security_action,
            )
        )