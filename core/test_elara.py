import asyncio
from core.agents.elara import ElaraAgent


async def main():

    elara = ElaraAgent()

    print("ELARA INFO:")
    print(elara.info())

    result = await elara.handle(
        task="Get player information",
        context={
            "source": "elara_test",
        },
    )

    print("\nELARA RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())




