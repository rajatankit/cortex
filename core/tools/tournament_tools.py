"""
tools/tournament_tools.py

Modular tool definitions for ARIA (Tournament Management).
No database/API calls yet — in-memory placeholder data only.
Replace the internal logic later with real Battle-Crown DB/API calls
without changing function signatures.
"""

from __future__ import annotations
from typing import Any, Dict

from .tool import Tool, ToolRisk
from copy import deepcopy

# Placeholder in-memory store — replace with real DB later.
_TOURNAMENTS: Dict[str, Dict[str, Any]] = {
    "T1": {"id": "T1", "name": "Summer Cup", "time": "19:00", "status": "scheduled"},
}


async def read_tournament(context: Dict[str, Any]) -> Dict[str, Any]:
    tournament_id = context.get("tournament_id")

    if tournament_id:
        tournament = _TOURNAMENTS.get(tournament_id)
        if tournament is None:
            return {"status": "not_found", "tournament_id": tournament_id}
        return {"status": "ok", "tournament": dict(tournament),}

    return {"status": "ok", "tournaments": [dict(tournament) for tournament in _TOURNAMENTS.values()],}


async def create_tournament(context: Dict[str, Any]) -> Dict[str, Any]:
    name = context.get("tournament_name")
    time_str = context.get("time")

    if not name or not time_str:
        return {"status": "error", "message": "tournament_name and time are required"}

    new_id = f"T{len(_TOURNAMENTS) + 1}"
    tournament = {"id": new_id, "name": name, "time": time_str, "status": "scheduled"}
    _TOURNAMENTS[new_id] = tournament

    return {"status": "created", "tournament": dict(tournament),}


async def manage_tournament(context: Dict[str, Any]) -> Dict[str, Any]:
    tournament_id = context.get("tournament_id")
    updates = context.get("updates", {})

    if not tournament_id:
        return {"status": "error", "message": "tournament_id is required"}

    tournament = _TOURNAMENTS.get(tournament_id)
    if tournament is None:
        return {"status": "not_found", "tournament_id": tournament_id}

    tournament.update(updates)
    return {"status": "updated", "tournament": dict(tournament),}


TOURNAMENT_TOOLS = (
    Tool(
        name="read_tournament",
        description="Reads one or all tournaments.",
        required_action="read_tournament",
        risk=ToolRisk.LOW,
        handler=read_tournament,
    ),
    Tool(
        name="create_tournament",
        description="Creates a new tournament.",
        required_action="create_tournament",
        risk=ToolRisk.HIGH,
        handler=create_tournament,
    ),
    Tool(
        name="manage_tournament",
        description="Updates an existing tournament (time, status, etc).",
        required_action="manage_tournament",
        risk=ToolRisk.MEDIUM,
        handler=manage_tournament,
    ),
)


def register_tournament_tools(tool_registry) -> None:
    for tool in TOURNAMENT_TOOLS:
        if not tool_registry.exists(tool.name):
            tool_registry.register(tool)





