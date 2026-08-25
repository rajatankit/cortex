from dataclasses import dataclass

from core.agent_controller import AgentController


@dataclass(frozen=True)
class RouteResult:
    success: bool
    agent_id: str
    action: str
    message: str


class ActionRouter:
    """
    Routes incoming CORTEX requests to the correct agent.
    """

    def __init__(self, controller: AgentController):
        self.controller = controller

    async def route(
        self,
        agent_id: str,
        action: str,
        task: str,
        context: dict | None = None,
    ) -> RouteResult:

        result = await self.controller.execute(
            agent_id=agent_id,
            action=action,
            task=task,
            context=context,
        )

        return RouteResult(
            success=result.success,
            agent_id=result.agent_id,
            action=result.action,
            message=result.message,
        )




