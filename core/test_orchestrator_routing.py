import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX ORCHESTRATOR ROUTING INTEGRATION TEST")
    print("=" * 60)

    cortex = build_cortex()

    orchestrator = cortex["orchestrator"]
    registry = cortex["registry"]

    # --------------------------------------------------
    # TEST 1: VERIFY ARIA EXISTS
    # --------------------------------------------------

    print("\nTEST 1: VERIFY VALID AGENT")

    aria = registry.get("ARIA")

    if aria is None:
        print("VALID AGENT LOOKUP: FAIL")
        return

    print(aria.info())
    print("VALID AGENT LOOKUP: PASS")

    # --------------------------------------------------
    # TEST 2: DISPATCH LOW-RISK TASK
    # --------------------------------------------------

    print("\nTEST 2: DISPATCH READ TASK")

    result = await orchestrator.dispatch(
        agent_id="ARIA",
        action="read_tournament",
        task="Read orchestrator routing test tournament",
        context={
            "tournament_name": "ORCHESTRATOR ROUTING TEST",
        },
    )

    print(result)

    if not result.success:
        print("VALID DISPATCH: FAIL")
        return

    if result.agent != "ARIA":
        print("AGENT ROUTING: FAIL")
        return

    if result.data.get("action") != "read_tournament":
        print("ACTION ROUTING: FAIL")
        return

    if result.data.get("decision") != "allow":
        print("DECISION ROUTING: FAIL")
        return

    print("VALID DISPATCH: PASS")
    print("AGENT ROUTING: PASS")
    print("ACTION ROUTING: PASS")
    print("DECISION ROUTING: PASS")

    # --------------------------------------------------
    # TEST 3: UNKNOWN AGENT
    # --------------------------------------------------

    print("\nTEST 3: UNKNOWN AGENT BLOCK")

    unknown_result = await orchestrator.dispatch(
        agent_id="UNKNOWN_AGENT",
        action="read_tournament",
        task="Unauthorized routing test",
        context={},
    )

    print(unknown_result)

    if (
        not unknown_result.success
        and unknown_result.agent == "UNKNOWN_AGENT"
    ):
        print("UNKNOWN AGENT BLOCK: PASS")
    else:
        print("UNKNOWN AGENT BLOCK: FAIL")
        return

    # --------------------------------------------------
    # TEST 4: DISABLED AGENT
    # --------------------------------------------------

    print("\nTEST 4: DISABLED AGENT BLOCK")

    original_enabled = aria.enabled
    aria.enabled = False

    disabled_result = await orchestrator.dispatch(
        agent_id="ARIA",
        action="read_tournament",
        task="Disabled agent routing test",
        context={},
    )

    print(disabled_result)

    if (
        not disabled_result.success
        and "disabled" in disabled_result.message.lower()
    ):
        print("DISABLED AGENT BLOCK: PASS")
    else:
        print("DISABLED AGENT BLOCK: FAIL")
        aria.enabled = original_enabled
        return

    # --------------------------------------------------
    # TEST 5: RESTORE AGENT
    # --------------------------------------------------

    print("\nTEST 5: RESTORE ARIA")

    aria.enabled = original_enabled

    if aria.enabled:
        print("AGENT RESTORE: PASS")
    else:
        print("AGENT RESTORE: FAIL")
        return

    # --------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------

    print("\nSECURITY VERIFICATION")
    print("-" * 60)
    print("VALID AGENT LOOKUP: PASS")
    print("VALID DISPATCH: PASS")
    print("AGENT ROUTING: PASS")
    print("ACTION ROUTING: PASS")
    print("DECISION ROUTING: PASS")
    print("UNKNOWN AGENT BLOCK: PASS")
    print("DISABLED AGENT BLOCK: PASS")
    print("AGENT RESTORE: PASS")

    print("\nORCHESTRATOR ROUTING: PASS")
    print(
        "CORTEX correctly routed valid tasks through the "
        "controller and blocked invalid or disabled agents."
    )

    print("\n" + "=" * 60)
    print("CORTEX ORCHESTRATOR ROUTING INTEGRATION TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




