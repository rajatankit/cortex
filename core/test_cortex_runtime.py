import asyncio
from core.cortex_bootstrap import bootstrap_cortex


async def main():
    print("CORTEX RUNTIME INTEGRATION TEST")
    print("=" * 50)

    # --------------------------------------------------
    # 1. BOOTSTRAP
    # --------------------------------------------------

    runtime = bootstrap_cortex()

    print("\nTEST 1: HEALTH")
    print(runtime.health_report.summary())

    # --------------------------------------------------
    # 2. REGISTERED AGENTS
    # --------------------------------------------------

    print("\nTEST 2: REGISTERED AGENTS")

    agents = runtime.agent_registry.list_agents()

    for agent in agents:
        print(agent)

    # --------------------------------------------------
    # 3. REGISTERED TOOLS
    # --------------------------------------------------

    print("\nTEST 3: REGISTERED TOOLS")

    tools = runtime.tool_registry.list_tools()

    for tool in tools:
        print(
            f"{tool.name} | "
            f"action={tool.required_action} | "
            f"risk={tool.risk.value}"
        )

    # --------------------------------------------------
    # 4. LOW-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 4: LOW-RISK TOOL")

    result = await runtime.tool_gateway.execute(
        agent_id="ARIA",
        tool_name="read_tournament",
        task="Read tournament information",
        context={
            "tournament_id": "T1",
        },
    )

    print(result)

    # --------------------------------------------------
    # 5. HIGH-RISK TOOL
    # --------------------------------------------------

    print("\nTEST 5: HIGH-RISK TOOL")

    result = await runtime.tool_gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create a new tournament",
        context={
            "tournament_name": "CORTEX Test Cup",
            "time": "20:00",
        },
    )

    print(result)

    # --------------------------------------------------
    # 6. PENDING APPROVALS
    # --------------------------------------------------

    print("\nTEST 6: PENDING APPROVALS")

    pending = runtime.approval_gate.list_pending()

    for request in pending:
        print(request)

    # --------------------------------------------------
    # 7. AUDIT LOG
    # --------------------------------------------------

    print("\nTEST 7: AUDIT LOG")

    for event in runtime.audit_logger.list_events():
        print(event)

    print("\nAUDIT COUNT:")
    print(runtime.audit_logger.count())

    print("\n" + "=" * 50)
    print("CORTEX RUNTIME INTEGRATION TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




