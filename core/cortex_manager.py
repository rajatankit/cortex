from dataclasses import dataclass

from core.agent_registry import AgentRegistry
from core.orchestrator import Orchestrator


@dataclass(frozen=True)
class RoutingDecision:
    agent_id: str
    reason: str


class CortexManager:
    """
    CORTEX leader / manager layer.

    Determines which specialist agent should receive
    a task and then dispatches it through the Orchestrator.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        orchestrator: Orchestrator,
    ):
        self.registry = registry
        self.orchestrator = orchestrator

    def route(self, task: str) -> RoutingDecision:
        """
        Determine which specialist agent should handle a task.
        """

        text = task.lower()

        # ARIA — Tournament Management
        if any(
            word in text
            for word in (
                "tournament",
                "room",
                "entry",
                "prize pool",
            )
        ):
            return RoutingDecision(
                agent_id="ARIA",
                reason="Tournament-related task",
            )

        # ELARA — Player Information
        if any(
            word in text
            for word in (
                "player",
                "profile",
                "uid",
                "ign",
            )
        ):
            return RoutingDecision(
                agent_id="ELARA",
                reason="Player-information task",
            )

        # VAULT — Notification Management
        if any(
            word in text
            for word in (
                "notification logs",
                "notification queue",
                "notification management",
                "manage notification",
            )
        ):
            return RoutingDecision(
                agent_id="VAULT",
                reason="Notification-management task",
            )

        # LYRA — Notifications
        if any(
            word in text
            for word in (
                "notification",
                "notify",
                "alert",
            )
        ):
            return RoutingDecision(
                agent_id="LYRA",
                reason="Notification task",
            )

        # ORION — Match Operations
        if any(
            word in text
            for word in (
                "match",
                "room id",
                "match result",
            )
        ):
            return RoutingDecision(
                agent_id="ORION",
                reason="Match-operation task",
            )

        # NOVA — Finance
        if any(
            word in text
            for word in (
                "money",
                "finance",
                "wallet",
                "withdraw",
                "deposit",
                "payment",
            )
        ):
            return RoutingDecision(
                agent_id="NOVA",
                reason="Finance-related task",
            )

        # ATLAS — Coding & Engineering
        if any(
            word in text
            for word in (
                "code",
                "bug",
                "program",
                "developer",
            )
        ):
            return RoutingDecision(
                agent_id="ATLAS",
                reason="Coding-related task",
            )

        # SENTINEL — Security
        if any(
            word in text
            for word in (
                "security",
                "attack",
                "threat",
                "scan",
                "suspicious",
            )
        ):
            return RoutingDecision(
                agent_id="SENTINEL",
                reason="Security-related task",
            )

        # Safe fallback
        return RoutingDecision(
            agent_id="SENTINEL",
            reason="No specialist matched; security review fallback",
        )

    async def dispatch(
        self,
        task: str,
        action: str,
        context: dict | None = None,
    ):
        """
        Route the task through CORTEX and execute it
        using the appropriate specialist agent.
        """

        routing = self.route(task)

        result = await self.orchestrator.dispatch(
            agent_id=routing.agent_id,
            action=action,
            task=task,
            context=context,
        )

        return routing, result




