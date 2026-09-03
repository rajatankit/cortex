"""
tools/tournament_tools.py

Modular tool definitions for ARIA (Tournament Management).

read_tournament reads REAL data from Battle Crown's "tournaments"
table in Neon Postgres. roomId/roomPassword are deliberately NEVER
returned here - room credentials are protected data and belong to
VAULT's read_room_data flow only (see tools/vault_tools.py), which
goes through a dedicated Battle Crown API rather than a raw query.

create_tournament now writes a REAL document to the Firestore
"tournaments" collection (the same collection you create tournaments
in manually from the Firebase console). Battle Crown's dashboard
listener then mirrors that document into Postgres via
/api/tournament/sync, same as it does for anything created manually.

manage_tournament is still an in-memory sandbox placeholder - editing
a live tournament (changing prizes, status, etc.) isn't wired to
Firestore yet.
"""

from __future__ import annotations
from typing import Any, Dict

from .tool import Tool, ToolRisk
from core.db import fetch, fetchrow
from core.firebase_client import get_firestore_client

# Placeholder in-memory store - still used by manage_tournament below,
# which remains sandboxed (see docstring).
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
    title = context.get("tournament_name") or context.get("title")

    if not title:
        return {"status": "error", "message": "tournament_name (title) is required"}

    game = context.get("game", "BGMI")
    map_name = context.get("map")
    mode = context.get("mode")
    entry_fee = context.get("entryFee")
    max_slots = context.get("maxSlots", 100)
    first_prize = context.get("firstPrize", 0)
    second_prize = context.get("secondPrize", 0)
    third_prize = context.get("thirdPrize", 0)
    kill_reward = context.get("killReward", 5)
    date = context.get("date") or context.get("time")

    doc_data = {
        "title": title,
        "game": game,
        "map": map_name,
        "mode": mode,
        "entryFee": entry_fee,
        "maxSlots": max_slots,
        "joinedCount": 0,
        "status": "upcoming",
        "firstPrize": first_prize,
        "secondPrize": second_prize,
        "thirdPrize": third_prize,
        "killReward": kill_reward,
        "date": date,
    }

    db = get_firestore_client()
    # auto-generated doc id, same as clicking "Add document" with a
    # blank id in the Firebase console.
    _, doc_ref = db.collection("tournaments").add(doc_data)

    created = dict(doc_data)
    created["id"] = doc_ref.id

    return {"status": "created", "tournament": created}


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