"""
Tests for core/task_planner.py.

These tests exercise TaskPlanner in isolation using a minimal
fake AgentRegistry (so this file has no dependency on the full
agent/tool wiring), plus one integration check (TEST 10) against
the real bootstrap_cortex() to confirm the existing security
foundation is untouched.
"""

import asyncio
import inspect

from core.task_planner import (
    StepSpec,
    TaskPlanner,
    TaskPlannerError,
)


# ============================================================
# MINIMAL FAKE REGISTRY
# ============================================================

class _FakeAgent:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.enabled = True


class _FakeAgentRegistry:
    """
    Implements only the surface TaskPlanner actually uses:
    .get(agent_id) -> agent | None
    """

    def __init__(self, agent_ids):
        self._agents = {aid: _FakeAgent(aid) for aid in agent_ids}

    def get(self, agent_id: str):
        return self._agents.get(agent_id)


KNOWN_AGENTS = (
    "ARIA",
    "ELARA",
    "LYRA",
    "VAULT",
    "ORION",
    "NOVA",
    "ATLAS",
    "SENTINEL",
)


class _FakeIntent:
    def __init__(self, success, agent_id, action, context=None, message=""):
        self.success = success
        self.agent_id = agent_id
        self.action = action
        self.context = context or {}
        self.message = message


def _planner() -> TaskPlanner:
    return TaskPlanner(_FakeAgentRegistry(KNOWN_AGENTS))


# ============================================================
# TEST 1: VALID SINGLE-STEP PLAN
# ============================================================

def test_1_valid_single_step_plan():
    print("\nTEST 1: VALID SINGLE-STEP PLAN")

    planner = _planner()

    plan = planner.build_plan(
        original_request="Create a tournament",
        step_specs=[
            StepSpec(agent_id="ARIA", action="create_tournament"),
        ],
    )

    assert len(plan.steps) == 1
    assert plan.steps[0].agent_id == "ARIA"
    assert plan.steps[0].action == "create_tournament"
    assert plan.steps[0].depends_on == ()

    print(plan)
    print("TEST 1: PASS")


# ============================================================
# TEST 2: VALID MULTI-STEP PLAN
# ============================================================

def test_2_valid_multi_step_plan():
    print("\nTEST 2: VALID MULTI-STEP PLAN")

    planner = _planner()

    plan = planner.build_plan(
        original_request="Create a tournament and notify the players",
        step_specs=[
            StepSpec(
                step_id="step_1",
                agent_id="ARIA",
                action="create_tournament",
            ),
            StepSpec(
                step_id="step_2",
                agent_id="LYRA",
                action="send_notification",
                depends_on=("step_1",),
            ),
        ],
    )

    assert len(plan.steps) == 2
    assert plan.steps[0].agent_id == "ARIA"
    assert plan.steps[1].agent_id == "LYRA"
    assert plan.steps[1].depends_on == ("step_1",)

    print(plan)
    print("TEST 2: PASS")


# ============================================================
# TEST 3: DEPENDENCY VALIDATION / ORDERING
# ============================================================

def test_3_dependency_ordering():
    print("\nTEST 3: DEPENDENCY VALIDATION")

    planner = _planner()

    plan = planner.build_plan(
        original_request="Create a tournament and notify the players",
        step_specs=[
            StepSpec(
                step_id="step_1",
                agent_id="ARIA",
                action="create_tournament",
            ),
            StepSpec(
                step_id="step_2",
                agent_id="LYRA",
                action="send_notification",
                depends_on=("step_1",),
            ),
        ],
    )

    ordered = plan.ordered_steps()

    assert [step.step_id for step in ordered] == ["step_1", "step_2"]

    print(ordered)
    print("TEST 3: PASS")


# ============================================================
# TEST 4: UNKNOWN AGENT REJECTION
# ============================================================

def test_4_unknown_agent_rejected():
    print("\nTEST 4: UNKNOWN AGENT REJECTION")

    planner = _planner()

    try:
        planner.build_plan(
            original_request="Do something with a fake agent",
            step_specs=[
                StepSpec(agent_id="GHOST", action="do_something"),
            ],
        )
        raise AssertionError("Expected TaskPlannerError, got success.")
    except TaskPlannerError as exc:
        print(exc)

    print("TEST 4: PASS")


# ============================================================
# TEST 5: EMPTY ACTION REJECTION
# ============================================================

def test_5_empty_action_rejected():
    print("\nTEST 5: EMPTY ACTION REJECTION")

    planner = _planner()

    try:
        planner.build_plan(
            original_request="Do nothing",
            step_specs=[
                StepSpec(agent_id="ARIA", action="   "),
            ],
        )
        raise AssertionError("Expected TaskPlannerError, got success.")
    except TaskPlannerError as exc:
        print(exc)

    print("TEST 5: PASS")


# ============================================================
# TEST 6: MISSING DEPENDENCY REJECTION
# ============================================================

def test_6_missing_dependency_rejected():
    print("\nTEST 6: MISSING DEPENDENCY REJECTION")

    planner = _planner()

    try:
        planner.build_plan(
            original_request="Notify players about a tournament",
            step_specs=[
                StepSpec(
                    step_id="step_1",
                    agent_id="LYRA",
                    action="send_notification",
                    depends_on=("step_missing",),
                ),
            ],
        )
        raise AssertionError("Expected TaskPlannerError, got success.")
    except TaskPlannerError as exc:
        print(exc)

    print("TEST 6: PASS")


# ============================================================
# TEST 7: SELF-DEPENDENCY REJECTION
# ============================================================

def test_7_self_dependency_rejected():
    print("\nTEST 7: SELF-DEPENDENCY REJECTION")

    planner = _planner()

    try:
        planner.build_plan(
            original_request="Self-referential step",
            step_specs=[
                StepSpec(
                    step_id="step_1",
                    agent_id="ARIA",
                    action="create_tournament",
                    depends_on=("step_1",),
                ),
            ],
        )
        raise AssertionError("Expected TaskPlannerError, got success.")
    except TaskPlannerError as exc:
        print(exc)

    print("TEST 7: PASS")


# ============================================================
# TEST 8: CIRCULAR DEPENDENCY REJECTION
# ============================================================

def test_8_circular_dependency_rejected():
    print("\nTEST 8: CIRCULAR DEPENDENCY REJECTION")

    planner = _planner()

    try:
        planner.build_plan(
            original_request="Circular plan",
            step_specs=[
                StepSpec(
                    step_id="step_1",
                    agent_id="ARIA",
                    action="create_tournament",
                    depends_on=("step_2",),
                ),
                StepSpec(
                    step_id="step_2",
                    agent_id="LYRA",
                    action="send_notification",
                    depends_on=("step_1",),
                ),
            ],
        )
        raise AssertionError("Expected TaskPlannerError, got success.")
    except TaskPlannerError as exc:
        print(exc)

    print("TEST 8: PASS")


# ============================================================
# TEST 9: PLANNER DOES NOT EXECUTE TOOLS
# ============================================================

def test_9_planner_does_not_execute():
    print("\nTEST 9: PLANNER DOES NOT EXECUTE TOOLS")

    # Structural guarantee: no coroutine functions on TaskPlanner,
    # meaning nothing here can await a tool call.
    for name, member in inspect.getmembers(TaskPlanner):
        if inspect.isfunction(member) or inspect.ismethod(member):
            assert not inspect.iscoroutinefunction(member), (
                f"TaskPlanner.{name} is async — planner must stay "
                "synchronous and side-effect free."
            )

    # No tool/approval/audit collaborators are held anywhere on
    # the instance.
    planner = _planner()
    forbidden_attrs = (
        "tool_gateway",
        "tool_registry",
        "approval_gate",
        "audit_logger",
        "decision_engine",
        "permission_engine",
    )
    for attr in forbidden_attrs:
        assert not hasattr(planner, attr), (
            f"TaskPlanner must not hold a reference to '{attr}'."
        )

    # Building a plan from intent also produces plain data, not
    # a coroutine.
    intent = _FakeIntent(
        success=True,
        agent_id="ARIA",
        action="create_tournament",
    )
    plan = planner.plan_from_intent(intent, original_request="Create a tournament")
    assert not inspect.iscoroutine(plan)

    print("TEST 9: PASS")


# ============================================================
# TEST 10: EXISTING FOUNDATION REMAINS UNTOUCHED
# ============================================================

def test_10_existing_foundation_untouched():
    print("\nTEST 10: EXISTING FOUNDATION SECURITY COMPONENTS UNTOUCHED")
    from core.cortex_bootstrap import bootstrap_cortex

    runtime = bootstrap_cortex()

    assert runtime.health_report.is_healthy()

    status = runtime.status()
    assert status["permission_engine"] is True
    assert status["decision_engine"] is True
    assert status["approval_gate"] is True
    assert status["agent_controller"] is True
    assert status["tool_gateway"] is True
    assert status["audit_logger"] is True

    print(runtime.health_report.summary())
    print("TEST 10: PASS")


# ============================================================
# RUNNER
# ============================================================

def main():
    print("CORTEX TASK PLANNER TEST SUITE")
    print("=" * 60)

    test_1_valid_single_step_plan()
    test_2_valid_multi_step_plan()
    test_3_dependency_ordering()
    test_4_unknown_agent_rejected()
    test_5_empty_action_rejected()
    test_6_missing_dependency_rejected()
    test_7_self_dependency_rejected()
    test_8_circular_dependency_rejected()
    test_9_planner_does_not_execute()
    test_10_existing_foundation_untouched()

    print("\n" + "=" * 60)
    print("TASK PLANNER TEST SUITE: ALL PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()





