import asyncio
from core.cortex_bootstrap import build_cortex


EXPECTED_ROUTES = {
    "Create a new tournament": "ARIA",
    "Check player UID": "ELARA",
    "Review notification logs": "VAULT",
    "Send notification alert": "LYRA",
    "Verify match result": "ORION",
    "Check wallet deposit": "NOVA",
    "Fix this code bug": "ATLAS",
    "Investigate suspicious security attack": "SENTINEL",
    "Something completely unknown": "SENTINEL",
}


async def main():
    print("CORTEX MANAGER ROUTING SECURITY TEST")
    print("=" * 60)

    cortex = build_cortex()
    manager = cortex["manager"]

    print("\nTEST 1: VERIFY TASK ROUTING")

    for task, expected_agent in EXPECTED_ROUTES.items():
        decision = manager.route(task)

        print(
            f"{task!r}"
            f" -> {decision.agent_id}"
            f" | expected={expected_agent}"
        )

        if decision.agent_id != expected_agent:
            print("ROUTING: FAIL")
            return

    print("TASK ROUTING: PASS")

    print("\nTEST 2: VERIFY ROUTING REASONS")

    for task, expected_agent in EXPECTED_ROUTES.items():
        decision = manager.route(task)

        if not decision.reason:
            print(f"Missing routing reason for: {task}")
            print("ROUTING REASON: FAIL")
            return

        if decision.agent_id != expected_agent:
            print("ROUTING REASON: FAIL")
            return

    print("ROUTING REASON: PASS")

    print("\nTEST 3: VERIFY SECURITY FALLBACK")

    fallback_task = "Something completely unknown"
    fallback = manager.route(fallback_task)

    print(f"Fallback agent: {fallback.agent_id}")
    print(f"Fallback reason: {fallback.reason}")

    if fallback.agent_id != "SENTINEL":
        print("SECURITY FALLBACK: FAIL")
        return

    print("SECURITY FALLBACK: PASS")

    print("\nTEST 4: VERIFY ALL REGISTERED SPECIALISTS")

    registered_ids = {
        agent["id"]
        for agent in cortex["registry"].list_agents()
    }

    expected_ids = {
        "ARIA",
        "ELARA",
        "LYRA",
        "VAULT",
        "ORION",
        "NOVA",
        "ATLAS",
        "SENTINEL",
    }

    print(f"Registered agents: {sorted(registered_ids)}")

    if not expected_ids.issubset(registered_ids):
        print("SPECIALIST REGISTRY: FAIL")
        return

    print("SPECIALIST REGISTRY: PASS")

    print("\nSECURITY VERIFICATION")
    print("-" * 60)
    print("TASK ROUTING: PASS")
    print("ROUTING REASON: PASS")
    print("SECURITY FALLBACK: PASS")
    print("SPECIALIST REGISTRY: PASS")

    print("\nCORTEX MANAGER ROUTING: PASS")
    print(
        "CORTEX correctly routes tasks to specialist agents "
        "and uses SENTINEL as the safe fallback."
    )

    print("\n" + "=" * 60)
    print("CORTEX MANAGER ROUTING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




