import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL REJECTION SECURITY TEST")
    print("=" * 50)

    cortex = build_cortex()

    tool_gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    # --------------------------------------------------
    # TEST 1 — REQUEST HIGH-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 1: REQUEST HIGH-RISK TOOL")

    result = await tool_gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create tournament that requires approval",
        context={
            "tournament_name": "Rejected Tournament",
            "time": "21:00",
        },
    )

    print(result)

    if result.success:
        print("ERROR: High-risk tool executed without approval.")
        return

    request_id = result.data.get("request_id")

    if not request_id:
        print("ERROR: No approval request ID returned.")
        return

    print("\nREQUEST ID:")
    print(request_id)

    # --------------------------------------------------
    # TEST 2 — VERIFY PENDING REQUEST
    # --------------------------------------------------

    print("\nTEST 2: PENDING APPROVAL")

    request = approval_gate.get(request_id)

    print(request)

    if request is None:
        print("ERROR: Approval request not found.")
        return

    # --------------------------------------------------
    # TEST 3 — REJECT REQUEST
    # --------------------------------------------------

    print("\nTEST 3: REJECT REQUEST")

    rejected = approval_gate.reject(request_id)

    print(rejected)

    if rejected.status.value == "rejected":
        print("REJECTION: PASS")
    else:
        print("REJECTION: FAILED")

    # --------------------------------------------------
    # TEST 4 — TRY EXECUTION AFTER REJECTION
    # --------------------------------------------------

    print("\nTEST 4: EXECUTION AFTER REJECTION")

    execution = await tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context={
            "tournament_name": "Rejected Tournament",
            "time": "21:00",
        },
    )

    print(execution)

    if not execution.success:
        print("POST-REJECTION BLOCK: PASS")
    else:
        print("SECURITY FAILURE: Rejected request executed.")

    # --------------------------------------------------
    # TEST 5 — TRY TO APPROVE REJECTED REQUEST
    # --------------------------------------------------

    print("\nTEST 5: RE-APPROVE REJECTED REQUEST")

    try:
        approval_gate.approve(request_id)
        print("SECURITY FAILURE: Rejected request was approved again.")

    except ValueError as exc:
        print("EXPECTED ERROR:")
        print(exc)
        print("RE-APPROVAL BLOCK: PASS")

    # --------------------------------------------------
    # TEST 6 — VERIFY NO PENDING REQUEST
    # --------------------------------------------------

    print("\nTEST 6: PENDING APPROVALS")

    pending = approval_gate.list_pending()

    print(pending)

    if not any(
        request.request_id == request_id
        for request in pending
    ):
        print("PENDING QUEUE CLEANUP: PASS")
    else:
        print("PENDING QUEUE CLEANUP: FAILED")

    print("\n" + "=" * 50)
    print("APPROVAL REJECTION SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




