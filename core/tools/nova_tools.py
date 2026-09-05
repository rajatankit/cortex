"""
tools/nova_tools.py

NOVA finance tools for CORTEX.

read_wallet reads REAL data from the Battle Crown "User" table in
Neon Postgres. read_withdrawal_status now ALSO reads real data - when
no transaction_id is given, it lists real pending (or any given
status) rows from "withdrawal_requests", joined with "User" for
email/name. The transaction_id-specific branch below it is still
sandbox/placeholder (kept for backward compatibility until that path
is wired to a real table too).

read_transaction, validate_transaction, read_deposit_status, and
report_suspicious_transaction are still sandbox/placeholder data -
wire those up the same way (see read_wallet / read_withdrawal_status
as the template) once you're ready.

No write/mutation is ever performed here - every query is a SELECT.
"""

from __future__ import annotations

from typing import Any, Dict

from .tool import Tool, ToolRisk
from core.db import fetch, fetchrow


# ============================================================
# SANDBOX DATA (still used by the placeholder tools below)
# ============================================================

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
# READ WALLET  (REAL DATA)
# ============================================================

async def read_wallet(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    # Accept either key: "uid" is what the Next.js voice-command
    # route actually sends (the Firebase UID); "user_id" is kept as
    # a fallback so any other existing caller still works.
    uid = context.get("uid") or context.get("user_id")

    if not uid:
        return {
            "status": "error",
            "message": "uid is required",
        }

    row = await fetchrow(
        '''
        SELECT
            "uid",
            "email",
            "name",
            "depositWallet",
            "winningsWallet"
        FROM "User"
        WHERE "uid" = $1
        ''',
        uid,
    )

    if row is None:
        return {
            "status": "not_found",
            "uid": uid,
        }

    return {
        "status": "ok",
        "wallet": {
            "uid": row["uid"],
            "email": row["email"],
            "name": row["name"],
            "deposit_wallet": row["depositWallet"],
            "winnings_wallet": row["winningsWallet"],
            "total_balance": (
                (row["depositWallet"] or 0)
                + (row["winningsWallet"] or 0)
            ),
            "currency": "INR",
        },
    }


# ============================================================
# READ TRANSACTION  (still sandbox - TODO: wire to wallet_transactions)
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
# VALIDATE TRANSACTION  (still sandbox)
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
# DEPOSIT STATUS  (still sandbox)
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
# WITHDRAWAL STATUS  (REAL DATA when listing by status;
# sandbox fallback preserved for a specific transaction_id lookup)
# ============================================================

async def read_withdrawal_status(
    context: Dict[str, Any],
) -> Dict[str, Any]:

    transaction_id = context.get("transaction_id")
    status = context.get("status")

    if not transaction_id:
        # Real read: list withdrawal_requests by status (default
        # "pending"), joined with User for who it belongs to.
        status_filter = str(status or "pending").strip().lower()

        rows = await fetch(
            '''
            SELECT
                wr."id", wr."amount", wr."upiId", wr."status",
                wr."createdAt", u."email", u."name", u."uid"
            FROM "withdrawal_requests" wr
            LEFT JOIN "User" u ON u."id" = wr."userId"
            WHERE LOWER(wr."status") = $1
            ORDER BY wr."createdAt" DESC
            LIMIT 20
            ''',
            status_filter,
        )

        return {
            "status": "ok",
            "withdrawals": [
                {
                    "id": r["id"],
                    "amount": r["amount"],
                    "upi_id": r["upiId"],
                    "status": r["status"],
                    "created_at": (
                        r["createdAt"].isoformat() if r["createdAt"] else None
                    ),
                    "user_email": r["email"],
                    "user_name": r["name"],
                    "uid": r["uid"],
                }
                for r in rows
            ],
        }

    # Legacy sandbox lookup by a specific placeholder transaction id.
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
# REPORT SUSPICIOUS TRANSACTION  (still sandbox)
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
        description="Reads a user's real wallet balance from Battle Crown.",
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
        description="Reads real pending (or given status) withdrawal requests, or a sandbox one by transaction_id.",
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