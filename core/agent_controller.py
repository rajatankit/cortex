from dataclasses import dataclass
from core.agent import AgentResult
from core.agent_registry import AgentRegistry
from core.decision import Decision, DecisionEngine
from core.audit_logger import AuditLogger
from core.approval_gate import ApprovalGate


@dataclass(frozen=True)
class ControlResult:
    success: bool
    agent_id: str
    action: str
    decision: Decision
    message: str


class AgentController:
    """
    CORTEX authorization/control layer.

    Responsibilities:
    - Validate agent
    - Validate enabled state
    - Evaluate permissions/risk
    - Create approval requests
    - Validate approved requests
    - Re-check permissions
    - Optionally execute the agent itself

    Tool execution itself belongs to ToolGateway.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        decision_engine: DecisionEngine,
        audit_logger: AuditLogger,
        approval_gate: ApprovalGate,
    ):
        self.registry = registry
        self.decision_engine = decision_engine
        self.audit_logger = audit_logger
        self.approval_gate = approval_gate

    # =========================================================
    # AUDIT
    # =========================================================

    def _record(
        self,
        result: ControlResult,
    ) -> ControlResult:

        self.audit_logger.log(
            agent_id=result.agent_id,
            action=result.action,
            decision=result.decision.value,
            success=result.success,
            message=result.message,
        )

        return result

    # =========================================================
    # NORMAL EXECUTION / AUTHORIZATION
    # =========================================================

    async def execute(
        self,
        agent_id: str,
        action: str,
        task: str,
        context: dict | None = None,
        tool_name: str | None = None,
        execute_agent: bool = True,
    ) -> ControlResult:

        # -----------------------------------------------------
        # 1. AGENT VALIDATION
        # -----------------------------------------------------

        agent = self.registry.get(agent_id)

        if agent is None:
            return self._record(
                ControlResult(
                    success=False,
                    agent_id=agent_id,
                    action=action,
                    decision=Decision.DENY,
                    message=f"Agent not registered: {agent_id}",
                )
            )

        if not agent.enabled:
            return self._record(
                ControlResult(
                    success=False,
                    agent_id=agent_id,
                    action=action,
                    decision=Decision.DENY,
                    message=f"Agent is disabled: {agent_id}",
                )
            )

        # -----------------------------------------------------
        # 2. DECISION ENGINE
        # -----------------------------------------------------

        decision = self.decision_engine.evaluate(
            agent_id,
            action,
        )

        # -----------------------------------------------------
        # 3. REVIEW / APPROVAL
        # -----------------------------------------------------

        if decision.decision == Decision.REVIEW:

            request = self.approval_gate.create_request(
                agent_id=agent_id,
                action=action,
                task=task,
                tool_name=tool_name,
                context=context,
            )

            return self._record(
                ControlResult(
                    success=False,
                    agent_id=agent_id,
                    action=action,
                    decision=Decision.REVIEW,
                    message=(
                        "Approval required. "
                        f"Request ID: {request.request_id}"
                    ),
                )
            )

        # -----------------------------------------------------
        # 4. DENY / BLOCK
        # -----------------------------------------------------

        if decision.decision != Decision.ALLOW:

            return self._record(
                ControlResult(
                    success=False,
                    agent_id=agent_id,
                    action=action,
                    decision=decision.decision,
                    message=(
                        f"Action '{action}' was not executed. "
                        f"Decision: {decision.decision.value}"
                    ),
                )
            )

        # -----------------------------------------------------
        # 5. AUTHORIZATION-ONLY MODE
        #
        # ToolGateway uses this mode.
        # The gateway will execute the actual tool itself.
        # -----------------------------------------------------

        if not execute_agent:
            return self._record(
                ControlResult(
                    success=True,
                    agent_id=agent_id,
                    action=action,
                    decision=Decision.ALLOW,
                    message="Action authorized successfully.",
                )
            )

        # -----------------------------------------------------
        # 6. DIRECT AGENT EXECUTION
        # -----------------------------------------------------

        result: AgentResult = await agent.handle(
            task=task,
            context=context or {},
        )

        return self._record(
            ControlResult(
                success=result.success,
                agent_id=agent_id,
                action=action,
                decision=decision.decision,
                message=result.message,
            )
        )

    # =========================================================
    # APPROVED AGENT EXECUTION
    # =========================================================

    async def approve_and_execute(
        self,
        request_id: str,
        context: dict | None = None,
    ) -> ControlResult:

        request = self.approval_gate.get(request_id)

        if request is None:
            return self._record(
                ControlResult(
                    success=False,
                    agent_id="UNKNOWN",
                    action="UNKNOWN",
                    decision=Decision.DENY,
                    message=(
                        f"Approval request not found: {request_id}"
                    ),
                )
            )

        # -----------------------------------------------------
        # EXPIRATION
        # -----------------------------------------------------

        request = self.approval_gate.check_expiration(request_id)

        if request is None:
            return self._record(
                ControlResult(
                    success=False,
                    agent_id="UNKNOWN",
                    action="UNKNOWN",
                    decision=Decision.DENY,
                    message=(
                        f"Approval request not found: {request_id}"
                    ),
                )
            )

        # -----------------------------------------------------
        # APPROVAL STATUS
        # -----------------------------------------------------

        if request.status.value != "approved":
            return self._record(
                ControlResult(
                    success=False,
                    agent_id=request.agent_id,
                    action=request.action,
                    decision=Decision.REVIEW,
                    message=(
                        "Approval required before execution. "
                        f"Current status: {request.status.value}"
                    ),
                )
            )

        # -----------------------------------------------------
        # AGENT VALIDATION
        # -----------------------------------------------------

        agent = self.registry.get(request.agent_id)

        if agent is None:
            return self._record(
                ControlResult(
                    success=False,
                    agent_id=request.agent_id,
                    action=request.action,
                    decision=Decision.DENY,
                    message=(
                        f"Agent not registered: "
                        f"{request.agent_id}"
                    ),
                )
            )

        if not agent.enabled:
            return self._record(
                ControlResult(
                    success=False,
                    agent_id=request.agent_id,
                    action=request.action,
                    decision=Decision.DENY,
                    message=(
                        f"Agent is disabled: "
                        f"{request.agent_id}"
                    ),
                )
            )

        # -----------------------------------------------------
        # PERMISSION RE-CHECK
        # -----------------------------------------------------

        permission_allowed = (
            self.decision_engine.permission_engine.is_allowed(
                request.agent_id,
                request.action,
            )
        )

        if not permission_allowed:
            return self._record(
                ControlResult(
                    success=False,
                    agent_id=request.agent_id,
                    action=request.action,
                    decision=Decision.DENY,
                    message=(
                        "Execution blocked: permission was "
                        "removed after approval."
                    ),
                )
            )

        # -----------------------------------------------------
        # APPROVED CONTEXT ONLY
        # -----------------------------------------------------

        approved_context = request.context or {}

        result: AgentResult = await agent.handle(
            task=request.task,
            context=approved_context,
        )

        # -----------------------------------------------------
        # CONSUME APPROVAL
        # -----------------------------------------------------

        if result.success:
            self.approval_gate.mark_executed(request_id)

        return self._record(
            ControlResult(
                success=result.success,
                agent_id=request.agent_id,
                action=request.action,
                decision=Decision.ALLOW,
                message=result.message,
            )
        )
