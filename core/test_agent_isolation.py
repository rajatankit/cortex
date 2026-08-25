import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX AGENT ISOLATION TEST")
    print("=" * 50)

    cortex = build_cortex()

    tool_gateway = cortex["tool_gateway"]
    permissions = cortex["permissions"]
    audit_logger = cortex["audit_logger"]

    # --------------------------------------------------
    # TEST 1 — ARIA PERMISSION
    # --------------------------------------------------

    print("\nTEST 1: ARIA PERMISSION")

    aria_allowed = permissions.is_allowed(
        "ARIA",
        "create_tournament",
    )

    print("ARIA allowed:", aria_allowed)

    # --------------------------------------------------
    # TEST 2 — ELARA PERMISSION
    # --------------------------------------------------

    print("\nTEST 2: ELARA PERMISSION")

    elara_allowed = permissions.is_allowed(
        "ELARA",
        "create_tournament",
    )

    print("ELARA allowed:", elara_allowed)

    # --------------------------------------------------
    # TEST 3 — ELARA TRIES ARIA'S HIGH-RISK ACTION
    # --------------------------------------------------

    print("\nTEST 3: ELARA ATTEMPTS CREATE TOURNAMENT")

    result = await tool_gateway.execute(
        agent_id="ELARA",
        tool_name="create_tournament",
        task="Create a tournament using another agent's permission",
        context={
            "tournament_name": "Isolation Test Tournament",
            "time": "22:00",
        },
    )

    print(result)

    # --------------------------------------------------
    # TEST 4 — SECURITY VERIFICATION
    # --------------------------------------------------

    print("\nTEST 4: SECURITY VERIFICATION")

    if not elara_allowed and not result.success:
        print("AGENT ISOLATION: PASS")
        print("ELARA cannot use ARIA's create_tournament permission.")
    else:
        print("AGENT ISOLATION: FAILED")
        print("SECURITY ISSUE: ELARA accessed an unauthorized action.")

    # --------------------------------------------------
    # TEST 5 — VERIFY ARIA STILL HAS PERMISSION
    # --------------------------------------------------

    print("\nTEST 5: ARIA PERMISSION STILL INTACT")

    aria_after = permissions.is_allowed(
        "ARIA",
        "create_tournament",
    )

    print("ARIA allowed after ELARA attempt:", aria_after)

    # --------------------------------------------------
    # TEST 6 — AUDIT LOG
    # --------------------------------------------------

    print("\nTEST 6: AUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nAUDIT COUNT:")
    print(audit_logger.count())

    print("\n" + "=" * 50)
    print("AGENT ISOLATION TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




