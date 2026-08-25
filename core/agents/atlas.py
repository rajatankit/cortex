from __future__ import annotations

from typing import Any

from core.agent import AgentResult, BaseAgent


class AtlasAgent(BaseAgent):
    """
    ATLAS — CORTEX Coding & Engineering Agent.

    ATLAS handles authorized engineering-related operations.

    Important:
    - ATLAS does not directly modify the filesystem.
    - Actual tool execution belongs to ToolGateway.
    - High-risk code modification requires approval.
    """

    agent_id = "ATLAS"
    name = "Atlas"
    role = "Coding & Engineering"

    SUPPORTED_OPERATIONS = {
        "read_code",
        "modify_code",
    }

    async def handle(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:

        context = context or {}

        operation = context.get("operation")

        if not operation:
            return AgentResult(
                success=False,
                agent=self.agent_id,
                message="ATLAS operation is required.",
                data={
                    "task": task,
                    "error": "missing_operation",
                },
            )

        if operation not in self.SUPPORTED_OPERATIONS:
            return AgentResult(
                success=False,
                agent=self.agent_id,
                message=f"Unsupported ATLAS operation: {operation}",
                data={
                    "task": task,
                    "operation": operation,
                    "error": "unsupported_operation",
                },
            )

        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=f"ATLAS accepted operation: {operation}",
            data={
                "task": task,
                "operation": operation,
                "context": context,
            },
        )