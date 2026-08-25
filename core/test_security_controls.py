import asyncio
from core.cortex_bootstrap import build_cortex
from core.cortex_manager import CortexManager


async def main():

    cortex = build_cortex()

    manager = CortexManager(
        registry=cortex["registry"],
        orchestrator=cortex["orchestrator"],
    )

    approval_gate = cortex["approval_gate"]
    controller = cortex["controller"]
    audit_logger = cortex["audit_logger"]
    registry = cortex["registry"]

    print("CORTEX SECURITY CONTROLS TEST")
    print("=" * 50)

    # -------------------------------------------------
    # TEST 1 — UNAPPROVED REQUEST MUST NOT EXECUTE
    # -------------------------------------------------

    print("\nTEST 1: UNAPPROVED REQUEST")

    routing, result = await manager.dispatch(
        task="Process a financial payment",
        action="process_financial_action",
    )

    print(result)

    pending = approval_gate.list_pending()

    if not pending:
        print("FAIL: No approval request created.")
        return

    request = pending[-1]

    blocked = await controller.approve_and_execute(
        request_id=request.request_id,
    )

    print("\nUNAPPROVED EXECUTION RESULT:")
    print(blocked)

    # -------------------------------------------------
    # TEST 2 — PERMISSION REMOVED AFTER APPROVAL
    # -------------------------------------------------

    print("\n" + "=" * 50)
    print("TEST 2: PERMISSION REMOVED AFTER APPROVAL")

    routing, result = await manager.dispatch(
        task="Process another financial payment",
        action="process_financial_action",
    )

    print("\nREQUEST RESULT:")
    print(result)

    pending = approval_gate.list_pending()

    request = pending[-1]

    approval_gate.approve(
        request.request_id
    )

    # Remove permission after approval
    permissions = cortex["permissions"]

    permissions.revoke(
        agent_id="NOVA",
        action="process_financial_action",
    )

    blocked = await controller.approve_and_execute(
        request_id=request.request_id,
    )

    print("\nPERMISSION REMOVED RESULT:")
    print(blocked)

    # -------------------------------------------------
    # TEST 3 — DISABLED AGENT
    # -------------------------------------------------

    print("\n" + "=" * 50)
    print("TEST 3: DISABLED AGENT")

    nova = registry.get("NOVA")

    nova.enabled = False

    disabled_result = await manager.dispatch(
        task="Check wallet balance",
        action="read_financial_data",
    )

    print("\nDISABLED AGENT RESULT:")
    print(disabled_result)

    # Restore NOVA for future tests
    nova.enabled = True

    # -------------------------------------------------
    # AUDIT LOG
    # -------------------------------------------------

    print("\n" + "=" * 50)
    print("AUDIT LOG")

    for event in audit_logger.list_events():
        print(event)

    print("\n" + "=" * 50)
    print("CORTEX SECURITY CONTROLS TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




