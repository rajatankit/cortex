import asyncio
from core.cortex_bootstrap import build_cortex
from core.tools.tool import Tool, ToolRisk


async def dummy_handler(context=None):
    return {
        "status": "ok",
        "context": context or {},
    }


def main():
    print("CORTEX TOOL REGISTRY INTEGRITY TEST")
    print("=" * 60)

    cortex = build_cortex()
    registry = cortex["tool_registry"]

    # --------------------------------------------------
    # TEST 1: VERIFY REGISTERED TOOL COUNT
    # --------------------------------------------------

    print("\nTEST 1: VERIFY REGISTERED TOOL COUNT")

    tools = registry.list_tools()
    count = registry.count()

    print(f"Registry count: {count}")
    print("Registered tools:")

    for tool in tools:
        print(
            f"- {tool.name} | "
            f"action={tool.required_action} | "
            f"risk={tool.risk.value}"
        )

    if count == len(tools) and count > 0:
        print("TOOL REGISTRY COUNT: PASS")
    else:
        print("TOOL REGISTRY COUNT: FAIL")
        return

    # --------------------------------------------------
    # TEST 2: VERIFY EVERY REGISTERED TOOL IS RETRIEVABLE
    # --------------------------------------------------

    print("\nTEST 2: VERIFY TOOL LOOKUP")

    lookup_ok = True

    for tool in tools:
        found = registry.get(tool.name)

        if found is None:
            lookup_ok = False
            print(f"Lookup failed: {tool.name}")
        elif found.name != tool.name:
            lookup_ok = False
            print(f"Name mismatch: {tool.name}")

    if lookup_ok:
        print("REGISTERED TOOL LOOKUP: PASS")
    else:
        print("REGISTERED TOOL LOOKUP: FAIL")
        return

    # --------------------------------------------------
    # TEST 3: UNKNOWN TOOL MUST NOT EXIST
    # --------------------------------------------------

    print("\nTEST 3: UNKNOWN TOOL BLOCK")

    unknown_tool = "definitely_not_registered_tool"

    found = registry.get(unknown_tool)
    exists = registry.exists(unknown_tool)

    print(f"Unknown tool lookup: {found}")
    print(f"Unknown tool exists: {exists}")

    if found is None and exists is False:
        print("UNKNOWN TOOL BLOCK: PASS")
    else:
        print("UNKNOWN TOOL BLOCK: FAIL")
        return

    # --------------------------------------------------
    # TEST 4: VERIFY TOOL ACTION BINDINGS
    # --------------------------------------------------

    print("\nTEST 4: VERIFY TOOL ACTION BINDINGS")

    binding_ok = True

    for tool in tools:
        if not tool.required_action:
            binding_ok = False
            print(
                f"Missing required action: {tool.name}"
            )
            continue

        resolved = registry.find_by_action(
            tool.required_action
        )

        if resolved is None:
            binding_ok = False
            print(
                f"No tool found for action: "
                f"{tool.required_action}"
            )
        elif resolved.name != tool.name:
            binding_ok = False
            print(
                f"Action binding mismatch: "
                f"{tool.required_action} -> "
                f"{resolved.name}, expected {tool.name}"
            )

    if binding_ok:
        print("TOOL ACTION BINDINGS: PASS")
    else:
        print("TOOL ACTION BINDINGS: FAIL")
        return

    # --------------------------------------------------
    # TEST 5: DUPLICATE TOOL REGISTRATION MUST FAIL
    # --------------------------------------------------

    print("\nTEST 5: DUPLICATE TOOL REGISTRATION")

    existing_name = tools[0].name

    duplicate_tool = Tool(
        name=existing_name,
        description="Duplicate registration security test",
        required_action="duplicate_test_action",
        risk=ToolRisk.LOW,
        handler=dummy_handler,
    )

    duplicate_blocked = False

    try:
        registry.register(duplicate_tool)
    except ValueError as exc:
        duplicate_blocked = True
        print(f"Duplicate registration rejected: {exc}")

    if duplicate_blocked:
        print("DUPLICATE TOOL BLOCK: PASS")
    else:
        print("DUPLICATE TOOL BLOCK: FAIL")
        return

    # --------------------------------------------------
    # TEST 6: VERIFY DUPLICATE DID NOT ALTER REGISTRY
    # --------------------------------------------------

    print("\nTEST 6: VERIFY REGISTRY WAS NOT CORRUPTED")

    final_count = registry.count()
    original_tool = registry.get(existing_name)

    if (
        final_count == count
        and original_tool is not None
        and original_tool.name == existing_name
        and original_tool.required_action
        != "duplicate_test_action"
    ):
        print("REGISTRY INTEGRITY: PASS")
    else:
        print("REGISTRY INTEGRITY: FAIL")
        return

    # --------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------

    print("\nSECURITY VERIFICATION")
    print("-" * 60)
    print("TOOL REGISTRY COUNT: PASS")
    print("REGISTERED TOOL LOOKUP: PASS")
    print("UNKNOWN TOOL BLOCK: PASS")
    print("TOOL ACTION BINDINGS: PASS")
    print("DUPLICATE TOOL BLOCK: PASS")
    print("REGISTRY INTEGRITY: PASS")

    print("\nTOOL REGISTRY SECURITY: PASS")
    print(
        "Registered tools remained uniquely identifiable, "
        "unknown tools were rejected, action bindings remained "
        "intact, and duplicate registration was blocked."
    )

    print("\n" + "=" * 60)
    print("CORTEX TOOL REGISTRY INTEGRITY TEST COMPLETE")


if __name__ == "__main__":
    main()




