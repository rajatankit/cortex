import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX PERMISSION REVOCATION TEST")
    print("=" * 50)

    cortex = build_cortex()

    tool_gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]
    permissions = cortex["permissions"]
    audit_logger = cortex["audit_logger"]

    agent_id = "ARIA"
    tool_name = "create_tournament"
    action = "create_tournament"

    # --------------------------------------------------
    # TEST 1 — VERIFY PERMISSION EXISTS
    # --------------------------------------------------

    print("\nTEST 1: INITIAL PERMISSION")

    print(
        "Allowed:",
        permissions.is_allowed(agent_id, action)
    )

    print(
        "Risk:",
        permissions.get_risk(agent_id, action)
    )

    # --------------------------------------------------
    # TEST 2 — REQUEST HIGH-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 2: REQUEST HIGH-RISK TOOL")

    result = await tool_gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task="Create tournament before permission revocation",
        context={
            "tournament_name": "Security Test Tournament",
            "time": "21:00",
        },
    )

    print(result)

    request_id = result.data.get("request_id")

    if not request_id:
        print("\nERROR: Approval request was not created.")
        return

    # --------------------------------------------------
    # TEST 3 — APPROVE REQUEST
    # --------------------------------------------------

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    # --------------------------------------------------
    # TEST 4 — REVOKE PERMISSION AFTER APPROVAL
    # --------------------------------------------------

    print("\nTEST 4: REVOKE PERMISSION")

    revoked = permissions.revoke(
        agent_id,
        action,
    )

    print("Permission revoked:", revoked)

    print(
        "Allowed after revoke:",
        permissions.is_allowed(agent_id, action)
    )

    # --------------------------------------------------
    # TEST 5 — TRY EXECUTION AFTER REVOCATION
    # --------------------------------------------------

    print("\nTEST 5: EXECUTION AFTER REVOCATION")

    execution = await tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context={
            "tournament_name": "Security Test Tournament",
            "time": "21:00",
        },
    )

    print(execution)

    # --------------------------------------------------
    # TEST 6 — SECURITY VERIFICATION
    # --------------------------------------------------

    print("\nTEST 6: SECURITY VERIFICATION")

    if not execution.success:
        print("PERMISSION REVOCATION: PASS")
        print("Execution correctly blocked after permission removal.")
    else:
        print("PERMISSION REVOCATION: FAILED")
        print("SECURITY ISSUE: Tool executed after permission removal.")

    # --------------------------------------------------
    # TEST 7 — AUDIT LOG
    # --------------------------------------------------

    print("\nTEST 7: AUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nAUDIT COUNT:")
    print(audit_logger.count())

    print("\n" + "=" * 50)
    print("PERMISSION REVOCATION TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




