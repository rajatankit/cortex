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

    async def process_once(self) -> None:
        """
        One complete cycle: Listen → Process → Speak
        """
        # 1. Listen
        user_text = self.voice.listen(duration=self.listen_duration)

        if not user_text:
            await self.voice.speak("I didn't catch that. Please try again.")
            return

        # Exit commands
        if user_text.lower() in {"exit", "quit", "stop", "bye", "goodbye"}:
            await self.voice.speak("Shutting down voice control. Goodbye.")
            self._running = False
            return

        # 2. Send to CORTEX (secure pipeline)
        try:
            result = await self.runtime.execute_intent(request=user_text)
        except Exception as exc:
            await self.voice.speak(f"Sorry, something went wrong. {str(exc)[:100]}")
            return

        # 3. Speak the response
        response_text = result.message or "Done."

        # Make response a bit cleaner for voice
        if len(response_text) > 300:
            response_text = response_text[:280] + "... I have more details if needed."

        await self.voice.speak(response_text)

    async def run(self) -> None:
        """
        Start continuous voice loop.
        """
        self._running = True

        await self.voice.speak("CORTEX voice control online. How can I help you?")

        while self._running:
            try:
                await self.process_once()
            except KeyboardInterrupt:
                await self.voice.speak("Voice control stopped.")
                break
            except Exception as exc:
                print(f"[VoiceLoop Error] {exc}")
                await self.voice.speak("An error occurred. Continuing.")

    def start(self) -> None:
        """
        Synchronous entry point.
        """
        asyncio.run(self.run())