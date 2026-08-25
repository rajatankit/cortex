from __future__ import annotations

from typing import Any

from core.agent import AgentResult, BaseAgent


class NovaAgent(BaseAgent):
    """
    NOVA — CORTEX Finance Agent.

    NOVA handles finance-related tasks that are explicitly
    authorized by the CORTEX control layer.

    Important:
    - No real-money operations are performed here.
    - No payment provider is contacted.
    - Actual tool execution belongs to ToolGateway.
    """

    agent_id = "NOVA"
    name = "Nova"
    role = "Finance"

    SUPPORTED_OPERATIONS = {
        "read_wallet",
        "read_transaction",
        "validate_transaction",
        "read_deposit_status",
        "read_withdrawal_status",
        "report_suspicious_transaction",
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
                message="NOVA operation is required.",
                data={
                    "task": task,
                    "error": "missing_operation",
                },
            )

        if operation not in self.SUPPORTED_OPERATIONS:
            return AgentResult(
                success=False,
                agent=self.agent_id,
                message=f"Unsupported NOVA operation: {operation}",
                data={
                    "task": task,
                    "operation": operation,
                    "error": "unsupported_operation",
                },
            )

        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=f"NOVA accepted operation: {operation}",
            data={
                "task": task,
                "operation": operation,
                "context": context,
            },
        )