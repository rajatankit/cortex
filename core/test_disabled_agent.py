import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX DISABLED AGENT SECURITY TEST")
    print("=" * 50)

    cortex = build_cortex()

    registry = cortex["registry"]
    tool_gateway = cortex["tool_gateway"]
    permissions = cortex["permissions"]
    audit_logger = cortex["audit_logger"]

    agent_id = "ARIA"
    tool_name = "read_tournament"
    action = "read_tournament"

    # --------------------------------------------------
    # TEST 1 — VERIFY AGENT EXISTS
    # --------------------------------------------------

    print("\nTEST 1: AGENT STATUS")

    agent = registry.get(agent_id)

    if agent is None:
        print("ERROR: ARIA is not registered.")
        return

    print("Agent:", agent.info())
    print("Enabled:", agent.enabled)

    # --------------------------------------------------
    # TEST 2 — VERIFY PERMISSION EXISTS
    # --------------------------------------------------

    print("\nTEST 2: PERMISSION")

    allowed_before = permissions.is_allowed(
        agent_id,
        action,
    )

    print("Permission allowed:", allowed_before)

    # --------------------------------------------------
    # TEST 3 — DISABLE AGENT
    # --------------------------------------------------

    print("\nTEST 3: DISABLE AGENT")

    agent.enabled = False

    print("Enabled after disable:", agent.enabled)

    # --------------------------------------------------
    # TEST 4 — TRY TOOL EXECUTION
    # --------------------------------------------------

    print("\nTEST 4: DISABLED AGENT EXECUTION")

    result = await tool_gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task="Read tournament while agent is disabled",
        context={},
    )

    print(result)

    # --------------------------------------------------
    # TEST 5 — SECURITY VERIFICATION
    # --------------------------------------------------

    print("\nTEST 5: SECURITY VERIFICATION")

    if not result.success:
        print("DISABLED AGENT SECURITY: PASS")
        print("Disabled agent was blocked from execution.")
    else:
        print("DISABLED AGENT SECURITY: FAILED")
        print("SECURITY ISSUE: Disabled agent executed a tool.")

    # --------------------------------------------------
    # TEST 6 — RESTORE AGENT
    # --------------------------------------------------

    print("\nTEST 6: RESTORE AGENT")

    agent.enabled = True

    print("Enabled after restore:", agent.enabled)

    # --------------------------------------------------
    # TEST 7 — VERIFY EXECUTION AFTER RESTORE
    # --------------------------------------------------

    print("\nTEST 7: EXECUTION AFTER RESTORE")

    restored_result = await tool_gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task="Read tournament after agent restore",
        context={},
    )

    print(restored_result)

    if restored_result.success:
        print("AGENT RESTORE: PASS")
    else:
        print("AGENT RESTORE: FAILED")

    # --------------------------------------------------
    # TEST 8 — AUDIT LOG
    # --------------------------------------------------

    print("\nTEST 8: AUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nAUDIT COUNT:")
    print(audit_logger.count())

    print("\n" + "=" * 50)
    print("DISABLED AGENT SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




