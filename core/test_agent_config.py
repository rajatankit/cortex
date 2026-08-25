from core.agent_config import AGENT_CONFIGS, get_agent_config


print("CORTEX AI TEAM:")
print()

for config in AGENT_CONFIGS:
    print(
        f"{config.agent_id} | "
        f"{config.name} | "
        f"{config.role}"
    )

print()
print("TOTAL AGENTS:", len(AGENT_CONFIGS))

print()
print("ARIA CONFIG:")
print(get_agent_config("ARIA"))

print()
print("NOVA CONFIG:")
print(get_agent_config("NOVA"))

print()
print("SENTINEL CONFIG:")
print(get_agent_config("SENTINEL"))

print()
print("UNKNOWN:")
print(get_agent_config("UNKNOWN"))




