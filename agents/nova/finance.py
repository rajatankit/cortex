from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    user_id: str
    transaction_type: str
    amount: float
    status: str


class NovaFinanceService:
    """
    Sandbox finance service for NOVA.

    This service intentionally uses in-memory data.
    It does NOT connect to real payment providers.
    """

    def __init__(self) -> None:
        self._wallets: dict[str, float] = {
            "user_001": 1000.0,
            "user_002": 500.0,
        }

        self._transactions: dict[str, Transaction] = {
            "TXN001": Transaction(
                transaction_id="TXN001",
                user_id="user_001",
                transaction_type="deposit",
                amount=500.0,
                status="success",
            ),
            "TXN002": Transaction(
                transaction_id="TXN002",
                user_id="user_002",
                transaction_type="withdrawal",
                amount=200.0,
                status="pending",
            ),
        }

    def get_wallet_balance(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return {
                "success": False,
                "error": "user_id is required",
            }

        if user_id not in self._wallets:
            return {
                "success": False,
                "error": f"Unknown user: {user_id}",
            }

        return {
            "success": True,
            "user_id": user_id,
            "balance": self._wallets[user_id],
            "currency": "INR",
        }

    def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        if not transaction_id:
            return {
                "success": False,
                "error": "transaction_id is required",
            }

        transaction = self._transactions.get(transaction_id)

        if transaction is None:
            return {
                "success": False,
                "error": f"Transaction not found: {transaction_id}",
            }

        return {
            "success": True,
            "transaction": {
                "transaction_id": transaction.transaction_id,
                "user_id": transaction.user_id,
                "transaction_type": transaction.transaction_type,
                "amount": transaction.amount,
                "status": transaction.status,
            },
        }

    def validate_transaction(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:
        result = self.get_transaction(transaction_id)

        if not result["success"]:
            return result

        transaction = result["transaction"]

        valid = (
            transaction["amount"] > 0
            and transaction["status"]
            in {"success", "pending", "failed"}
        )

        return {
            "success": True,
            "transaction_id": transaction_id,
            "valid": valid,
            "reason": (
                "Transaction passed validation."
                if valid
                else "Transaction failed validation."
            ),
        }

    def get_deposit_status(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:
        result = self.get_transaction(transaction_id)

        if not result["success"]:
            return result

        transaction = result["transaction"]

        if transaction["transaction_type"] != "deposit":
            return {
                "success": False,
                "error": "Transaction is not a deposit.",
            }

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": transaction["status"],
        }

    def get_withdrawal_status(
        self,
        transaction_id: str,
    ) -> dict[str, Any]:
        result = self.get_transaction(transaction_id)

        if not result["success"]:
            return result

        transaction = result["transaction"]

        if transaction["transaction_type"] != "withdrawal":
            return {
                "success": False,
                "error": "Transaction is not a withdrawal.",
            }

        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": transaction["status"],
        }

    def report_suspicious_transaction(
        self,
        transaction_id: str,
        reason: str,
    ) -> dict[str, Any]:
        if not transaction_id:
            return {
                "success": False,
                "error": "transaction_id is required",
            }

        if not reason:
            return {
                "success": False,
                "error": "reason is required",
            }

        if transaction_id not in self._transactions:
            return {
                "success": False,
                "error": f"Transaction not found: {transaction_id}",
            }

        return {
            "success": True,
            "transaction_id": transaction_id,
            "reported": True,
            "reason": reason,
        }