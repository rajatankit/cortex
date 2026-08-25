import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL ACTION-BINDING SECURITY TEST")
    print("=" * 55)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    agent_id = "ARIA"
    approved_action = "create_tournament"
    attacker_action = "delete_tournament"

    context = {
        "tournament_name": "ACTION BINDING TEST TOURNAMENT",
        "time": "22:00",
    }

    print("\nTEST 1: REQUEST CREATE-TOURNAMENT ACTION")

    result = await gateway.execute(
        agent_id=agent_id,
        tool_name="create_tournament",
        task="Create action-binding test tournament",
        context=context,
    )

    print(result)

    request_id = result.data.get("request_id")

    if not request_id:
        print("TEST FAILED: No approval request ID returned.")
        return

    print("\nREQUEST ID:")
    print(request_id)

    print("\nTEST 2: VERIFY APPROVED ACTION")

    request = approval_gate.get(request_id)

    print(request)

    if request is None:
        print("ACTION BINDING: FAIL")
        print("Approval request was not found.")
        return

    if request.action != approved_action:
        print("ACTION BINDING: FAIL")
        print(
            f"Expected action: {approved_action}"
        )
        print(
            f"Actual action: {request.action}"
        )
        return

    print("ORIGINAL ACTION BINDING: PASS")

    print("\nTEST 3: APPROVE CREATE-TOURNAMENT ACTION")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.action != approved_action:
        print("ACTION BINDING: FAIL")
        return

    print("APPROVAL ACTION BINDING: PASS")

    print("\nTEST 4: ATTEMPT ACTION TAMPERING")

    print(f"Approved action: {approved_action}")
    print(f"Unauthorized action: {attacker_action}")

    try:
        # Simulate an attacker attempting to change
        # the action stored inside the approval.
        current = approval_gate.get(request_id)

        tampered = type(current)(
            request_id=current.request_id,
            agent_id=current.agent_id,
            action=attacker_action,
            task=current.task,
            status=current.status,
            created_at=current.created_at,
            tool_name=current.tool_name,
            context=current.context,
            expires_at=current.expires_at,
        )

        approval_gate._requests[request_id] = tampered

        print("ACTION TAMPERING ATTEMPT:")
        print(tampered)

    except Exception as exc:
        print("ACTION TAMPERING ATTEMPT FAILED:")
        print(exc)

    print("\nTEST 5: VERIFY ACTION-BINDING INTEGRITY")

    stored = approval_gate.get(request_id)

    print(stored)

    if stored is None:
        print("ACTION BINDING: FAIL")
        return

    if stored.action != approved_action:
        print("ACTION BINDING: FAIL")
        print(
            "Approved action was modified inside the approval request."
        )
        print(
            "The approval gate currently allows action tampering."
        )
        return

    print("ACTION BINDING: PASS")
    print("Approved action remained unchanged.")

    print("\nSECURITY VERIFICATION")
    print("-" * 55)

    print("APPROVAL ACTION-BINDING: PASS")

    print("\n" + "=" * 55)
    print("APPROVAL ACTION-BINDING SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




