import asyncio
from core.cortex_bootstrap import bootstrap_cortex


async def main():
    print("CORTEX ELARA RUNTIME END-TO-END SECURITY TEST")
    print("=" * 60)

    runtime = bootstrap_cortex()

    # --------------------------------------------------
    # TEST 1: ELARA NATURAL LANGUAGE INTENT
    # --------------------------------------------------

    print("\nTEST 1: ELARA NATURAL LANGUAGE INTENT")

    intent = runtime.intent_engine.parse(
        "Check player information"
    )

    print(intent)

    assert intent.success is True
    assert intent.agent_id == "ELARA"
    assert intent.action == "read_player_data"

    print("ELARA INTENT: PASS")

    # --------------------------------------------------
    # TEST 2: ELARA TOOL REGISTRATION
    # --------------------------------------------------

    print("\nTEST 2: ELARA TOOL REGISTRATION")

    tool = runtime.tool_registry.get(
        "read_player_data"
    )

    print(tool)

    assert tool is not None
    assert tool.name == "read_player_data"
    assert tool.required_action == "read_player_data"

    print("ELARA TOOL REGISTRATION: PASS")

    # --------------------------------------------------
    # TEST 3: LOW-RISK ELARA EXECUTION
    # --------------------------------------------------

    print("\nTEST 3: ELARA NATURAL LANGUAGE EXECUTION")

    result = await runtime.execute_intent(
        "Check player information",
        context={
            "player_id": "P1",
        },
    )

    print(result)

    assert result.success is True
    assert result.agent_id == "ELARA"
    assert result.data["intent_agent"] == "ELARA"
    assert result.data["intent_action"] == "read_player_data"
    assert result.data["tool"] == "read_player_data"

    print("ELARA NATURAL LANGUAGE EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 4: VERIFY RESULT
    # --------------------------------------------------

    print("\nTEST 4: ELARA TOOL RESULT")

    result_data = result.data["result"]

    print(result_data)

    assert isinstance(result_data, dict)
    assert result_data.get("status") == "ok"

    print("ELARA TOOL EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 5: MEDIUM-RISK UPDATE MUST REQUIRE REVIEW
    # --------------------------------------------------

    print("\nTEST 5: ELARA MEDIUM-RISK APPROVAL GATE")

    result = await runtime.execute_intent(
        "Update player information",
        context={
            "player_id": "P1",
            "name": "Security Test Player",
        },
    )

    print(result)

    assert result.success is False
    assert result.agent_id == "ELARA"
    assert result.data["intent_action"] == "update_player_data"
    assert result.data["decision"] == "review"
    assert result.data["risk"] == "medium"
    assert result.data["request_id"] is not None

    print("ELARA APPROVAL GATE: PASS")

    # --------------------------------------------------
    # TEST 6: VERIFY APPROVAL BINDING
    # --------------------------------------------------

    print("\nTEST 6: ELARA APPROVAL BINDING")

    pending = runtime.pending_approvals()

    print(f"Pending approvals: {len(pending)}")

    assert len(pending) >= 1

    latest = pending[-1]

    print(latest)

    assert latest.agent_id == "ELARA"
    assert latest.action == "update_player_data"
    assert latest.tool_name == "update_player_data"

    print("ELARA APPROVAL BINDING: PASS")

    # --------------------------------------------------
    # TEST 7: UNKNOWN INTENT BLOCK
    # --------------------------------------------------

    print("\nTEST 7: ELARA UNKNOWN INTENT BLOCK")

    result = await runtime.execute_intent(
        "Do something completely unrelated"
    )

    print(result)

    assert result.success is False
    assert result.agent_id == "UNKNOWN"

    print("ELARA UNKNOWN INTENT BLOCK: PASS")

    # --------------------------------------------------
    # TEST 8: AUDIT VERIFICATION
    # --------------------------------------------------

    print("\nTEST 8: ELARA AUDIT VERIFICATION")

    events = runtime.audit_events()

    for event in events:
        print(event)

    elara_events = [
        event
        for event in events
        if event.agent_id == "ELARA"
    ]

    assert len(elara_events) >= 2

    print("ELARA AUDIT: PASS")

    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ELARA SECURITY VERIFICATION")
    print("-" * 60)

    print("ELARA INTENT: PASS")
    print("ELARA TOOL REGISTRATION: PASS")
    print("ELARA LOW-RISK EXECUTION: PASS")
    print("ELARA TOOL RESULT: PASS")
    print("ELARA MEDIUM-RISK APPROVAL GATE: PASS")
    print("ELARA APPROVAL BINDING: PASS")
    print("ELARA UNKNOWN INTENT BLOCK: PASS")
    print("ELARA AUDIT: PASS")

    print("\nCORTEX ELARA RUNTIME: PASS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())




