import asyncio
from core.cortex_bootstrap import bootstrap_cortex


async def main():
    print("CORTEX INTENT RUNTIME END-TO-END SECURITY TEST")
    print("=" * 60)

    runtime = bootstrap_cortex()

    # --------------------------------------------------
    # TEST 1: INTENT ENGINE
    # --------------------------------------------------

    print("\nTEST 1: NATURAL LANGUAGE INTENT")

    intent = runtime.intent_engine.parse(
        "Create a new tournament"
    )

    print(intent)

    assert intent.success is True
    assert intent.agent_id == "ARIA"
    assert intent.action == "create_tournament"

    print("INTENT PARSING: PASS")

    # --------------------------------------------------
    # TEST 2: LOW-RISK NATURAL LANGUAGE EXECUTION
    # --------------------------------------------------

    print("\nTEST 2: LOW-RISK NATURAL LANGUAGE EXECUTION")

    result = await runtime.execute_intent(
        "Check tournament"
    )

    print(result)

    assert result.agent_id == "ARIA"
    assert result.data["intent_agent"] == "ARIA"
    assert result.data["intent_action"] == "read_tournament"

    print("LOW-RISK INTENT EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 3: HIGH-RISK NATURAL LANGUAGE EXECUTION
    # --------------------------------------------------

    print("\nTEST 3: HIGH-RISK NATURAL LANGUAGE EXECUTION")

    result = await runtime.execute_intent(
        "Create a new tournament",
        context={
            "tournament_name": "E2E Security Test",
            "time": "21:00",
        },
    )

    print(result)

    assert result.agent_id == "ARIA"
    assert result.data["intent_agent"] == "ARIA"
    assert result.data["intent_action"] == "create_tournament"
    assert result.data["decision"] == "review"
    assert result.success is False

    print("HIGH-RISK APPROVAL GATE: PASS")

    # --------------------------------------------------
    # TEST 4: VERIFY APPROVAL WAS CREATED
    # --------------------------------------------------

    print("\nTEST 4: VERIFY APPROVAL CREATION")

    pending = runtime.pending_approvals()

    print(f"Pending approvals: {len(pending)}")

    assert len(pending) >= 1

    latest = pending[-1]

    print(latest)

    assert latest.agent_id == "ARIA"
    assert latest.action == "create_tournament"
    assert latest.tool_name == "create_tournament"

    print("APPROVAL BINDING: PASS")

    # --------------------------------------------------
    # TEST 5: UNKNOWN INTENT
    # --------------------------------------------------

    print("\nTEST 5: UNKNOWN INTENT BLOCK")

    result = await runtime.execute_intent(
        "Do something completely unsupported"
    )

    print(result)

    assert result.success is False
    assert result.agent_id == "UNKNOWN"

    print("UNKNOWN INTENT BLOCK: PASS")

    # --------------------------------------------------
    # TEST 6: EMPTY INTENT
    # --------------------------------------------------

    print("\nTEST 6: EMPTY INTENT BLOCK")

    result = await runtime.execute_intent("")

    print(result)

    assert result.success is False
    assert result.agent_id == "UNKNOWN"

    print("EMPTY INTENT BLOCK: PASS")

    # --------------------------------------------------
    # TEST 7: AUDIT
    # --------------------------------------------------

    print("\nTEST 7: AUDIT VERIFICATION")

    events = runtime.audit_events()

    for event in events:
        print(event)

    assert len(events) >= 2

    print("AUDIT INTEGRATION: PASS")

    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("SECURITY VERIFICATION")
    print("-" * 60)

    print("INTENT PARSING: PASS")
    print("LOW-RISK INTENT EXECUTION: PASS")
    print("HIGH-RISK APPROVAL GATE: PASS")
    print("APPROVAL BINDING: PASS")
    print("UNKNOWN INTENT BLOCK: PASS")
    print("EMPTY INTENT BLOCK: PASS")
    print("AUDIT INTEGRATION: PASS")

    print("\nCORTEX FOUNDATION END-TO-END: PASS")
    print(
        "Natural-language requests are routed through the "
        "CORTEX security pipeline without bypassing controls."
    )

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())




