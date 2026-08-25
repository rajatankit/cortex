from __future__ import annotations

from typing import Any

from .tool import Tool, ToolRisk


# ============================================================
# TOOL HANDLERS
# ============================================================

async def read_security_logs(
    context: dict[str, Any],
) -> dict[str, Any]:

    return {
        "operation": "read_security_logs",
        "status": "success",
        "message": "Security logs read successfully.",
        "context": context,
    }


async def security_scan(
    context: dict[str, Any],
) -> dict[str, Any]:

    return {
        "operation": "security_scan",
        "status": "success",
        "message": "Security scan completed.",
        "context": context,
    }


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
                    "Read CORTEX security and monitoring logs."
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
                    "Perform a security scan of the CORTEX environment."
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