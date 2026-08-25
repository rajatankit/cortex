from core.agent_config import AGENT_CONFIGS
from core.permissions import PermissionEngine


class PermissionLoader:
    """
    Loads permissions from centralized agent configuration.
    """

    def __init__(self, permission_engine: PermissionEngine):
        self.permission_engine = permission_engine

    def load(self) -> None:
        for agent_config in AGENT_CONFIGS:

            for action, risk in agent_config.actions:

                self.permission_engine.grant(
                    agent_id=agent_config.agent_id,
                    action=action,
                    risk=risk,
                )
