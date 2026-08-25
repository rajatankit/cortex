from __future__ import annotations

from typing import Any

from core.tools.tool import Tool, ToolRisk


# ============================================================
# READ CODE
# ============================================================

async def read_code(
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Read-only engineering operation.

    ATLAS does not directly modify files.
    Actual execution remains controlled by ToolGateway.
    """

    context = context or {}

    return {
        "operation": "read_code",
        "status": "accepted",
        "context": context,
    }


# ============================================================
# MODIFY CODE
# ============================================================

async def modify_code(
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High-risk engineering operation.

    Actual code modification must only occur after
    authorization and approval through CORTEX.
    """

    context = context or {}

    return {
        "operation": "modify_code",
        "status": "accepted",
        "context": context,
    }


# ============================================================
# REGISTRATION
# ============================================================

def register_atlas_tools(tool_registry) -> None:

    # --------------------------------------------------------
    # READ CODE
    # --------------------------------------------------------

    if not tool_registry.exists("read_code"):

        tool_registry.register(
            Tool(
                name="read_code",
                description=(
                    "Read source code and inspect engineering "
                    "information without modifying files."
                ),
                required_action="read_code",
                risk=ToolRisk.LOW,
                handler=read_code,
            )
        )

    # --------------------------------------------------------
    # MODIFY CODE
    # --------------------------------------------------------

    if not tool_registry.exists("modify_code"):

        tool_registry.register(
            Tool(
                name="modify_code",
                description=(
                    "Modify source code through an authorized "
                    "and approved engineering operation."
                ),
                required_action="modify_code",
                risk=ToolRisk.HIGH,
                handler=modify_code,
            )
        )