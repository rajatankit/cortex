"""
CORTEX Notification Tools
Battle Crown notification integration.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict

from .tool import Tool, ToolRisk


BATTLE_CROWN_BRIDGE_URL = os.getenv(
    "BATTLE_CROWN_BRIDGE_URL",
    "http://localhost:3000",
)

BATTLE_CROWN_BRIDGE_TOKEN = os.getenv(
    "BATTLE_CROWN_BRIDGE_TOKEN",
    "",
)


def _normalize_bridge_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Battle Crown's notification bridge returns {"success": true/false, ...}
    without a "status" key. CORTEX's tool contract expects "status".
    Maps based on the bridge's own "action" field so each notification
    action gets the correct status word. Payloads that already carry a
    "status" key (e.g. from the error branches in this file) pass
    through unchanged.
    """
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)

    if "status" in normalized:
        return normalized

    if normalized.get("success") is True:
        status_map = {
            "send_personal_notification": "sent",
            "read_notification_logs": "ok",
            "manage_notifications": "updated",
        }
        normalized["status"] = status_map.get(normalized.get("action"), "ok")
    elif normalized.get("success") is False:
        normalized["status"] = "error"
        if "message" not in normalized and "error" in normalized:
            normalized["message"] = normalized["error"]

    return normalized


async def _call_battle_crown(
    action: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:

    if not BATTLE_CROWN_BRIDGE_TOKEN:
        return {
            "status": "error",
            "message": "BATTLE_CROWN_BRIDGE_TOKEN is not configured",
        }

    payload = json.dumps(
        {
            "action": action,
            "context": context,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{BATTLE_CROWN_BRIDGE_URL}/api/cortex/notifications",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BATTLE_CROWN_BRIDGE_TOKEN}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read().decode("utf-8")

            try:
                return _normalize_bridge_response(json.loads(data))
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "Battle Crown returned invalid JSON",
                    "http_status": response.status,
                    "response_body": data,
                }

    except urllib.error.HTTPError as error:

        try:
            error_body = error.read().decode("utf-8")
        except Exception:
            error_body = ""

        return {
            "status": "error",
            "message": (
                f"HTTP {error.code}: "
                f"{error.reason}"
            ),
            "http_status": error.code,
            "response_body": error_body,
        }

    except urllib.error.URLError as error:

        return {
            "status": "error",
            "message": f"Battle Crown bridge connection failed: {error}",
        }

    except TimeoutError:

        return {
            "status": "error",
            "message": "Battle Crown bridge request timed out",
        }

    except Exception as error:

        return {
            "status": "error",
            "message": str(error),
        }


async def send_notification(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    player_id = context.get("player_id")
    message = context.get("message")
    title = context.get(
        "title",
        "Battle Crown",
    )

    if not player_id:
        return {
            "status": "error",
            "message": "player_id is required",
        }

    if not message:
        return {
            "status": "error",
            "message": "message is required",
        }

    return await _call_battle_crown(
        "send_personal_notification",
        {
            "player_id": player_id,
            "title": title,
            "message": message,
        },
    )


async def manage_notifications(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    return await _call_battle_crown(
        "manage_notifications",
        context,
    )


async def read_notification_logs(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    return await _call_battle_crown(
        "read_notification_logs",
        context,
    )


NOTIFICATION_TOOLS = (
    Tool(
        name="send_notification",
        description=(
            "Sends a personal Battle Crown "
            "notification to a player."
        ),
        required_action="send_notification",
        risk=ToolRisk.MEDIUM,
        handler=send_notification,
    ),
    Tool(
        name="manage_notifications",
        description=(
            "Manages an existing Battle Crown "
            "notification."
        ),
        required_action="manage_notifications",
        risk=ToolRisk.MEDIUM,
        handler=manage_notifications,
    ),
    Tool(
        name="read_notification_logs",
        description=(
            "Reads Battle Crown notification history."
        ),
        required_action="read_notification_logs",
        risk=ToolRisk.LOW,
        handler=read_notification_logs,
    ),
)


def register_notification_tools(
    tool_registry,
) -> None:

    for tool in NOTIFICATION_TOOLS:

        if not tool_registry.exists(tool.name):
            tool_registry.register(tool)