import asyncio
from core.agents.vault import VaultAgent


async def main():

    vault = VaultAgent()

    print("VAULT INFO:")
    print(vault.info())

    result = await vault.handle(
        task="Manage notification queue",
        context={
            "source": "vault_test",
        },
    )

    print("\nVAULT RESULT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())




