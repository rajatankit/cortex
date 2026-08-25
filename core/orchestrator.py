from typing import Any
from core.agent import AgentResult
from core.agent_controller import AgentController
from core.agent_registry import AgentRegistry


class Orchestrator:
    """
    Routes CORTEX tasks through the AgentController.

    The Orchestrator decides WHERE a task goes.
    The AgentController decides WHETHER it may execute.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        controller: AgentController,
    ):
        self.registry = registry
        self.controller = controller

    async def dispatch(
        self,
        agent_id: str,
        action: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:

        agent = self.registry.get(agent_id)

        if agent is None:
            return AgentResult(
                success=False,
                agent=agent_id,
                message=f"Agent '{agent_id}' is not registered.",
            )

        if not agent.enabled:
            return AgentResult(
                success=False,
                agent=agent_id,
                message=f"Agent '{agent_id}' is currently disabled.",
            )

        control_result = await self.controller.execute(
            agent_id=agent_id,
            action=action,
            task=task,
            context=context,
        )

        return AgentResult(
            success=control_result.success,
            agent=agent_id,
            message=control_result.message,
            data={
                "action": action,
                "decision": control_result.decision.value,
            },
        )




