import asyncio
import inspect

from core.voice_loop import VoiceLoop
from core.cortex_runtime import CortexRuntime


async def main():
    print("=" * 60)
    print("        CORTEX VOICE CONTROL TEST")
    print("=" * 60)

    print("[1/3] Creating CortexRuntime...")

    try:
        # Show constructor requirements so we don't silently
        # initialize the runtime incorrectly.
        sig = inspect.signature(CortexRuntime)
        print(f"[INFO] CortexRuntime signature: {sig}")

        runtime = CortexRuntime()

    except TypeError as exc:
        print()
        print("[ERROR] CortexRuntime needs initialization arguments.")
        print(f"[ERROR] {exc}")
        print()
        print("VoiceLoop itself is OK.")
        print("Runtime bootstrap must be connected using the existing")
        print("CORTEX bootstrap/initialization path.")
        return

    except Exception as exc:
        print()
        print(f"[ERROR] CortexRuntime initialization failed:")
        print(f"{type(exc).__name__}: {exc}")
        return

    print("[OK] CortexRuntime created.")
    print()

    print("[2/3] Creating VoiceLoop...")

    try:
        voice_loop = VoiceLoop(
            runtime=runtime,
            listen_duration=6.0,
        )
    except Exception as exc:
        print()
        print(f"[ERROR] VoiceLoop initialization failed:")
        print(f"{type(exc).__name__}: {exc}")
        return

    print("[OK] VoiceLoop created.")
    print()

    print("[3/3] Starting CORTEX voice control...")
    print()
    print("Speak a command such as:")
    print("  tournament check kar")
    print("  room check kar")
    print("  player dikhao")
    print("  wallet balance batao")
    print("  match check karo")
    print("  security scan karo")
    print()
    print("Say 'exit' / 'quit' / 'stop' to stop.")
    print()
    print("=" * 60)

    try:
        await voice_loop.run()
    except KeyboardInterrupt:
        print()
        print("[INFO] Voice control stopped by keyboard.")
    except Exception as exc:
        print()
        print(f"[ERROR] VoiceLoop runtime error:")
        print(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
