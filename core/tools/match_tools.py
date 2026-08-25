"""
ORION tools - Battle-Crown match operations.
"""

from __future__ import annotations

from typing import Any, Dict

from .tool import Tool, ToolRisk


_MATCHES: Dict[str, Dict[str, Any]] = {}


async def read_match_data(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    match_id = context.get("match_id")

    return {
        "status": "requested",
        "match_id": match_id,
        "source": "battle_crown",
        "operation": "read_match_data",
    }


async def update_match_data(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    match_id = context.get("match_id")
    updates = context.get("updates", {})

    if not match_id:
        return {
            "status": "error",
            "message": "match_id is required",
        }

    if not isinstance(updates, dict):
        return {
            "status": "error",
            "message": "updates must be a dictionary",
        }

    return {
        "status": "requested",
        "match_id": match_id,
        "updates": updates,
        "source": "battle_crown",
        "operation": "update_match_data",
    }


async def verify_match(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    match_id = context.get("match_id")

    if not match_id:
        return {
            "status": "error",
            "message": "match_id is required",
        }

    return {
        "status": "requested",
        "match_id": match_id,
        "action": str(
            context.get(
                "verify_action",
                "APPROVE",
            )
        ).upper(),
        "source": "battle_crown",
        "operation": "verify_match",
    }


MATCH_TOOLS = (
    Tool(
        name="read_match_data",
        description="Reads Battle-Crown match data.",
        required_action="read_match_data",
        risk=ToolRisk.LOW,
        handler=read_match_data,
    ),
    Tool(
        name="update_match_data",
        description="Updates permitted Battle-Crown match data.",
        required_action="update_match_data",
        risk=ToolRisk.MEDIUM,
        handler=update_match_data,
    ),
    Tool(
        name="verify_match",
        description="Verifies a Battle-Crown match.",
        required_action="verify_match",
        risk=ToolRisk.HIGH,
        handler=verify_match,
    ),
)


def register_match_tools(tool_registry) -> None:

    for tool in MATCH_TOOLS:

        if not tool_registry.exists(tool.name):
            tool_registry.register(tool)
