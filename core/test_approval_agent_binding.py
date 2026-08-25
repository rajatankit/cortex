import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL AGENT-BINDING SECURITY TEST")
    print("=" * 50)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    original_agent = "ARIA"
    attacker_agent = "NOVA"
    tool_name = "create_tournament"

    original_context = {
        "tournament_name": "AGENT BINDING TEST TOURNAMENT",
        "time": "22:00",
    }

    print("\nTEST 1: REQUEST ARIA HIGH-RISK TOOL")

    result = await gateway.execute(
        agent_id=original_agent,
        tool_name=tool_name,
        task="Create agent-binding test tournament",
        context=original_context,
    )

    print(result)

    if not result.data:
        print("TEST FAILED: No result data returned.")
        return

    request_id = result.data.get("request_id")

    if not request_id:
        print("TEST FAILED: No approval request ID returned.")
        return

    print("\nREQUEST ID:")
    print(request_id)

    print("\nTEST 2: APPROVE ARIA REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.agent_id != original_agent:
        print("TEST FAILED: Approval agent mismatch.")
        return

    print("ORIGINAL AGENT BINDING: PASS")

    print("\nTEST 3: ATTEMPT EXECUTION AS NOVA")

    tampered_context = {
        "tournament_name": "NOVA UNAUTHORIZED TOURNAMENT",
        "time": "23:59",
    }

    execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=attacker_agent,
        context=tampered_context,
    )

    print(execution)

    print("\nTEST 4: VERIFY NOVA WAS BLOCKED")

    if execution.success:
        print("AGENT BINDING: FAIL")
        print(
            "NOVA executed an approval belonging to ARIA."
        )
    else:
        print("AGENT BINDING BLOCK: PASS")
        print(
            "NOVA was correctly blocked from using "
            "ARIA's approval."
        )

    print("\nTEST 5: VERIFY APPROVAL WAS NOT CONSUMED")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if final_request is None:
        print("STATE VERIFICATION: FAIL")
        return

    if final_request.status.value == "approved":
        print("APPROVAL REMAINS APPROVED: PASS")
    else:
        print(
            "APPROVAL STATE: "
            f"{final_request.status.value}"
        )

    print("\nTEST 6: ORIGINAL ARIA EXECUTION")

    original_execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=original_agent,
        context=original_context,
    )

    print(original_execution)

    if original_execution.success:
        print("ORIGINAL AGENT EXECUTION: PASS")
    else:
        print("ORIGINAL AGENT EXECUTION: FAIL")

    print("\nTEST 7: FINAL APPROVAL STATUS")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if (
        final_request is not None
        and final_request.status.value == "executed"
    ):
        print("APPROVAL STATE TRANSITION: PASS")
    else:
        print("APPROVAL STATE TRANSITION: FAIL")

    print("\nSECURITY VERIFICATION")
    print("-" * 50)

    if (
        not execution.success
        and final_request is not None
        and final_request.status.value == "executed"
        and original_execution.success
    ):
        print("APPROVAL AGENT-BINDING: PASS")
        print(
            "NOVA was blocked and ARIA successfully "
            "executed its own approved request."
        )
    else:
        print("APPROVAL AGENT-BINDING: FAIL")

    print("\n" + "=" * 50)
    print("APPROVAL AGENT-BINDING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




