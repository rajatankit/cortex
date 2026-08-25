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
                    "tournament bana",
                    "tournament banao",
                    "tournament bana do",
                    "tournament bana de",
                    "naya tournament bana",
                    "naya tournament banao",
                    "naya tournament bana do",
                    "ek tournament bana",
                    "ek naya tournament banao",
                    "tournament create kar",
                    "tournament create karo",
                    "tournament create kar do",
                    "tournament start kar",
                    "tournament start karo",
                    "tournament shuru kar",
                    "tournament shuru karo",
                    "tournament add kar",
                    "tournament add karo",
                ),
            ),

            IntentRule(
                agent_id="ARIA",
                action="manage_tournament",
                priority=90,
                phrases=(
                    "tournament update kar",
                    "tournament update karo",
                    "tournament update kar do",
                    "tournament edit kar",
                    "tournament edit karo",
                    "tournament change kar",
                    "tournament change karo",
                    "tournament cancel kar",
                    "tournament cancel karo",
                    "tournament band kar",
                    "tournament band karo",
                    "tournament modify kar",
                    "tournament modify karo",
                    "tournament ko update karo",
                    "tournament ki details badlo",
                    "tournament ka time change karo",
                ),
            ),

            IntentRule(
                agent_id="ARIA",
                action="read_tournament",
                priority=50,
                phrases=(
                    "tournament check kar",
                    "tournament check karo",
                    "tournament check kar do",
                    "tournament dikha",
                    "tournament dikhao",
                    "tournament dikha do",
                    "tournament bata",
                    "tournament batao",
                    "tournament bata do",
                    "tournament dekh",
                    "tournament dekho",
                    "tournament dekh lo",
                    "tournament ki details",
                    "tournament ki details batao",
                    "tournament ki information",
                    "tournament ki jaankari",
                    "tournament ki jaankari do",
                    "tournament ka status",
                    "tournament ka status batao",
                    "tournament ka status kya hai",
                    "tournament ke baare me batao",
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
                    "player update kar",
                    "player update karo",
                    "player update kar do",
                    "player ka data update kar",
                    "player ka data update karo",
                    "player ki details update kar",
                    "player ki details update karo",
                    "player profile update kar",
                    "player profile update karo",
                    "player edit kar",
                    "player edit karo",
                    "player ki jaankari badlo",
                    "player ka data badlo",
                    "player ki details change karo",
                ),
            ),

            IntentRule(
                agent_id="ELARA",
                action="read_player_data",
                priority=50,
                phrases=(
                    "player check kar",
                    "player check karo",
                    "player check kar do",
                    "player dikha",
                    "player dikhao",
                    "player dikha do",
                    "player details batao",
                    "player ki details",
                    "player ki details batao",
                    "player ka data",
                    "player ka data batao",
                    "player ki information",
                    "player ki jaankari",
                    "player ki jaankari do",
                    "player profile dikhao",
                    "player uid batao",
                    "player ka uid kya hai",
                    "player ke baare me batao",
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
                    "notification bhej",
                    "notification bhejo",
                    "notification bhej do",
                    "player ko notify kar",
                    "player ko notify karo",
                    "player ko message bhejo",
                    "alert bhejo",
                    "player ko alert bhej do",
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
                    "room bana",
                    "room banao",
                    "room bana do",
                    "naya room bana",
                    "room password save kar",
                    "room password store karo",
                    "room data save karo",
                    "room ki details save karo",
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
                    "room update kar",
                    "room update karo",
                    "room ka password badlo",
                    "room password change karo",
                    "room ki details badlo",
                    "room edit karo",
                ),
            ),

            IntentRule(
                agent_id="VAULT",
                action="read_room_data",
                priority=50,
                phrases=(
                    "room check kar",
                    "room check karo",
                    "room check kar do",
                    "room dikha",
                    "room dikhao",
                    "room dikha do",
                    "room details batao",
                    "room ki details",
                    "room ka data",
                    "room id batao",
                    "room ki jaankari do",
                    "room password batao",
                    "room ke baare me batao",
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
                    "match update kar",
                    "match update karo",
                    "match ka result update karo",
                    "match ki details badlo",
                    "match cancel karo",
                    "match edit karo",
                ),
            ),

            IntentRule(
                agent_id="ORION",
                action="read_match_data",
                priority=50,
                phrases=(
                    "match check kar",
                    "match check karo",
                    "match check kar do",
                    "match dikha",
                    "match dikhao",
                    "match details batao",
                    "match ki details",
                    "match ka data",
                    "matches dikhao",
                    "match ki jaankari do",
                    "match ka status batao",
                    "match ke baare me batao",
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
                    "suspicious transaction report karo",
                    "fraud report karo",
                    "transaction ko flag karo",
                    "is transaction ki complaint karo",
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
                    "transaction verify karo",
                    "transaction validate karo",
                    "transaction sahi hai ya nahi check karo",
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
                    "deposit ka status batao",
                    "deposit check karo",
                    "mera deposit kaha hai",
                    "deposit ki jaankari do",
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
                    "withdrawal ka status batao",
                    "withdrawal check karo",
                    "mera withdrawal kaha hai",
                    "paisa withdraw hua ya nahi batao",
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
                    "transaction dikhao",
                    "transaction ki details batao",
                    "transaction check karo",
                    "mera transaction dikhao",
                ),
            ),

            IntentRule(
                agent_id="NOVA",
                action="read_wallet",
                priority=50,
                phrases=(
                    "wallet check kar",
                    "wallet check karo",
                    "wallet check kar do",
                    "wallet dikha",
                    "wallet dikhao",
                    "wallet balance batao",
                    "wallet ka balance batao",
                    "balance check kar",
                    "balance check karo",
                    "balance batao",
                    "mere wallet ka balance",
                    "mera balance kitna hai",
                    "wallet me kitna paisa hai",
                    "mera paisa kitna hai",
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
                    "code fix karo",
                    "code update karo",
                    "bug fix karo",
                    "code me error thik karo",
                    "code edit karo",
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
                    "code dikhao",
                    "code check karo",
                    "code padho",
                    "code dekho",
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
                    "attacker ko block karo",
                    "security action lo",
                    "attack ka response do",
                    "hamle ka jawab do",
                ),
            ),

            IntentRule(
                agent_id="SENTINEL",
                action="security_scan",
                priority=90,
                phrases=(
                    "security check kar",
                    "security check karo",
                    "security scan kar",
                    "security scan karo",
                    "threats check kar",
                    "threat check karo",
                    "security dekh",
                    "security scan chalao",
                    "threats dhundo",
                    "khatra check karo",
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
                    "security logs dikhao",
                    "security ki history batao",
                    "security events dikhao",
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