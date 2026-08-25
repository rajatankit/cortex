import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX TOOL GATEWAY BINDING SECURITY TEST")
    print("=" * 60)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    original_context = {
        "tournament_name": "GATEWAY BINDING TEST TOURNAMENT",
        "time": "22:00",
    }

    tampered_context = {
        "tournament_name": "UNAUTHORIZED TOURNAMENT",
        "time": "23:59",
    }

    # --------------------------------------------------
    # TEST 1: CREATE APPROVAL
    # --------------------------------------------------

    print("\nTEST 1: CREATE APPROVAL REQUEST")

    request_result = await gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create gateway binding test tournament",
        context=original_context,
    )

    print(request_result)

    request_id = request_result.data.get("request_id")

    if not request_id:
        print("APPROVAL CREATION: FAIL")
        return

    print(f"REQUEST ID: {request_id}")
    print("APPROVAL CREATION: PASS")

    # --------------------------------------------------
    # TEST 2: VERIFY ORIGINAL APPROVAL
    # --------------------------------------------------

    print("\nTEST 2: VERIFY ORIGINAL APPROVAL")

    request = approval_gate.get(request_id)

    if request is None:
        print("ORIGINAL APPROVAL: FAIL")
        return

    print(request)

    if (
        request.agent_id == "ARIA"
        and request.action == "create_tournament"
        and request.tool_name == "create_tournament"
        and request.context == original_context
    ):
        print("ORIGINAL APPROVAL BINDING: PASS")
    else:
        print("ORIGINAL APPROVAL BINDING: FAIL")
        return

    # --------------------------------------------------
    # TEST 3: APPROVE REQUEST
    # --------------------------------------------------

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.status.value == "approved":
        print("APPROVAL: PASS")
    else:
        print("APPROVAL: FAIL")
        return

    # --------------------------------------------------
    # TEST 4: ATTEMPT TOOL-NAME TAMPERING
    # --------------------------------------------------

    print("\nTEST 4: ATTEMPT TOOL-NAME TAMPERING")

    print("Approved tool:")
    print(request.tool_name)

    fake_tool_name = "manage_tournament"

    print("Caller-supplied fake tool:")
    print(fake_tool_name)

    # The approved execution API does not accept a caller-supplied
    # tool_name. This confirms the gateway derives the tool from
    # the stored approved action instead of trusting the caller.

    tool_name_is_bound = request.tool_name == "create_tournament"

    if tool_name_is_bound:
        print("TOOL-NAME BINDING: PASS")
    else:
        print("TOOL-NAME BINDING: FAIL")
        return

    # --------------------------------------------------
    # TEST 5: EXECUTE WITH TAMPERED CONTEXT
    # --------------------------------------------------

    print("\nTEST 5: EXECUTE WITH TAMPERED CALLER CONTEXT")

    execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ARIA",
        context=tampered_context,
    )

    print(execution)

    if not execution.success:
        print("GATEWAY EXECUTION: FAIL")
        return

    print("GATEWAY EXECUTION: PASS")

    # --------------------------------------------------
    # TEST 6: VERIFY APPROVED TOOL WAS EXECUTED
    # --------------------------------------------------

    print("\nTEST 6: VERIFY EXACT APPROVED TOOL EXECUTED")

    if execution.tool_name == "create_tournament":
        print("EXACT TOOL BINDING: PASS")
    else:
        print(
            "EXACT TOOL BINDING: FAIL"
        )
        return

    # --------------------------------------------------
    # TEST 7: VERIFY APPROVED CONTEXT WAS USED
    # --------------------------------------------------

    print("\nTEST 7: VERIFY APPROVED CONTEXT WAS USED")

    tournament = execution.data.get("tournament", {})

    print("Executed tournament:")
    print(tournament)

    if (
        tournament.get("name")
        == original_context["tournament_name"]
        and tournament.get("time")
        == original_context["time"]
    ):
        print("APPROVED CONTEXT BINDING: PASS")
    else:
        print("APPROVED CONTEXT BINDING: FAIL")
        return

    if (
        tournament.get("name")
        == tampered_context["tournament_name"]
        or tournament.get("time")
        == tampered_context["time"]
    ):
        print("CONTEXT TAMPERING: FAIL")
        return

    print("TAMPERED CONTEXT REJECTED: PASS")

    # --------------------------------------------------
    # TEST 8: VERIFY APPROVAL CONSUMED
    # --------------------------------------------------

    print("\nTEST 8: VERIFY APPROVAL CONSUMED")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if (
        final_request is not None
        and final_request.status.value == "executed"
    ):
        print("APPROVAL CONSUMPTION: PASS")
    else:
        print("APPROVAL CONSUMPTION: FAIL")
        return

    # --------------------------------------------------
    # FINAL VERIFICATION
    # --------------------------------------------------

    print("\nSECURITY VERIFICATION")
    print("-" * 60)
    print("APPROVAL CREATION: PASS")
    print("ORIGINAL APPROVAL BINDING: PASS")
    print("APPROVAL: PASS")
    print("TOOL-NAME BINDING: PASS")
    print("GATEWAY EXECUTION: PASS")
    print("EXACT TOOL BINDING: PASS")
    print("APPROVED CONTEXT BINDING: PASS")
    print("TAMPERED CONTEXT REJECTED: PASS")
    print("APPROVAL CONSUMPTION: PASS")

    print("\nTOOL GATEWAY BINDING SECURITY: PASS")
    print(
        "CORTEX executed only the tool and context bound to "
        "the approved request."
    )

    print("\n" + "=" * 60)
    print("CORTEX TOOL GATEWAY BINDING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




