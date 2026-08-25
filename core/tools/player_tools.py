"""
tools/player_tools.py

ELARA player-information tools.
"""

from __future__ import annotations

from typing import Any, Dict

from .tool import Tool, ToolRisk


_PLAYERS: Dict[str, Dict[str, Any]] = {
    "P1": {
        "id": "P1",
        "name": "Rajat",
        "rank": "Gold",
        "wins": 12,
        "losses": 4,
    },
}


async def read_player_data(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    player_id = context.get("player_id")

    if player_id:
        player = _PLAYERS.get(player_id)

        if player is None:
            return {
                "status": "not_found",
                "player_id": player_id,
            }

        return {
            "status": "ok",
            "player": dict(player),
        }

    return {
        "status": "ok",
        "players": [
            dict(player)
            for player in _PLAYERS.values()
        ],
    }


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
        description="Reads one or all players' data.",
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
