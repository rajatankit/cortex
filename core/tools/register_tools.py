"""
tools/register_tools.py

Centralized tool registration for CORTEX. Calls each domain-specific
registration function so bootstrap only needs a single import/call.
Individual registration functions already guard against duplicate
registration via tool_registry.exists(), so this simply delegates.

RECONSTRUCTED from confirmed real tool files (tournament_tools.py,
player_tools.py, notification_tools.py, vault_tools.py,
match_tools.py, nova_tools.py, atlas_tools.py, sentinel_tools.py)
and cross-checked against cortex_bootstrap.py's
tool_registry.count() == 24 health check:

    tournament(3) + player(2) + notification(3) + vault(3)
    + match(2) + nova(6) + atlas(2) + sentinel(3) = 24  [OK]

VERIFY this against your actual file before trusting it blindly -
this was reconstructed, not read directly from your repo.
"""

from __future__ import annotations

from .tournament_tools import register_tournament_tools
from .player_tools import register_player_tools
from .notification_tools import register_notification_tools
from .vault_tools import register_vault_tools
from .match_tools import register_match_tools
from .nova_tools import register_nova_tools
from .atlas_tools import register_atlas_tools
from .sentinel_tools import register_sentinel_tools


def register_all_tools(tool_registry) -> None:
    register_tournament_tools(tool_registry)
    register_player_tools(tool_registry)
    register_notification_tools(tool_registry)
    register_vault_tools(tool_registry)
    register_match_tools(tool_registry)
    register_nova_tools(tool_registry)
    register_atlas_tools(tool_registry)
    register_sentinel_tools(tool_registry)