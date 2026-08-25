import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX MEDIUM-RISK TOOL TEST")
    print("=" * 50)

    cortex = build_cortex()

    tool_gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]
    audit_logger = cortex["audit_logger"]

    # --------------------------------------------------
    # TEST 1 — MEDIUM-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 1: MANAGE TOURNAMENT")

    result = await tool_gateway.execute(
        agent_id="ARIA",
        tool_name="manage_tournament",
        task="Update tournament status",
        context={
            "tournament_id": "T1",
            "updates": {
                "status": "live",
            },
        },
    )

    print(result)

    # --------------------------------------------------
    # TEST 2 — CHECK DECISION
    # --------------------------------------------------

    print("\nTEST 2: DECISION")

    if result.success:
        print("MEDIUM-RISK TOOL EXECUTED DIRECTLY")
    else:
        print("MEDIUM-RISK TOOL BLOCKED")
        print("Decision:", result.data.get("decision"))

    # --------------------------------------------------
    # TEST 3 — PENDING APPROVAL
    # --------------------------------------------------

    print("\nTEST 3: PENDING APPROVALS")

    pending = approval_gate.list_pending()

    for request in pending:
        print(request)

    # --------------------------------------------------
    # TEST 4 — IF APPROVAL REQUIRED, APPROVE IT
    # --------------------------------------------------

    if pending:
        request = pending[-1]

        print("\nTEST 4: APPROVING REQUEST")

        approved = approval_gate.approve(
            request.request_id
        )

        print(approved)

        # --------------------------------------------------
        # TEST 5 — EXECUTE AFTER APPROVAL
        # --------------------------------------------------

        print("\nTEST 5: APPROVED EXECUTION")

        execution = await tool_gateway.approve_and_execute(
            request_id=request.request_id,
            context={
                "tournament_id": "T1",
                "updates": {
                    "status": "live",
                },
            },
        )

        print(execution)

    # --------------------------------------------------
    # TEST 6 — AUDIT
    # --------------------------------------------------

    print("\nTEST 6: AUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nAUDIT COUNT:")
    print(audit_logger.count())

    print("\n" + "=" * 50)
    print("MEDIUM-RISK TOOL TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




