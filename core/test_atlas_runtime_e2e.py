from __future__ import annotations

import pytest

from core.cortex_bootstrap import bootstrap_cortex


ATLAS = "ATLAS"

ATLAS_TOOLS = (
    "read_code",
    "modify_code",
)


@pytest.fixture
def runtime():
    return bootstrap_cortex()


# ============================================================
# RUNTIME BOOTSTRAP
# ============================================================

def test_atlas_runtime_bootstrap(runtime):
    assert runtime is not None

    assert runtime.agent_registry.get(ATLAS) is not None

    assert runtime.agent_registry.get(ATLAS).enabled is True

    # 21 existing tools + 2 ATLAS tools + 3 SENTINEL tools
    assert runtime.tool_registry.count() == 25  


# ============================================================
# TOOL LOOKUP
# ============================================================

@pytest.mark.parametrize("tool_name", ATLAS_TOOLS)
def test_atlas_runtime_tool_lookup(runtime, tool_name):
    tool = runtime.tool_registry.get(tool_name)

    assert tool is not None
    assert tool.name == tool_name


# ============================================================
# READ_CODE E2E
# ============================================================

@pytest.mark.asyncio
async def test_atlas_read_code_execution(runtime):
    result = await runtime.tool_gateway.execute(
        agent_id=ATLAS,
        tool_name="read_code",
        task="ATLAS read_code E2E test",
        context={
            "operation": "read_code",
        },
    )

    assert result.agent_id == ATLAS
    assert result.tool_name == "read_code"

    assert result.success is True

    assert result.data is not None
    assert result.data["operation"] == "read_code"


# ============================================================
# MODIFY_CODE AUTHORIZATION
# ============================================================

@pytest.mark.asyncio
async def test_atlas_modify_code_requires_high_risk_control(runtime):
    tool = runtime.tool_registry.get("modify_code")

    assert tool is not None
    assert tool.required_action == "modify_code"
    assert tool.risk.value == "high"

    result = await runtime.tool_gateway.execute(
        agent_id=ATLAS,
        tool_name="modify_code",
        task="ATLAS modify_code E2E test",
        context={
            "operation": "modify_code",
        },
    )

    assert result.agent_id == ATLAS
    assert result.tool_name == "modify_code"

    # HIGH-risk action must not silently execute.
    # It should either request approval or be denied by
    # the security pipeline.
    if result.success:
        pytest.fail(
            "HIGH-risk modify_code executed without approval."
        )

    message = result.message.lower()

    assert (
        "approval" in message
        or "review" in message
        or "deny" in message
        or "blocked" in message
        or "permission" in message
    )


# ============================================================
# WRONG AGENT
# ============================================================

@pytest.mark.asyncio
async def test_atlas_wrong_agent_is_blocked(runtime):
    result = await runtime.tool_gateway.execute(
        agent_id="NOVA",
        tool_name="modify_code",
        task="Wrong-agent ATLAS test",
        context={
            "operation": "modify_code",
        },
    )

    assert result.success is False

    message = result.message.lower()

    assert (
        "deny" in message
        or "blocked" in message
        or "permission" in message
        or "not allowed" in message
    )


# ============================================================
# UNKNOWN TOOL
# ============================================================

@pytest.mark.asyncio
async def test_atlas_unknown_tool_is_blocked(runtime):
    result = await runtime.tool_gateway.execute(
        agent_id=ATLAS,
        tool_name="unknown_atlas_tool",
        task="Unknown ATLAS tool test",
        context={},
    )

    assert result.success is False

    assert result.tool_name == "unknown_atlas_tool"

    assert "not registered" in result.message.lower()
