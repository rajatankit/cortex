from typing import Any
from core.agent import AgentResult, BaseAgent


class OrionAgent(BaseAgent):
    """
    ORION — CORTEX Match Operations Agent.

    Handles match-operation tasks that are explicitly
    routed to ORION by the CORTEX control layer.
    """

    agent_id = "ORION"
    name = "Orion"
    role = "Match Operations"

    async def handle(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:

        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=f"ORION handled: {task}",
            data=context or {},
        )
