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

    print("CORTEX APPROVED EXECUTION TEST")
    print("=" * 50)

    # 1. Send high-risk task
    routing, result = await manager.dispatch(
        task="Process a financial payment",
        action="process_financial_action",
        context={
            "source": "approved_execution_test",
        },
    )

    print("\nINITIAL RESULT:")
    print(result)

    # 2. Find pending approval
    pending = approval_gate.list_pending()

    if not pending:
        print("\nERROR: No pending approval found.")
        return

    request = pending[0]

    print("\nREQUEST CREATED:")
    print(request)

    # 3. Approve request
    approved = approval_gate.approve(
        request.request_id
    )

    print("\nREQUEST APPROVED:")
    print(approved)

    # 4. Execute ONLY after approval
    execution = await controller.approve_and_execute(
        request_id=request.request_id,
        context={
            "source": "approved_execution_test",
        },
    )

    print("\nAPPROVED EXECUTION RESULT:")
    print(execution)

    # 5. Audit verification
    print("\nAUDIT LOG:")

    for event in audit_logger.list_events():
        print(event)

    print("\n" + "=" * 50)
    print("APPROVED EXECUTION TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




