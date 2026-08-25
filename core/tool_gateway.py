from dataclasses import dataclass
from typing import Any

from core.agent_controller import AgentController
from core.agent_registry import AgentRegistry
from core.approval_gate import ApprovalGate
from core.audit_logger import AuditLogger
from core.permissions import PermissionEngine
from core.tools.tool_registry import ToolRegistry


@dataclass(frozen=True)
class ToolResult:
    success: bool
    agent_id: str
    tool_name: str
    message: str
    data: Any = None


class ToolGateway:
    """
    Secure execution gateway for CORTEX tools.

    Execution pipeline:

        Request
           â†“
        ToolGateway
           â†“
        Tool lookup
           â†“
        AgentController
           â†“
        PermissionEngine
           â†“
        DecisionEngine
           â†“
        ApprovalGate (if required)
           â†“
        Exact approved tool
           â†“
        Tool execution
           â†“
        Audit

    Important:
    ToolGateway owns actual tool execution.
    AgentController is used for authorization.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        controller: AgentController,
        registry: AgentRegistry,
        approval_gate: ApprovalGate,
        permissions: PermissionEngine,
        audit_logger: AuditLogger,
    ):
        self.tool_registry = tool_registry
        self.controller = controller
        self.registry = registry
        self.approval_gate = approval_gate
        self.permissions = permissions

        self.audit_logger = audit_logger
    # =========================================================
    # NORMAL TOOL EXECUTION
    # =========================================================

    async def execute(
        self,
        agent_id: str,
        tool_name: str,
        task: str,
        context: dict | None = None,
    ) -> ToolResult:

        # -----------------------------------------------------
        # TOOL LOOKUP
        # -----------------------------------------------------

        tool = self.tool_registry.get(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=tool_name,
                message=f"Tool not registered: {tool_name}",
            )

        # -----------------------------------------------------
        # AUTHORIZE ONLY
        #
        # Do NOT execute the agent here.
        # ToolGateway owns the actual tool execution.
        # -----------------------------------------------------

        control_result = await self.controller.execute(
            agent_id=agent_id,
            action=tool.required_action,
            task=task,
            context=context,
            tool_name=tool_name,
            execute_agent=False,
        )

        # -----------------------------------------------------
        # APPROVAL REQUIRED / DENY / BLOCK
        # -----------------------------------------------------

        if not control_result.success:

            request_id = None

            prefix = "Approval required. Request ID: "

            if control_result.message.startswith(prefix):
                request_id = control_result.message[len(prefix):]

            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=tool_name,
                message=control_result.message,
                data={
                    "decision": control_result.decision.value,
                    "risk": tool.risk.value,
                    "request_id": request_id,
                },
            )

        # -----------------------------------------------------
        # AUTHORIZED LOW-RISK EXECUTION
        # -----------------------------------------------------

        return await self._execute_tool(
            agent_id=agent_id,
            tool_name=tool_name,
            context=context,
        )

    # =========================================================
    # APPROVED TOOL EXECUTION
    # =========================================================

    async def approve_and_execute(
        self,
        request_id: str,
        agent_id: str,
        context: dict | None = None,
    ) -> ToolResult:

        # -----------------------------------------------------
        # LOAD REQUEST
        # -----------------------------------------------------

        request = self.approval_gate.get(request_id)

        if request is None:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name="UNKNOWN",
                message=(
                    f"Approval request not found: "
                    f"{request_id}"
                ),
            )

        # -----------------------------------------------------
        # AGENT BINDING
        # -----------------------------------------------------

        if agent_id != request.agent_id:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name="UNKNOWN",
                message=(
                    "Execution blocked: caller agent does not "
                    "match the approved agent."
                ),
            )

        # -----------------------------------------------------
        # EXPIRATION
        # -----------------------------------------------------

        request = self.approval_gate.check_expiration(
            request_id
        )

        if request is None:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name="UNKNOWN",
                message=(
                    f"Approval request not found: "
                    f"{request_id}"
                ),
            )

        # -----------------------------------------------------
        # RE-CHECK AGENT BINDING
        # -----------------------------------------------------

        if agent_id != request.agent_id:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name="UNKNOWN",
                message=(
                    "Execution blocked: caller agent does not "
                    "match the approved agent."
                ),
            )

        # -----------------------------------------------------
        # STATUS
        # -----------------------------------------------------

        if request.status.value != "approved":
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=request.tool_name or "UNKNOWN",
                message=(
                    "Approval required before tool execution. "
                    f"Current status: {request.status.value}"
                ),
            )

        # -----------------------------------------------------
        # AGENT VALIDATION
        # -----------------------------------------------------

        agent = self.registry.get(request.agent_id)

        if agent is None:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=request.tool_name or "UNKNOWN",
                message=f"Agent not registered: {agent_id}",
            )

        if not agent.enabled:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=request.tool_name or "UNKNOWN",
                message=f"Agent is disabled: {agent_id}",
            )

        # -----------------------------------------------------
        # PERMISSION RE-CHECK
        # -----------------------------------------------------

        if not self.permissions.is_allowed(
            request.agent_id,
            request.action,
        ):
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=request.tool_name or "UNKNOWN",
                message=(
                    "Execution blocked: permission was "
                    "removed after approval."
                ),
            )

        # -----------------------------------------------------
        # EXACT TOOL BINDING
        # -----------------------------------------------------

        if not request.tool_name:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name="UNKNOWN",
                message="Approval request has no bound tool.",
            )

        tool = self.tool_registry.get(request.tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=request.tool_name,
                message=(
                    f"Approved tool is no longer registered: "
                    f"{request.tool_name}"
                ),
            )

        # -----------------------------------------------------
        # ACTION â†” TOOL BINDING
        # -----------------------------------------------------

        if tool.required_action != request.action:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=tool.name,
                message=(
                    "Execution blocked: approved action does "
                    "not match the approved tool."
                ),
            )

        # -----------------------------------------------------
        # APPROVED CONTEXT ONLY
        #
        # Caller-supplied context is deliberately ignored.
        # -----------------------------------------------------

        approved_context = request.context or {}

        result = await self._execute_tool(
            agent_id=agent_id,
            tool_name=tool.name,
            context=approved_context,
        )

        # -----------------------------------------------------
        # AUDIT ACTUAL EXECUTION
        # -----------------------------------------------------

        self.audit_logger.log(
            agent_id=agent_id,
            action=request.action,
            decision="allow",
            success=result.success,
            message=result.message,
        )

        # -----------------------------------------------------
        # SINGLE-USE APPROVAL
        # -----------------------------------------------------

        if result.success:
            self.approval_gate.mark_executed(
                request_id
            )

        return result

    # =========================================================
    # INTERNAL TOOL EXECUTION
    # =========================================================

    async def _execute_tool(
        self,
        agent_id: str,
        tool_name: str,
        context: dict | None = None,
    ) -> ToolResult:

        tool = self.tool_registry.get(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=tool_name,
                message=f"Tool not registered: {tool_name}",
            )

        try:

            result = await tool.execute(
                context=context or {},
            )

            return ToolResult(
                success=True,
                agent_id=agent_id,
                tool_name=tool_name,
                message=(
                    f"Tool '{tool_name}' executed successfully."
                ),
                data=result,
            )

        except Exception as exc:

            return ToolResult(
                success=False,
                agent_id=agent_id,
                tool_name=tool_name,
                message=f"Tool execution failed: {exc}",
            )

