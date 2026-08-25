from __future__ import annotations

import pytest

from core.cortex_bootstrap import bootstrap_cortex


ATLAS_AGENT = "ATLAS"

ATLAS_OPERATIONS = (
    "read_code",
    "modify_code",
)


@pytest.fixture
def runtime():
    return bootstrap_cortex()


# ============================================================
# ATLAS AGENT
# ============================================================

@pytest.mark.asyncio
async def test_atlas_agent_is_registered(runtime):
    agent = runtime.agent_registry.get(ATLAS_AGENT)

    assert agent is not None
    assert agent.agent_id == ATLAS_AGENT
    assert agent.enabled is True


# ============================================================
# ATLAS TOOLS
# ============================================================

@pytest.mark.parametrize("tool_name", ATLAS_OPERATIONS)
def test_atlas_tools_are_registered(runtime, tool_name):
    tool = runtime.tool_registry.get(tool_name)

    assert tool is not None
    assert tool.name == tool_name


# ============================================================
# ATLAS OPERATION CONTRACT
# ============================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ATLAS_OPERATIONS)
async def test_atlas_accepts_supported_operations(
    runtime,
    operation,
):
    agent = runtime.agent_registry.get(ATLAS_AGENT)

    result = await agent.handle(
        task=f"ATLAS test for {operation}",
        context={
            "operation": operation,
        },
    )

    assert result.success is True
    assert result.agent == ATLAS_AGENT
    assert result.data["operation"] == operation


@pytest.mark.asyncio
async def test_atlas_requires_operation(runtime):
    agent = runtime.agent_registry.get(ATLAS_AGENT)

    result = await agent.handle(
        task="ATLAS missing operation test",
        context={},
    )

    assert result.success is False
    assert result.agent == ATLAS_AGENT
    assert "operation is required" in result.message.lower()


@pytest.mark.asyncio
async def test_atlas_rejects_unsupported_operation(runtime):
    agent = runtime.agent_registry.get(ATLAS_AGENT)

    result = await agent.handle(
        task="ATLAS unsupported operation test",
        context={
            "operation": "delete_database",
        },
    )

    assert result.success is False
    assert result.agent == ATLAS_AGENT
    assert "unsupported" in result.message.lower()


# ============================================================
# PERMISSIONS
# ============================================================

@pytest.mark.parametrize("tool_name", ATLAS_OPERATIONS)
def test_atlas_permissions_are_loaded(runtime, tool_name):
    tool = runtime.tool_registry.get(tool_name)

    assert tool is not None

    assert runtime.permission_engine.is_allowed(
        ATLAS_AGENT,
        tool.required_action,
    ) is True


def test_atlas_read_code_risk(runtime):
    tool = runtime.tool_registry.get("read_code")

    assert tool is not None
    assert tool.risk.value == "low"


def test_atlas_modify_code_risk(runtime):
    tool = runtime.tool_registry.get("modify_code")

    assert tool is not None
    assert tool.risk.value == "high"


# ============================================================
# WRONG AGENT / UNKNOWN ACTION
# ============================================================

def test_atlas_does_not_grant_read_code_to_wrong_agent(runtime):
    tool = runtime.tool_registry.get("read_code")

    assert tool is not None

    assert runtime.permission_engine.is_allowed(
        "NOVA",
        tool.required_action,
    ) is False


def test_atlas_does_not_grant_modify_code_to_wrong_agent(runtime):
    tool = runtime.tool_registry.get("modify_code")

    assert tool is not None

    assert runtime.permission_engine.is_allowed(
        "NOVA",
        tool.required_action,
    ) is False


def test_atlas_unknown_action_is_not_allowed(runtime):
    assert runtime.permission_engine.is_allowed(
        ATLAS_AGENT,
        "delete_database",
    ) is False


# ============================================================
# TOOL REGISTRY
# ============================================================

def test_atlas_tools_have_correct_actions(runtime):
    read_tool = runtime.tool_registry.get("read_code")
    modify_tool = runtime.tool_registry.get("modify_code")

    assert read_tool is not None
    assert modify_tool is not None

    assert read_tool.required_action == "read_code"
    assert modify_tool.required_action == "modify_code"
