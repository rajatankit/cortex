import asyncio
from core.cortex_bootstrap import build_cortex
from core.cortex_manager import CortexManager


async def main():

    cortex = build_cortex()

    manager = CortexManager(
        registry=cortex["registry"],
        orchestrator=cortex["orchestrator"],
    )

    print("CORTEX DISPATCH TEST")
    print("=" * 50)

    routing, result = await manager.dispatch(
        task="Check player information",
        action="read_player_data",
        context={
            "source": "cortex_dispatch_test",
        },
    )

    print("\nROUTING:")
    print(routing)

    print("\nRESULT:")
    print(result)

    print("\n" + "=" * 50)
    print("DISPATCH TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




