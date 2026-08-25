from __future__ import annotations

import pytest

from core.cortex_bootstrap import bootstrap_cortex
from core.agents.nova import NovaAgent


NOVA_AGENT = "NOVA"

NOVA_OPERATIONS = (
    "read_wallet",
    "read_transaction",
    "validate_transaction",
    "read_deposit_status",
    "read_withdrawal_status",
    "report_suspicious_transaction",
)


@pytest.fixture
def runtime():
    return bootstrap_cortex()


@pytest.fixture
def nova():
    return NovaAgent()


# ============================================================
# NOVA AGENT TESTS
# ============================================================


@pytest.mark.asyncio
async def test_nova_agent_registered(runtime):
    agent = runtime.agent_registry.get(NOVA_AGENT)

    assert agent is not None
    assert agent.agent_id == "NOVA"
    assert agent.name == "Nova"
    assert agent.role == "Finance"
    assert agent.enabled is True


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", NOVA_OPERATIONS)
async def test_nova_accepts_supported_operations(nova, operation):
    result = await nova.handle(
        task=f"Test NOVA operation: {operation}",
        context={
            "operation": operation,
        },
    )

    assert result.success is True
    assert result.agent == "NOVA"
    assert result.data["operation"] == operation


@pytest.mark.asyncio
async def test_nova_rejects_missing_operation(nova):
    result = await nova.handle(
        task="Test missing NOVA operation",
        context={},
    )

    assert result.success is False
    assert result.agent == "NOVA"
    assert "operation is required" in result.message


@pytest.mark.asyncio
async def test_nova_rejects_unsupported_operation(nova):
    result = await nova.handle(
        task="Test unsupported operation",
        context={
            "operation": "delete_wallet",
        },
    )

    assert result.success is False
    assert result.agent == "NOVA"
    assert "Unsupported NOVA operation" in result.message


# ============================================================
# TOOL REGISTRATION
# ============================================================


def test_all_nova_tools_registered(runtime):
    registry = runtime.tool_registry

    expected_tools = {
        "read_wallet",
        "read_transaction",
        "validate_transaction",
        "read_deposit_status",
        "read_withdrawal_status",
        "report_suspicious_transaction",
    }

    for tool_name in expected_tools:
        tool = registry.get(tool_name)

        assert tool is not None, (
            f"NOVA tool is not registered: {tool_name}"
        )


def test_nova_tools_are_six(runtime):
    registry = runtime.tool_registry

    expected_tools = {
        "read_wallet",
        "read_transaction",
        "validate_transaction",
        "read_deposit_status",
        "read_withdrawal_status",
        "report_suspicious_transaction",
    }

    registered = {
        name
        for name in expected_tools
        if registry.get(name) is not None
    }

    assert registered == expected_tools


# ============================================================
# NOVA TOOL METADATA
# ============================================================


@pytest.mark.parametrize("tool_name", NOVA_OPERATIONS)
def test_nova_tool_has_security_metadata(runtime, tool_name):
    tool = runtime.tool_registry.get(tool_name)

    assert tool is not None

    assert getattr(tool, "required_action", None), (
        f"{tool_name} has no required_action"
    )

    assert getattr(tool, "risk", None) is not None, (
        f"{tool_name} has no risk level"
    )

    assert callable(getattr(tool, "execute", None)), (
        f"{tool_name} has no executable function"
    )


# ============================================================
# GATEWAY UNKNOWN TOOL
# ============================================================


@pytest.mark.asyncio
async def test_unknown_tool_is_blocked(runtime):
    result = await runtime.tool_gateway.execute(
        agent_id=NOVA_AGENT,
        tool_name="nova_unknown_tool",
        task="Try an unknown NOVA tool",
        context={
            "operation": "nova_unknown_tool",
        },
    )

    assert result.success is False
    assert result.agent_id == NOVA_AGENT
    assert result.tool_name == "nova_unknown_tool"
    assert "not registered" in result.message.lower()


# ============================================================
# WRONG AGENT
# ============================================================


@pytest.mark.asyncio
async def test_wrong_agent_cannot_execute_nova_tool(runtime):
    result = await runtime.tool_gateway.execute(
        agent_id="ARIA",
        tool_name="read_wallet",
        task="ARIA attempts to execute NOVA finance tool",
        context={
            "operation": "read_wallet",
        },
    )

    assert result.success is False


# ============================================================
# NOVA PERMISSION EXISTENCE
# ============================================================


def test_nova_permissions_are_loaded(runtime):
    permissions = runtime.permission_engine

    for tool_name in NOVA_OPERATIONS:
        tool = runtime.tool_registry.get(tool_name)

        assert tool is not None

        action = tool.required_action

        assert permissions.is_allowed(
            NOVA_AGENT,
            action,
        ) is True