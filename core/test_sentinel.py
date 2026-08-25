import asyncio
from core.agents.sentinel import SentinelAgent


async def main():

    sentinel = SentinelAgent()

    print("SENTINEL INFO:")
    print(sentinel.info())

    result = await sentinel.handle(
        task="Run security scan",
        context={
            "source": "sentinel_test",
            "operation": "security_scan",
        },
    )

    print("\nSENTINEL RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())






