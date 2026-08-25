from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Permission:
    agent_id: str
    action: str
    risk: RiskLevel


class PermissionEngine:
    """
    Controls which actions each CORTEX agent is allowed to request.
    """

    def __init__(self):
        self._permissions: set[Permission] = set()

    def grant(
        self,
        agent_id: str,
        action: str,
        risk: RiskLevel = RiskLevel.LOW,
    ) -> None:
        self._permissions.add(
            Permission(
                agent_id=agent_id,
                action=action,
                risk=risk,
            )
        )

    def revoke(
        self,
        agent_id: str,
        action: str,
    ) -> bool:
        """
        Remove a specific permission.

        Returns:
            True  -> permission was removed
            False -> permission did not exist
        """

        permission_to_remove = None

        for permission in self._permissions:
            if (
                permission.agent_id == agent_id
                and permission.action == action
            ):
                permission_to_remove = permission
                break

        if permission_to_remove is None:
            return False

        self._permissions.remove(permission_to_remove)
        return True

    def is_allowed(
        self,
        agent_id: str,
        action: str,
    ) -> bool:
        return any(
            permission.agent_id == agent_id
            and permission.action == action
            for permission in self._permissions
        )

    def get_risk(
        self,
        agent_id: str,
        action: str,
    ) -> RiskLevel | None:
        for permission in self._permissions:
            if (
                permission.agent_id == agent_id
                and permission.action == action
            ):
                return permission.risk

        return None




