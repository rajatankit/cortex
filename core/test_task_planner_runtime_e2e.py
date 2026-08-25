import asyncio
from core.cortex_bootstrap import bootstrap_cortex
from core.task_planner import StepSpec, TaskPlannerError
import inspect


async def main():
    print("CORTEX TASK PLANNER <-> RUNTIME INTEGRATION TEST")
    print("=" * 60)

    runtime = bootstrap_cortex()

    # --------------------------------------------------
    # TEST 1: NATURAL LANGUAGE REQUEST -> VALID TASKPLAN
    # --------------------------------------------------

    print("\nTEST 1: NATURAL LANGUAGE REQUEST CREATES A VALID PLAN")

    intent = runtime.intent_engine.parse("Check tournament")
    assert intent.success is True

    plan = runtime.task_planner.plan_from_intent(
        intent,
        original_request="Check tournament",
    )

    print(plan)

    assert plan.status.value == "valid"
    assert len(plan.steps) == 1
    assert plan.steps[0].agent_id == "ARIA"
    assert plan.steps[0].action == "read_tournament"

    print("TEST 1: PASS")

    # --------------------------------------------------
    # TEST 2: SINGLE-STEP LOW-RISK INTENT EXECUTES VIA TOOLGATEWAY
    # --------------------------------------------------

    print("\nTEST 2: LOW-RISK INTENT EXECUTES THROUGH TOOLGATEWAY")

    result = await runtime.execute_intent("Check tournament")

    print(result)

    assert result.agent_id == "ARIA"
    assert result.data["intent_agent"] == "ARIA"
    assert result.data["intent_action"] == "read_tournament"
    assert result.data["plan_status"] == "completed"
    assert result.data["completed_steps"] == [
        result.data["steps"][0]["step_id"]
    ]
    assert result.data["blocked_steps"] == []

    print("LOW-RISK PLAN EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 3: HIGH-RISK INTENT REACHES EXISTING APPROVALGATE
    # --------------------------------------------------

    print("\nTEST 3: HIGH-RISK INTENT REACHES APPROVALGATE")

    result = await runtime.execute_intent(
        "Create a new tournament",
        context={
            "tournament_name": "Runtime Integration Test",
            "time": "21:00",
        },
    )

    print(result)

    assert result.success is False
    assert result.agent_id == "ARIA"
    assert result.data["intent_agent"] == "ARIA"
    assert result.data["intent_action"] == "create_tournament"
    assert result.data["decision"] == "review"
    assert result.data["plan_status"] == "blocked"
    assert result.data["request_id"] is not None

    print("HIGH-RISK APPROVAL GATE: PASS")

    # --------------------------------------------------
    # TEST 4: APPROVAL REQUEST BOUND TO THE PLANNED STEP
    # --------------------------------------------------

    print("\nTEST 4: APPROVAL REQUEST BOUND TO PLANNED STEP")

    pending = runtime.pending_approvals()

    assert len(pending) >= 1

    latest = pending[-1]

    print(latest)

    assert latest.agent_id == "ARIA"
    assert latest.action == "create_tournament"
    assert latest.tool_name == "create_tournament"
    assert latest.request_id == result.data["request_id"]

    print("APPROVAL BINDING: PASS")

    # --------------------------------------------------
    # TEST 5: MULTI-STEP PLAN EXECUTES IN DEPENDENCY ORDER
    # --------------------------------------------------

    print("\nTEST 5: MULTI-STEP PLAN EXECUTES IN DEPENDENCY ORDER")

    ok_plan = runtime.task_planner.build_plan(
        original_request="Check tournament twice, in order",
        step_specs=[
            StepSpec(
                step_id="step_1",
                agent_id="ARIA",
                action="read_tournament",
            ),
            StepSpec(
                step_id="step_2",
                agent_id="ARIA",
                action="read_tournament",
                depends_on=("step_1",),
            ),
        ],
    )

    plan_result = await runtime.execute_plan(ok_plan)

    print(plan_result)

    assert plan_result.success is True
    assert plan_result.data["plan_status"] == "completed"
    assert plan_result.data["completed_steps"] == ["step_1", "step_2"]
    assert plan_result.data["blocked_steps"] == []
    assert [s["step_id"] for s in plan_result.data["steps"]] == [
        "step_1",
        "step_2",
    ]

    print("MULTI-STEP DEPENDENCY ORDER: PASS")

    # --------------------------------------------------
    # TEST 6: DEPENDENT STEP DOES NOT EXECUTE IF DEPENDENCY FAILS
    # --------------------------------------------------

    print("\nTEST 6: DEPENDENT STEP BLOCKED WHEN DEPENDENCY FAILS")

    blocked_plan = runtime.task_planner.build_plan(
        original_request="Create tournament then check it",
        step_specs=[
            StepSpec(
                step_id="step_1",
                agent_id="ARIA",
                action="create_tournament",
                context={
                    "tournament_name": "Dependency Block Test",
                    "time": "22:00",
                },
            ),
            StepSpec(
                step_id="step_2",
                agent_id="ARIA",
                action="read_tournament",
                depends_on=("step_1",),
            ),
        ],
    )

    blocked_result = await runtime.execute_plan(blocked_plan)

    print(blocked_result)

    assert blocked_result.success is False
    assert blocked_result.data["plan_status"] == "blocked"
    assert blocked_result.data["completed_steps"] == []
    assert blocked_result.data["blocked_steps"] == ["step_1", "step_2"]

    step_1_record, step_2_record = blocked_result.data["steps"]

    assert step_1_record["decision"] == "review"
    assert step_2_record["decision"] == "blocked_dependency"
    assert "step_1" in step_2_record["message"]

    print("DEPENDENCY FAILURE BLOCKS DEPENDENT STEP: PASS")

    # --------------------------------------------------
    # TEST 7: UNKNOWN INTENT REJECTED
    # --------------------------------------------------

    print("\nTEST 7: UNKNOWN INTENT REJECTED")

    result = await runtime.execute_intent(
        "Do something completely unsupported"
    )

    print(result)

    assert result.success is False
    assert result.agent_id == "UNKNOWN"
    assert result.data["plan_id"] is None
    assert result.data["plan_status"] == "invalid"

    print("UNKNOWN INTENT BLOCK: PASS")

    # --------------------------------------------------
    # TEST 8: EMPTY REQUEST REJECTED
    # --------------------------------------------------

    print("\nTEST 8: EMPTY REQUEST REJECTED")

    result = await runtime.execute_intent("")

    print(result)

    assert result.success is False
    assert result.agent_id == "UNKNOWN"
    assert result.data["plan_status"] == "invalid"

    print("EMPTY REQUEST BLOCK: PASS")

    # --------------------------------------------------
    # TEST 9: AUDIT EVENTS STILL GENERATED
    # --------------------------------------------------

    print("\nTEST 9: AUDIT EVENTS STILL GENERATED")

    events = runtime.audit_events()

    print(f"Total audit events so far: {len(events)}")

    assert len(events) >= 4

    print("AUDIT INTEGRATION: PASS")

    # --------------------------------------------------
    # TEST 10: TASKPLANNER STILL HAS NO EXECUTION CAPABILITY
    # --------------------------------------------------

    print("\nTEST 10: TASKPLANNER HAS NO EXECUTION CAPABILITY")

    for name, member in inspect.getmembers(type(runtime.task_planner)):
        if inspect.isfunction(member):
            assert not inspect.iscoroutinefunction(member), (
                f"TaskPlanner.{name} must not be async."
            )

    forbidden_attrs = (
        "tool_gateway",
        "tool_registry",
        "approval_gate",
        "audit_logger",
        "decision_engine",
        "permission_engine",
    )
    for attr in forbidden_attrs:
        assert not hasattr(runtime.task_planner, attr)

    print("TASKPLANNER EXECUTION ISOLATION: PASS")

    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("INTEGRATION VERIFICATION")
    print("-" * 60)

    print("PLAN CREATION FROM INTENT: PASS")
    print("LOW-RISK PLAN EXECUTION: PASS")
    print("HIGH-RISK APPROVAL GATE: PASS")
    print("APPROVAL BINDING: PASS")
    print("MULTI-STEP DEPENDENCY ORDER: PASS")
    print("DEPENDENCY FAILURE BLOCKS DEPENDENT STEP: PASS")
    print("UNKNOWN INTENT BLOCK: PASS")
    print("EMPTY REQUEST BLOCK: PASS")
    print("AUDIT INTEGRATION: PASS")
    print("TASKPLANNER EXECUTION ISOLATION: PASS")

    print("\nCORTEX TASKPLANNER RUNTIME INTEGRATION: PASS")
    print(
        "Plans are ordered by TaskPlanner but every step still "
        "executes only through the existing ToolGateway security "
        "pipeline."
    )

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())




