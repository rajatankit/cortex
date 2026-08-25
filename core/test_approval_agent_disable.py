import asyncio
import sys
from pathlib import Path

# Allow imports from CORTEX core/
CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL AGENT-DISABLE SECURITY TEST")
    print("=" * 60)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]
    registry = cortex["registry"]

    agent_id = "ARIA"
    tool_name = "create_tournament"

    original_context = {
        "tournament_name": "AGENT DISABLE TEST TOURNAMENT",
        "time": "22:00",
    }

    task = "Create agent-disable security test tournament"

    # --------------------------------------------------
    # TEST 1: VERIFY ARIA EXISTS AND IS ENABLED
    # --------------------------------------------------

    print("\nTEST 1: VERIFY ARIA IS ENABLED")

    agent = registry.get(agent_id)

    if agent is None:
        print("ARIA AGENT: FAIL")
        print("ARIA is not registered.")
        return

    print(f"ARIA enabled before approval: {agent.enabled}")

    if agent.enabled is not True:
        print("ARIA AGENT: FAIL")
        print("ARIA must start enabled.")
        return

    print("ARIA AGENT: PASS")

    # --------------------------------------------------
    # TEST 2: CREATE APPROVAL REQUEST
    # --------------------------------------------------

    print("\nTEST 2: CREATE APPROVAL REQUEST")

    request_result = await gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task=task,
        context=original_context,
    )

    print(request_result)

    request_id = None

    if isinstance(request_result.data, dict):
        request_id = request_result.data.get("request_id")

    if not request_id:
        print("APPROVAL REQUEST: FAIL")
        print("No request ID was returned.")
        return

    print(f"\nREQUEST ID:\n{request_id}")

    request = approval_gate.get(request_id)

    if request is None:
        print("APPROVAL REQUEST: FAIL")
        return

    print("\nORIGINAL APPROVAL REQUEST:")
    print(request)

    # --------------------------------------------------
    # TEST 3: APPROVE REQUEST
    # --------------------------------------------------

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.status.value != "approved":
        print("APPROVAL: FAIL")
        return

    print("APPROVAL: PASS")

    # --------------------------------------------------
    # TEST 4: DISABLE ARIA AFTER APPROVAL
    # --------------------------------------------------

    print("\nTEST 4: DISABLE ARIA AFTER APPROVAL")

    agent.enabled = False

    print(f"ARIA enabled after disable: {agent.enabled}")

    if agent.enabled is not False:
        print("AGENT DISABLE: FAIL")
        return

    print("AGENT DISABLE: PASS")

    # --------------------------------------------------
    # TEST 5: ATTEMPT EXECUTION AFTER AGENT DISABLE
    # --------------------------------------------------

    print("\nTEST 5: ATTEMPT EXECUTION AFTER AGENT DISABLE")

    execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context=original_context,
    )

    print(execution)

    if execution.success:
        print("POST-DISABLE BLOCK: FAIL")
        print("Disabled agent was allowed to execute.")
        return

    expected_message = f"Agent is disabled: {agent_id}"

    if execution.message != expected_message:
        print("POST-DISABLE BLOCK: FAIL")
        print(f"Expected: {expected_message}")
        print(f"Received: {execution.message}")
        return

    print("POST-DISABLE BLOCK: PASS")
    print("Execution was blocked because ARIA was disabled.")

    # --------------------------------------------------
    # TEST 6: VERIFY APPROVAL WAS NOT CONSUMED
    # --------------------------------------------------

    print("\nTEST 6: VERIFY APPROVAL WAS NOT CONSUMED")

    after_block = approval_gate.get(request_id)

    print(after_block)

    if after_block is None:
        print("APPROVAL STATE: FAIL")
        return

    if after_block.status.value != "approved":
        print("APPROVAL STATE: FAIL")
        print(
            "Failed execution changed the approval state to "
            f"{after_block.status.value}."
        )
        return

    print("APPROVAL REMAINS APPROVED: PASS")
    print("Failed execution did not consume the approval.")

    # --------------------------------------------------
    # TEST 7: RE-ENABLE ARIA
    # --------------------------------------------------

    print("\nTEST 7: RESTORE ARIA")

    agent.enabled = True

    print(f"ARIA enabled after restore: {agent.enabled}")

    if agent.enabled is not True:
        print("AGENT RESTORE: FAIL")
        return

    print("AGENT RESTORE: PASS")

    # --------------------------------------------------
    # TEST 8: EXECUTE AFTER RESTORATION
    # --------------------------------------------------

    print("\nTEST 8: EXECUTE APPROVED REQUEST AFTER RESTORATION")

    restored_execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context=original_context,
    )

    print(restored_execution)

    if not restored_execution.success:
        print("RESTORED EXECUTION: FAIL")
        print(restored_execution.message)
        return

    print("RESTORED EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 9: VERIFY FINAL APPROVAL STATE
    # --------------------------------------------------

    print("\nTEST 9: VERIFY FINAL APPROVAL STATE")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if final_request is None:
        print("FINAL STATE: FAIL")
        return

    if final_request.status.value != "executed":
        print("FINAL STATE: FAIL")
        print(
            "Expected executed status, got "
            f"{final_request.status.value}"
        )
        return

    print("APPROVAL STATE TRANSITION: PASS")

    # --------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------

    print("\nSECURITY VERIFICATION")
    print("-" * 60)

    print("AGENT DISABLE AFTER APPROVAL: PASS")
    print("Disabled ARIA could not execute the approved request.")
    print("Approval remained intact while execution was blocked.")
    print("Restored ARIA could execute the still-valid approval.")

    print("\n" + "=" * 60)
    print("APPROVAL AGENT-DISABLE SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




