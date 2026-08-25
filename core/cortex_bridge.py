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
    agent_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    task: str = Field(min_length=1)
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

