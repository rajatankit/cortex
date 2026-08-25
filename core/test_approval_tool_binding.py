import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL TOOL-BINDING SECURITY TEST")
    print("=" * 50)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    agent_id = "ARIA"
    approved_tool = "create_tournament"
    unauthorized_tool = "delete_tournament"

    approved_context = {
        "tournament_name": "TOOL BINDING TEST TOURNAMENT",
        "time": "22:00",
    }

    print("\nTEST 1: REQUEST ARIA CREATE-TOURNAMENT TOOL")

    result = await gateway.execute(
        agent_id=agent_id,
        tool_name=approved_tool,
        task="Create tool-binding test tournament",
        context=approved_context,
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

    print("\nTEST 2: VERIFY APPROVAL TOOL")

    request = approval_gate.get(request_id)

    if request is None:
        print("TEST FAILED: Approval request not found.")
        return

    print(request)

    if request.tool_name != approved_tool:
        print("ORIGINAL TOOL BINDING: FAIL")
        return

    print("ORIGINAL TOOL BINDING: PASS")

    print("\nTEST 3: APPROVE CREATE-TOURNAMENT REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.tool_name != approved_tool:
        print("APPROVAL TOOL BINDING: FAIL")
        return

    print("APPROVAL TOOL BINDING: PASS")

    print("\nTEST 4: VERIFY GATEWAY DOES NOT ACCEPT TOOL OVERRIDE")

    # The current approve_and_execute API intentionally does NOT
    # accept a caller-supplied tool_name.
    #
    # This is important: an attacker cannot simply say:
    #
    #   tool_name="delete_tournament"
    #
    # while using an approval for:
    #
    #   create_tournament
    #
    # because the gateway resolves the tool from the approved
    # authorization itself.

    try:
        await gateway.approve_and_execute(
            agent_id=agent_id,
            request_id=request_id,
            context=approved_context,
            tool_name=unauthorized_tool,
        )

        print("TOOL OVERRIDE: FAIL")
        print(
            "Gateway unexpectedly accepted a caller-supplied "
            "tool override."
        )

        return

    except TypeError as exc:
        print("TOOL OVERRIDE BLOCK: PASS")
        print(
            "Gateway rejected the unauthorized tool override."
        )
        print(f"Python API rejection: {exc}")

    print("\nTEST 5: VERIFY APPROVAL REMAINS APPROVED")

    current = approval_gate.get(request_id)

    print(current)

    if current is None:
        print("STATE VERIFICATION: FAIL")
        return

    if current.status.value != "approved":
        print("STATE VERIFICATION: FAIL")
        print(
            "Unauthorized tool override changed approval state."
        )
        return

    print("APPROVAL REMAINS APPROVED: PASS")

    print("\nTEST 6: EXECUTE ORIGINAL APPROVED TOOL")

    execution = await gateway.approve_and_execute(
        agent_id=agent_id,
        request_id=request_id,
        context=approved_context,
    )

    print(execution)

    if not execution.success:
        print("ORIGINAL EXECUTION: FAIL")
        return

    if execution.tool_name != approved_tool:
        print("ORIGINAL EXECUTION: FAIL")
        print(
            f"Expected: {approved_tool}"
        )
        print(
            f"Executed: {execution.tool_name}"
        )
        return

    print("ORIGINAL TOOL EXECUTION: PASS")

    print("\nTEST 7: VERIFY FINAL APPROVAL STATE")

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

    security_pass = (
        request.tool_name == approved_tool
        and approved.tool_name == approved_tool
        and current.status.value == "approved"
        and execution.success
        and execution.tool_name == approved_tool
        and final_request is not None
        and final_request.status.value == "executed"
    )

    if security_pass:
        print("APPROVAL TOOL-BINDING: PASS")
        print(
            "Unauthorized tool override was rejected and "
            "execution remained bound to the approved tool."
        )
    else:
        print("APPROVAL TOOL-BINDING: FAIL")

    print("\n" + "=" * 50)
    print("APPROVAL TOOL-BINDING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




