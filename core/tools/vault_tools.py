"""
CORTEX VAULT tools.

Protected Battle Crown integration:
- Room credentials  → /api/cortex/rooms
- Tournament create → /api/cortex/tournaments  (Firestore public + Neon secrets)
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Dict

from dotenv import load_dotenv

from .tool import Tool, ToolRisk


load_dotenv()


BATTLE_CROWN_BRIDGE_URL = os.getenv(
    "BATTLE_CROWN_BRIDGE_URL",
    "http://localhost:3000",
).rstrip("/")

BATTLE_CROWN_BRIDGE_TOKEN = os.getenv(
    "BATTLE_CROWN_BRIDGE_TOKEN",
    "",
)


def _normalize_bridge_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Battle Crown bridge returns payload under "data".
    CORTEX room tools historically expect "room".
    Tournament tools keep "data" as-is.
    """
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)

    # Only remap for room-style responses
    action = normalized.get("action") or ""
    if (
        "data" in normalized
        and "room" not in normalized
        and action in {"store_room_data", "read_room_data", "update_room_data"}
    ):
        normalized["room"] = normalized.pop("data")

    return normalized


async def _call_battle_crown(
    path: str,
    action: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    path examples:
      /api/cortex/rooms
      /api/cortex/tournaments
    """

    if not BATTLE_CROWN_BRIDGE_TOKEN:
        return {
            "status": "error",
            "message": "BATTLE_CROWN_BRIDGE_TOKEN is not configured",
        }

    payload = json.dumps({
        "action": action,
        "context": context,
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{BATTLE_CROWN_BRIDGE_URL}{path}",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BATTLE_CROWN_BRIDGE_TOKEN}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read().decode("utf-8")
            return _normalize_bridge_response(json.loads(data))

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }


# ============================================================
# ROOM TOOLS  →  /api/cortex/rooms
# ============================================================

async def read_room_data(context: Dict[str, Any]) -> Dict[str, Any]:
    room_id = context.get("room_id")
    if not room_id:
        return {"status": "error", "message": "room_id is required"}

    return await _call_battle_crown(
        "/api/cortex/rooms",
        "read_room_data",
        {"room_id": room_id},
    )


async def store_room_data(context: Dict[str, Any]) -> Dict[str, Any]:
    room_id = context.get("room_id")
    tournament_id = context.get("tournament_id")
    password = context.get("password")
    game = context.get("game")
    status = context.get("status")
    capacity = context.get("capacity")

    if not room_id:
        return {"status": "error", "message": "room_id is required"}
    if not tournament_id:
        return {"status": "error", "message": "tournament_id is required"}
    if not password:
        return {"status": "error", "message": "password is required"}

    return await _call_battle_crown(
        "/api/cortex/rooms",
        "store_room_data",
        {
            "room_id": room_id,
            "tournament_id": tournament_id,
            "password": password,
            "game": game,
            "status": status,
            "capacity": capacity,
        },
    )


async def update_room_data(context: Dict[str, Any]) -> Dict[str, Any]:
    room_id = context.get("room_id")
    updates = context.get("updates", {})

    if not room_id:
        return {"status": "error", "message": "room_id is required"}
    if not isinstance(updates, dict):
        return {"status": "error", "message": "updates must be a dictionary"}

    return await _call_battle_crown(
        "/api/cortex/rooms",
        "update_room_data",
        {
            "room_id": room_id,
            "updates": updates,
        },
    )


# ============================================================
# TOURNAMENT TOOLS  →  /api/cortex/tournaments
# ============================================================

async def create_tournament(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a public tournament (Firestore) + Neon ops row.
    Optional room_id/password can be set at create time.
    """
    title = context.get("title") or context.get("name")
    if not title:
        # Allow agent to pass a simple default if user only said "tournament banao"
        title = context.get("tournament_title") or "CORTEX Tournament"

    payload = {
        "title": title,
        "game": context.get("game") or "Free Fire",
        "map": context.get("map"),
        "mode": context.get("mode"),
        "status": context.get("status") or "upcoming",
        "capacity": context.get("capacity") or context.get("maxSlots") or 100,
        "entry_fee": context.get("entry_fee") or context.get("entryFee") or "0",
        "first_prize": context.get("first_prize") or context.get("firstPrize"),
        "second_prize": context.get("second_prize") or context.get("secondPrize"),
        "third_prize": context.get("third_prize") or context.get("thirdPrize"),
        "kill_reward": context.get("kill_reward") or context.get("killReward"),
        "room_id": context.get("room_id") or context.get("roomId"),
        "password": context.get("password") or context.get("room_password"),
        "start_time": context.get("start_time") or context.get("startTime"),
    }

    # Drop empty optionals
    payload = {k: v for k, v in payload.items() if v is not None and v != ""}

    result = await _call_battle_crown(
        "/api/cortex/tournaments",
        "create_tournament",
        payload,
    )

    return result


async def get_tournament(context: Dict[str, Any]) -> Dict[str, Any]:
    tournament_id = context.get("tournament_id") or context.get("id")
    firestore_id = context.get("firestore_id")

    if not tournament_id and not firestore_id:
        return {
            "status": "error",
            "message": "tournament_id or firestore_id is required",
        }

    return await _call_battle_crown(
        "/api/cortex/tournaments",
        "get_tournament",
        {
            "tournament_id": tournament_id,
            "firestore_id": firestore_id,
        },
    )


# ============================================================
# REGISTRY
# ============================================================

VAULT_TOOLS = (
    Tool(
        name="store_room_data",
        description="Stores protected Battle Crown room data on an existing tournament.",
        required_action="store_room_data",
        risk=ToolRisk.HIGH,
        handler=store_room_data,
    ),
    Tool(
        name="read_room_data",
        description="Reads protected Battle Crown room data.",
        required_action="read_room_data",
        risk=ToolRisk.MEDIUM,
        handler=read_room_data,
    ),
    Tool(
        name="update_room_data",
        description="Updates protected Battle Crown room data.",
        required_action="update_room_data",
        risk=ToolRisk.HIGH,
        handler=update_room_data,
    ),
    Tool(
        name="create_tournament",
        description=(
            "Creates a new Battle Crown tournament. "
            "Use when the user asks to create/start a tournament or match. "
            "Writes to website list (Firestore) and secure DB (Neon)."
        ),
        required_action="create_tournament",
        risk=ToolRisk.HIGH,
        handler=create_tournament,
    ),
    Tool(
        name="get_tournament",
        description="Reads a Battle Crown tournament by tournament_id or firestore_id.",
        required_action="get_tournament",
        risk=ToolRisk.MEDIUM,
        handler=get_tournament,
    ),
)


def register_vault_tools(tool_registry) -> None:
    for tool in VAULT_TOOLS:
        if not tool_registry.exists(tool.name):
            tool_registry.register(tool)