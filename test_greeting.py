import asyncio
from unittest.mock import AsyncMock

from core.voice_loop import VoiceLoop


class Runtime:
    def __init__(self):
        self.execute_intent = AsyncMock()


class Voice:
    def __init__(self):
        self.speak = AsyncMock()

    def listen(self, duration):
        return "hello"


async def main():
    voice = Voice()
    runtime = Runtime()

    loop = VoiceLoop(runtime, voice)

    await loop.process_once()

    print("SPEAK:", voice.speak.call_args)
    print("RUNTIME CALLED:", runtime.execute_intent.called)


asyncio.run(main())