from dataclasses import dataclass
from enum import Enum
from core.permissions import PermissionEngine, RiskLevel


class Decision(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"
    BLOCK = "block"


@dataclass(frozen=True)
class DecisionResult:
    agent_id: str
    action: str
    allowed: bool
    risk: RiskLevel | None
    decision: Decision


class DecisionEngine:
    """
    Converts permission + risk information into a CORTEX decision.

    Security policy:

        LOW      -> ALLOW
        MEDIUM   -> REVIEW
        HIGH     -> REVIEW
        CRITICAL -> BLOCK

    Important:
    - Permission must exist before any action can proceed.
    - Medium and high risk actions require explicit approval.
    - Critical actions are blocked at the decision layer.
    """

    def __init__(self, permission_engine: PermissionEngine):
        self.permission_engine = permission_engine

    def evaluate(
        self,
        agent_id: str,
        action: str,
    ) -> DecisionResult:

        # ---------------------------------------------------------
        # 1. VERIFY PERMISSION
        # ---------------------------------------------------------

        allowed = self.permission_engine.is_allowed(
            agent_id,
            action,
        )

        risk = self.permission_engine.get_risk(
            agent_id,
            action,
        )

        # ---------------------------------------------------------
        # 2. DENY UNKNOWN / UNAUTHORIZED ACTIONS
        # ---------------------------------------------------------

        if not allowed or risk is None:
            decision = Decision.DENY

        # ---------------------------------------------------------
        # 3. LOW RISK
        # ---------------------------------------------------------

        elif risk == RiskLevel.LOW:
            decision = Decision.ALLOW

        # ---------------------------------------------------------
        # 4. MEDIUM RISK
        # ---------------------------------------------------------
        #
        # MEDIUM actions require explicit human/boss approval.
        #
        # Example:
        # ELARA -> update_player_data
        # LYRA  -> send_notification
        # VAULT -> manage_notifications
        #

        elif risk == RiskLevel.MEDIUM:
            decision = Decision.REVIEW

        # ---------------------------------------------------------
        # 5. HIGH RISK
        # ---------------------------------------------------------
        #
        # HIGH actions also require explicit approval.
        #
        # Example:
        # ARIA  -> create_tournament
        # NOVA  -> process_financial_action
        # ATLAS -> modify_code
        #

        elif risk == RiskLevel.HIGH:
            decision = Decision.REVIEW

        # ---------------------------------------------------------
        # 6. CRITICAL RISK
        # ---------------------------------------------------------
        #
        # Critical operations must never be automatically executed.
        # They are blocked at the decision layer until a future
        # explicit security workflow is implemented.
        #

        elif risk == RiskLevel.CRITICAL:
            decision = Decision.BLOCK

        # ---------------------------------------------------------
        # 7. DEFENSIVE FALLBACK
        # ---------------------------------------------------------

        else:
            decision = Decision.BLOCK

        return DecisionResult(
            agent_id=agent_id,
            action=action,
            allowed=allowed,
            risk=risk,
            decision=decision,
        )




