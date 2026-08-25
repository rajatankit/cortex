from __future__ import annotations

from typing import Any

from core.agent import AgentResult, BaseAgent

from .finance import NovaFinanceService


class NovaAgent(BaseAgent):
    """
    NOVA — CORTEX Finance / Wallet specialist.

    NOVA performs sandbox finance operations only.
    Authorization is handled by CORTEX's existing control layer.
    """

    agent_id = "NOVA"
    name = "NOVA"
    role = "Finance / Wallet Operations"

    ALLOWED_OPERATIONS = {
        "get_wallet_balance",
        "get_transaction",
        "validate_transaction",
        "get_deposit_status",
        "get_withdrawal_status",
        "report_suspicious_transaction",
    }

    def __init__(
        self,
        finance_service: NovaFinanceService | None = None,
    ) -> None:
        super().__init__()
        self.finance = finance_service or NovaFinanceService()

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
            )

        if operation not in self.ALLOWED_OPERATIONS:
            return AgentResult(
                success=False,
                agent=self.agent_id,
                message=f"Unsupported NOVA operation: {operation}",
            )

        try:
            if operation == "get_wallet_balance":
                result = self.finance.get_wallet_balance(
                    context.get("user_id", "")
                )

            elif operation == "get_transaction":
                result = self.finance.get_transaction(
                    context.get("transaction_id", "")
                )

            elif operation == "validate_transaction":
                result = self.finance.validate_transaction(
                    context.get("transaction_id", "")
                )

            elif operation == "get_deposit_status":
                result = self.finance.get_deposit_status(
                    context.get("transaction_id", "")
                )

            elif operation == "get_withdrawal_status":
                result = self.finance.get_withdrawal_status(
                    context.get("transaction_id", "")
                )

            elif operation == "report_suspicious_transaction":
                result = self.finance.report_suspicious_transaction(
                    context.get("transaction_id", ""),
                    context.get("reason", ""),
                )

            else:
                return AgentResult(
                    success=False,
                    agent=self.agent_id,
                    message=f"Unsupported NOVA operation: {operation}",
                )

        except Exception as exc:
            return AgentResult(
                success=False,
                agent=self.agent_id,
                message=f"NOVA operation failed: {exc}",
            )

        return AgentResult(
            success=bool(result.get("success")),
            agent=self.agent_id,
            message=(
                "NOVA operation completed successfully."
                if result.get("success")
                else result.get("error", "NOVA operation failed.")
            ),
            data=result,
        )