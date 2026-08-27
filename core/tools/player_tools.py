"""
tools/player_tools.py

ELARA player-information tools.

read_player_data now reads REAL data from Battle Crown's "User" and
match_history tables in Neon Postgres. update_player_data is left as
a sandbox no-op deliberately: writing player data from a voice
command has no validation/approval step yet, so it should not touch
production data until that's designed. Wire it up through
ApprovalGate + a real UPDATE once that's ready.
"""

from __future__ import annotations

from typing import Any, Dict

from .tool import Tool, ToolRisk
from core.db import fetch, fetchrow


# ============================================================
# SANDBOX DATA (kept only for update_player_data below)
# ============================================================

_PLAYERS: Dict[str, Dict[str, Any]] = {
    "P1": {
        "id": "P1",
        "name": "Rajat",
        "rank": "Gold",
        "wins": 12,
        "losses": 4,
    },
}


# ============================================================
# READ PLAYER DATA  (REAL DATA)
# ============================================================

async def read_player_data(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    uid = context.get("uid")
    name = context.get("name") or context.get("player_name")

    if not uid and not name:
        return {
            "status": "error",
            "message": "uid or name is required",
        }

    if uid:
        user = await fetchrow(
            '''
            SELECT
                "uid", "email", "name", "level", "crowns",
                "matchesPlayed", "bgmiIgn", "bgmiUid",
                "ffIgn", "ffUid", "bio"
            FROM "User"
            WHERE "uid" = $1
            ''',
            uid,
        )

        if user is None:
            return {"status": "not_found", "uid": uid}

        recent_matches = await fetch(
            '''
            SELECT "tournamentName", "kills", "prizeWon", "status", "createdAt"
            FROM match_history
            WHERE "userId" = (SELECT "id" FROM "User" WHERE "uid" = $1)
            ORDER BY "createdAt" DESC
            LIMIT 5
            ''',
            uid,
        )

        return {
            "status": "ok",
            "player": {
                "uid": user["uid"],
                "email": user["email"],
                "name": user["name"],
                "level": user["level"],
                "crowns": user["crowns"],
                "matches_played": user["matchesPlayed"],
                "bgmi_ign": user["bgmiIgn"],
                "free_fire_ign": user["ffIgn"],
                "bio": user["bio"],
                "recent_matches": [
                    {
                        "tournament": m["tournamentName"],
                        "kills": m["kills"],
                        "prize_won": m["prizeWon"],
                        "status": m["status"],
                    }
                    for m in recent_matches
                ],
            },
        }

    # Name-based lookup - partial, case-insensitive, capped at 5
    # matches so a common name doesn't dump the whole table.
    matches = await fetch(
        '''
        SELECT "uid", "name", "level", "crowns", "matchesPlayed"
        FROM "User"
        WHERE "name" ILIKE $1
        LIMIT 5
        ''',
        f"%{name}%",
    )

    if not matches:
        return {"status": "not_found", "name": name}

    return {
        "status": "ok",
        "players": [
            {
                "uid": m["uid"],
                "name": m["name"],
                "level": m["level"],
                "crowns": m["crowns"],
                "matches_played": m["matchesPlayed"],
            }
            for m in matches
        ],
    }


# ============================================================
# UPDATE PLAYER DATA  (still sandbox - see module docstring)
# ============================================================

async def update_player_data(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    player_id = context.get("player_id")
    updates = context.get("updates", {})

    if not player_id:
        return {
            "status": "error",
            "message": "player_id is required",
        }

    player = _PLAYERS.get(player_id)

    if player is None:
        return {
            "status": "not_found",
            "player_id": player_id,
        }

    if not isinstance(updates, dict):
        return {
            "status": "error",
            "message": "updates must be an object",
        }

    player.update(updates)

    return {
        "status": "updated",
        "player": dict(player),
    }


PLAYER_TOOLS = (
    Tool(
        name="read_player_data",
        description="Reads a real player's profile and recent match history.",
        required_action="read_player_data",
        risk=ToolRisk.LOW,
        handler=read_player_data,
    ),
    Tool(
        name="update_player_data",
        description="Updates an existing player's data.",
        required_action="update_player_data",
        risk=ToolRisk.MEDIUM,
        handler=update_player_data,
    ),
)


def register_player_tools(tool_registry) -> None:

    for tool in PLAYER_TOOLS:

        if not tool_registry.exists(tool.name):
            tool_registry.register(tool)