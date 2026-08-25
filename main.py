from fastapi import FastAPI

from config.agents import AGENT_DEFINITIONS
from core.agent import BaseAgent, AgentResult
from core.agent_registry import AgentRegistry
from core.orchestrator import Orchestrator
from core.permissions import PermissionEngine, RiskLevel


class PlaceholderAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, role: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.enabled = True

    async def handle(
        self,
        task: str,
        context=None,
    ) -> AgentResult:
        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=f"{self.name} received the task.",
            data={
                "task": task,
            },
        )


app = FastAPI(
    title="CORTEX",
    description="AI Command Center",
    version="0.1.0",
)

registry = AgentRegistry()
orchestrator = Orchestrator(registry)

permission_engine = PermissionEngine()

permission_engine.grant(
    "aria",
    "view_tournament",
    RiskLevel.LOW,
)

permission_engine.grant(
    "aria",
    "analyze_tournament",
    RiskLevel.LOW,
)


print("CORTEX PERMISSIONS:")
print(permission_engine.is_allowed("aria", "view_tournament"))
print(permission_engine.get_risk("aria", "view_tournament"))


for agent_id, definition in AGENT_DEFINITIONS.items():
    registry.register(
        PlaceholderAgent(
            agent_id=agent_id,
            name=definition["name"],
            role=definition["role"],
        )
    )


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


@app.post("/api/v1/test-task")
async def test_task(agent_id: str, task: str):
    result = await orchestrator.dispatch(
        agent_id=agent_id,
        task=task,
    )

    return {
        "success": result.success,
        "agent": result.agent,
        "message": result.message,
        "data": result.data,
    }


@app.get("/api/v1/permissions/check")
async def check_permission(
    agent_id: str,
    action: str,
):
    allowed = permission_engine.is_allowed(
        agent_id,
        action,
    )

    risk = permission_engine.get_risk(
        agent_id,
        action,
    )

    return {
        "agent": agent_id,
        "action": action,
        "allowed": allowed,
        "risk": risk.value if risk else None,
    }
