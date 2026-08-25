import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL CONTEXT-INTEGRITY SECURITY TEST")
    print("=" * 60)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    agent_id = "ARIA"
    tool_name = "create_tournament"

    approved_context = {
        "tournament_name": "CONTEXT INTEGRITY TEST TOURNAMENT",
        "time": "22:00",
    }

    tampered_context = {
        "tournament_name": "UNAUTHORIZED TAMPERED TOURNAMENT",
        "time": "23:59",
    }

    print("\nTEST 1: CREATE APPROVAL WITH ORIGINAL CONTEXT")

    result = await gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task="Create context-integrity test tournament",
        context=approved_context,
    )

    print(result)

    request_id = None

    if result.data:
        request_id = result.data.get("request_id")

    if not request_id:
        print("TEST FAILED: No approval request ID returned.")
        return

    print("\nREQUEST ID:")
    print(request_id)

    request = approval_gate.get(request_id)

    if request is None:
        print("TEST FAILED: Approval request not found.")
        return

    print("\nORIGINAL APPROVAL REQUEST:")
    print(request)

    print("\nTEST 2: VERIFY ORIGINAL CONTEXT")

    if request.context == approved_context:
        print("ORIGINAL CONTEXT: PASS")
    else:
        print("ORIGINAL CONTEXT: FAIL")
        print("Stored context does not match the approved context.")
        return

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.status.value == "approved":
        print("APPROVAL: PASS")
    else:
        print("APPROVAL: FAIL")
        return

    print("\nTEST 4: ATTEMPT CONTEXT TAMPERING")

    print("Approved context:")
    print(approved_context)

    print("\nTampered caller context:")
    print(tampered_context)

    print("\nTEST 5: EXECUTE USING TAMPERED CALLER CONTEXT")

    execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context=tampered_context,
    )

    print(execution)

    print("\nTEST 6: VERIFY EXECUTION USED APPROVED CONTEXT")

    if not execution.success:
        print("CONTEXT EXECUTION: FAIL")
        print("Original approved request could not execute.")
        return

    executed_name = None
    executed_time = None

    if execution.data:
        tournament = execution.data.get("tournament", {})

        if isinstance(tournament, dict):
            executed_name = tournament.get("name")
            executed_time = tournament.get("time")

    print("Executed tournament name:")
    print(executed_name)

    print("Executed tournament time:")
    print(executed_time)

    if (
        executed_name == approved_context["tournament_name"]
        and executed_time == approved_context["time"]
    ):
        print("CONTEXT INTEGRITY: PASS")
        print(
            "Execution remained bound to the original "
            "approved context."
        )
    else:
        print("CONTEXT INTEGRITY: FAIL")
        print(
            "Execution used tampered caller-supplied context."
        )

    print("\nTEST 7: VERIFY TAMPERED CONTEXT WAS NOT STORED")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if final_request is None:
        print("FINAL STATE: FAIL")
        return

    if final_request.context == approved_context:
        print("STORED CONTEXT INTEGRITY: PASS")
        print(
            "Tampered caller context was not stored "
            "inside the approval."
        )
    else:
        print("STORED CONTEXT INTEGRITY: FAIL")
        print(
            "Approval context was modified unexpectedly."
        )

    print("\nTEST 8: VERIFY APPROVAL WAS CONSUMED")

    if final_request.status.value == "executed":
        print("APPROVAL STATE TRANSITION: PASS")
    else:
        print(
            "APPROVAL STATE TRANSITION: FAIL"
            f" Current state: {final_request.status.value}"
        )

    print("\nTEST 9: ATTEMPT REPLAY")

    replay = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context=approved_context,
    )

    print(replay)

    if not replay.success:
        print("CONTEXT REPLAY BLOCK: PASS")
        print(
            "Executed approval cannot be reused."
        )
    else:
        print("CONTEXT REPLAY BLOCK: FAIL")
        print(
            "Executed approval was incorrectly reusable."
        )

    print("\nSECURITY VERIFICATION")
    print("-" * 60)

    context_execution_pass = (
        execution.success
        and executed_name == approved_context["tournament_name"]
        and executed_time == approved_context["time"]
    )

    stored_context_pass = (
        final_request.context == approved_context
    )

    state_pass = (
        final_request.status.value == "executed"
    )

    replay_pass = not replay.success

    if (
        context_execution_pass
        and stored_context_pass
        and state_pass
        and replay_pass
    ):
        print("APPROVAL CONTEXT-INTEGRITY: PASS")
        print(
            "Caller context tampering was ignored, "
            "approved context was executed, "
            "and the approval could not be replayed."
        )
    else:
        print("APPROVAL CONTEXT-INTEGRITY: FAIL")

    print("\n" + "=" * 60)
    print("APPROVAL CONTEXT-INTEGRITY SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




