import asyncio
from core.cortex_bootstrap import build_cortex
from core.cortex_manager import CortexManager


async def main():

    cortex = build_cortex()

    manager = CortexManager(
        registry=cortex["registry"],
        orchestrator=cortex["orchestrator"],
    )

    print("CORTEX APPROVAL FLOW TEST")
    print("=" * 50)

    # High-risk finance task
    routing, result = await manager.dispatch(
        task="Process a financial payment",
        action="process_financial_action",
        context={
            "source": "cortex_approval_test",
        },
    )

    print("\nROUTING:")
    print(routing)

    print("\nRESULT:")
    print(result)

    print("\nAUDIT LOG:")

    audit_logger = cortex["audit_logger"]

    for event in audit_logger.list_events():
        print(event)

    print("\n" + "=" * 50)
    print("CORTEX APPROVAL FLOW TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




