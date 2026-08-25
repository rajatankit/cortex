from __future__ import annotations

import pytest

from core.cortex_bootstrap import bootstrap_cortex


NOVA = "NOVA"


NOVA_TOOLS = (
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


# ============================================================
# BOOTSTRAP
# ============================================================


def test_nova_runtime_bootstrap(runtime):
    assert runtime is not None

    assert runtime.agent_registry.get("NOVA") is not None

    assert runtime.agent_registry.get("NOVA").enabled is True

    assert runtime.tool_registry.count() == 25


# ============================================================
# NOVA â†’ TOOL GATEWAY
# ============================================================


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", NOVA_TOOLS)
async def test_nova_tool_gateway_authorization(
    runtime,
    tool_name,
):
    tool = runtime.tool_registry.get(tool_name)

    assert tool is not None

    result = await runtime.tool_gateway.execute(
        agent_id=NOVA,
        tool_name=tool_name,
        task=f"NOVA E2E test for {tool_name}",
        context={
            "operation": tool_name,
        },
    )

    # LOW-risk authorized tools should execute.
    #
    # If the tool requires approval, the gateway must return
    # an approval request instead of executing immediately.
    if result.success:
        assert result.agent_id == NOVA
        assert result.tool_name == tool_name

    else:
        assert result.agent_id == NOVA

        message = result.message.lower()

        assert (
            "approval" in message
            or "denied" in message
            or "blocked" in message
            or "permission" in message
        )


# ============================================================
# UNKNOWN TOOL
# ============================================================


@pytest.mark.asyncio
async def test_nova_e2e_unknown_tool_blocked(runtime):
    result = await runtime.tool_gateway.execute(
        agent_id=NOVA,
        tool_name="nova_fake_tool",
        task="NOVA unknown tool security test",
        context={
            "operation": "nova_fake_tool",
        },
    )

    assert result.success is False
    assert result.tool_name == "nova_fake_tool"
    assert "not registered" in result.message.lower()


# ============================================================
# WRONG AGENT â†’ NOVA TOOL
# ============================================================


@pytest.mark.asyncio
async def test_wrong_agent_blocked_from_nova_tool(runtime):
    result = await runtime.tool_gateway.execute(
        agent_id="SENTINEL",
        tool_name="read_wallet",
        task="Unauthorized finance access attempt",
        context={
            "operation": "read_wallet",
        },
    )

    assert result.success is False


# ============================================================
# NOVA PERMISSION ENFORCEMENT
# ============================================================


@pytest.mark.asyncio
async def test_nova_permission_enforcement(runtime):
    tool = runtime.tool_registry.get("read_wallet")

    assert tool is not None

    action = tool.required_action

    assert runtime.permission_engine.is_allowed(
        NOVA,
        action,
    ) is True


# ============================================================
# AGENT DISABLE TEST
# ============================================================


@pytest.mark.asyncio
async def test_disabled_nova_cannot_execute(runtime):
    nova = runtime.agent_registry.get(NOVA)

    assert nova is not None

    nova.enabled = False

    result = await runtime.tool_gateway.execute(
        agent_id=NOVA,
        tool_name="read_wallet",
        task="Disabled NOVA execution test",
        context={
            "operation": "read_wallet",
        },
    )

    assert result.success is False


# ============================================================
# AUDIT LOGGER EXISTENCE
# ============================================================


def test_nova_runtime_has_audit_logger(runtime):
    assert runtime.audit_logger is not None


# ============================================================
# SECURITY COMPONENTS
# ============================================================


def test_nova_runtime_security_pipeline(runtime):
    assert runtime.permission_engine is not None
    assert runtime.decision_engine is not None
    assert runtime.approval_gate is not None
    assert runtime.agent_controller is not None
    assert runtime.tool_gateway is not None


# ============================================================
# FULL RUNTIME HEALTH
# ============================================================


def test_nova_runtime_health(runtime):
    report = runtime.health_report

    assert report is not None
    assert report.is_healthy() is True

