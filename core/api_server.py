"""
core/api_server.py

Minimal HTTP server exposing CORTEX's execute_intent()/execute_tool()
pipeline over the network, so external clients (e.g. the "Personal AI"
Next.js page) can dispatch commands.

SECURITY:
- Every request must carry Authorization: Bearer <CORTEX_BRIDGE_TOKEN>
  (a NEW, separate secret from BATTLE_CROWN_BRIDGE_TOKEN - do not
  reuse that one here, they protect opposite directions).
- This server does NOT bypass PermissionEngine/DecisionEngine/
  ApprovalGate. High-risk actions still come back with
  decision="review" and a request_id; this server never
  auto-approves anything.
- CORTEX_BRIDGE_TOKEN must be a long random secret, never committed
  to source control.

RUN (local dev, from the Cortex project root):
    .venv\\Scripts\\python.exe -m uvicorn core.api_server:app --host 0.0.0.0 --port 8000

This server is NOT internet-reachable by itself. For a Vercel-deployed
frontend to reach it, you need either:
  - a tunnel (e.g. `cloudflared tunnel --url http://localhost:8000`,
    or ngrok) pointed at this server while your PC is on, or
  - deploying this FastAPI app somewhere with a public URL.
Set CORTEX_BRIDGE_URL on the Vercel side to whatever public URL you
end up using, and CORTEX_BRIDGE_TOKEN to match this server's token.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.cortex_bootstrap import bootstrap_cortex

CORTEX_BRIDGE_TOKEN = os.getenv("CORTEX_BRIDGE_TOKEN", "")

if not CORTEX_BRIDGE_TOKEN:
    raise RuntimeError(
        "CORTEX_BRIDGE_TOKEN environment variable is not set. "
        "Set it to a long random secret before starting this server."
    )

app = FastAPI(title="CORTEX Bridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORTEX_ALLOWED_ORIGIN", "*").split(","),
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

# Built once at process startup - reused across requests so audit
# events, approval state, and in-memory tool stores persist for the
# lifetime of this server (same as any long-running deployment).
runtime = bootstrap_cortex()


class DispatchRequest(BaseModel):
    task: str
    agent_id: str | None = None
    action: str | None = None
    context: dict[str, Any] | None = None


def _check_auth(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")

    token = authorization[len("Bearer "):]

    if token != CORTEX_BRIDGE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid bridge token.")


@app.post("/dispatch")
async def dispatch(
    body: DispatchRequest,
    authorization: str | None = Header(default=None),
):
    _check_auth(authorization)

    if not body.task or not body.task.strip():
        raise HTTPException(status_code=400, detail="task is required.")

    context = body.context or {}

    if body.agent_id and body.action:
        # Explicit agent/action dispatch (existing callers, e.g.
        # Battle Crown's ARIA tournament-read integration).
        result = await runtime.execute_tool(
            agent_id=body.agent_id,
            tool_name=body.action,
            task=body.task,
            context=context,
        )
    else:
        # Natural-language dispatch (voice/text commands) - routed
        # through IntentEngine -> TaskPlanner -> ToolGateway exactly
        # like every other CORTEX entrypoint.
        result = await runtime.execute_intent(body.task, context=context)

    return {
        "success": result.success,
        "agent_id": result.agent_id,
        "message": result.message,
        "data": result.data,
    }


@app.get("/health")
async def health():
    return {
        "healthy": runtime.health_report.is_healthy(),
        "summary": runtime.health_report.summary(),
    }


# ============================================================
# APPROVAL REQUEST MODEL
# ============================================================

class ApproveRequest(BaseModel):
    request_id: str
    agent_id: str


# ============================================================
# LIST PENDING APPROVALS
# ============================================================

@app.get("/approvals")
async def list_pending_approvals(
    authorization: str | None = Header(default=None),
):
    _check_auth(authorization)

    pending = runtime.pending_approvals()

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
    body: ApproveRequest,
    authorization: str | None = Header(default=None),
):
    _check_auth(authorization)

    existing = runtime.get_approval(body.request_id)

    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Approval request not found: {body.request_id}",
        )

    if existing.status.value == "pending":
        try:
            runtime.approve_request(body.request_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    result = await runtime.tool_gateway.approve_and_execute(
        request_id=body.request_id,
        agent_id=body.agent_id,
    )

    return {
        "success": result.success,
        "agent_id": result.agent_id,
        "message": result.message,
        "data": result.data,
    }