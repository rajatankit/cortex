"""
tools/nova_tools.py

NOVA finance tools for CORTEX.

Development/test implementation only.

No real-money transaction is performed.
No external payment provider is contacted.
"""

from __future__ import annotations

from typing import Any, Dict

from .tool import Tool, ToolRisk


# ============================================================
# SANDBOX DATA
# ============================================================

_WALLETS: Dict[str, Dict[str, Any]] = {
    "U1": {
        "user_id": "U1",
        "balance": 1000.0,
        "currency": "INR",
    },
    "U2": {
        "user_id": "U2",
        "balance": 500.0,
        "currency": "INR",
    },
}


_TRANSACTIONS: Dict[str, Dict[str, Any]] = {
    "TXN1": {
        "transaction_id": "TXN1",
        "user_id": "U1",
        "type": "deposit",
        "amount": 500.0,
        "status": "success",
    },
    "TXN2": {
        "transaction_id": "TXN2",
        "user_id": "U2",
        "type": "withdrawal",
        "amount": 200.0,
        "status": "pending",
    },
}


# ============================================================
# READ WALLET
# ============================================================

async def read_wallet(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    user_id = context.get("user_id")

    if not user_id:
        return {
            "status": "error",
            "message": "user_id is required",
        }

    wallet = _WALLETS.get(user_id)

    if wallet is None:
        return {
            "status": "not_found",
            "user_id": user_id,
        }

    return {
        "status": "ok",
        "wallet": dict(wallet),
    }


# ============================================================
# READ TRANSACTION
# ============================================================

async def read_transaction(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    transaction_id = context.get("transaction_id")

    if not transaction_id:
        return {
            "status": "error",
            "message": "transaction_id is required",
        }

    transaction = _TRANSACTIONS.get(transaction_id)

    if transaction is None:
        return {
            "status": "not_found",
            "transaction_id": transaction_id,
        }

    return {
        "status": "ok",
        "transaction": dict(transaction),
    }


# ============================================================
# VALIDATE TRANSACTION
# ============================================================

async def validate_transaction(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    transaction_id = context.get("transaction_id")

    if not transaction_id:
        return {
            "status": "error",
            "message": "transaction_id is required",
        }

    transaction = _TRANSACTIONS.get(transaction_id)

    if transaction is None:
        return {
            "status": "not_found",
            "transaction_id": transaction_id,
        }

    amount = transaction.get("amount", 0)
    status = transaction.get("status")

    valid_statuses = {
        "pending",
        "success",
        "failed",
        "cancelled",
    }

    valid = (
        isinstance(amount, (int, float))
        and amount > 0
        and status in valid_statuses
    )

    return {
        "status": "valid" if valid else "invalid",
        "transaction_id": transaction_id,
        "valid": valid,
    }


# ============================================================
# DEPOSIT STATUS
# ============================================================

async def read_deposit_status(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    transaction_id = context.get("transaction_id")

    if not transaction_id:
        return {
            "status": "error",
            "message": "transaction_id is required",
        }

    transaction = _TRANSACTIONS.get(transaction_id)

    if transaction is None:
        return {
            "status": "not_found",
            "transaction_id": transaction_id,
        }

    if transaction.get("type") != "deposit":
        return {
            "status": "error",
            "message": "Transaction is not a deposit.",
            "transaction_id": transaction_id,
        }

    return {
        "status": "ok",
        "transaction_id": transaction_id,
        "deposit_status": transaction.get("status"),
    }


# ============================================================
# WITHDRAWAL STATUS
# ============================================================

async def read_withdrawal_status(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    transaction_id = context.get("transaction_id")

    if not transaction_id:
        return {
            "status": "error",
            "message": "transaction_id is required",
        }

    transaction = _TRANSACTIONS.get(transaction_id)

    if transaction is None:
        return {
            "status": "not_found",
            "transaction_id": transaction_id,
        }

    if transaction.get("type") != "withdrawal":
        return {
            "status": "error",
            "message": "Transaction is not a withdrawal.",
            "transaction_id": transaction_id,
        }

    return {
        "status": "ok",
        "transaction_id": transaction_id,
        "withdrawal_status": transaction.get("status"),
    }


# ============================================================
# REPORT SUSPICIOUS TRANSACTION
# ============================================================

async def report_suspicious_transaction(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    transaction_id = context.get("transaction_id")
    reason = context.get("reason")

    if not transaction_id:
        return {
            "status": "error",
            "message": "transaction_id is required",
        }

    if not reason:
        return {
            "status": "error",
            "message": "reason is required",
        }

    if transaction_id not in _TRANSACTIONS:
        return {
            "status": "not_found",
            "transaction_id": transaction_id,
        }

    return {
        "status": "reported",
        "transaction_id": transaction_id,
        "reason": reason,
    }


# ============================================================
# TOOL DEFINITIONS
# ============================================================

NOVA_TOOLS = (
    Tool(
        name="read_wallet",
        description="Reads a user's sandbox wallet balance.",
        required_action="read_wallet",
        risk=ToolRisk.LOW,
        handler=read_wallet,
    ),

    Tool(
        name="read_transaction",
        description="Reads a sandbox transaction.",
        required_action="read_transaction",
        risk=ToolRisk.LOW,
        handler=read_transaction,
    ),

    Tool(
        name="validate_transaction",
        description="Validates a sandbox transaction.",
        required_action="validate_transaction",
        risk=ToolRisk.MEDIUM,
        handler=validate_transaction,
    ),

    Tool(
        name="read_deposit_status",
        description="Reads the status of a sandbox deposit.",
        required_action="read_deposit_status",
        risk=ToolRisk.LOW,
        handler=read_deposit_status,
    ),

    Tool(
        name="read_withdrawal_status",
        description="Reads the status of a sandbox withdrawal.",
        required_action="read_withdrawal_status",
        risk=ToolRisk.LOW,
        handler=read_withdrawal_status,
    ),

    Tool(
        name="report_suspicious_transaction",
        description="Reports a suspicious sandbox transaction.",
        required_action="report_suspicious_transaction",
        risk=ToolRisk.HIGH,
        handler=report_suspicious_transaction,
    ),
)


# ============================================================
# REGISTRATION
# ============================================================

def register_nova_tools(tool_registry) -> None:
    for tool in NOVA_TOOLS:
        if not tool_registry.exists(tool.name):
            tool_registry.register(tool)