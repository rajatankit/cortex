import pytest

from core.cortex_bootstrap import build_cortex
from core.tools.tool import ToolRisk


AGENTS = [
    "ARIA",
    "ELARA",
    "LYRA",
    "VAULT",
    "ORION",
    "NOVA",
    "ATLAS",
    "SENTINEL",
]


def test_full_team_registered_and_enabled():
    cortex = build_cortex()

    registry = cortex["registry"]

    registered_ids = {
        agent["id"]
        for agent in registry.list_agents()
    }

    assert registered_ids == set(AGENTS)

    for agent_id in AGENTS:
        agent = registry.get(agent_id)
        assert agent is not None
        assert agent.enabled is True


def test_full_team_has_authorized_tools():
    cortex = build_cortex()

    permissions = cortex["permissions"]
    tool_registry = cortex["tool_registry"]

    for agent_id in AGENTS:
        authorized_tools = []

        for tool in tool_registry.list_tools():
            if permissions.is_allowed(
                agent_id,
                tool.required_action,
            ):
                authorized_tools.append(tool)

        assert authorized_tools, (
            f"{agent_id} has no authorized tools"
        )


def test_full_team_tool_isolation():
    cortex = build_cortex()

    permissions = cortex["permissions"]
    tool_registry = cortex["tool_registry"]

    for tool in tool_registry.list_tools():
        authorized_agents = [
            agent_id
            for agent_id in AGENTS
            if permissions.is_allowed(
                agent_id,
                tool.required_action,
            )
        ]

        assert authorized_agents, (
            f"No agent is authorized for {tool.name}"
        )


@pytest.mark.asyncio
async def test_full_team_authorized_dispatch():
    cortex = build_cortex()

    orchestrator = cortex["orchestrator"]
    permissions = cortex["permissions"]
    tool_registry = cortex["tool_registry"]

    for agent_id in AGENTS:
        candidate = None

        for tool in tool_registry.list_tools():
            if permissions.is_allowed(
                agent_id,
                tool.required_action,
            ):
                candidate = tool
                break

        assert candidate is not None, (
            f"{agent_id} has no authorized tool"
        )

        result = await orchestrator.dispatch(
            agent_id=agent_id,
            action=candidate.required_action,
            task=f"Full team integration test for {candidate.name}",
        )

        assert result is not None
        assert result.agent == agent_id
        assert isinstance(result.success, bool)


def test_full_team_audit_logger_available():
    cortex = build_cortex()

    audit_logger = cortex["audit_logger"]

    assert audit_logger is not None
    assert audit_logger.count() >= 0


def test_full_team_approval_gate_available():
    cortex = build_cortex()

    approval_gate = cortex["approval_gate"]

    assert approval_gate is not None
    assert approval_gate.list_pending() is not None
