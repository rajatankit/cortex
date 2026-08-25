import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL REPLAY SECURITY TEST")
    print("=" * 50)

    cortex = build_cortex()

    tool_gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    # --------------------------------------------------
    # TEST 1 — REQUEST HIGH-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 1: REQUEST HIGH-RISK TOOL")

    first_request = await tool_gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create replay-test tournament",
        context={
            "tournament_name": "Replay Test Tournament",
            "time": "22:00",
        },
    )

    print(first_request)

    request_id = first_request.data.get("request_id")

    if not request_id:
        print("ERROR: No approval request ID.")
        return

    # --------------------------------------------------
    # TEST 2 — APPROVE
    # --------------------------------------------------

    print("\nTEST 2: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    # --------------------------------------------------
    # TEST 3 — FIRST EXECUTION
    # --------------------------------------------------

    print("\nTEST 3: FIRST APPROVED EXECUTION")

    execution_1 = await tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context={
            "tournament_name": "Replay Test Tournament",
            "time": "22:00",
        },
    )

    print(execution_1)

    if execution_1.success:
        print("FIRST EXECUTION: PASS")
    else:
        print("FIRST EXECUTION: FAILED")
        return

    # --------------------------------------------------
    # TEST 4 — REPLAY SAME APPROVAL
    # --------------------------------------------------

    print("\nTEST 4: REPLAY SAME APPROVAL")

    execution_2 = await tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context={
            "tournament_name": "Replay Attack Tournament",
            "time": "23:00",
        },
    )

    print(execution_2)

    if not execution_2.success:
        print("REPLAY PROTECTION: PASS")
        print("Previously approved request cannot be reused.")
    else:
        print("SECURITY FAILURE: Approved request was replayed.")

    # --------------------------------------------------
    # TEST 5 — FINAL REQUEST STATUS
    # --------------------------------------------------

    print("\nTEST 5: FINAL APPROVAL STATUS")

    final_request = approval_gate.get(request_id)

    print(final_request)

    print("\n" + "=" * 50)
    print("APPROVAL REPLAY SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




