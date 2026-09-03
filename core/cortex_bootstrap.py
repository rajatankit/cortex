from __future__ import annotations

from core.agent_registry import AgentRegistry
from core.permissions import PermissionEngine
from core.permission_loader import PermissionLoader
from core.decision import DecisionEngine
from core.approval_gate import ApprovalGate
from core.audit_logger import AuditLogger

from core.voice_audit import VoiceAudit
from core.agent_controller import AgentController
from core.tool_gateway import ToolGateway
from core.tools.tool_registry import ToolRegistry
from core.tools.register_tools import register_all_tools

from core.cortex_health import CortexHealth, CortexHealthReport
from core.cortex_manager import CortexManager
from core.orchestrator import Orchestrator
from core.intent_engine import IntentEngine
from core.task_planner import TaskPlanner
from core.cortex_runtime import CortexRuntime
from core.agents.aria import AriaAgent
from core.agents.elara import ElaraAgent
from core.agents.lyra import LyraAgent
from core.agents.vault import VaultAgent
from core.agents.orion import OrionAgent
from core.agents.nova import NovaAgent
from core.agents.atlas import AtlasAgent
from core.agents.sentinel import SentinelAgent


class CortexBootstrapError(Exception):
    """
    Raised when CORTEX fails to reach a healthy startup state.
    """
    pass



# ============================================================
# AGENT REGISTRATION
# ============================================================

def _register_agents(
    registry: AgentRegistry,
) -> None:
    """
    Register all CORTEX specialist agents.

    Expected team size:
        8 specialists
    """

    agents = (
        AriaAgent(),
        ElaraAgent(),
        LyraAgent(),
        VaultAgent(),
        OrionAgent(),
        NovaAgent(),
        AtlasAgent(),
        SentinelAgent(),
    )

    for agent in agents:
        registry.register(agent)


# ============================================================
# BOOTSTRAP
# ============================================================

def bootstrap_cortex() -> CortexRuntime:
    """
    Build and validate the complete CORTEX runtime.

    Startup order:

        AuditLogger
             â†“
        PermissionEngine
             â†“
        PermissionLoader
             â†“
        AgentRegistry
             â†“
        Agents
             â†“
        DecisionEngine
             â†“
        ApprovalGate
             â†“
        AgentController
             â†“
        Orchestrator
             â†“
        CortexManager
             â†“
        IntentEngine
             â†“
        TaskPlanner
             â†“
        ToolRegistry
             â†“
        ToolGateway
             â†“
        Health Check
             â†“
        Runtime
    """

    # ========================================================
    # 1. AUDIT LOGGER
    # ========================================================

    audit_logger = AuditLogger()

    voice_audit = VoiceAudit(
        audit_logger=audit_logger,
    )

    # ========================================================
    # 2. PERMISSION ENGINE
    # ========================================================

    permission_engine = PermissionEngine()

    # ========================================================
    # 3. PERMISSION LOADER
    # ========================================================

    permission_loader = PermissionLoader(
        permission_engine=permission_engine,
    )

    permission_loader.load()

    # ========================================================
    # 4. AGENT REGISTRY
    # ========================================================

    agent_registry = AgentRegistry()

    # ========================================================
    # 5. REGISTER ALL SPECIALISTS
    # ========================================================

    _register_agents(agent_registry)

    # ========================================================
    # 6. DECISION ENGINE
    # ========================================================

    decision_engine = DecisionEngine(
        permission_engine=permission_engine,
    )

    # ========================================================
    # 7. APPROVAL GATE
    # ========================================================

    approval_gate = ApprovalGate()

    # ========================================================
    # 8. AGENT CONTROLLER
    # ========================================================

    agent_controller = AgentController(
        registry=agent_registry,
        decision_engine=decision_engine,
        audit_logger=audit_logger,
        approval_gate=approval_gate,
    )

    # ========================================================
    # 9. ORCHESTRATOR
    # ========================================================

    orchestrator = Orchestrator(
        registry=agent_registry,
        controller=agent_controller,
    )

    # ========================================================
    # 10. CORTEX MANAGER
    # ========================================================

    manager = CortexManager(
        registry=agent_registry,
        orchestrator=orchestrator,
    )

    # ========================================================
    # 11. INTENT ENGINE
    # ========================================================

    intent_engine = IntentEngine()

    # ========================================================
    # 12. TASK PLANNER
    # ========================================================
    #
    # Planning-only layer. Depends solely on AgentRegistry (to
    # validate that a planned agent actually exists). It never
    # touches ToolGateway, PermissionEngine, DecisionEngine, or
    # ApprovalGate.
    #

    task_planner = TaskPlanner(
        agent_registry=agent_registry,
    )

    # ========================================================
    # 13. TOOL REGISTRY
    # ========================================================

    tool_registry = ToolRegistry()

    register_all_tools(tool_registry)

    # ========================================================
    # 14. TOOL GATEWAY
    # ========================================================

    tool_gateway = ToolGateway(
        tool_registry=tool_registry,
        controller=agent_controller,
        registry=agent_registry,
        approval_gate=approval_gate,
        permissions=permission_engine,
        audit_logger=audit_logger,
    )
    # ========================================================
    # 15. HEALTH MONITOR
    # ========================================================

    health = CortexHealth()

    # --------------------------------------------------------
    # Core security
    # --------------------------------------------------------

    health.register(
        "audit_logger",
        lambda: audit_logger is not None,
    )

    health.register(
        "permission_engine",
        lambda: permission_engine is not None,
    )

    health.register(
        "permission_loader",
        lambda: permission_loader is not None,
    )

    # --------------------------------------------------------
    # Agents
    # --------------------------------------------------------

    health.register(
        "agent_registry",
        lambda: agent_registry is not None,
    )

    health.register(
        "agents",
        lambda: len(agent_registry.list_agents()) == 8,
    )

    # --------------------------------------------------------
    # Decision / approval / controller
    # --------------------------------------------------------

    health.register(
        "decision_engine",
        lambda: decision_engine is not None,
    )

    health.register(
        "approval_gate",
        lambda: approval_gate is not None,
    )

    health.register(
        "agent_controller",
        lambda: agent_controller is not None,
    )

    # --------------------------------------------------------
    # Routing / intelligence
    # --------------------------------------------------------

    health.register(
        "orchestrator",
        lambda: orchestrator is not None,
    )

    health.register(
        "manager",
        lambda: manager is not None,
    )

    health.register(
        "intent_engine",
        lambda: intent_engine is not None,
    )

    health.register(
        "task_planner",
        lambda: task_planner is not None,
    )

    # --------------------------------------------------------
    # Tools
    # --------------------------------------------------------

    health.register(
        "tool_registry",
        lambda: tool_registry is not None
        and tool_registry.count() > 0,
    )

    health.register(
        "tool_gateway",
        lambda: tool_gateway is not None,
    )

    # ========================================================
    # 16. RUN HEALTH CHECK
    # ========================================================

    report = health.run()

    if not report.is_healthy():
        raise CortexBootstrapError(
            report.summary()
        )

    # ========================================================
    # 17. BUILD COMPLETE RUNTIME
    # ========================================================

    return CortexRuntime(
        # Security
        agent_registry=agent_registry,
        permission_engine=permission_engine,
        permission_loader=permission_loader,
        decision_engine=decision_engine,
        approval_gate=approval_gate,
        audit_logger=audit_logger,
        voice_audit=voice_audit,
        agent_controller=agent_controller,

        # Routing
        orchestrator=orchestrator,
        manager=manager,
        intent_engine=intent_engine,
        task_planner=task_planner,

        # Tools
        tool_registry=tool_registry,
        tool_gateway=tool_gateway,

        # Health
        health=health,
        health_report=report,
    )


# ============================================================
# BACKWARD-COMPATIBLE BUILDER
# ============================================================

def build_cortex() -> dict:
    """
    Backward-compatible builder used by existing CORTEX tests
    and older modules.

    Returns both the individual components and the complete
    CortexRuntime object.
    """

    runtime = bootstrap_cortex()

    return {
        # ----------------------------------------------------
        # Agents
        # ----------------------------------------------------

        "registry": runtime.agent_registry,
        "agents": runtime.agent_registry.list_agents(),

        # ----------------------------------------------------
        # Security
        # ----------------------------------------------------

        "permissions": runtime.permission_engine,
        "permission_loader": runtime.permission_loader,
        "decision_engine": runtime.decision_engine,
        "approval_gate": runtime.approval_gate,
        "audit_logger": runtime.audit_logger,
        "voice_audit": runtime.voice_audit,

        # ----------------------------------------------------
        # Controller / routing
        # ----------------------------------------------------

        "controller": runtime.agent_controller,
        "agent_controller": runtime.agent_controller,
        "orchestrator": runtime.orchestrator,
        "manager": runtime.manager,
        "intent_engine": runtime.intent_engine,
        "task_planner": runtime.task_planner,

        # ----------------------------------------------------
        # Tools
        # ----------------------------------------------------

        "tool_registry": runtime.tool_registry,
        "tool_gateway": runtime.tool_gateway,

        # ----------------------------------------------------
        # Health
        # ----------------------------------------------------

        "health": runtime.health,
        "health_report": runtime.health_report,

        # ----------------------------------------------------
        # Complete runtime
        # ----------------------------------------------------

        "runtime": runtime,
    }


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    try:
        runtime = bootstrap_cortex()

        print(
            runtime.health_report.summary()
        )

    except CortexBootstrapError as exc:

        print("CORTEX BOOTSTRAP FAILED")
        print("=" * 50)
        print(exc)

        raise SystemExit(1)








