import asyncio
from core.cortex_bootstrap import bootstrap_cortex


async def main():
    print("CORTEX ORION RUNTIME END-TO-END SECURITY TEST")
    print("=" * 60)

    runtime = bootstrap_cortex()

    # --------------------------------------------------
    # TEST 1: ORION NATURAL LANGUAGE INTENT
    # --------------------------------------------------

    print("\nTEST 1: ORION NATURAL LANGUAGE INTENT")

    intent = runtime.intent_engine.parse(
        "Check match information"
    )

    print(intent)

    assert intent.success is True
    assert intent.agent_id == "ORION"
    assert intent.action == "read_match_data"

    print("ORION INTENT: PASS")

    # --------------------------------------------------
    # TEST 2: ORION TOOL REGISTRATION
    # --------------------------------------------------

    print("\nTEST 2: ORION TOOL REGISTRATION")

    read_tool = runtime.tool_registry.get(
        "read_match_data"
    )

    manage_tool = runtime.tool_registry.get(
        "manage_match"
    )

    print(read_tool)
    print(manage_tool)

    assert read_tool is not None
    assert read_tool.name == "read_match_data"
    assert read_tool.required_action == "read_match_data"

    assert manage_tool is not None
    assert manage_tool.name == "manage_match"
    assert manage_tool.required_action == "manage_match"

    print("ORION TOOL REGISTRATION: PASS")

    # --------------------------------------------------
    # TEST 3: LOW-RISK MATCH READ
    # --------------------------------------------------

    print("\nTEST 3: ORION LOW-RISK EXECUTION")

    result = await runtime.execute_intent(
        "Check match information",
        context={
            "match_id": "M1",
        },
    )

    print(result)

    assert result.success is True
    assert result.agent_id == "ORION"
    assert result.data["intent_agent"] == "ORION"
    assert result.data["intent_action"] == "read_match_data"
    assert result.data["tool"] == "read_match_data"

    print("ORION LOW-RISK EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 4: VERIFY MATCH RESULT
    # --------------------------------------------------

    print("\nTEST 4: ORION MATCH RESULT")

    result_data = result.data["result"]

    print(result_data)

    assert isinstance(result_data, dict)
    assert result_data.get("status") == "ok"
    assert result_data["match"]["id"] == "M1"

    print("ORION TOOL RESULT: PASS")

    # --------------------------------------------------
    # TEST 5: HIGH-RISK MATCH MANAGEMENT
    # --------------------------------------------------

    print("\nTEST 5: ORION HIGH-RISK APPROVAL GATE")

    result = await runtime.execute_intent(
        "Manage match",
        context={
            "match_id": "M1",
            "updates": {
                "status": "completed",
                "winner": "P1",
            },
        },
    )

    print(result)

    assert result.success is False
    assert result.agent_id == "ORION"
    assert result.data["intent_action"] == "manage_match"
    assert result.data["decision"] == "review"
    assert result.data["risk"] == "high"
    assert result.data["request_id"] is not None

    print("ORION APPROVAL GATE: PASS")

    # --------------------------------------------------
    # TEST 6: VERIFY APPROVAL BINDING
    # --------------------------------------------------

    print("\nTEST 6: ORION APPROVAL BINDING")

    pending = runtime.pending_approvals()

    print(f"Pending approvals: {len(pending)}")

    assert len(pending) >= 1

    latest = pending[-1]

    print(latest)

    # Agent/action/tool binding
    assert latest.agent_id == "ORION"
    assert latest.action == "manage_match"
    assert latest.tool_name == "manage_match"

    # Approved context binding
    assert latest.context is not None
    assert latest.context["match_id"] == "M1"
    assert latest.context["updates"]["status"] == "completed"
    assert latest.context["updates"]["winner"] == "P1"

    print("ORION APPROVAL BINDING: PASS")

    # --------------------------------------------------
    # TEST 7: UNKNOWN INTENT BLOCK
    # --------------------------------------------------

    print("\nTEST 7: ORION UNKNOWN INTENT BLOCK")

    result = await runtime.execute_intent(
        "Do something completely unrelated"
    )

    print(result)

    assert result.success is False
    assert result.agent_id == "UNKNOWN"

    print("ORION UNKNOWN INTENT BLOCK: PASS")

    # --------------------------------------------------
    # TEST 8: AUDIT VERIFICATION
    # --------------------------------------------------

    print("\nTEST 8: ORION AUDIT VERIFICATION")

    events = runtime.audit_events()

    for event in events:
        print(event)

    orion_events = [
        event
        for event in events
        if event.agent_id == "ORION"
    ]

    assert len(orion_events) >= 2

    print("ORION AUDIT: PASS")

    # --------------------------------------------------
    # FINAL
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("ORION SECURITY VERIFICATION")
    print("-" * 60)

    print("ORION INTENT: PASS")
    print("ORION TOOL REGISTRATION: PASS")
    print("ORION LOW-RISK EXECUTION: PASS")
    print("ORION TOOL RESULT: PASS")
    print("ORION HIGH-RISK APPROVAL GATE: PASS")
    print("ORION APPROVAL BINDING: PASS")
    print("ORION UNKNOWN INTENT BLOCK: PASS")
    print("ORION AUDIT: PASS")

    print("\nCORTEX ORION RUNTIME: PASS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())




