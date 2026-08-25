import asyncio
from core.cortex_bootstrap import build_cortex
from core.permissions import RiskLevel


async def main():
    print("CORTEX CRITICAL-RISK SECURITY TEST")
    print("=" * 50)

    cortex = build_cortex()

    permissions = cortex["permissions"]
    decision_engine = cortex["decision_engine"]
    approval_gate = cortex["approval_gate"]
    audit_logger = cortex["audit_logger"]
    registry = cortex["registry"]

    agent_id = "SENTINEL"
    action = "critical_security_action"

    # --------------------------------------------------
    # TEST 1 — REGISTER A CRITICAL PERMISSION
    # --------------------------------------------------

    print("\nTEST 1: CRITICAL PERMISSION")

    permissions.grant(
        agent_id=agent_id,
        action=action,
        risk=RiskLevel.CRITICAL,
    )

    print(
        "Permission allowed:",
        permissions.is_allowed(agent_id, action),
    )

    print(
        "Risk:",
        permissions.get_risk(agent_id, action),
    )

    # --------------------------------------------------
    # TEST 2 — DECISION ENGINE
    # --------------------------------------------------

    print("\nTEST 2: DECISION ENGINE")

    decision = decision_engine.evaluate(
        agent_id=agent_id,
        action=action,
    )

    print(decision)

    # --------------------------------------------------
    # TEST 3 — VERIFY CRITICAL IS BLOCKED
    # --------------------------------------------------

    print("\nTEST 3: CRITICAL DECISION")

    if decision.decision.value == "block":
        print("CRITICAL RISK DECISION: PASS")
        print("Critical action is blocked.")
    else:
        print("CRITICAL RISK DECISION: FAILED")
        print("Critical action was not blocked.")

    # --------------------------------------------------
    # TEST 4 — VERIFY NO APPROVAL REQUEST
    # --------------------------------------------------

    print("\nTEST 4: APPROVAL GATE")

    pending = approval_gate.list_pending()

    print("Pending approvals:", pending)

    if not pending:
        print("CRITICAL APPROVAL BYPASS: PASS")
        print("Critical action did not enter the normal approval queue.")
    else:
        print("CRITICAL APPROVAL BYPASS: FAILED")

    # --------------------------------------------------
    # TEST 5 — VERIFY SENTINEL EXISTS
    # --------------------------------------------------

    print("\nTEST 5: AGENT STATUS")

    agent = registry.get(agent_id)

    if agent is not None and agent.enabled:
        print("SENTINEL:", agent.info())
        print("Agent status: PASS")
    else:
        print("Agent status: FAILED")

    # --------------------------------------------------
    # TEST 6 — AUDIT LOG
    # --------------------------------------------------

    print("\nTEST 6: AUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\nAUDIT COUNT:")
    print(audit_logger.count())

    print("\n" + "=" * 50)
    print("CRITICAL-RISK SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




