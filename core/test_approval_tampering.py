import asyncio
from core.cortex_bootstrap import bootstrap_cortex


async def main():
    print("CORTEX APPROVAL TAMPERING SECURITY TEST")
    print("=" * 50)

    runtime = bootstrap_cortex()

    gateway = runtime.tool_gateway
    approval_gate = runtime.approval_gate

    # --------------------------------------------------
    # TEST 1: REQUEST HIGH-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 1: REQUEST HIGH-RISK TOOL")

    original_context = {
        "tournament_name": "ORIGINAL APPROVED TOURNAMENT",
        "time": "21:00",
    }

    result = await gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create the original approved tournament",
        context=original_context,
    )

    print(result)

    if not result.data or not result.data.get("request_id"):
        print("\nTAMPERING TEST: FAIL")
        print("No approval request was created.")
        return

    request_id = result.data["request_id"]

    print("\nREQUEST ID:")
    print(request_id)

    # --------------------------------------------------
    # TEST 2: VERIFY ORIGINAL APPROVAL CONTEXT
    # --------------------------------------------------

    print("\nTEST 2: VERIFY APPROVAL CONTEXT")

    request = approval_gate.get(request_id)

    print(request)

    if request is None:
        print("\nTAMPERING TEST: FAIL")
        print("Approval request not found.")
        return

    if request.context != original_context:
        print("\nTAMPERING TEST: FAIL")
        print("Original context was not stored correctly.")
        return

    print("ORIGINAL CONTEXT: PASS")

    # --------------------------------------------------
    # TEST 3: APPROVE REQUEST
    # --------------------------------------------------

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    # --------------------------------------------------
    # TEST 4: ATTEMPT CONTEXT TAMPERING
    # --------------------------------------------------

    print("\nTEST 4: ATTEMPT CONTEXT TAMPERING")

    tampered_context = {
        "tournament_name": "TAMPERED TOURNAMENT",
        "time": "23:59",
    }

    print("Original context:")
    print(original_context)

    print("Tampered context:")
    print(tampered_context)

    tampered_result = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context=tampered_context,
    )

    print("\nEXECUTION RESULT:")
    print(tampered_result)

    # --------------------------------------------------
    # TEST 5: VERIFY APPROVED CONTEXT WAS USED
    # --------------------------------------------------

    print("\nTEST 5: VERIFY APPROVED CONTEXT")

    if not tampered_result.success:
        print("EXECUTION: FAIL")
        print("Approved request could not execute.")
        return

    tournament = tampered_result.data.get("tournament", {})

    executed_name = tournament.get("name")
    executed_time = tournament.get("time")

    print("Executed tournament name:", executed_name)
    print("Executed tournament time:", executed_time)

    if (
        executed_name == original_context["tournament_name"]
        and executed_time == original_context["time"]
    ):
        print("CONTEXT INTEGRITY: PASS")
        print(
            "Tampered context was ignored. "
            "Original approved context was executed."
        )
    else:
        print("CONTEXT INTEGRITY: FAIL")
        print(
            "Execution used context different from "
            "the approved context."
        )

    # --------------------------------------------------
    # TEST 6: VERIFY REPLAY IS STILL BLOCKED
    # --------------------------------------------------

    print("\nTEST 6: REPLAY AFTER EXECUTION")

    replay_result = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context=tampered_context,
    )

    print(replay_result)

    if not replay_result.success:
        print("REPLAY PROTECTION: PASS")
    else:
        print("REPLAY PROTECTION: FAIL")

    # --------------------------------------------------
    # TEST 7: FINAL APPROVAL STATUS
    # --------------------------------------------------

    print("\nTEST 7: FINAL APPROVAL STATUS")

    final_request = approval_gate.get(request_id)

    print(final_request)

    # --------------------------------------------------
    # FINAL SECURITY VERIFICATION
    # --------------------------------------------------

    context_safe = (
        tampered_result.success
        and executed_name == original_context["tournament_name"]
        and executed_time == original_context["time"]
    )

    replay_safe = not replay_result.success

    executed_state = (
        final_request is not None
        and final_request.status.value == "executed"
    )

    print("\nSECURITY VERIFICATION")

    if context_safe:
        print("APPROVAL CONTEXT INTEGRITY: PASS")
    else:
        print("APPROVAL CONTEXT INTEGRITY: FAIL")

    if replay_safe:
        print("APPROVAL REPLAY PROTECTION: PASS")
    else:
        print("APPROVAL REPLAY PROTECTION: FAIL")

    if executed_state:
        print("APPROVAL STATE TRANSITION: PASS")
    else:
        print("APPROVAL STATE TRANSITION: FAIL")

    if context_safe and replay_safe and executed_state:
        print("\nAPPROVAL TAMPERING SECURITY: PASS")
        print(
            "Approved execution remained bound to the "
            "original authorization context."
        )
    else:
        print("\nAPPROVAL TAMPERING SECURITY: FAIL")

    print("\n" + "=" * 50)
    print("APPROVAL TAMPERING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




