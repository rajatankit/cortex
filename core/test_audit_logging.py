import asyncio
from core.cortex_bootstrap import build_cortex
from core.decision import Decision


async def main():
    print("CORTEX AUDIT LOGGING SECURITY TEST")
    print("=" * 60)

    cortex = build_cortex()

    controller = cortex["agent_controller"]
    audit_logger = cortex["audit_logger"]

    # Start clean so this test only examines its own events.
    audit_logger.clear()

    # --------------------------------------------------
    # TEST 1: VERIFY CLEAN AUDIT LOG
    # --------------------------------------------------

    print("\nTEST 1: VERIFY CLEAN AUDIT LOG")

    initial_count = audit_logger.count()

    print(f"Initial audit event count: {initial_count}")

    if initial_count == 0:
        print("AUDIT LOG CLEAN: PASS")
    else:
        print("AUDIT LOG CLEAN: FAIL")
        return

    # --------------------------------------------------
    # TEST 2: GENERATE REVIEW EVENT
    # --------------------------------------------------

    print("\nTEST 2: GENERATE REVIEW EVENT")

    review_result = await controller.execute(
        agent_id="ARIA",
        action="create_tournament",
        task="Create audit logging review test tournament",
        context={
            "tournament_name": "AUDIT REVIEW TEST",
            "time": "22:00",
        },
        tool_name="create_tournament",
    )

    print(review_result)

    events = audit_logger.list_events()

    if (
        len(events) == 1
        and events[-1].agent_id == "ARIA"
        and events[-1].action == "create_tournament"
        and events[-1].decision == Decision.REVIEW.value
        and events[-1].success is False
    ):
        print("REVIEW AUDIT EVENT: PASS")
    else:
        print("REVIEW AUDIT EVENT: FAIL")
        return

    # --------------------------------------------------
    # TEST 3: GENERATE DENY EVENT
    # --------------------------------------------------

    print("\nTEST 3: GENERATE DENY EVENT")

    deny_result = await controller.execute(
        agent_id="ARIA",
        action="delete_tournament",
        task="Attempt unauthorized delete operation",
        context={
            "tournament_id": "UNAUTHORIZED-TEST",
        },
        tool_name="delete_tournament",
    )

    print(deny_result)

    events = audit_logger.list_events()

    if len(events) < 2:
        print("DENY AUDIT EVENT: FAIL")
        return

    deny_event = events[-1]

    if (
        deny_event.agent_id == "ARIA"
        and deny_event.action == "delete_tournament"
        and deny_event.decision == Decision.DENY.value
        and deny_event.success is False
    ):
        print("DENY AUDIT EVENT: PASS")
    else:
        print("DENY AUDIT EVENT: FAIL")
        return

    # --------------------------------------------------
    # TEST 4: GENERATE ALLOW EVENT
    # --------------------------------------------------

    print("\nTEST 4: GENERATE ALLOW EVENT")

    allow_result = await controller.execute(
        agent_id="ARIA",
        action="read_tournament",
        task="Read audit logging test tournament",
        context={
            "tournament_name": "AUDIT ALLOW TEST",
        },
        tool_name="read_tournament",
    )

    print(allow_result)

    events = audit_logger.list_events()

    if len(events) < 3:
        print("ALLOW AUDIT EVENT: FAIL")
        return

    allow_event = events[-1]

    if (
        allow_event.agent_id == "ARIA"
        and allow_event.action == "read_tournament"
        and allow_event.decision == Decision.ALLOW.value
        and allow_event.success is True
    ):
        print("ALLOW AUDIT EVENT: PASS")
    else:
        print("ALLOW AUDIT EVENT: FAIL")
        return

    # --------------------------------------------------
    # TEST 5: VERIFY EVENT ORDER
    # --------------------------------------------------

    print("\nTEST 5: VERIFY AUDIT EVENT ORDER")

    events = audit_logger.list_events()

    expected_actions = [
        "create_tournament",
        "delete_tournament",
        "read_tournament",
    ]

    actual_actions = [
        event.action
        for event in events
    ]

    print("Expected order:")
    print(expected_actions)

    print("Actual order:")
    print(actual_actions)

    if actual_actions == expected_actions:
        print("AUDIT EVENT ORDER: PASS")
    else:
        print("AUDIT EVENT ORDER: FAIL")
        return

    # --------------------------------------------------
    # TEST 6: VERIFY TIMESTAMPS
    # --------------------------------------------------

    print("\nTEST 6: VERIFY AUDIT TIMESTAMPS")

    timestamps_present = all(
        bool(event.timestamp)
        for event in events
    )

    if timestamps_present:
        print("AUDIT TIMESTAMPS: PASS")
    else:
        print("AUDIT TIMESTAMPS: FAIL")
        return

    # --------------------------------------------------
    # TEST 7: VERIFY MESSAGE INTEGRITY
    # --------------------------------------------------

    print("\nTEST 7: VERIFY AUDIT MESSAGE INTEGRITY")

    messages_present = all(
        isinstance(event.message, str)
        and len(event.message) > 0
        for event in events
    )

    if messages_present:
        print("AUDIT MESSAGE INTEGRITY: PASS")
    else:
        print("AUDIT MESSAGE INTEGRITY: FAIL")
        return

    # --------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------

    print("\nFINAL AUDIT EVENTS")
    print("-" * 60)

    for index, event in enumerate(events, start=1):
        print(
            f"{index}. "
            f"agent={event.agent_id}, "
            f"action={event.action}, "
            f"decision={event.decision}, "
            f"success={event.success}"
        )

    print("\nSECURITY VERIFICATION")
    print("-" * 60)
    print("REVIEW AUDIT EVENT: PASS")
    print("DENY AUDIT EVENT: PASS")
    print("ALLOW AUDIT EVENT: PASS")
    print("AUDIT EVENT ORDER: PASS")
    print("AUDIT TIMESTAMPS: PASS")
    print("AUDIT MESSAGE INTEGRITY: PASS")

    print("\nAUDIT LOGGING SECURITY: PASS")
    print(
        "CORTEX correctly recorded review, deny, and allow "
        "decisions with ordered and complete audit events."
    )

    print("\n" + "=" * 60)
    print("CORTEX AUDIT LOGGING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




