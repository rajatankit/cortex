from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4

from core.agent_registry import AgentRegistry


# ============================================================
# ERRORS
# ============================================================

class TaskPlannerError(Exception):
    """
    Raised when a requested plan cannot be safely constructed.

    The TaskPlanner never returns a partially-valid or
    best-effort plan; any structural problem raises this
    instead of producing something a caller might mistakenly
    execute.
    """
    pass


# ============================================================
# ENUMS
# ============================================================

class PlanStatus(str, Enum):
    VALID = "valid"


class StepStatus(str, Enum):
    PLANNED = "planned"


# ============================================================
# INPUT (UNVALIDATED)
# ============================================================

@dataclass(frozen=True)
class StepSpec:
    """
    Minimal, unvalidated description of one requested step.

    This is the input to TaskPlanner.build_plan(). Validation
    happens inside the planner; a StepSpec carries no
    guarantees on its own.
    """

    agent_id: str
    action: str
    context: dict[str, Any] | None = None
    depends_on: tuple[str, ...] = ()
    step_id: str | None = None


# ============================================================
# OUTPUT (VALIDATED, IMMUTABLE)
# ============================================================

@dataclass(frozen=True)
class PlannedStep:
    """
    A single, unexecuted step in an execution plan.

    A PlannedStep describes intended work only. It carries no
    authorization, permission, or approval state of its own —
    those are determined later by PermissionEngine,
    DecisionEngine, and ApprovalGate when the step is actually
    submitted for execution.
    """

    step_id: str
    agent_id: str
    action: str
    context: dict[str, Any]
    depends_on: tuple[str, ...] = ()
    status: StepStatus = StepStatus.PLANNED


@dataclass(frozen=True)
class TaskPlan:
    """
    A deterministic, validated, unexecuted execution plan.
    """

    plan_id: str
    original_request: str
    steps: tuple[PlannedStep, ...]
    status: PlanStatus

    def step_by_id(self, step_id: str) -> PlannedStep | None:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def ordered_steps(self) -> tuple[PlannedStep, ...]:
        """
        Return steps in a deterministic dependency-respecting
        order (Kahn's algorithm). Ties are broken by the
        original step order.

        This is a pure convenience helper for callers deciding
        execution order later. It does not execute anything.
        """

        index_of = {
            step.step_id: position
            for position, step in enumerate(self.steps)
        }

        remaining_deps = {
            step.step_id: set(step.depends_on) for step in self.steps
        }

        ready = sorted(
            (
                step_id
                for step_id, deps in remaining_deps.items()
                if not deps
            ),
            key=lambda step_id: index_of[step_id],
        )

        ordered: list[str] = []
        by_id = {step.step_id: step for step in self.steps}

        # Steps whose dependency is `dep` become ready once `dep`
        # is placed.
        dependents: dict[str, list[str]] = {
            step.step_id: [] for step in self.steps
        }
        for step in self.steps:
            for dep in step.depends_on:
                dependents[dep].append(step.step_id)

        while ready:
            ready.sort(key=lambda step_id: index_of[step_id])
            current = ready.pop(0)
            ordered.append(current)

            for dependent_id in dependents[current]:
                remaining_deps[dependent_id].discard(current)
                if not remaining_deps[dependent_id]:
                    ready.append(dependent_id)

        # Validation already guarantees acyclicity, so this should
        # always consume every step. Defensive check kept anyway.
        if len(ordered) != len(self.steps):
            raise TaskPlannerError(
                "Internal error: plan ordering did not resolve "
                "all steps (unexpected cycle)."
            )

        return tuple(by_id[step_id] for step_id in ordered)


# ============================================================
# PLANNER
# ============================================================

class TaskPlanner:
    """
    Converts a validated intent (or a set of structured step
    specs) into a deterministic TaskPlan.

    The TaskPlanner is NOT a security authority. It never:

      - executes tools
      - calls ToolGateway
      - approves or rejects requests
      - bypasses AgentController, PermissionEngine,
        DecisionEngine, or ApprovalGate
      - writes audit events

    It only validates plan *structure*: that referenced agents
    exist, actions are non-empty, and dependencies between
    steps are well-formed and acyclic. Every step in a
    produced plan still has to pass through the existing
    CORTEX execution pipeline (AgentController -> PermissionEngine
    -> DecisionEngine -> ApprovalGate -> ToolGateway) exactly as
    it does today.
    """

    def __init__(self, agent_registry: AgentRegistry):
        self._agent_registry = agent_registry

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------

    def plan_from_intent(
        self,
        intent: Any,
        original_request: str | None = None,
    ) -> TaskPlan:
        """
        Build a single-step plan from a validated IntentResult
        (or any object exposing .success, .agent_id, .action,
        .context, .message).
        """

        if intent is None:
            raise TaskPlannerError("Intent cannot be None.")

        if not getattr(intent, "success", False):
            raise TaskPlannerError(
                "Cannot plan from a failed intent: "
                f"{getattr(intent, 'message', 'unknown error')}"
            )

        spec = StepSpec(
            agent_id=getattr(intent, "agent_id", ""),
            action=getattr(intent, "action", ""),
            context=dict(getattr(intent, "context", {}) or {}),
        )

        request_text = (
            original_request
            if original_request is not None
            else getattr(intent, "message", "")
        )

        return self.build_plan(
            original_request=request_text,
            step_specs=[spec],
        )

    def build_plan(
        self,
        original_request: str,
        step_specs: list[StepSpec],
    ) -> TaskPlan:
        """
        Build and validate a (possibly multi-step) execution
        plan from a list of StepSpecs.

        Raises TaskPlannerError on any structural problem.
        Never returns a partially valid plan.
        """

        if not original_request or not original_request.strip():
            raise TaskPlannerError("Original request cannot be empty.")

        if not step_specs:
            raise TaskPlannerError(
                "A plan must contain at least one step."
            )

        steps: list[PlannedStep] = []
        seen_ids: set[str] = set()

        for index, spec in enumerate(step_specs, start=1):
            step_id = (spec.step_id or f"step_{index}").strip()

            if not step_id:
                raise TaskPlannerError(
                    f"Step at position {index} has an empty step_id."
                )

            if step_id in seen_ids:
                raise TaskPlannerError(f"Duplicate step ID: {step_id}")
            seen_ids.add(step_id)

            agent_id = (spec.agent_id or "").strip()
            action = (spec.action or "").strip()

            if not agent_id:
                raise TaskPlannerError(
                    f"Step '{step_id}' is missing an agent_id."
                )

            if self._agent_registry.get(agent_id) is None:
                raise TaskPlannerError(
                    f"Step '{step_id}' references unknown agent: "
                    f"{agent_id}"
                )

            if not action:
                raise TaskPlannerError(
                    f"Step '{step_id}' has an empty action."
                )

            context = spec.context if spec.context is not None else {}

            if not isinstance(context, dict):
                raise TaskPlannerError(
                    f"Step '{step_id}' has malformed context "
                    "(must be a dict)."
                )

            depends_on = tuple(spec.depends_on or ())

            if step_id in depends_on:
                raise TaskPlannerError(
                    f"Step '{step_id}' cannot depend on itself."
                )

            steps.append(
                PlannedStep(
                    step_id=step_id,
                    agent_id=agent_id,
                    action=action,
                    context=dict(context),
                    depends_on=depends_on,
                )
            )

        all_ids = {step.step_id for step in steps}

        for step in steps:
            for dep in step.depends_on:
                if dep not in all_ids:
                    raise TaskPlannerError(
                        f"Step '{step.step_id}' depends on unknown "
                        f"step: {dep}"
                    )

        self._validate_acyclic(steps)

        return TaskPlan(
            plan_id=str(uuid4()),
            original_request=original_request,
            steps=tuple(steps),
            status=PlanStatus.VALID,
        )

    # --------------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------------

    @staticmethod
    def _validate_acyclic(steps: list[PlannedStep]) -> None:
        """
        Deterministic cycle detection over the dependency graph
        using iterative-safe recursive DFS with three colors.
        """

        graph = {step.step_id: step.depends_on for step in steps}

        WHITE, GRAY, BLACK = 0, 1, 2
        color = {step_id: WHITE for step_id in graph}

        def visit(step_id: str, path: list[str]) -> None:
            color[step_id] = GRAY
            path.append(step_id)

            for dep in graph[step_id]:
                if color[dep] == GRAY:
                    cycle_start = path.index(dep)
                    cycle = " -> ".join(path[cycle_start:] + [dep])
                    raise TaskPlannerError(
                        f"Circular dependency detected: {cycle}"
                    )
                if color[dep] == WHITE:
                    visit(dep, path)

            path.pop()
            color[step_id] = BLACK

        for step in steps:
            if color[step.step_id] == WHITE:
                visit(step.step_id, [])




