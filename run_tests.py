import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CORE = ROOT / "core"

test_files = sorted(CORE.glob("test_*.py"))

print("=" * 70)
print("CORTEX FULL REGRESSION TEST RUNNER")
print("=" * 70)
print(f"TEST FILES FOUND: {len(test_files)}")
print()

passed = []
failed = []
skipped = []

for test_file in test_files:
    print("\n" + "-" * 70)
    print(f"RUNNING: {test_file.name}")
    print("-" * 70)

    result = subprocess.run(
        [sys.executable, str(test_file)],
        cwd=str(CORE),
    )

    if result.returncode == 0:
        passed.append(test_file.name)
        print(f"\n[PASS] {test_file.name}")
    else:
        failed.append(test_file.name)
        print(f"\n[FAIL] {test_file.name}")

print("\n" + "=" * 70)
print("CORTEX REGRESSION SUMMARY")
print("=" * 70)

print(f"TOTAL : {len(test_files)}")
print(f"PASS  : {len(passed)}")
print(f"FAIL  : {len(failed)}")

if skipped:
    print(f"SKIP  : {len(skipped)}")

print("\nPASSED TESTS:")
for name in passed:
    print(f"  [PASS] {name}")

if failed:
    print("\nFAILED TESTS:")
    for name in failed:
        print(f"  [FAIL] {name}")

print("\n" + "=" * 70)

if failed:
    print("CORTEX REGRESSION: FAIL")
    print("Fix the failed tests before adding new features.")
    sys.exit(1)
else:
    print("CORTEX REGRESSION: ALL PASS")
    print("Security foundation is stable.")
    sys.exit(0)
