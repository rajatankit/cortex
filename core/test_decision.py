from core.permissions import PermissionEngine, RiskLevel
from core.decision import DecisionEngine


permissions = PermissionEngine()

permissions.grant(
    agent_id="ARIA",
    action="read_data",
    risk=RiskLevel.LOW,
)

permissions.grant(
    agent_id="ARIA",
    action="modify_data",
    risk=RiskLevel.HIGH,
)

permissions.grant(
    agent_id="ARIA",
    action="critical_action",
    risk=RiskLevel.CRITICAL,
)


cortex = DecisionEngine(permissions)


print(cortex.evaluate("ARIA", "read_data"))
print(cortex.evaluate("ARIA", "modify_data"))
print(cortex.evaluate("ARIA", "critical_action"))
print(cortex.evaluate("ARIA", "unknown_action"))





