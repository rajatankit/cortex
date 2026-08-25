import asyncio
from core.agent import AgentResult, BaseAgent
from core.agent_controller import AgentController
from core.agent_registry import AgentRegistry
from core.decision import DecisionEngine
from core.permissions import PermissionEngine, RiskLevel
from core.audit_logger import AuditLogger
from core.approval_gate import ApprovalGate


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
            message=f"ARIA completed task: {task}",
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

    # 4. Audit + Approval
    audit_logger = AuditLogger()
    approval_gate = ApprovalGate()

    # 5. CORTEX Controller
    controller = AgentController(
        registry=registry,
        decision_engine=decision_engine,
        audit_logger=audit_logger,
        approval_gate=approval_gate,
    )

    # --------------------------------
    # TEST 1: LOW RISK → ALLOW
    # --------------------------------

    result = await controller.execute(
        agent_id="ARIA",
        action="read_data",
        task="Read player data",
    )

    print("\nALLOW TEST:")
    print(result)

    # --------------------------------
    # TEST 2: HIGH RISK → REVIEW
    # --------------------------------

    review_result = await controller.execute(
        agent_id="ARIA",
        action="modify_data",
        task="Modify player data",
    )

    print("\nREVIEW TEST:")
    print(review_result)

    # Extract approval request ID
    request_id = review_result.message.split(
        "Request ID: "
    )[1]

    print("\nAPPROVAL REQUEST ID:")
    print(request_id)

    # --------------------------------
    # TEST 3: CHECK PENDING REQUEST
    # --------------------------------

    pending_requests = approval_gate.list_pending()

    print("\nPENDING APPROVALS:")
    for request in pending_requests:
        print(request)

    # --------------------------------
    # TEST 4: HUMAN APPROVES
    # --------------------------------

    approved_request = approval_gate.approve(
        request_id
    )

    print("\nAPPROVED REQUEST:")
    print(approved_request)

    # --------------------------------
    # TEST 5: APPROVED → EXECUTE
    # --------------------------------

    approved_result = await controller.approve_and_execute(
        request_id=request_id,
        context={
            "approved_by": "HUMAN",
        },
    )

    print("\nAPPROVED EXECUTION TEST:")
    print(approved_result)

    # --------------------------------
    # TEST 6: UNKNOWN AGENT
    # --------------------------------

    unknown_result = await controller.execute(
        agent_id="UNKNOWN",
        action="read_data",
        task="Read data",
    )

    print("\nUNKNOWN AGENT TEST:")
    print(unknown_result)

    # --------------------------------
    # AUDIT LOG
    # --------------------------------

    print("\nAUDIT LOG:")

    for event in audit_logger.list_events():
        print(event)


if __name__ == "__main__":
    asyncio.run(main())





