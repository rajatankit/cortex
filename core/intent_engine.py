from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IntentResult:
    success: bool
    agent_id: str
    action: str
    context: dict[str, Any]
    message: str


@dataclass(frozen=True)
class IntentRule:
    """
    Immutable natural-language intent rule.

    priority:
        Higher priority rules are evaluated first.

    phrases:
        Natural-language phrases that can identify the intent.
    """

    agent_id: str
    action: str
    priority: int
    phrases: tuple[str, ...]


class IntentEngine:
    """
    Converts a natural-language CORTEX request into a
    structured agent/action/context intent.

    SECURITY BOUNDARY
    -----------------
    This layer:

        DOES:
            - Validate the request
            - Normalize natural language
            - Identify an agent
            - Identify an action
            - Preserve request context

        DOES NOT:
            - Execute tools
            - Check permissions
            - Approve actions
            - Bypass ApprovalGate
            - Modify application state

    Execution remains:

        IntentEngine
            ↓
        TaskPlanner
            ↓
        ToolGateway
            ↓
        AgentController
            ↓
        PermissionEngine
            ↓
        DecisionEngine
            ↓
        ApprovalGate
            ↓
        Tool
            ↓
        AuditLogger
    """

    def __init__(self) -> None:

        # =========================================================
        # INTENT RULES
        # =========================================================
        #
        # Higher priority means stronger intent.
        #
        # This prevents ambiguous phrases such as:
        #
        #     "update player information"
        #
        # from being incorrectly classified as:
        #
        #     read_player_data
        #
        # because "player information" also appears in the
        # read rule.
        #
        # =========================================================

        self._rules: tuple[IntentRule, ...] = (

            # =====================================================
            # ARIA — TOURNAMENT MANAGEMENT
            # =====================================================

            IntentRule(
                agent_id="ARIA",
                action="create_tournament",
                priority=100,
                phrases=(
                    "create a tournament",
                    "create tournament",
                    "create new tournament",
                    "new tournament",
                    "make a tournament",
                    "start a tournament",
                ),
            ),

            IntentRule(
                agent_id="ARIA",
                action="manage_tournament",
                priority=90,
                phrases=(
                    "update tournament",
                    "edit tournament",
                    "change tournament",
                    "manage tournament",
                    "modify tournament",
                    "cancel tournament",
                    "delete tournament",
                ),
            ),

            IntentRule(
                agent_id="ARIA",
                action="read_tournament",
                priority=50,
                phrases=(
                    "read tournament",
                    "check tournament",
                    "show tournament",
                    "view tournament",
                    "list tournaments",
                    "tournament information",
                    "tournament details",
                    "show tournaments",
                ),
            ),

            # =====================================================
            # ELARA — PLAYER INFORMATION
            # =====================================================

            IntentRule(
                agent_id="ELARA",
                action="update_player_data",
                priority=100,
                phrases=(
                    "update player information",
                    "update player profile",
                    "update player data",
                    "edit player information",
                    "edit player profile",
                    "edit player data",
                    "change player information",
                    "change player profile",
                    "change player data",
                    "update player",
                    "edit player",
                    "change player",
                    "modify player",
                ),
            ),

            IntentRule(
                agent_id="ELARA",
                action="read_player_data",
                priority=50,
                phrases=(
                    "read player",
                    "check player",
                    "show player",
                    "view player",
                    "player information",
                    "player profile",
                    "player data",
                    "player uid",
                    "player details",
                    "show players",
                    "list players",
                ),
            ),

            # =====================================================
            # LYRA — NOTIFICATIONS
            # =====================================================

            IntentRule(
                agent_id="LYRA",
                action="send_notification",
                priority=80,
                phrases=(
                    "send notification",
                    "send a notification",
                    "notify player",
                    "send alert",
                    "send message to player",
                    "notify the player",
                ),
            ),

            # =====================================================
            # VAULT — PROTECTED ROOM DATA
            # =====================================================

            IntentRule(
                agent_id="VAULT",
                action="store_room_data",
                priority=100,
                phrases=(
                    "store room data",
                    "save room data",
                    "create room",
                    "create protected room",
                    "store room password",
                    "protect room data",
                    "add room data",
                ),
            ),

            IntentRule(
                agent_id="VAULT",
                action="update_room_data",
                priority=90,
                phrases=(
                    "update room",
                    "update room data",
                    "edit room",
                    "change room",
                    "modify room",
                    "update room password",
                    "change room password",
                    "set room password",
                ),
            ),

            IntentRule(
                agent_id="VAULT",
                action="read_room_data",
                priority=50,
                phrases=(
                    "read room",
                    "check room",
                    "show room",
                    "view room",
                    "room information",
                    "room details",
                    "room data",
                    "room id",
                    "get room id",
                ),
            ),

            # =====================================================
            # ORION — MATCH OPERATIONS
            # =====================================================

            IntentRule(
                agent_id="ORION",
                action="manage_match",
                priority=90,
                phrases=(
                    "manage match",
                    "update match",
                    "edit match",
                    "change match",
                    "modify match",
                    "match result",
                    "update match result",
                    "change match result",
                    "edit match result",
                ),
            ),

            IntentRule(
                agent_id="ORION",
                action="read_match_data",
                priority=50,
                phrases=(
                    "read match",
                    "check match",
                    "show match",
                    "view match",
                    "match information",
                    "match details",
                    "match data",
                    "show matches",
                    "list matches",
                ),
            ),

            # =====================================================
            # NOVA — FINANCE
            # =====================================================

            IntentRule(
                agent_id="NOVA",
                action="report_suspicious_transaction",
                priority=100,
                phrases=(
                    "report suspicious transaction",
                    "report suspicious activity",
                    "flag transaction",
                    "flag suspicious transaction",
                    "report fraud",
                ),
            ),

            IntentRule(
                agent_id="NOVA",
                action="validate_transaction",
                priority=90,
                phrases=(
                    "validate transaction",
                    "verify transaction",
                    "check transaction validity",
                ),
            ),

            IntentRule(
                agent_id="NOVA",
                action="read_deposit_status",
                priority=60,
                phrases=(
                    "deposit status",
                    "check deposit status",
                    "read deposit status",
                    "deposit information",
                ),
            ),

            IntentRule(
                agent_id="NOVA",
                action="read_withdrawal_status",
                priority=60,
                phrases=(
                    "withdrawal status",
                    "check withdrawal status",
                    "read withdrawal status",
                    "withdrawal information",
                ),
            ),

            IntentRule(
                agent_id="NOVA",
                action="read_transaction",
                priority=55,
                phrases=(
                    "read transaction",
                    "check transaction",
                    "show transaction",
                    "transaction details",
                    "transaction information",
                ),
            ),

            IntentRule(
                agent_id="NOVA",
                action="read_wallet",
                priority=50,
                phrases=(
                    "read wallet",
                    "check wallet",
                    "show wallet",
                    "view wallet",
                    "wallet balance",
                    "account balance",
                    "check balance",
                ),
            ),

            # =====================================================
            # ATLAS — CODING & ENGINEERING
            # =====================================================

            IntentRule(
                agent_id="ATLAS",
                action="modify_code",
                priority=100,
                phrases=(
                    "fix code",
                    "fix the code",
                    "modify code",
                    "change code",
                    "edit code",
                    "update code",
                    "fix bug",
                    "fix a bug",
                    "debug code",
                    "modify the code",
                    "change the code",
                ),
            ),

            IntentRule(
                agent_id="ATLAS",
                action="read_code",
                priority=50,
                phrases=(
                    "read code",
                    "inspect code",
                    "check code",
                    "show code",
                    "view code",
                    "review code",
                    "code information",
                    "code details",
                ),
            ),

            # =====================================================
            # SENTINEL — SECURITY
            # =====================================================

            IntentRule(
                agent_id="SENTINEL",
                action="security_action",
                priority=110,
                phrases=(
                    "security action",
                    "respond to attack",
                    "respond to security attack",
                    "handle security attack",
                    "take security action",
                    "block attacker",
                ),
            ),

            IntentRule(
                agent_id="SENTINEL",
                action="security_scan",
                priority=90,
                phrases=(
                    "security scan",
                    "scan security",
                    "scan for threats",
                    "scan for vulnerabilities",
                    "security check",
                    "run security scan",
                    "check for threats",
                ),
            ),

            IntentRule(
                agent_id="SENTINEL",
                action="read_security_logs",
                priority=50,
                phrases=(
                    "security logs",
                    "security events",
                    "security history",
                    "read security logs",
                    "show security logs",
                    "view security logs",
                ),
            ),
        )

        # =========================================================
        # PREPARE RULES
        # =========================================================
        #
        # Sort once during initialization.
        #
        # Primary:
        #     priority DESC
        #
        # Secondary:
        #     longest phrase DESC
        #
        # This gives explicit high-priority actions precedence
        # while also preferring more specific phrases.
        #
        # =========================================================

        self._ordered_rules = tuple(
            sorted(
                self._rules,
                key=lambda rule: (
                    -rule.priority,
                    -max(
                        (len(self._normalize(phrase)) for phrase in rule.phrases),
                        default=0,
                    ),
                ),
            )
        )

    # =============================================================
    # NORMALIZATION
    # =============================================================

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalize natural-language input.

        Operations:
            - lowercase
            - replace punctuation with spaces
            - collapse repeated whitespace
            - strip leading/trailing whitespace

        Example:

            "  UPDATE Player Information!!! "

        becomes:

            "update player information"
        """

        normalized = text.lower().strip()

        # Replace punctuation/symbols with spaces.
        normalized = re.sub(
            r"[^a-z0-9\s]",
            " ",
            normalized,
        )

        # Collapse repeated whitespace.
        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized.strip()

    # =============================================================
    # PHRASE MATCHING
    # =============================================================

    @staticmethod
    def _phrase_matches(
        text: str,
        phrase: str,
    ) -> bool:
        """
        Match a complete phrase using word boundaries.

        This avoids accidental substring matches.

        Example:

            "update player"

        matches:

            "update player information"

        but avoids unrelated partial-word matches.
        """

        normalized_phrase = IntentEngine._normalize(phrase)

        if not normalized_phrase:
            return False

        pattern = (
            r"(?<!\w)"
            + re.escape(normalized_phrase)
            + r"(?!\w)"
        )

        return re.search(
            pattern,
            text,
        ) is not None

    # =============================================================
    # RULE MATCHING
    # =============================================================

    def _find_matching_rule(
        self,
        text: str,
    ) -> IntentRule | None:
        """
        Return the highest-priority matching intent rule.
        """

        for rule in self._ordered_rules:

            for phrase in rule.phrases:

                if self._phrase_matches(
                    text=text,
                    phrase=phrase,
                ):
                    return rule

        return None

    # =============================================================
    # PUBLIC PARSER
    # =============================================================

    def parse(
        self,
        request: str,
        context: dict[str, Any] | None = None,
    ) -> IntentResult:

        # ---------------------------------------------------------
        # 1. EMPTY REQUEST
        # ---------------------------------------------------------

        if not request or not request.strip():
            return IntentResult(
                success=False,
                agent_id="UNKNOWN",
                action="UNKNOWN",
                context=dict(context or {}),
                message="Request cannot be empty.",
            )

        # ---------------------------------------------------------
        # 2. NORMALIZE
        # ---------------------------------------------------------

        text = self._normalize(request)

        if not text:
            return IntentResult(
                success=False,
                agent_id="UNKNOWN",
                action="UNKNOWN",
                context=dict(context or {}),
                message="Request cannot be empty.",
            )

        # ---------------------------------------------------------
        # 3. FIND INTENT
        # ---------------------------------------------------------

        rule = self._find_matching_rule(text)

        # ---------------------------------------------------------
        # 4. UNKNOWN INTENT
        # ---------------------------------------------------------

        if rule is None:
            return IntentResult(
                success=False,
                agent_id="UNKNOWN",
                action="UNKNOWN",
                context=dict(context or {}),
                message="Unable to identify a supported intent.",
            )

        # ---------------------------------------------------------
        # 5. SUCCESS
        # ---------------------------------------------------------

        return IntentResult(
            success=True,
            agent_id=rule.agent_id,
            action=rule.action,
            context=dict(context or {}),
            message="Intent identified successfully.",
        )

    # =============================================================
    # DEBUG / INSPECTION
    # =============================================================

    def supported_intents(self) -> tuple[tuple[str, str], ...]:
        """
        Return all supported agent/action combinations.
        """

        return tuple(
            (rule.agent_id, rule.action)
            for rule in self._rules
        )

    def rules_for_agent(
        self,
        agent_id: str,
    ) -> tuple[IntentRule, ...]:
        """
        Return all rules belonging to a specific agent.
        """

        normalized_agent = agent_id.strip().upper()

        return tuple(
            rule
            for rule in self._rules
            if rule.agent_id == normalized_agent
        )

    def has_action(
        self,
        action: str,
    ) -> bool:
        """
        Check whether an action is supported by the intent engine.
        """

        normalized_action = action.strip()

        return any(
            rule.action == normalized_action
            for rule in self._rules
        )