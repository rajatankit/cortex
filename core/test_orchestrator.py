import asyncio
from core.agent import AgentResult, BaseAgent
from core.agent_controller import AgentController
from core.agent_registry import AgentRegistry
from core.decision import DecisionEngine
from core.permissions import PermissionEngine, RiskLevel
from core.audit_logger import AuditLogger
from core.approval_gate import ApprovalGate
from core.orchestrator import Orchestrator


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
            message=f"ARIA handled: {task}",
            data=context or {},
        )


async def main():

    # 1. Registry
    registry = AgentRegistry()

    aria = TestAgent()
    registry.register(aria)

    # 2. Permissions
    permissions = PermissionEngine()

    permissions.grant(
        agent_id="ARIA",
        action="read_data",
        risk=RiskLevel.LOW,
    )

    permissions.grant(
        agent_id="ARIA",
        action="modify_data",
        risk=RiskLevel.HIGH,
    )

    # 3. Decision Engine
    decision_engine = DecisionEngine(permissions)

    # 4. Security systems
    audit_logger = AuditLogger()
    approval_gate = ApprovalGate()

    # 5. Controller
    controller = AgentController(
        registry=registry,
        decision_engine=decision_engine,
        audit_logger=audit_logger,
        approval_gate=approval_gate,
    )

    # 6. Orchestrator
    orchestrator = Orchestrator(
        registry=registry,
        controller=controller,
    )

    # --------------------------------
    # TEST 1: LOW RISK
    # --------------------------------

    result = await orchestrator.dispatch(
        agent_id="ARIA",
        action="read_data",
        task="Check system status",
        context={"source": "orchestrator_test"},
    )

    print("\nLOW RISK TEST:")
    print(result)

    # --------------------------------
    # TEST 2: HIGH RISK
    # --------------------------------

    result = await orchestrator.dispatch(
        agent_id="ARIA",
        action="modify_data",
        task="Modify player data",
    )

    print("\nHIGH RISK TEST:")
    print(result)

    # --------------------------------
    # TEST 3: UNKNOWN AGENT
    # --------------------------------

    result = await orchestrator.dispatch(
        agent_id="UNKNOWN",
        action="read_data",
        task="Read data",
    )

    print("\nUNKNOWN AGENT TEST:")
    print(result)

    # --------------------------------
    # AUDIT
    # --------------------------------

    print("\nAUDIT LOG:")

    for event in audit_logger.list_events():
        print(event)


if __name__ == "__main__":
    asyncio.run(main())





