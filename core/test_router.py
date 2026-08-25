import asyncio

from core.action_router import ActionRouter
from core.agent import AgentResult, BaseAgent
from core.agent_controller import AgentController
from core.agent_registry import AgentRegistry
from core.approval_gate import ApprovalGate
from core.audit_logger import AuditLogger
from core.decision import DecisionEngine
from core.permissions import PermissionEngine, RiskLevel


class HelperAgent(BaseAgent):
    agent_id = "ARIA"
    name = "Aria"
    role = "Operations"

    async def handle(
        self,
        task: str,
        context: dict | None = None,
    ) -> AgentResult:

        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=f"ARIA completed: {task}",
            data=context or {},
        )


async def main():

    registry = AgentRegistry()
    registry.register(TestAgent())

    permissions = PermissionEngine()

    permissions.grant(
        "ARIA",
        "read_data",
        RiskLevel.LOW,
    )

    decision_engine = DecisionEngine(permissions)
    audit_logger = AuditLogger()
    approval_gate = ApprovalGate()

    controller = AgentController(
        registry=registry,
        decision_engine=decision_engine,
        audit_logger=audit_logger,
        approval_gate=approval_gate,
    )

    router = ActionRouter(controller)

    result = await router.route(
        agent_id="ARIA",
        action="read_data",
        task="Read player data",
        context={"player_id": "TEST-001"},
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())





