from core.permissions import PermissionEngine
from core.permission_loader import PermissionLoader


permissions = PermissionEngine()

loader = PermissionLoader(permissions)

loader.load()


tests = [
    ("ARIA", "create_tournament"),
    ("ARIA", "manage_tournament"),

    ("ELARA", "read_player_data"),

    ("LYRA", "send_notification"),

    ("VAULT", "store_room_data"),

    ("ORION", "manage_match"),

    ("NOVA", "read_financial_data"),
    ("NOVA", "process_financial_action"),

    ("ATLAS", "read_code"),
    ("ATLAS", "modify_code"),

    ("SENTINEL", "security_scan"),
    ("SENTINEL", "security_action"),
]


print("CORTEX PERMISSION TESTS:")
print()

for agent_id, action in tests:

    allowed = permissions.is_allowed(
        agent_id,
        action,
    )

    risk = permissions.get_risk(
        agent_id,
        action,
    )

    print(
        agent_id,
        "|",
        action,
        "| allowed:",
        allowed,
        "| risk:",
        risk,
    )


print("\nUNKNOWN ACTION:")

print(
    permissions.is_allowed(
        "ARIA",
        "delete_everything",
    )
)




