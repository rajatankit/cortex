from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.agent_registry import AgentRegistry
from core.permissions import PermissionEngine
from core.permission_loader import PermissionLoader
from core.decision import DecisionEngine
from core.approval_gate import ApprovalGate
from core.audit_logger import AuditLogger
from core.voice_audit import VoiceAudit
from core.agent_controller import AgentController
from core.orchestrator import Orchestrator
from core.cortex_manager import CortexManager
from core.intent_engine import IntentEngine
from core.task_planner import TaskPlanner, TaskPlan, PlannedStep, TaskPlannerError
from core.tool_gateway import ToolGateway
from core.tools.tool_registry import ToolRegistry
from core.cortex_health import CortexHealth, CortexHealthReport


@dataclass(frozen=True)
class RuntimeResult:
    """
    Standard result returned by CORTEX runtime operations.
    """

    success: bool
    agent_id: str
    message: str
    data: Any = None


@dataclass
class CortexRuntime:
    """
    Complete CORTEX runtime.

    Security-sensitive execution must continue through the
    established security pipeline:

        IntentEngine
            â†“
        TaskPlanner            (planning only â€” no execution)
            â†“
        ToolGateway
            â†“
        AgentController
            â†“
        PermissionEngine
            â†“
        DecisionEngine
            â†“
        ApprovalGate
            â†“
        Tool Execution
            â†“
        AuditLogger

    This runtime class does not bypass the security layers.
    TaskPlanner only decides step ORDER; every step still goes
    through ToolGateway exactly as a single intent always has.
    """

    # ============================================================
    # SECURITY FOUNDATION
    # ============================================================

    agent_registry: AgentRegistry
    permission_engine: PermissionEngine
    permission_loader: PermissionLoader
    decision_engine: DecisionEngine
    approval_gate: ApprovalGate
    audit_logger: AuditLogger
    voice_audit: VoiceAudit
    agent_controller: AgentController

    # ============================================================
    # ROUTING / MANAGEMENT
    # ============================================================

    orchestrator: Orchestrator
    manager: CortexManager
    intent_engine: IntentEngine
    task_planner: TaskPlanner

    # ============================================================
    # TOOL SYSTEM
    # ============================================================

    tool_registry: ToolRegistry
    tool_gateway: ToolGateway

    # ============================================================
    # HEALTH
    # ============================================================

    health: CortexHealth
    health_report: CortexHealthReport

    # ============================================================
    # NATURAL LANGUAGE INTENT
    # ============================================================

    async def execute_intent(
        self,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> RuntimeResult:
        """
        Convert a natural-language request into an intent, turn it
        into a TaskPlan, and execute the plan's steps in dependency
        order through ToolGateway.

        Example:

            "Check tournament"

        becomes:

            ARIA / read_tournament

        The tool is NEVER executed directly here â€” every step goes
        through execute_plan(), which routes each step through
        ToolGateway exactly as before.
        """

        # --------------------------------------------------------
        # 1. VALIDATE REQUEST
        # --------------------------------------------------------

        if not request or not request.strip():
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message="Request cannot be empty.",
                data={
                    "intent_success": False,
                    "intent_agent": "UNKNOWN",
                    "intent_action": "UNKNOWN",
                    "action": "UNKNOWN",
                    "context": dict(context or {}),
                    "plan_id": None,
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        # --------------------------------------------------------
        # 2. PARSE NATURAL LANGUAGE INTENT
        # --------------------------------------------------------

        try:
            intent = self.intent_engine.parse(
                request=request,
                context=context,
            )

        except Exception as exc:
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message=f"Intent parsing failed: {exc}",
                data={
                    "intent_success": False,
                    "intent_agent": "UNKNOWN",
                    "intent_action": "UNKNOWN",
                    "action": "UNKNOWN",
                    "context": dict(context or {}),
                    "plan_id": None,
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        # --------------------------------------------------------
        # 3. HANDLE UNKNOWN INTENT
        # --------------------------------------------------------

        if not intent.success:
            return RuntimeResult(
                success=False,
                agent_id=intent.agent_id,
                message=intent.message,
                data={
                    "intent_success": False,
                    "intent_agent": intent.agent_id,
                    "intent_action": intent.action,
                    "action": intent.action,
                    "context": intent.context,
                    "plan_id": None,
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        # --------------------------------------------------------
        # 4. VALIDATE AGENT
        # --------------------------------------------------------

        if not intent.agent_id or intent.agent_id == "UNKNOWN":
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message="Intent did not identify a valid agent.",
                data={
                    "intent_success": True,
                    "intent_agent": intent.agent_id,
                    "intent_action": intent.action,
                    "action": intent.action,
                    "context": intent.context,
                    "plan_id": None,
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        # --------------------------------------------------------
        # 5. VALIDATE ACTION
        # --------------------------------------------------------

        if not intent.action or intent.action == "UNKNOWN":
            return RuntimeResult(
                success=False,
                agent_id=intent.agent_id,
                message="Intent did not identify a valid action.",
                data={
                    "intent_success": True,
                    "intent_agent": intent.agent_id,
                    "intent_action": intent.action,
                    "action": intent.action,
                    "context": intent.context,
                    "plan_id": None,
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        # --------------------------------------------------------
        # 6. BUILD EXECUTION PLAN (PLANNING ONLY â€” NO EXECUTION)
        # --------------------------------------------------------
        #
        # IMPORTANT:
        #
        # TaskPlanner only validates and orders steps. It never
        # calls ToolGateway, never checks permissions, never
        # approves anything.
        #

        try:
            plan = self.task_planner.plan_from_intent(
                intent=intent,
                original_request=request,
            )

        except TaskPlannerError as exc:
            return RuntimeResult(
                success=False,
                agent_id=intent.agent_id,
                message=f"Plan creation failed: {exc}",
                data={
                    "intent_success": True,
                    "intent_agent": intent.agent_id,
                    "intent_action": intent.action,
                    "action": intent.action,
                    "context": intent.context,
                    "plan_id": None,
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        # --------------------------------------------------------
        # 7. EXECUTE THE PLAN THROUGH THE EXISTING SECURITY PIPELINE
        # --------------------------------------------------------

        plan_result = await self.execute_plan(plan)

        # --------------------------------------------------------
        # 8. MERGE INTENT + PLAN INFORMATION
        # --------------------------------------------------------
        #
        # Backward compatibility: for a single-step plan (the
        # common case â€” one natural-language request, one action)
        # the original flat fields (tool/decision/risk/request_id/
        # result/context) are still populated at the top level of
        # `data`, exactly as execute_intent() has always returned
        # them. Plan-level fields are always added alongside them.
        #

        merged_data = dict(plan_result.data or {})
        merged_data["intent_success"] = True
        merged_data["intent_agent"] = intent.agent_id
        merged_data["intent_action"] = intent.action
        merged_data["action"] = intent.action

        steps_data = merged_data.get("steps", [])

        if len(plan.steps) == 1 and steps_data:
            primary = steps_data[0]
            merged_data["context"] = primary["context"]
            merged_data["tool"] = primary["tool"]
            merged_data["decision"] = primary["decision"]
            merged_data["risk"] = primary["risk"]
            merged_data["request_id"] = primary["request_id"]
            merged_data["result"] = primary["result"]
        else:
            merged_data.setdefault("context", intent.context)
            merged_data.setdefault("tool", None)
            merged_data.setdefault("decision", None)
            merged_data.setdefault("risk", None)
            merged_data.setdefault("request_id", None)
            merged_data.setdefault("result", None)

        return RuntimeResult(
            success=plan_result.success,
            agent_id=plan_result.agent_id,
            message=plan_result.message,
            data=merged_data,
        )

    # ============================================================
    # PLAN EXECUTION
    # ============================================================

    async def execute_plan(self, plan: TaskPlan) -> RuntimeResult:
        """
        Execute every step of a validated TaskPlan, in dependency
        order, through the existing ToolGateway security pipeline.

        Security properties:

        - Steps are ordered using TaskPlan.ordered_steps() only.
          No topological logic is duplicated here.
        - Every executed step goes through
          self.tool_gateway.execute(), the same entrypoint used by
          direct single-intent execution. Nothing calls a tool
          directly.
        - If a step's dependency did not complete successfully
          (denied, blocked, pending approval, or failed), the
          dependent step is SKIPPED, not executed. Skipping is
          decided here, in the runtime â€” TaskPlanner has no part
          in it.
        - ApprovalGate, PermissionEngine, and DecisionEngine
          behavior is untouched: a step requiring approval still
          returns success=False with decision="review" and a
          request_id, exactly as a single execute_intent() call
          always has.
        """

        if plan is None or not plan.steps:
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message="Plan has no steps to execute.",
                data={
                    "plan_id": getattr(plan, "plan_id", None),
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        try:
            ordered = plan.ordered_steps()
        except TaskPlannerError as exc:
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message=f"Plan ordering failed: {exc}",
                data={
                    "plan_id": plan.plan_id,
                    "plan_status": "invalid",
                    "steps": [],
                    "completed_steps": [],
                    "blocked_steps": [],
                },
            )

        step_order = [step.step_id for step in plan.steps]
        step_records: list[dict[str, Any]] = []
        completed_ids: set[str] = set()
        blocked_ids: set[str] = set()

        for step in ordered:
            unmet = [
                dep for dep in step.depends_on
                if dep not in completed_ids
            ]

            if unmet:
                record = self._blocked_step_record(
                    step=step,
                    reason=(
                        "Skipped: unmet dependency/dependencies: "
                        f"{', '.join(unmet)}"
                    ),
                )
                step_records.append(record)
                blocked_ids.add(step.step_id)
                continue

            try:
                result = await self.tool_gateway.execute(
                    agent_id=step.agent_id,
                    tool_name=step.action,
                    task=plan.original_request,
                    context=step.context,
                )

            except Exception as exc:
                record = self._blocked_step_record(
                    step=step,
                    reason=f"Step execution failed: {exc}",
                )
                step_records.append(record)
                blocked_ids.add(step.step_id)
                continue

            record = self._executed_step_record(step=step, result=result)
            step_records.append(record)

            if result.success:
                completed_ids.add(step.step_id)
            else:
                blocked_ids.add(step.step_id)

        overall_success = len(completed_ids) == len(plan.steps)

        if len(plan.steps) == 1:
            primary = step_records[0]
            top_agent_id = primary["agent_id"]
            top_message = primary["message"]
        else:
            top_agent_id = "MULTI"
            top_message = (
                f"Plan '{plan.plan_id}' executed: "
                f"{len(completed_ids)}/{len(plan.steps)} step(s) completed."
            )

        data = {
            "plan_id": plan.plan_id,
            "plan_status": "completed" if overall_success else "blocked",
            "steps": step_records,
            "completed_steps": [
                sid for sid in step_order if sid in completed_ids
            ],
            "blocked_steps": [
                sid for sid in step_order if sid in blocked_ids
            ],
        }

        return RuntimeResult(
            success=overall_success,
            agent_id=top_agent_id,
            message=top_message,
            data=data,
        )

    # ------------------------------------------------------------
    # PLAN EXECUTION HELPERS
    # ------------------------------------------------------------

    @staticmethod
    def _executed_step_record(
        step: PlannedStep,
        result: Any,
    ) -> dict[str, Any]:

        result_data = getattr(result, "data", None)

        if not isinstance(result_data, dict):
            result_data = {}

        return {
            "step_id": step.step_id,
            "agent_id": result.agent_id,
            "action": step.action,
            "context": dict(step.context),
            "depends_on": list(step.depends_on),
            "success": result.success,
            "message": result.message,
            "tool": getattr(result, "tool_name", step.action),
            "decision": result_data.get("decision"),
            "risk": result_data.get("risk"),
            "request_id": result_data.get("request_id"),
            "result": result_data,
        }

    @staticmethod
    def _blocked_step_record(
        step: PlannedStep,
        reason: str,
    ) -> dict[str, Any]:

        return {
            "step_id": step.step_id,
            "agent_id": step.agent_id,
            "action": step.action,
            "context": dict(step.context),
            "depends_on": list(step.depends_on),
            "success": False,
            "message": reason,
            "tool": None,
            "decision": "blocked_dependency",
            "risk": None,
            "request_id": None,
            "result": None,
        }

    # ============================================================
    # STRUCTURED TASK EXECUTION
    # ============================================================

    async def execute_task(
        self,
        task: str,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> RuntimeResult:
        """
        Execute an already-structured task through CortexManager.
        """

        if not task or not task.strip():
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message="Task cannot be empty.",
            )

        if not action or not action.strip():
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message="Action cannot be empty.",
            )

        try:
            routing, result = await self.manager.dispatch(
                task=task,
                action=action,
                context=context,
            )

        except Exception as exc:
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message=f"Runtime task execution failed: {exc}",
            )

        result_data = getattr(result, "data", None)

        if not isinstance(result_data, dict):
            result_data = {}

        return RuntimeResult(
            success=result.success,
            agent_id=routing.agent_id,
            message=result.message,
            data={
                "reason": routing.reason,
                "action": action,
                "decision": result_data.get("decision"),
                "risk": result_data.get("risk"),
                "request_id": result_data.get("request_id"),
                "result": result_data,
            },
        )

    # ============================================================
    # DIRECT TOOL EXECUTION
    # ============================================================

    async def execute_tool(
        self,
        agent_id: str,
        tool_name: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> RuntimeResult:
        """
        Execute a registered tool through ToolGateway.
        """

        if not agent_id or not agent_id.strip():
            return RuntimeResult(
                success=False,
                agent_id="UNKNOWN",
                message="Agent ID cannot be empty.",
            )

        if not tool_name or not tool_name.strip():
            return RuntimeResult(
                success=False,
                agent_id=agent_id,
                message="Tool name cannot be empty.",
            )

        if not task or not task.strip():
            return RuntimeResult(
                success=False,
                agent_id=agent_id,
                message="Task cannot be empty.",
            )

        try:
            result = await self.tool_gateway.execute(
                agent_id=agent_id,
                tool_name=tool_name,
                task=task,
                context=context,
            )

        except Exception as exc:
            return RuntimeResult(
                success=False,
                agent_id=agent_id,
                message=f"Tool execution failed: {exc}",
            )

        return RuntimeResult(
            success=result.success,
            agent_id=result.agent_id,
            message=result.message,
            data=result.data,
        )

    # ============================================================
    # APPROVAL MANAGEMENT
    # ============================================================

    def pending_approvals(self):
        """
        Return all pending approval requests.
        """

        return self.approval_gate.list_pending()

    def get_approval(
        self,
        request_id: str,
    ):
        """
        Return a specific approval request.
        """

        if not request_id:
            return None

        return self.approval_gate.get(request_id)

    def approve_request(
        self,
        request_id: str,
    ):
        """
        Approve a pending request.
        """

        if not request_id:
            return None

        return self.approval_gate.approve(request_id)

    def reject_request(
        self,
        request_id: str,
    ):
        """
        Reject a pending request.
        """

        if not request_id:
            return None

        return self.approval_gate.reject(request_id)

    # ============================================================
    # AUDIT
    # ============================================================

    def audit_events(self):
        """
        Return all audit events.
        """

        return self.audit_logger.list_events()

    def audit_count(self) -> int:
        """
        Return number of audit events.
        """

        return self.audit_logger.count()

    # ============================================================
    # STATUS
    # ============================================================

    def manager_status(self) -> str:
        return (
            "CORTEX manager operational"
            if self.manager is not None
            else "CORTEX manager unavailable"
        )

    def controller_status(self) -> str:
        return (
            "CORTEX controller operational"
            if self.agent_controller is not None
            else "CORTEX controller unavailable"
        )

    def gateway_status(self) -> str:
        return (
            "CORTEX tool gateway operational"
            if self.tool_gateway is not None
            else "CORTEX tool gateway unavailable"
        )

    def intent_status(self) -> str:
        return (
            "CORTEX intent engine operational"
            if self.intent_engine is not None
            else "CORTEX intent engine unavailable"
        )

    def planner_status(self) -> str:
        return (
            "CORTEX task planner operational"
            if self.task_planner is not None
            else "CORTEX task planner unavailable"
        )

    def status(self) -> dict[str, Any]:
        """
        Return a complete runtime status snapshot.
        """

        return {
            "agent_registry": self.agent_registry is not None,
            "permission_engine": self.permission_engine is not None,
            "permission_loader": self.permission_loader is not None,
            "decision_engine": self.decision_engine is not None,
            "approval_gate": self.approval_gate is not None,
            "audit_logger": self.audit_logger is not None,
            "voice_audit": self.voice_audit is not None,
            "agent_controller": self.agent_controller is not None,
            "orchestrator": self.orchestrator is not None,
            "manager": self.manager is not None,
            "intent_engine": self.intent_engine is not None,
            "task_planner": self.task_planner is not None,
            "tool_registry": self.tool_registry is not None,
            "tool_gateway": self.tool_gateway is not None,
            "health": self.health is not None,
            "health_report": self.health_report is not None,
            "audit_events": self.audit_count(),
        }






