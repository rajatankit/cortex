from core.audit_logger import AuditLogger


def main():

    print("CORTEX AUDIT LOGGER TEST")
    print("=" * 50)

    logger = AuditLogger()

    # ALLOW event
    allow_event = logger.log(
        agent_id="ARIA",
        action="read_tournament",
        decision="allow",
        success=True,
        message="Tournament data read successfully.",
    )

    # REVIEW event
    review_event = logger.log(
        agent_id="NOVA",
        action="process_financial_action",
        decision="review",
        success=False,
        message="Approval required.",
    )

    # DENY event
    deny_event = logger.log(
        agent_id="SENTINEL",
        action="security_action",
        decision="deny",
        success=False,
        message="Security action denied.",
    )

    print("\nRECORDED EVENTS:")

    for event in logger.list_events():
        print(event)

    print("\nEVENT COUNT:")
    print(logger.count())

    print("\nINTEGRITY CHECK:")

    events = logger.list_events()

    assert len(events) == 3
    assert events[0].decision == "allow"
    assert events[1].decision == "review"
    assert events[2].decision == "deny"

    assert events[0].success is True
    assert events[1].success is False
    assert events[2].success is False

    print("Audit events: PASS")
    print("Decision tracking: PASS")
    print("Success tracking: PASS")

    # Test clear()
    logger.clear()

    print("\nAFTER CLEAR:")
    print("Event count:", logger.count())

    assert logger.count() == 0

    print("Clear operation: PASS")

    print("\n" + "=" * 50)
    print("CORTEX AUDIT LOGGER TEST COMPLETE")


if __name__ == "__main__":
    main()




