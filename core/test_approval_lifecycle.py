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

    print("CORTEX APPROVAL LIFECYCLE TEST")
    print("=" * 50)

    # 1. Create high-risk request through CORTEX
    routing, result = await manager.dispatch(
        task="Process a financial payment",
        action="process_financial_action",
        context={
            "source": "approval_lifecycle_test",
        },
    )

    print("\nINITIAL RESULT:")
    print(result)

    # 2. Get pending approval
    pending = approval_gate.list_pending()

    print("\nPENDING REQUESTS:")

    for request in pending:
        print(request)

    if not pending:
        print("ERROR: No pending approval found.")
        return

    request = pending[0]

    # 3. Approve request
    approved = approval_gate.approve(
        request.request_id
    )

    print("\nAPPROVED REQUEST:")
    print(approved)

    # 4. Verify status
    current = approval_gate.get(
        request.request_id
    )

    print("\nFINAL STATUS:")
    print(current.status)

    print("\n" + "=" * 50)
    print("APPROVAL LIFECYCLE TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




