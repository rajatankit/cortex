import asyncio
from core.agents.lyra import LyraAgent


async def main():

    lyra = LyraAgent()

    print("LYRA INFO:")
    print(lyra.info())

    result = await lyra.handle(
        task="Send tournament notification",
        context={
            "source": "lyra_test",
        },
    )

    print("\nLYRA RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())




