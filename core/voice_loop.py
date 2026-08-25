from __future__ import annotations

import asyncio
from typing import Optional

from core.voice_interface import VoiceInterface
from core.cortex_runtime import CortexRuntime


class VoiceLoop:
    """
    Continuous Voice Control Loop for CORTEX.

    Flow:
        Listen → STT → runtime.execute_intent() → TTS → Repeat

    Security pipeline is fully respected.
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

    @staticmethod
    def normalize_hinglish(text: str) -> str:
        """
        Convert common Hindi/Hinglish voice commands into clear
        English commands that IntentEngine already understands.

        This only normalizes the user request. It does NOT bypass
        IntentEngine, permissions, DecisionEngine, ApprovalGate,
        ToolGateway, or any other security layer.
        """
        original = text.strip()
        lower = " ".join(original.lower().split())

        # ============================================
        # SPECIALIST SWITCHING
        # ============================================
        if any(p in lower for p in [
            "aria se baat", "aria ko bula", "aria se baat karwa",
            "aria se baat karwao", "aria ko call kar", "talk to aria"
        ]):
            return "Talk to ARIA"

        if any(p in lower for p in [
            "elara se baat", "elara ko bula", "elara se baat karwa",
            "elara se baat karwao", "talk to elara"
        ]):
            return "Talk to ELARA"

        if any(p in lower for p in [
            "lyra se baat", "lyra ko bula", "lyra se baat karwa",
            "talk to lyra"
        ]):
            return "Talk to LYRA"

        if any(p in lower for p in [
            "vault se baat", "vault ko bula", "vault se baat karwa",
            "talk to vault"
        ]):
            return "Talk to VAULT"

        if any(p in lower for p in [
            "orion se baat", "orion ko bula", "orion se baat karwa",
            "talk to orion"
        ]):
            return "Talk to ORION"

        if any(p in lower for p in [
            "nova se baat", "nova ko bula", "nova se baat karwa",
            "nova se baat karwao", "talk to nova"
        ]):
            return "Talk to NOVA"

        if any(p in lower for p in [
            "atlas se baat", "atlas ko bula", "atlas se baat karwa",
            "talk to atlas"
        ]):
            return "Talk to ATLAS"

        if any(p in lower for p in [
            "sentinel se baat", "sentinel ko bula", "sentinel se baat karwa",
            "talk to sentinel"
        ]):
            return "Talk to SENTINEL"

        # ============================================
        # TOURNAMENT COMMANDS
        # ============================================
        if any(p in lower for p in [
            "tournament check kar", "tournament check karo",
            "tournament ka status", "tournament status bata",
            "tournament dikha", "tournament dikhao",
            "tournament dekh", "tournament dekho",
            "tournament ki details", "tournament check karke bata"
        ]):
            return "Check Tournament"

        if any(p in lower for p in [
            "tournament live kar", "tournament live karo",
            "tournament live krde", "tournament live kr do",
            "tournament start kar", "tournament start karo"
        ]):
            return "Start Tournament"

        # ============================================
        # SYSTEM COMMANDS
        # ============================================
        if any(p in lower for p in [
            "system status", "status bata", "health check",
            "system kaisa hai", "cortex status"
        ]):
            return "System Status"

        return original

    async def process_once(self) -> None:
        """
        One complete cycle: Listen → Process → Speak
        """
        # 1. Listen
        user_text = self.voice.listen(duration=self.listen_duration)

        if not user_text:
            await self.voice.speak(
                "Sunai nahi diya bhai. Ek baar phir se bolna."
            )
            return

        # Normalize common Hindi/Hinglish commands
        user_text = self.normalize_hinglish(user_text)

        # Conversational greetings
        greetings = {
            "hello",
            "hi",
            "hey",
            "hello cortex",
            "hi cortex",
            "hey cortex",
            "namaste",
            "namaste cortex",
            "kaise ho",
            "kya haal hai",
            "kya haal",
        }

        if user_text.lower().strip() in greetings:
            await self.voice.speak(
                "Haan bhai, CORTEX online hai. Batao kya karna hai?"
            )
            return

        # Exit commands
        exit_commands = {
            "exit",
            "quit",
            "stop",
            "bye",
            "goodbye",
            "band kar",
            "band karo",
            "chup ho ja",
            "so ja",
        }

        if user_text.lower().strip() in exit_commands:
            await self.voice.speak(
                "Theek hai bhai. Voice control band kar raha hoon. Baad mein milte hain."
            )
            self._running = False
            return

        # 2. Send to CORTEX (secure pipeline)
        try:
            result = await self.runtime.execute_intent(request=user_text)
        except Exception as exc:
            await self.voice.speak(
                f"Kuch problem aa gayi bhai. {str(exc)[:80]}"
            )
            return

        # 3. Speak the response (human style)
        response_text = result.message or "Ho gaya bhai."

        # Clean long responses for voice
        if len(response_text) > 280:
            response_text = (
                response_text[:260]
                + "... baaki details chahiye toh bol dena."
            )

        await self.voice.speak(response_text)

    async def run(self) -> None:
        """
        Start continuous voice loop.
        """
        self._running = True

        await self.voice.speak(
            "CORTEX voice control online hai. Boliye, kya karna hai?"
        )

        while self._running:
            try:
                await self.process_once()
            except KeyboardInterrupt:
                await self.voice.speak("Voice control band kiya.")
                break
            except Exception as exc:
                print(f"[VoiceLoop Error] {exc}")
                await self.voice.speak(
                    "Thoda error aaya, lekin main continue kar raha hoon."
                )

    def start(self) -> None:
        """
        Synchronous entry point.
        """
        asyncio.run(self.run())