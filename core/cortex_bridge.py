from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from core.cortex_bootstrap import bootstrap_cortex, CortexBootstrapError


# ============================================================
# CORTEX BRIDGE
# ============================================================

app = FastAPI(
    title="CORTEX Bridge",
    version="1.0.0",
)


# ============================================================
# AUTHENTICATION
# ============================================================

BRIDGE_TOKEN = os.getenv("CORTEX_BRIDGE_TOKEN")

if not BRIDGE_TOKEN:
    raise RuntimeError(
        "CORTEX_BRIDGE_TOKEN environment variable is not set."
    )


def verify_bridge_token(
    authorization: str | None,
) -> None:

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header.",
        )

    expected = f"Bearer {BRIDGE_TOKEN}"

    if authorization != expected:
        raise HTTPException(
            status_code=403,
            detail="Invalid CORTEX bridge token.",
        )


# ============================================================
# REQUEST MODELS
# ============================================================

class DispatchRequest(BaseModel):
    task: str = Field(min_length=1)
    agent_id: str | None = None
    action: str | None = None
    tool_name: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# CORTEX RUNTIME
# ============================================================

try:
    cortex = bootstrap_cortex()
except CortexBootstrapError as exc:
    raise RuntimeError(
        f"CORTEX bootstrap failed: {exc}"
    ) from exc


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "success": True,
        "service": "CORTEX",
        "status": "healthy",
        "health": cortex.health_report.summary(),
    }


# ============================================================
# DISPATCH
# ============================================================

@app.post("/dispatch")
async def dispatch(
    request: DispatchRequest,
    authorization: str | None = Header(default=None),
):
    verify_bridge_token(authorization)

    if request.tool_name:
        if not request.agent_id:
            raise HTTPException(
                status_code=400,
                detail="agent_id is required when tool_name is provided.",
            )

        result = await cortex.tool_gateway.execute(
            agent_id=request.agent_id,
            tool_name=request.tool_name,
            task=request.task,
            context=request.context,
        )

        return {
            "success": result.success,
            "agent": result.agent_id,
            "message": result.message,
            "data": result.data,
        }

    if request.agent_id and request.action:
        result = await cortex.orchestrator.dispatch(
            agent_id=request.agent_id,
            action=request.action,
            task=request.task,
            context=request.context,
        )

        return {
            "success": result.success,
            "agent": result.agent,
            "message": result.message,
            "data": result.data,
        }

    # NATURAL-LANGUAGE FALLBACK: no agent_id/action given (e.g. the
    # phone/voice command center) - route through the full
    # IntentEngine -> TaskPlanner -> ToolGateway pipeline exactly
    # like every other CORTEX entrypoint.
    result = await cortex.execute_intent(request.task, context=request.context)

    return {
        "success": result.success,
        "agent": result.agent_id,
        "message": result.message,
        "data": result.data,
    }


# ============================================================
# CORTEX STATUS
# ============================================================

@app.get("/status")
async def status(
    authorization: str | None = Header(default=None),
):
    verify_bridge_token(authorization)

    return {
        "success": True,
        "agents": [
            agent.info() if hasattr(agent, "info") else agent
            for agent in cortex.agent_registry.list_agents()
        ],
        "tool_count": cortex.tool_registry.count(),
        "health": cortex.health_report.summary(),
    }


    # ============================================================
    # APPROVAL REQUEST MODEL
    # ============================================================

class ApproveRequest(BaseModel):
    request_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)


# ============================================================
# LIST PENDING APPROVALS
# ============================================================

@app.get("/approvals")
async def list_pending_approvals(
    authorization: str | None = Header(default=None),
):
    verify_bridge_token(authorization)

    pending = cortex.pending_approvals()

    return {
        "success": True,
        "pending": [
            {
                "request_id": request.request_id,
                "agent_id": request.agent_id,
                "action": request.action,
                "task": request.task,
                "status": request.status.value,
                "created_at": request.created_at,
                "expires_at": request.expires_at,
            }
            for request in pending
        ],
    }


# ============================================================
# APPROVE + EXECUTE
# ============================================================

@app.post("/approve")
async def approve(
    request: ApproveRequest,
    authorization: str | None = Header(default=None),
):
    verify_bridge_token(authorization)

    existing = cortex.get_approval(request.request_id)

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Approval request not found: {request.request_id}",
        )

    if existing.status.value == "pending":
        try:
            cortex.approve_request(request.request_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    result = await cortex.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id=request.agent_id,
    )

    return {
        "success": result.success,
        "agent": result.agent_id,
        "message": result.message,
        "data": result.data,
    }


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "core.cortex_bridge:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )

