import asyncio
from core.agents.orion import OrionAgent


async def main():

    orion = OrionAgent()

    print("ORION INFO:")
    print(orion.info())

    result = await orion.handle(
        task="Manage active match",
        context={
            "source": "orion_test",
        },
    )

    print("\nORION RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())




