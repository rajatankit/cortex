from typing import Any
from core.agent import AgentResult, BaseAgent


class ElaraAgent(BaseAgent):
    """
    ELARA — CORTEX Player Information Agent.

    Handles player-information tasks explicitly
    routed through the CORTEX control layer.
    """

    agent_id = "ELARA"
    name = "Elara"
    role = "Player Information"

    async def handle(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:

        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=f"ELARA handled: {task}",
            data=context or {},
        )




