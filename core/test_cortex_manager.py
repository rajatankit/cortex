from core.cortex_manager import CortexManager
from core.cortex_bootstrap import build_cortex


cortex = build_cortex()

registry = cortex["registry"]
orchestrator = cortex["orchestrator"]

manager = CortexManager(
    registry=registry,
    orchestrator=orchestrator,
)


tests = [
    "Create a new tournament",
    "Get player information",
    "Send a notification",
    "Manage notification queue",
    "Manage active match",
    "Check wallet balance",
    "Fix a coding bug",
    "Run a security scan",
]


print("CORTEX ROUTING TEST")
print("=" * 50)

for task in tests:

    decision = manager.route(task)

    print(
        f"\nTASK: {task}"
    )

    print(
        f"ROUTED TO: {decision.agent_id}"
    )

    print(
        f"REASON: {decision.reason}"
    )


print("\n" + "=" * 50)
print("ROUTING TEST COMPLETE")




