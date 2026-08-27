"""
tools/tournament_tools.py

Modular tool definitions for ARIA (Tournament Management).

read_tournament now reads REAL data from Battle Crown's "tournaments"
table in Neon Postgres. roomId/roomPassword are deliberately NEVER
returned here - room credentials are protected data and belong to
VAULT's read_room_data flow only (see tools/vault_tools.py), which
goes through a dedicated Battle Crown API rather than a raw query.

create_tournament and manage_tournament are left as in-memory
sandbox placeholders on purpose: creating/editing a real tournament
from a voice command has no approval/validation step yet. Wire these
to real INSERT/UPDATE only after that's designed (they're already
marked HIGH/MEDIUM risk in ToolRisk, so ApprovalGate is the right
place to add that gate).
"""

from __future__ import annotations
from typing import Any, Dict

from .tool import Tool, ToolRisk
from core.db import fetch, fetchrow

# Placeholder in-memory store - still used by create_tournament and
# manage_tournament below, which remain sandboxed (see docstring).
_TOURNAMENTS: Dict[str, Dict[str, Any]] = {
    "T1": {"id": "T1", "name": "Summer Cup", "time": "19:00", "status": "scheduled"},
}


def _serialize_tournament(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "game": row["game"],
        "map": row["map"],
        "mode": row["mode"],
        "entry_fee": row["entryFee"],
        "max_slots": row["maxSlots"],
        "joined_count": row["joinedCount"],
        "status": row["status"],
        "start_time": (
            row["startTime"].isoformat() if row["startTime"] else None
        ),
        "first_prize": row["firstPrize"],
        "second_prize": row["secondPrize"],
        "third_prize": row["thirdPrize"],
        "kill_reward": row["killReward"],
        # roomId / roomPassword intentionally omitted - VAULT-only data.
    }


_TOURNAMENT_COLUMNS = '''
    "id", "title", "game", "map", "mode", "entryFee", "maxSlots",
    "joinedCount", "status", "startTime", "firstPrize",
    "secondPrize", "thirdPrize", "killReward"
'''


async def read_tournament(context: Dict[str, Any]) -> Dict[str, Any]:

    tournament_id = context.get("tournament_id")
    status = context.get("status")

    if tournament_id:
        try:
            numeric_id = int(tournament_id)
        except (TypeError, ValueError):
            return {
                "status": "error",
                "message": "tournament_id must be numeric",
            }

        row = await fetchrow(
            f'''
            SELECT {_TOURNAMENT_COLUMNS}
            FROM tournaments
            WHERE "id" = $1
            ''',
            numeric_id,
        )

        if row is None:
            return {"status": "not_found", "tournament_id": tournament_id}

        return {"status": "ok", "tournament": _serialize_tournament(row)}

    if status:
        rows = await fetch(
            f'''
            SELECT {_TOURNAMENT_COLUMNS}
            FROM tournaments
            WHERE "status" = $1
            ORDER BY "startTime" ASC NULLS LAST
            LIMIT 20
            ''',
            status,
        )
    else:
        # No filter given (e.g. "tournament check karo" with no
        # specifics) - default to live/upcoming ones, most relevant
        # first, capped so the spoken summary stays short.
        rows = await fetch(
            f'''
            SELECT {_TOURNAMENT_COLUMNS}
            FROM tournaments
            WHERE "status" IN ('live', 'upcoming', 'ongoing')
            ORDER BY "startTime" ASC NULLS LAST
            LIMIT 20
            '''
        )

    return {
        "status": "ok",
        "tournaments": [_serialize_tournament(row) for row in rows],
    }


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
        description="Reads real tournaments (live/upcoming by default, or by id/status).",
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