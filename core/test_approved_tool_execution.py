import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVED TOOL EXECUTION TEST")
    print("=" * 50)

    cortex = build_cortex()

    tool_gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]
    audit_logger = cortex["audit_logger"]

    # --------------------------------------------------
    # TEST 1 — REQUEST HIGH-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 1: REQUEST HIGH-RISK TOOL")

    result = await tool_gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create a new tournament",
        context={
            "tournament_name": "CORTEX Approved Tournament",
            "time": "20:00",
        },
    )

    print(result)

    if result.success:
        print("\nERROR: High-risk tool executed without approval.")
        return

    request_id = result.data.get("request_id")

    if not request_id:
        print("\nERROR: No approval request ID returned.")
        return

    print("\nAPPROVAL REQUEST ID:")
    print(request_id)

    # --------------------------------------------------
    # TEST 2 — CHECK PENDING APPROVAL
    # --------------------------------------------------

    print("\nTEST 2: PENDING APPROVAL")

    pending = approval_gate.list_pending()

    for request in pending:
        print(request)

    # --------------------------------------------------
    # TEST 3 — APPROVE REQUEST
    # --------------------------------------------------

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    # --------------------------------------------------
    # TEST 4 — EXECUTE AFTER APPROVAL
    # --------------------------------------------------

    print("\nTEST 4: APPROVED TOOL EXECUTION")

    execution = await tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context={
            "tournament_name": "CORTEX Approved Tournament",
            "time": "20:00",
        },
    )

    print(execution)

    # --------------------------------------------------
    # TEST 5 — VERIFY RESULT
    # --------------------------------------------------

    print("\nTEST 5: VERIFY EXECUTION RESULT")

    if execution.success:
        print("APPROVED EXECUTION: PASS")
    else:
        print("APPROVED EXECUTION: FAILED")

    # --------------------------------------------------
    # TEST 6 — AUDIT LOG
    # --------------------------------------------------

    print("\nTEST 6: AUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nAUDIT COUNT:")
    print(audit_logger.count())

    print("\n" + "=" * 50)
    print("APPROVED TOOL EXECUTION TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




