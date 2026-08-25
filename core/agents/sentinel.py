from __future__ import annotations

from typing import Any

from core.agent import AgentResult, BaseAgent


class SentinelAgent(BaseAgent):
    """
    SENTINEL — CORTEX Security Guardian.

    SENTINEL handles security-related operations that are
    explicitly authorized by the CORTEX control layer.

    Important:
    - SENTINEL does not bypass the security pipeline.
    - Tool execution belongs to ToolGateway.
    - High/critical-risk operations must be controlled by
      PermissionEngine, DecisionEngine and ApprovalGate.
    """

    agent_id = "SENTINEL"
    name = "Sentinel"
    role = "Security Guardian"

    SUPPORTED_OPERATIONS = {
        "read_security_logs",
        "security_scan",
        "security_action",
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
                message="SENTINEL operation is required.",
                data={
                    "task": task,
                    "error": "missing_operation",
                },
            )

        if operation not in self.SUPPORTED_OPERATIONS:
            return AgentResult(
                success=False,
                agent=self.agent_id,
                message=(
                    f"Unsupported SENTINEL operation: "
                    f"{operation}"
                ),
                data={
                    "task": task,
                    "operation": operation,
                    "error": "unsupported_operation",
                },
            )

        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=(
                f"SENTINEL accepted operation: "
                f"{operation}"
            ),
            data={
                "task": task,
                "operation": operation,
                "context": context,
            },
        )