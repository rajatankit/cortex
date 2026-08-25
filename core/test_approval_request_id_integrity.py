import asyncio
from dataclasses import replace
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL REQUEST-ID INTEGRITY SECURITY TEST")
    print("=" * 58)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    agent_id = "ARIA"
    tool_name = "create_tournament"

    original_task = "Create request-ID integrity test tournament"

    original_context = {
        "tournament_name": "REQUEST ID INTEGRITY TEST TOURNAMENT",
        "time": "22:00",
    }

    print("\nTEST 1: CREATE ORIGINAL APPROVAL REQUEST")

    result = await gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task=original_task,
        context=original_context,
    )

    print(result)

    if result.success:
        print("TEST FAILED: High-risk request executed without approval.")
        return

    if not result.data:
        print("TEST FAILED: No approval data returned.")
        return

    request_id = result.data.get("request_id")

    if not request_id:
        print("TEST FAILED: No request ID returned.")
        return

    print("\nORIGINAL REQUEST ID:")
    print(request_id)

    original_request = approval_gate.get(request_id)

    if original_request is None:
        print("TEST FAILED: Original approval request not found.")
        return

    print("\nORIGINAL APPROVAL REQUEST:")
    print(original_request)

    print("\nTEST 2: VERIFY REQUEST-ID SELF INTEGRITY")

    if original_request.request_id == request_id:
        print("REQUEST-ID SELF INTEGRITY: PASS")
    else:
        print("REQUEST-ID SELF INTEGRITY: FAIL")
        return

    print("\nTEST 3: APPROVE ORIGINAL REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.status.value != "approved":
        print("APPROVAL: FAIL")
        return

    print("APPROVAL: PASS")

    print("\nTEST 4: CREATE FAKE REQUEST ID")

    fake_request_id = "00000000-0000-0000-0000-000000000000"

    print("Original request ID:")
    print(request_id)

    print("\nFake request ID:")
    print(fake_request_id)

    fake_lookup = approval_gate.get(fake_request_id)

    if fake_lookup is None:
        print("FAKE REQUEST LOOKUP: PASS")
        print("Unknown request ID was not accepted.")
    else:
        print("FAKE REQUEST LOOKUP: FAIL")
        print("Unknown request ID returned an approval.")
        return

    print("\nTEST 5: ATTEMPT EXECUTION WITH FAKE REQUEST ID")

    fake_execution = await gateway.approve_and_execute(
        request_id=fake_request_id,
        agent_id=agent_id,
        context=original_context,
    )

    print(fake_execution)

    if not fake_execution.success:
        print("FAKE REQUEST EXECUTION BLOCK: PASS")
        print("Fake request ID could not execute an approved action.")
    else:
        print("FAKE REQUEST EXECUTION BLOCK: FAIL")
        return

    print("\nTEST 6: ATTEMPT REQUEST-ID SUBSTITUTION")

    # Create a second legitimate approval request.
    second_context = {
        "tournament_name": "SECOND REQUEST TOURNAMENT",
        "time": "23:00",
    }

    second_result = await gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task="Create second request-ID integrity test tournament",
        context=second_context,
    )

    print(second_result)

    if second_result.success:
        print("TEST FAILED: Second request executed without approval.")
        return

    if not second_result.data:
        print("TEST FAILED: Second approval data missing.")
        return

    second_request_id = second_result.data.get("request_id")

    if not second_request_id:
        print("TEST FAILED: Second request ID missing.")
        return

    if second_request_id == request_id:
        print("TEST FAILED: Two approval requests received the same ID.")
        return

    print("\nFIRST REQUEST ID:")
    print(request_id)

    print("\nSECOND REQUEST ID:")
    print(second_request_id)

    print("REQUEST-ID UNIQUENESS: PASS")

    print("\nTEST 7: VERIFY REQUESTS ARE NOT INTERCHANGEABLE")

    first_request = approval_gate.get(request_id)
    second_request = approval_gate.get(second_request_id)

    if first_request is None or second_request is None:
        print("REQUEST LOOKUP: FAIL")
        return

    if first_request.request_id != request_id:
        print("FIRST REQUEST ID INTEGRITY: FAIL")
        return

    if second_request.request_id != second_request_id:
        print("SECOND REQUEST ID INTEGRITY: FAIL")
        return

    if first_request.context == second_request.context:
        print("REQUEST SEPARATION: FAIL")
        print("Both approvals contain identical contexts.")
        return

    print("REQUEST SEPARATION: PASS")
    print("Each request remains bound to its own request ID and context.")

    print("\nTEST 8: APPROVE SECOND REQUEST")

    approved_second = approval_gate.approve(second_request_id)

    print(approved_second)

    if approved_second.status.value != "approved":
        print("SECOND APPROVAL: FAIL")
        return

    print("SECOND APPROVAL: PASS")

    print("\nTEST 9: EXECUTE FIRST REQUEST USING ITS ORIGINAL ID")

    first_execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context={
            "tournament_name": "TAMPERED FIRST CONTEXT",
            "time": "23:59",
        },
    )

    print(first_execution)

    if not first_execution.success:
        print("FIRST REQUEST EXECUTION: FAIL")
        print(first_execution.message)
        return

    executed_name = (
        first_execution.data
        .get("tournament", {})
        .get("name")
    )

    executed_time = (
        first_execution.data
        .get("tournament", {})
        .get("time")
    )

    if executed_name != original_context["tournament_name"]:
        print("FIRST REQUEST CONTEXT: FAIL")
        print("Execution was not bound to the original approval.")
        return

    if executed_time != original_context["time"]:
        print("FIRST REQUEST CONTEXT: FAIL")
        print("Execution was not bound to the original approval.")
        return

    print("FIRST REQUEST EXECUTION: PASS")
    print("Execution remained bound to the original approval context.")

    print("\nTEST 10: VERIFY SECOND REQUEST REMAINS UNUSED")

    second_after_first = approval_gate.get(second_request_id)

    print(second_after_first)

    if second_after_first is None:
        print("SECOND REQUEST STATE: FAIL")
        return

    if second_after_first.status.value != "approved":
        print("SECOND REQUEST STATE: FAIL")
        print(
            f"Expected approved, got {second_after_first.status.value}"
        )
        return

    print("SECOND REQUEST REMAINS APPROVED: PASS")
    print("Executing the first request did not consume the second approval.")

    print("\nTEST 11: ATTEMPT REPLAY USING FIRST REQUEST ID")

    replay = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context=original_context,
    )

    print(replay)

    if not replay.success:
        print("REQUEST-ID REPLAY BLOCK: PASS")
        print("Executed request ID cannot be reused.")
    else:
        print("REQUEST-ID REPLAY BLOCK: FAIL")
        return

    print("\nTEST 12: FINAL REQUEST-ID STATE VERIFICATION")

    final_first = approval_gate.get(request_id)
    final_second = approval_gate.get(second_request_id)

    print("\nFIRST REQUEST:")
    print(final_first)

    print("\nSECOND REQUEST:")
    print(final_second)

    if final_first is None or final_second is None:
        print("FINAL STATE: FAIL")
        return

    if final_first.status.value != "executed":
        print("FIRST REQUEST FINAL STATE: FAIL")
        return

    if final_second.status.value != "approved":
        print("SECOND REQUEST FINAL STATE: FAIL")
        return

    print("FINAL REQUEST STATE: PASS")

    print("\nSECURITY VERIFICATION")
    print("-" * 58)

    print("REQUEST-ID SELF INTEGRITY: PASS")
    print("UNKNOWN REQUEST-ID BLOCK: PASS")
    print("REQUEST-ID UNIQUENESS: PASS")
    print("REQUEST SEPARATION: PASS")
    print("REQUEST-ID REPLAY PROTECTION: PASS")
    print("REQUEST-ID STATE ISOLATION: PASS")

    print("\nAPPROVAL REQUEST-ID INTEGRITY: PASS")
    print(
        "Approval requests remained uniquely bound to their own "
        "request IDs and could not be substituted or replayed."
    )

    print("\n" + "=" * 58)
    print("APPROVAL REQUEST-ID INTEGRITY SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




