import asyncio
from core.cortex_bootstrap import bootstrap_cortex


async def main():
    print("CORTEX LYRA RUNTIME END-TO-END TEST")
    print("=" * 60)

    runtime = bootstrap_cortex()

    # --------------------------------------------------
    # TEST 1: LYRA NATURAL LANGUAGE INTENT
    # --------------------------------------------------

    print("\nTEST 1: LYRA NATURAL LANGUAGE INTENT")

    intent = runtime.intent_engine.parse(
        "Send notification to player"
    )

    print(intent)

    assert intent.success is True
    assert intent.agent_id == "LYRA"
    assert intent.action == "send_notification"

    print("LYRA INTENT: PASS")

    # --------------------------------------------------
    # TEST 2: LYRA TOOL REGISTRATION
    # --------------------------------------------------

    print("\nTEST 2: LYRA TOOL REGISTRATION")

    tool = runtime.tool_registry.get(
        "send_notification"
    )

    print(tool)

    assert tool is not None
    assert tool.name == "send_notification"
    assert tool.required_action == "send_notification"

    print("LYRA TOOL REGISTRATION: PASS")

    # --------------------------------------------------
    # TEST 3: LYRA NATURAL LANGUAGE EXECUTION
    # MEDIUM RISK -> APPROVAL REQUIRED
    # --------------------------------------------------

    print("\nTEST 3: LYRA NATURAL LANGUAGE EXECUTION")

    result = await runtime.execute_intent(
        "Send notification to player",
        context={
            "player_id": "P1",
            "message": "CORTEX LYRA test notification",
        },
    )

    print(result)

    assert result.agent_id == "LYRA"
    assert result.data["intent_agent"] == "LYRA"
    assert result.data["intent_action"] == "send_notification"

    # send_notification is MEDIUM risk.
    # Therefore execution must stop for approval.
    assert result.success is False
    assert result.data["decision"] == "review"
    assert result.data["risk"] == "medium"
    assert result.data["request_id"] is not None

    request_id = result.data["request_id"]

    print("LYRA MEDIUM-RISK APPROVAL GATE: PASS")

    # --------------------------------------------------
    # TEST 4: LYRA APPROVAL
    # --------------------------------------------------

    print("\nTEST 4: LYRA APPROVAL")

    approval = runtime.approve_request(request_id)

    print(approval)

    assert approval is not None
    assert approval.request_id == request_id
    assert approval.agent_id == "LYRA"
    assert approval.action == "send_notification"
    assert approval.status.value == "approved"

    print("LYRA APPROVAL: PASS")

    # --------------------------------------------------
    # TEST 5: LYRA APPROVED TOOL EXECUTION
    # --------------------------------------------------

    print("\nTEST 5: LYRA APPROVED TOOL EXECUTION")

    approved_result = await runtime.tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="LYRA",
    )

    print(approved_result)

    assert approved_result.success is True
    assert approved_result.agent_id == "LYRA"
    assert approved_result.tool_name == "send_notification"

    tool_result = approved_result.data

    print(tool_result)

    assert tool_result["status"] == "sent"
    assert "notification" in tool_result

    notification = tool_result["notification"]

    assert notification["player_id"] == "P1"
    assert notification["message"] == (
        "CORTEX LYRA test notification"
    )
    assert notification["status"] == "sent"

    print("LYRA APPROVED TOOL EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 6: LYRA APPROVAL REPLAY PROTECTION
    # --------------------------------------------------

    print("\nTEST 6: LYRA APPROVAL REPLAY PROTECTION")

    replay_result = await runtime.tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="LYRA",
    )

    print(replay_result)

    assert replay_result.success is False
    assert "executed" in replay_result.message.lower()

    print("LYRA REPLAY PROTECTION: PASS")

    # --------------------------------------------------
    # TEST 7: LYRA AUDIT
    # --------------------------------------------------

    print("\nTEST 7: LYRA AUDIT")

    events = runtime.audit_events()

    for event in events:
        print(event)

    assert len(events) >= 1

    # Find the successful LYRA notification execution.
    lyra_events = [
        event
        for event in events
        if event.agent_id == "LYRA"
        and event.action == "send_notification"
    ]

    assert len(lyra_events) >= 1

    successful_events = [
        event
        for event in lyra_events
        if event.success is True
    ]

    assert len(successful_events) >= 1

    latest_successful_event = successful_events[-1]

    assert latest_successful_event.agent_id == "LYRA"
    assert latest_successful_event.action == "send_notification"
    assert latest_successful_event.success is True

    print("LYRA AUDIT: PASS")

    # --------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("LYRA SECURITY VERIFICATION")
    print("-" * 60)

    print("LYRA INTENT: PASS")
    print("LYRA TOOL REGISTRATION: PASS")
    print("LYRA MEDIUM-RISK APPROVAL GATE: PASS")
    print("LYRA APPROVAL: PASS")
    print("LYRA APPROVED TOOL EXECUTION: PASS")
    print("LYRA REPLAY PROTECTION: PASS")
    print("LYRA AUDIT: PASS")

    print("\nCORTEX LYRA RUNTIME: PASS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())




