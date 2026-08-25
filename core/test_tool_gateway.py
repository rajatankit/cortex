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


async def read_tournament_tool(context=None):
    return {
        "tournament": "Battle Crown Test Tournament",
        "status": "active",
    }


async def create_tournament_tool(context=None):
    return {
        "status": "created",
        "message": "Test tournament created",
    }


async def main():

    print("CORTEX TOOL GATEWAY TEST")
    print("=" * 50)

    # Agent Registry
    registry = AgentRegistry()
    registry.register(TestAgent())

    # Permissions
    permissions = PermissionEngine()

    permissions.grant(
        agent_id="ARIA",
        action="read_tournament",
        risk=RiskLevel.LOW,
    )

    permissions.grant(
        agent_id="ARIA",
        action="create_tournament",
        risk=RiskLevel.HIGH,
    )

    # Decision Engine
    decision_engine = DecisionEngine(permissions)

    # Audit + Approval
    audit_logger = AuditLogger()
    approval_gate = ApprovalGate()

    # Controller
    controller = AgentController(
        registry=registry,
        decision_engine=decision_engine,
        audit_logger=audit_logger,
        approval_gate=approval_gate,
    )

    # Tool Registry
    tool_registry = ToolRegistry()

    read_tool = Tool(
        name="read_tournament",
        description="Read tournament information",
        required_action="read_tournament",
        risk=ToolRisk.LOW,
        handler=read_tournament_tool,
    )

    create_tool = Tool(
        name="create_tournament",
        description="Create a new tournament",
        required_action="create_tournament",
        risk=ToolRisk.HIGH,
        handler=create_tournament_tool,
    )

    tool_registry.register(read_tool)
    tool_registry.register(create_tool)

    # Tool Gateway
    gateway = ToolGateway(
        tool_registry=tool_registry,
        controller=controller,
        registry=registry,
        approval_gate=approval_gate,
        permissions=permissions,
    )

    # TEST 1
    print("\nTEST 1: LOW-RISK TOOL")

    result = await gateway.execute(
        agent_id="ARIA",
        tool_name="read_tournament",
        task="Read tournament information",
    )

    print(result)

    # TEST 2
    print("\nTEST 2: HIGH-RISK TOOL")

    result = await gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create a new tournament",
    )

    print(result)

    # TEST 3
    print("\nTEST 3: UNKNOWN TOOL")

    result = await gateway.execute(
        agent_id="ARIA",
        tool_name="delete_everything",
        task="Delete everything",
    )

    print(result)

    # AUDIT
    print("\nAUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nTOOL COUNT:")
    print(tool_registry.count())

    print("\nCORTEX TOOL GATEWAY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())





