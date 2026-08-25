from core.cortex_bootstrap import bootstrap_cortex
from core.voice_loop import VoiceLoop

def main():
    print("=" * 60)
    print("CORTEX VOICE CONTROL")
    print("=" * 60)

    print("[1/2] Bootstrapping CORTEX...")
    cortex = bootstrap_cortex()
    print("[OK] CORTEX online.")

    print("[2/2] Starting voice control...")
    voice_loop = VoiceLoop(runtime=cortex)

    try:
        voice_loop.start()
    except KeyboardInterrupt:
        print("\n[CORTEX] Voice control stopped.")
    except Exception as exc:
        print(f"\n[CORTEX] Fatal error: {exc}")

if __name__ == "__main__":
    main()
