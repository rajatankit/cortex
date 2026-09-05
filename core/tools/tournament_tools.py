"""
tools/tournament_tools.py

Modular tool definitions for ARIA (Tournament Management).

read_tournament reads REAL data from Battle Crown's "tournaments"
table in Neon Postgres. roomId/roomPassword are deliberately NEVER
returned here - room credentials are protected data and belong to
VAULT's read_room_data flow only (see tools/vault_tools.py).

create_tournament calls Battle Crown hybrid bridge:
  POST /api/cortex/tournaments
  → Firestore (website list) + Neon (ops row, optional room secrets)

manage_tournament is still an in-memory sandbox placeholder.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict

from dotenv import load_dotenv

from .tool import Tool, ToolRisk
from core.db import fetch, fetchrow

load_dotenv()

BATTLE_CROWN_BRIDGE_URL = os.getenv(
    "BATTLE_CROWN_BRIDGE_URL",
    "http://localhost:3000",
).rstrip("/")

BATTLE_CROWN_BRIDGE_TOKEN = os.getenv(
    "BATTLE_CROWN_BRIDGE_TOKEN",
    "",
)

# Placeholder in-memory store - still used by manage_tournament below.
_TOURNAMENTS: Dict[str, Dict[str, Any]] = {
    "T1": {
        "id": "T1",
        "name": "Summer Cup",
        "time": "19:00",
        "status": "scheduled",
    },
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


def _call_create_tournament_bridge(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls Battle Crown hybrid API:
    Firestore (public list) + Neon (ops + optional room secrets).
    """
    if not BATTLE_CROWN_BRIDGE_TOKEN:
        return {
            "status": "error",
            "message": "BATTLE_CROWN_BRIDGE_TOKEN is not configured",
        }

    title = (
        context.get("tournament_name")
        or context.get("title")
        or context.get("name")
    )

    if not title:
        return {
            "status": "error",
            "message": "tournament_name (title) is required",
        }

    bridge_context = {
        "title": title,
        "game": context.get("game") or "Free Fire",
        "map": context.get("map"),
        "mode": context.get("mode"),
        "status": context.get("status") or "upcoming",
        "capacity": context.get("maxSlots")
        or context.get("capacity")
        or 100,
        "entry_fee": context.get("entryFee")
        or context.get("entry_fee")
        or "0",
        "first_prize": context.get("firstPrize")
        or context.get("first_prize")
        or 0,
        "second_prize": context.get("secondPrize")
        or context.get("second_prize")
        or 0,
        "third_prize": context.get("thirdPrize")
        or context.get("third_prize")
        or 0,
        "kill_reward": context.get("killReward")
        or context.get("kill_reward")
        or 5,
        "room_id": context.get("room_id") or context.get("roomId"),
        "password": context.get("password")
        or context.get("room_password")
        or context.get("roomPassword"),
        "start_time": context.get("start_time")
        or context.get("startTime")
        or context.get("date")
        or context.get("time"),
    }

    # Drop empty values
    bridge_context = {
        k: v
        for k, v in bridge_context.items()
        if v is not None and v != ""
    }

    payload = json.dumps({
        "action": "create_tournament",
        "context": bridge_context,
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{BATTLE_CROWN_BRIDGE_URL}/api/cortex/tournaments",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BATTLE_CROWN_BRIDGE_TOKEN}",
        },
        method="POST",
    )

    # ---- DEBUG: log exactly what we're sending, before the call ----
    print(f"[TOURNAMENT DEBUG] POST {BATTLE_CROWN_BRIDGE_URL}/api/cortex/tournaments")
    print(f"[TOURNAMENT DEBUG] bridge_context={bridge_context}")
    print(f"[TOURNAMENT DEBUG] token_configured={bool(BATTLE_CROWN_BRIDGE_TOKEN)}")

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read().decode("utf-8")
            parsed = json.loads(data)
            print(f"[TOURNAMENT DEBUG] bridge HTTP {response.status} response={parsed}")
            return parsed
    except Exception as error:
        # This branch also catches HTTPError (4xx/5xx from Next.js),
        # which normally carries the real error body - surface it.
        error_body = None
        try:
            error_body = error.read().decode("utf-8")
        except Exception:
            pass
        print(f"[TOURNAMENT DEBUG] bridge call FAILED: {error} body={error_body}")
        return {
            "status": "error",
            "message": str(error),
            "response_body": error_body,
        }


async def create_tournament(context: Dict[str, Any]) -> Dict[str, Any]:
    print(f"[TOURNAMENT DEBUG] create_tournament called with context={context}")
    result = _call_create_tournament_bridge(context)
    print(f"[TOURNAMENT DEBUG] final result={result}")

    # Normalize bridge response for CORTEX / speech layer
    if result.get("status") == "created":
        data = result.get("data") or {}
        return {
            "status": "created",
            "message": result.get("message")
            or "Tournament created successfully",
            "tournament": {
                "tournament_id": data.get("tournament_id"),
                "firestore_id": data.get("firestore_id"),
                "title": data.get("title"),
                "game": data.get("game"),
                "status": data.get("status"),
                "capacity": data.get("capacity"),
                "room_id": data.get("room_id"),
                # password not spoken / not required in public reply
            },
        }

    return {
        "status": result.get("status") or "error",
        "message": result.get("message") or "Tournament create failed",
        "raw": result,
    }


async def manage_tournament(context: Dict[str, Any]) -> Dict[str, Any]:
    tournament_id = context.get("tournament_id")
    updates = context.get("updates", {})

    if not tournament_id:
        return {"status": "error", "message": "tournament_id is required"}

    tournament = _TOURNAMENTS.get(tournament_id)
    if tournament is None:
        return {"status": "not_found", "tournament_id": tournament_id}

    tournament.update(updates)
    return {"status": "updated", "tournament": dict(tournament)}


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
        description=(
            "Creates a new Battle Crown tournament on the website and database. "
            "Use when the user asks to create a tournament, match, or cup "
            "(e.g. 'tournament bana do', 'naya tournament create karo')."
        ),
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