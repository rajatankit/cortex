from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

from config.agents import AGENT_DEFINITIONS
from core.agent import AgentResult
from core.agent_registry import AgentRegistry
from core.agent_controller import AgentController
from core.orchestrator import Orchestrator
from core.permissions import PermissionEngine, RiskLevel
from core.decision import DecisionEngine
from core.audit_logger import AuditLogger
from core.approval_gate import ApprovalGate
from core.llm_agent import LLMAgent


app = FastAPI(
    title="CORTEX",
    description="AI Command Center",
    version="0.1.0",
)

# =============================================================
# CORE LAYER WIRING
# =============================================================

registry = AgentRegistry()

permission_engine = PermissionEngine()

decision_engine = DecisionEngine(permission_engine)
audit_logger = AuditLogger()
approval_gate = ApprovalGate()

controller = AgentController(
    registry=registry,
    decision_engine=decision_engine,
    audit_logger=audit_logger,
    approval_gate=approval_gate,
)

orchestrator = Orchestrator(registry, controller)

# =============================================================
# PERMISSIONS (dev/testing seed — move to config later)
# =============================================================

permission_engine.grant("aria", "view_tournament", RiskLevel.LOW)
permission_engine.grant("aria", "analyze_tournament", RiskLevel.LOW)
permission_engine.grant("aria", "create_tournament", RiskLevel.HIGH)
permission_engine.grant("lyra", "send_notification", RiskLevel.MEDIUM)

# =============================================================
# AGENT REGISTRATION (LLM-backed specialists — real intelligence)
# =============================================================

for agent_id, definition in AGENT_DEFINITIONS.items():
    registry.register(
        LLMAgent(
            agent_id=agent_id,
            name=definition["name"],
            role=definition["role"],
            specialty=definition.get("specialty", definition["role"]),
        )
    )

print(f"CORTEX: {len(registry.list_agents())} specialists registered.")

# =============================================================
# ROUTES
# =============================================================

@app.get("/health")
async def health():
    return {
        "status": "online",
        "system": "CORTEX",
        "version": "0.1.0",
    }


@app.get("/api/v1/status")
async def status():
    return {
        "cortex": "online",
        "agents_registered": len(registry.list_agents()),
    }


@app.get("/api/v1/agents")
async def agents():
    return {
        "count": len(registry.list_agents()),
        "agents": registry.list_agents(),
    }


@app.get("/api/v1/permissions/check")
async def check_permission(agent_id: str, action: str):
    allowed = permission_engine.is_allowed(agent_id, action)
    risk = permission_engine.get_risk(agent_id, action)

    return {
        "agent": agent_id,
        "action": action,
        "allowed": allowed,
        "risk": risk.value if risk else None,
    }


# =============================================================
# DISPATCH ENDPOINT
# =============================================================

class DispatchRequest(BaseModel):
    agent_id: str
    action: str
    task: str
    context: dict[str, Any] | None = None


@app.post("/dispatch")
async def dispatch(payload: DispatchRequest):
    result = await orchestrator.dispatch(
        agent_id=payload.agent_id,
        action=payload.action,
        task=payload.task,
        context=payload.context,
    )

    response = {
        "success": result.success,
        "agent": result.agent,
        "message": result.message,
        "data": result.data,
    }

    # -----------------------------------------------------
    # Detect REVIEW decisions and expose structured
    # verification info so the frontend can trigger the
    # right biometric prompt (fingerprint / fingerprint+face)
    # -----------------------------------------------------
    if (
        not result.success
        and isinstance(result.message, str)
        and result.message.startswith("VERIFICATION_REQUIRED:")
    ):
        parts = result.message.split(":")
        # VERIFICATION_REQUIRED:<level>:<request_id>
        if len(parts) == 3:
            response["verification_required"] = parts[1]
            response["request_id"] = parts[2]
            response["message"] = (
                "Ye action sensitive hai. "
                f"{parts[1]} verification chahiye."
            )

    return response


# =============================================================
# APPROVAL ENDPOINTS (fingerprint / fingerprint+face)
# =============================================================

class ApprovalPayload(BaseModel):
    fingerprint_verified: bool = False
    face_verified: bool = False


@app.post("/api/v1/approve/{request_id}")
async def approve_request(request_id: str, payload: ApprovalPayload):
    request = approval_gate.get(request_id)

    if request is None:
        return {"success": False, "message": "Request not found."}

    required = request.required_verification

    if required == "fingerprint" and not payload.fingerprint_verified:
        return {
            "success": False,
            "message": "Fingerprint verification required.",
        }

    if required == "fingerprint+face" and not (
        payload.fingerprint_verified and payload.face_verified
    ):
        return {
            "success": False,
            "message": (
                "High-risk action: fingerprint aur face scan "
                "dono verification chahiye."
            ),
        }

    try:
        approval_gate.approve(request_id)
    except ValueError as e:
        return {"success": False, "message": str(e)}

    result = await controller.approve_and_execute(request_id)

    return {
        "success": result.success,
        "message": result.message,
    }


@app.get("/api/v1/pending-approvals")
async def pending_approvals():
    pending = approval_gate.list_pending()
    return {"count": len(pending), "requests": pending}