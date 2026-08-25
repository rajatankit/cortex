import asyncio
from core.agent import AgentResult, BaseAgent
from core.agent_controller import AgentController
from core.agent_registry import AgentRegistry
from core.approval_gate import ApprovalGate
from core.audit_logger import AuditLogger
from core.decision import DecisionEngine
from core.permissions import PermissionEngine, RiskLevel
from core.tool_gateway import ToolGateway
from core.tools.tool import Tool, ToolRisk
from core.tools.tool_registry import ToolRegistry


class HelperAgent(BaseAgent):
    agent_id = "ARIA"
    name = "Aria"
    role = "Tournament Management"

    async def handle(
        self,
        task: str,
        context: dict | None = None,
    ) -> AgentResult:

        return AgentResult(
            success=True,
            agent=self.agent_id,
            message=f"ARIA handled: {task}",
            data=context or {},
        )


async def create_tournament(context=None):
    return {
        "status": "created",
        "tournament": "Approved Test Tournament",
    }


async def main():

    print("CORTEX TOOL APPROVAL TEST")
    print("=" * 50)

    registry = AgentRegistry()
    registry.register(TestAgent())

    permissions = PermissionEngine()

    permissions.grant(
        agent_id="ARIA",
        action="create_tournament",
        risk=RiskLevel.HIGH,
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

    tool_registry = ToolRegistry()

    tool_registry.register(
        Tool(
            name="create_tournament",
            description="Create tournament",
            required_action="create_tournament",
            risk=ToolRisk.HIGH,
            handler=create_tournament,
        )
    )

    gateway = ToolGateway(
        tool_registry=tool_registry,
        controller=controller,
        registry=registry,
        approval_gate=approval_gate,
        permissions=permissions,
    )

    print("\nSTEP 1: REQUEST")

    result = await gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create a new tournament",
    )

    print(result)

    request_id = result.data["request_id"]

    print("\nSTEP 2: APPROVE")

    approved = approval_gate.approve(request_id)

    print(approved)

    print("\nSTEP 3: APPROVED EXECUTION")

    final_result = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
    )

    print(final_result)

    print("\nAUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nCORTEX TOOL APPROVAL TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())





