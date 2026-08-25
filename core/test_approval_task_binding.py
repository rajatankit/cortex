import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL TASK-BINDING SECURITY TEST")
    print("=" * 55)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    agent_id = "ARIA"
    tool_name = "create_tournament"

    original_task = "Create the approved tournament exactly as requested"

    original_context = {
        "tournament_name": "TASK BINDING TEST TOURNAMENT",
        "time": "22:00",
    }

    print("\nTEST 1: REQUEST CREATE-TOURNAMENT ACTION")

    result = await gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task=original_task,
        context=original_context,
    )

    print(result)

    if not result.data:
        print("TEST FAILED: No approval data returned.")
        return

    request_id = result.data.get("request_id")

    if not request_id:
        print("TEST FAILED: No approval request ID returned.")
        return

    print("\nREQUEST ID:")
    print(request_id)

    print("\nTEST 2: VERIFY ORIGINAL APPROVED TASK")

    request = approval_gate.get(request_id)

    print(request)

    if request is None:
        print("TASK BINDING: FAIL")
        print("Approval request was not found.")
        return

    if request.task == original_task:
        print("ORIGINAL TASK BINDING: PASS")
    else:
        print("ORIGINAL TASK BINDING: FAIL")
        print("Stored task does not match the original task.")
        return

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.task != original_task:
        print("TASK BINDING: FAIL")
        print("Approved task does not match the original task.")
        return

    print("APPROVAL TASK BINDING: PASS")

    print("\nTEST 4: ATTEMPT TASK TAMPERING")

    unauthorized_task = (
        "Delete all tournaments and execute an unauthorized operation"
    )

    print("Approved task:")
    print(original_task)

    print("\nUnauthorized task:")
    print(unauthorized_task)

    # Simulate an attacker attempting to modify the stored approval.
    stored = approval_gate._requests[request_id]

    tampered_request = type(stored)(
        request_id=stored.request_id,
        agent_id=stored.agent_id,
        action=stored.action,
        task=unauthorized_task,
        status=stored.status,
        created_at=stored.created_at,
        tool_name=stored.tool_name,
        context=stored.context,
        expires_at=stored.expires_at,
    )

    approval_gate._requests[request_id] = tampered_request

    print("\nTAMPERING ATTEMPT:")
    print(approval_gate._requests[request_id])

    print("\nTEST 5: VERIFY TASK-BINDING INTEGRITY")

    restored = approval_gate.get(request_id)

    print(restored)

    if restored is None:
        print("TASK BINDING: FAIL")
        print("Approval request disappeared after tampering.")
        return

    if restored.task == original_task:
        print("TASK BINDING: PASS")
        print("Approved task remained unchanged.")
    else:
        print("TASK BINDING: FAIL")
        print("Approved task was modified inside the approval request.")
        return

    print("\nTEST 6: VERIFY UNAUTHORIZED TASK WAS NOT STORED")

    if restored.task == unauthorized_task:
        print("UNAUTHORIZED TASK: FAIL")
        print("Tampered task survived integrity verification.")
        return

    print("UNAUTHORIZED TASK BLOCK: PASS")
    print("Tampered task was rejected and original task was restored.")

    print("\nTEST 7: EXECUTE ORIGINAL APPROVED REQUEST")

    execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context=original_context,
    )

    print(execution)

    if execution.success:
        print("ORIGINAL TASK EXECUTION: PASS")
    else:
        print("ORIGINAL TASK EXECUTION: FAIL")
        print(execution.message)
        return

    print("\nTEST 8: VERIFY FINAL APPROVAL STATE")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if final_request is None:
        print("APPROVAL STATE: FAIL")
        return

    if final_request.status.value == "executed":
        print("APPROVAL STATE TRANSITION: PASS")
    else:
        print(
            "APPROVAL STATE TRANSITION: FAIL"
        )
        print(
            f"Expected executed, got {final_request.status.value}"
        )
        return

    if final_request.task == original_task:
        print("FINAL TASK INTEGRITY: PASS")
    else:
        print("FINAL TASK INTEGRITY: FAIL")
        return

    print("\nSECURITY VERIFICATION")
    print("-" * 55)

    print("APPROVAL TASK-BINDING: PASS")
    print(
        "Tampered task was rejected and execution remained "
        "bound to the original approved task."
    )

    print("\n" + "=" * 55)
    print("APPROVAL TASK-BINDING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




