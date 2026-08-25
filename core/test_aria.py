import asyncio
from core.agents.aria import AriaAgent


async def main():

    aria = AriaAgent()

    print("ARIA INFO:")
    print(aria.info())

    result = await aria.handle(
        task="Check system status",
        context={
            "source": "aria_test",
        },
    )

    print("\nARIA RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())




