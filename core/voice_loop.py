from __future__ import annotations

import asyncio
import re
from typing import Optional

from core.voice_interface import VoiceInterface
from core.cortex_runtime import CortexRuntime


class VoiceLoop:
    """
    Continuous Voice Control Loop for CORTEX.

    Flow:
        Listen → STT → Hinglish Normalization
        → CORTEX Runtime → IntentEngine
        → Permissions / Decision / Approval
        → ToolGateway → TTS

    Voice normalization NEVER bypasses the CORTEX security pipeline.
    """

    def __init__(
        self,
        runtime: CortexRuntime,
        voice: Optional[VoiceInterface] = None,
        listen_duration: float = 6.0,
    ):
        self.runtime = runtime
        self.voice = voice or VoiceInterface()
        self.listen_duration = listen_duration
        self._running = False

    # ============================================================
    # TEXT CLEANING
    # ============================================================

    @staticmethod
    def _clean(text: str) -> str:
        """
        Clean Whisper output before matching.
        """

        if not text:
            return ""

        text = text.lower().strip()

        # Common Whisper punctuation/noise.
        text = re.sub(r"[^\w\s]", " ", text)

        # Collapse whitespace.
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ============================================================
    # HINGLISH / HINDI → CANONICAL CORTEX COMMAND
    # ============================================================

    @staticmethod
    def normalize_hinglish(text: str) -> str:
        """
        Convert common Hindi/Hinglish voice commands into
        canonical English commands understood by IntentEngine.

        This function ONLY changes the natural-language request.

        It does NOT:
            - execute tools
            - check permissions
            - approve actions
            - bypass ApprovalGate
            - modify application state
        """

        original = text.strip()

        if not original:
            return ""

        lower = VoiceLoop._clean(original)

        # --------------------------------------------------------
        # EXIT / SHUTDOWN
        # --------------------------------------------------------

        exit_phrases = (
            "exit",
            "quit",
            "stop",
            "bye",
            "goodbye",
            "shutdown",
            "shut down",
            "voice band kar",
            "voice band karo",
            "voice control band kar",
            "voice control band karo",
            "cortex band kar",
            "cortex band karo",
            "cortex ko band kar",
            "cortex ko band karo",
            "bas kar",
            "bas karo",
            "band kar",
            "band karo",
        )

        if lower in exit_phrases:
            return "exit"

        # ========================================================
        # ARIA — TOURNAMENT
        # ========================================================

        tournament_create = (
            "tournament bana",
            "tournament banao",
            "tournament bana do",
            "tournament create kar",
            "tournament create karo",
            "tournament create kar do",
            "naya tournament bana",
            "naya tournament banao",
            "new tournament bana",
            "new tournament banao",
            "tournament start kar",
            "tournament start karo",
            "tournament shuru kar",
            "tournament shuru karo",
            "ek tournament bana",
            "ek naya tournament bana",
            "ek tournament create kar",
            "create tournament",
            "create a tournament",
            "new tournament",
            "start tournament",
        )

        if any(p in lower for p in tournament_create):
            return "Create Tournament"

        tournament_update = (
            "tournament update kar",
            "tournament update karo",
            "tournament ko update kar",
            "tournament ko update karo",
            "tournament edit kar",
            "tournament edit karo",
            "tournament ko edit kar",
            "tournament ko edit karo",
            "tournament change kar",
            "tournament change karo",
            "tournament modify kar",
            "tournament modify karo",
            "tournament manage kar",
            "tournament manage karo",
            "tournament me change kar",
            "tournament mein change kar",
            "tournament cancel kar",
            "tournament cancel karo",
            "tournament delete kar",
            "tournament delete karo",
            "update tournament",
            "edit tournament",
            "change tournament",
            "manage tournament",
            "modify tournament",
            "cancel tournament",
            "delete tournament",
        )

        if any(p in lower for p in tournament_update):
            return "Update Tournament"

        tournament_read = (
            "tournament check kar",
            "tournament check karo",
            "tournament chek kar",
            "tournament chek karo",
            "tournament ka status bata",
            "tournament ka status batao",
            "tournament ka status dikha",
            "tournament ka status dikhao",
            "tournament status bata",
            "tournament status batao",
            "tournament status dikha",
            "tournament status dikhao",
            "tournament dikha",
            "tournament dikhao",
            "tournament dekh",
            "tournament dekho",
            "tournament ki details bata",
            "tournament ki details batao",
            "tournament ki detail bata",
            "tournament ki detail batao",
            "tournament ki information bata",
            "tournament ki information batao",
            "tournament ke details bata",
            "tournament ke details batao",
            "tournament ke baare me bata",
            "tournament ke bare me bata",
            "tournament ke bare mein bata",
            "tournament ke baare mein bata",
            "tournament check karke bata",
            "tournament check karke batao",
            "tournament dekh ke bata",
            "tournament dekh ke batao",
            "tournament dikha ke bata",
            "tournament dikha ke batao",
            "tournament kya chal raha hai",
            "tournament ka kya status hai",
            "tournament active hai",
            "tournament open hai",
            "tournament ki info de",
            "tournament ki details de",
            "tournament ka data dikha",
            "tournament ka data bata",
            "check tournament",
            "show tournament",
            "view tournament",
            "read tournament",
            "tournament information",
            "tournament details",
            "show tournaments",
            "list tournaments",
        )

        if any(p in lower for p in tournament_read):
            return "Check Tournament"

        # ========================================================
        # ELARA — PLAYER
        # ========================================================

        player_update = (
            "player update kar",
            "player update karo",
            "player ko update kar",
            "player ko update karo",
            "player edit kar",
            "player edit karo",
            "player ko edit kar",
            "player ko edit karo",
            "player change kar",
            "player change karo",
            "player modify kar",
            "player modify karo",
            "player ki information update kar",
            "player ki information update karo",
            "player ki profile update kar",
            "player ki profile update karo",
            "player ka data update kar",
            "player ka data update karo",
            "player ki details update kar",
            "player ki details update karo",
            "player information change kar",
            "player profile change kar",
            "player data change kar",
            "update player",
            "update player information",
            "update player profile",
            "update player data",
            "edit player",
            "edit player information",
            "edit player profile",
            "edit player data",
            "change player",
            "change player information",
            "change player profile",
            "change player data",
            "modify player",
        )

        if any(p in lower for p in player_update):
            return "Update Player"

        player_read = (
            "player check kar",
            "player check karo",
            "player ko check kar",
            "player ko check karo",
            "player dikha",
            "player dikhao",
            "player dekh",
            "player dekho",
            "player ki details bata",
            "player ki details batao",
            "player ki information bata",
            "player ki information batao",
            "player ka data bata",
            "player ka data batao",
            "player ka profile bata",
            "player ka profile batao",
            "player ki profile dikha",
            "player ki profile dikhao",
            "player uid bata",
            "player ka uid bata",
            "player ka uid dikha",
            "players dikha",
            "players dikhao",
            "players ki list dikha",
            "players ki list dikhao",
            "check player",
            "show player",
            "view player",
            "read player",
            "player information",
            "player profile",
            "player data",
            "player uid",
            "player details",
            "show players",
            "list players",
        )

        if any(p in lower for p in player_read):
            return "Check Player"

        # ========================================================
        # LYRA — NOTIFICATIONS
        # ========================================================

        notification_commands = (
            "notification bhej",
            "notification bhejo",
            "notification send kar",
            "notification send karo",
            "notification bhej do",
            "message bhej",
            "message bhejo",
            "message send kar",
            "message send karo",
            "player ko message bhej",
            "player ko message bhejo",
            "player ko notification bhej",
            "player ko notification bhejo",
            "player ko notify kar",
            "player ko notify karo",
            "players ko notification bhej",
            "players ko notification bhejo",
            "alert bhej",
            "alert bhejo",
            "alert send kar",
            "alert send karo",
            "send notification",
            "send a notification",
            "notify player",
            "notify the player",
            "send alert",
            "send message to player",
        )

        if any(p in lower for p in notification_commands):
            return "Send Notification"

        # ========================================================
        # VAULT — ROOM
        # ========================================================

        room_store = (
            "room bana",
            "room banao",
            "room create kar",
            "room create karo",
            "room create kar do",
            "room data save kar",
            "room data save karo",
            "room data store kar",
            "room data store karo",
            "room information save kar",
            "room information save karo",
            "room password save kar",
            "room password save karo",
            "room ko protect kar",
            "room ko secure kar",
            "protected room bana",
            "protected room banao",
            "store room data",
            "save room data",
            "create room",
            "create protected room",
            "store room password",
            "protect room data",
            "add room data",
        )

        if any(p in lower for p in room_store):
            return "Store Room Data"

        room_update = (
            "room update kar",
            "room update karo",
            "room ko update kar",
            "room ko update karo",
            "room edit kar",
            "room edit karo",
            "room ko edit kar",
            "room ko edit karo",
            "room change kar",
            "room change karo",
            "room modify kar",
            "room modify karo",
            "room password change kar",
            "room password change karo",
            "room password update kar",
            "room password update karo",
            "room ki details change kar",
            "room ki details change karo",
            "room ka data change kar",
            "room ka data change karo",
            "update room",
            "update room data",
            "edit room",
            "change room",
            "modify room",
            "update room password",
            "change room password",
            "set room password",
        )

        if any(p in lower for p in room_update):
            return "Update Room"

        room_read = (
            "room check kar",
            "room check karo",
            "room ko check kar",
            "room ko check karo",
            "room dikha",
            "room dikhao",
            "room dekh",
            "room dekho",
            "room ki details bata",
            "room ki details batao",
            "room ki information bata",
            "room ki information batao",
            "room ka data bata",
            "room ka data batao",
            "room id bata",
            "room id dikha",
            "room ka id bata",
            "room ka id dikha",
            "room password bata",
            "room details dikha",
            "room details dikhao",
            "check room",
            "show room",
            "view room",
            "read room",
            "room information",
            "room details",
            "room data",
            "room id",
            "get room id",
        )

        if any(p in lower for p in room_read):
            return "Check Room"

        # ========================================================
        # ORION — MATCH
        # ========================================================

        match_manage = (
            "match update kar",
            "match update karo",
            "match ko update kar",
            "match ko update karo",
            "match edit kar",
            "match edit karo",
            "match ko edit kar",
            "match ko edit karo",
            "match change kar",
            "match change karo",
            "match modify kar",
            "match modify karo",
            "match result update kar",
            "match result update karo",
            "match ka result update kar",
            "match ka result update karo",
            "match result change kar",
            "match result change karo",
            "match result edit kar",
            "match result edit karo",
            "match manage kar",
            "match manage karo",
            "manage match",
            "update match",
            "edit match",
            "change match",
            "modify match",
            "match result",
            "update match result",
            "change match result",
            "edit match result",
        )

        if any(p in lower for p in match_manage):
            return "Manage Match"

        match_read = (
            "match check kar",
            "match check karo",
            "match dikha",
            "match dikhao",
            "match dekh",
            "match dekho",
            "match ki details bata",
            "match ki details batao",
            "match ki information bata",
            "match ki information batao",
            "match ka data bata",
            "match ka data batao",
            "matches dikha",
            "matches dikhao",
            "matches ki list dikha",
            "matches ki list dikhao",
            "check match",
            "show match",
            "view match",
            "read match",
            "match information",
            "match details",
            "match data",
            "show matches",
            "list matches",
        )

        if any(p in lower for p in match_read):
            return "Check Match"

        # ========================================================
        # NOVA — FINANCE / TRANSACTIONS
        # ========================================================

        suspicious_transaction = (
            "suspicious transaction report kar",
            "suspicious transaction report karo",
            "suspicious transaction ko report kar",
            "suspicious transaction ko report karo",
            "suspicious activity report kar",
            "suspicious activity report karo",
            "transaction flag kar",
            "transaction flag karo",
            "suspicious transaction flag kar",
            "suspicious transaction flag karo",
            "fraud report kar",
            "fraud report karo",
            "fraud transaction report kar",
            "fraud transaction report karo",
            "report suspicious transaction",
            "report suspicious activity",
            "flag transaction",
            "flag suspicious transaction",
            "report fraud",
        )

        if any(p in lower for p in suspicious_transaction):
            return "Report Suspicious Transaction"

        validate_transaction = (
            "transaction validate kar",
            "transaction validate karo",
            "transaction verify kar",
            "transaction verify karo",
            "transaction check kar",
            "transaction check karo",
            "transaction valid hai ya nahi",
            "transaction sahi hai ya nahi",
            "transaction genuine hai ya nahi",
            "payment verify kar",
            "payment verify karo",
            "payment check kar",
            "payment check karo",
            "validate transaction",
            "verify transaction",
            "check transaction validity",
        )

        if any(p in lower for p in validate_transaction):
            return "Validate Transaction"

        deposit_status = (
            "deposit status bata",
            "deposit status batao",
            "deposit ka status bata",
            "deposit ka status batao",
            "deposit check kar",
            "deposit check karo",
            "deposit ka status check kar",
            "deposit ka status check karo",
            "deposit ki information bata",
            "deposit ki information batao",
            "deposit details bata",
            "deposit details batao",
            "check deposit status",
            "read deposit status",
            "deposit status",
            "deposit information",
        )

        if any(p in lower for p in deposit_status):
            return "Check Deposit Status"

        withdrawal_status = (
            "withdrawal status bata",
            "withdrawal status batao",
            "withdrawal ka status bata",
            "withdrawal ka status batao",
            "withdrawal check kar",
            "withdrawal check karo",
            "withdrawal ka status check kar",
            "withdrawal ka status check karo",
            "withdrawal ki information bata",
            "withdrawal ki information batao",
            "withdrawal details bata",
            "withdrawal details batao",
            "check withdrawal status",
            "read withdrawal status",
            "withdrawal status",
            "withdrawal information",
        )

        if any(p in lower for p in withdrawal_status):
            return "Check Withdrawal Status"

        wallet_read = (
            "wallet check kar",
            "wallet check karo",
            "wallet dikha",
            "wallet dikhao",
            "wallet balance bata",
            "wallet balance batao",
            "wallet ka balance bata",
            "wallet ka balance batao",
            "mere wallet ka balance bata",
            "mera wallet check kar",
            "mera wallet dikha",
            "balance bata",
            "balance batao",
            "account balance bata",
            "account balance batao",
            "account ka balance bata",
            "account ka balance batao",
            "paise kitne hain",
            "wallet me kitne paise hain",
            "wallet mein kitne paise hain",
            "wallet me kitna balance hai",
            "wallet mein kitna balance hai",
            "read wallet",
            "check wallet",
            "show wallet",
            "view wallet",
            "wallet balance",
            "account balance",
            "check balance",
        )

        if any(p in lower for p in wallet_read):
            return "Check Wallet"

        transaction_read = (
            "transaction check kar",
            "transaction check karo",
            "transaction dikha",
            "transaction dikhao",
            "transaction details bata",
            "transaction details batao",
            "transaction ki details bata",
            "transaction ki details batao",
            "transaction ki information bata",
            "transaction ki information batao",
            "transaction ka data bata",
            "transaction ka data batao",
            "transactions dikha",
            "transactions dikhao",
            "payment details bata",
            "payment details batao",
            "read transaction",
            "show transaction",
            "transaction details",
            "transaction information",
        )

        if any(p in lower for p in transaction_read):
            return "Check Transaction"

        # ========================================================
        # ATLAS — CODE / ENGINEERING
        # ========================================================

        code_modify = (
            "code fix kar",
            "code fix karo",
            "code ko fix kar",
            "code ko fix karo",
            "code theek kar",
            "code theek karo",
            "code sahi kar",
            "code sahi karo",
            "code me bug fix kar",
            "code mein bug fix kar",
            "bug fix kar",
            "bug fix karo",
            "bug ko fix kar",
            "bug ko fix karo",
            "error fix kar",
            "error fix karo",
            "code modify kar",
            "code modify karo",
            "code change kar",
            "code change karo",
            "code edit kar",
            "code edit karo",
            "code update kar",
            "code update karo",
            "debug code",
            "fix code",
            "fix the code",
            "modify code",
            "change code",
            "edit code",
            "update code",
            "fix bug",
            "fix a bug",
            "modify the code",
            "change the code",
        )

        if any(p in lower for p in code_modify):
            return "Fix Code"

        code_read = (
            "code check kar",
            "code check karo",
            "code dekh",
            "code dekho",
            "code dikha",
            "code dikhao",
            "code inspect kar",
            "code inspect karo",
            "code review kar",
            "code review karo",
            "code ko review kar",
            "code ko review karo",
            "code ki details bata",
            "code ki details batao",
            "code ka data bata",
            "code ka data batao",
            "read code",
            "inspect code",
            "check code",
            "show code",
            "view code",
            "review code",
            "code information",
            "code details",
        )

        if any(p in lower for p in code_read):
            return "Check Code"

        # ========================================================
        # SENTINEL — SECURITY
        # ========================================================

        security_action = (
            "security action le",
            "security action lo",
            "security action kar",
            "security action karo",
            "attack ko handle kar",
            "attack ko handle karo",
            "security attack handle kar",
            "security attack handle karo",
            "security attack ka response de",
            "security attack ka response do",
            "attacker ko block kar",
            "attacker ko block karo",
            "hacker ko block kar",
            "hacker ko block karo",
            "threat ko block kar",
            "threat ko block karo",
            "respond to attack",
            "respond to security attack",
            "handle security attack",
            "take security action",
            "block attacker",
        )

        if any(p in lower for p in security_action):
            return "Security Action"

        security_scan = (
            "security scan kar",
            "security scan karo",
            "security check kar",
            "security check karo",
            "system security check kar",
            "system security check karo",
            "threat scan kar",
            "threat scan karo",
            "threats check kar",
            "threats check karo",
            "vulnerability scan kar",
            "vulnerability scan karo",
            "vulnerabilities check kar",
            "vulnerabilities check karo",
            "security me kuch problem hai kya",
            "security problem check kar",
            "security problem check karo",
            "scan for threats",
            "scan for vulnerabilities",
            "security scan",
            "security check",
            "run security scan",
            "check for threats",
        )

        if any(p in lower for p in security_scan):
            return "Security Scan"

        security_logs = (
            "security logs dikha",
            "security logs dikhao",
            "security logs check kar",
            "security logs check karo",
            "security events dikha",
            "security events dikhao",
            "security history dikha",
            "security history dikhao",
            "security ka history bata",
            "security ki history bata",
            "security events bata",
            "security events batao",
            "security logs",
            "security events",
            "security history",
            "read security logs",
            "show security logs",
            "view security logs",
        )

        if any(p in lower for p in security_logs):
            return "Security Logs"

        # ========================================================
        # GENERIC HINGLISH FALLBACKS
        # ========================================================
        #
        # These intentionally return canonical phrases only when
        # the domain is unambiguous.
        #

        generic_tournament = (
            "tournament bata",
            "tournament batao",
            "tournament dikha",
            "tournament dikhao",
        )

        if any(p in lower for p in generic_tournament):
            return "Check Tournament"

        generic_player = (
            "player bata",
            "player batao",
            "player dikha",
            "player dikhao",
        )

        if any(p in lower for p in generic_player):
            return "Check Player"

        generic_room = (
            "room bata",
            "room batao",
            "room dikha",
            "room dikhao",
        )

        if any(p in lower for p in generic_room):
            return "Check Room"

        generic_match = (
            "match bata",
            "match batao",
            "match dikha",
            "match dikhao",
        )

        if any(p in lower for p in generic_match):
            return "Check Match"

        # --------------------------------------------------------
        # No safe mapping found.
        #
        # Keep original request so IntentEngine can decide whether
        # it understands it.
        # --------------------------------------------------------

        return original

    # ============================================================
    # ONE VOICE CYCLE
    # ============================================================

    async def process_once(self) -> None:
        """
        One complete cycle:

            Listen → Normalize → Runtime → Speak
        """

        # --------------------------------------------------------
        # 1. LISTEN
        # --------------------------------------------------------

        user_text = self.voice.listen(
            duration=self.listen_duration
        )

        if not user_text:
            await self.voice.speak(
                "I didn't catch that. Please try again."
            )
            return

        print(f"[VoiceLoop] Raw: {user_text}")

        # --------------------------------------------------------
        # 2. HINGLISH NORMALIZATION
        # --------------------------------------------------------

        normalized_text = self.normalize_hinglish(user_text)

        print(f"[VoiceLoop] Normalized: {normalized_text}")

        # --------------------------------------------------------
        # 3. EXIT
        # --------------------------------------------------------

        if normalized_text.lower().strip() in {
            "exit",
            "quit",
            "stop",
            "bye",
            "goodbye",
        }:
            await self.voice.speak(
                "Shutting down voice control. Goodbye."
            )
            self._running = False
            return

        # --------------------------------------------------------
        # 4. CORTEX RUNTIME
        # --------------------------------------------------------

        try:
            result = await self.runtime.execute_intent(
                request=normalized_text
            )

        except Exception as exc:
            print(f"[VoiceLoop Error] {exc}")

            await self.voice.speak(
                f"Sorry, something went wrong. "
                f"{str(exc)[:100]}"
            )
            return

        # --------------------------------------------------------
        # 5. RESPONSE
        # --------------------------------------------------------

        response_text = (
            getattr(result, "message", None)
            or "Done."
        )

        # Clean response for TTS.
        response_text = str(response_text).strip()

        # Avoid extremely long spoken responses.
        if len(response_text) > 300:
            response_text = (
                response_text[:280]
                + ". I have more details if needed."
            )

        await self.voice.speak(response_text)

    # ============================================================
    # CONTINUOUS LOOP
    # ============================================================

    async def run(self) -> None:
        """
        Start continuous voice control.
        """

        self._running = True

        await self.voice.speak(
            "CORTEX voice control online. "
            "Aap mujhse Hinglish ya English mein baat kar sakte hain. "
            "Bataiye, main kya karun?"
        )

        while self._running:

            try:
                await self.process_once()

            except KeyboardInterrupt:
                self._running = False

                await self.voice.speak(
                    "Voice control stopped."
                )

                break

            except Exception as exc:
                print(
                    f"[VoiceLoop Error] "
                    f"{type(exc).__name__}: {exc}"
                )

                await self.voice.speak(
                    "Ek error aaya hai. "
                    "Main continue kar raha hoon."
                )

    # ============================================================
    # SYNCHRONOUS ENTRY POINT
    # ============================================================

    def start(self) -> None:
        """
        Synchronous entry point.
        """

        asyncio.run(self.run())