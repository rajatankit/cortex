from core.cortex_bootstrap import build_cortex


cortex = build_cortex()

registry = cortex["registry"]
permissions = cortex["permissions"]


print("CORTEX TEAM:")

for agent in registry.list_agents():
    print(
        f"{agent['id']} | "
        f"{agent['name']} | "
        f"{agent['role']} | "
        f"enabled={agent['enabled']}"
    )


print("\nTOTAL REGISTERED AGENTS:")
print(len(registry.list_agents()))


print("\nPERMISSION CHECKS:")

checks = [
    ("ARIA", "create_tournament"),
    ("ELARA", "read_player_data"),
    ("LYRA", "send_notification"),
    ("VAULT", "store_room_data"),
    ("ORION", "manage_match"),
    ("NOVA", "read_financial_data"),
    ("ATLAS", "read_code"),
    ("SENTINEL", "security_scan"),
]

for agent_id, action in checks:

    print(
        agent_id,
        "|",
        action,
        "| allowed:",
        permissions.is_allowed(
            agent_id,
            action,
        ),
        "| risk:",
        permissions.get_risk(
            agent_id,
            action,
        ),
    )


print("\nCORTEX STATUS: READY")




