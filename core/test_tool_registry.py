import asyncio
from core.tools.tool import Tool, ToolRisk
from core.tools.tool_registry import ToolRegistry


async def sample_tool():
    return {
        "status": "success",
        "message": "Sample tool executed"
    }


async def main():

    print("CORTEX TOOL REGISTRY TEST")
    print("=" * 50)

    registry = ToolRegistry()

    # Register sample tool
    tool = Tool(
        name="sample_tool",
        description="Test tool for CORTEX",
        required_action="read_data",
        risk=ToolRisk.LOW,
        handler=sample_tool,
    )

    registry.register(tool)

    print("\nREGISTERED TOOLS:")

    for item in registry.list_tools():
        print(
            f"{item.name} | "
            f"{item.required_action} | "
            f"{item.risk}"
        )

    print("\nTOOL COUNT:")
    print(registry.count())

    print("\nEXISTS TEST:")
    print("sample_tool:", registry.exists("sample_tool"))
    print("unknown_tool:", registry.exists("unknown_tool"))

    print("\nGET TOOL TEST:")

    found = registry.get("sample_tool")
    print(found)

    print("\nEXECUTION TEST:")

    result = await found.execute()
    print(result)

    print("\nCORTEX TOOL REGISTRY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




