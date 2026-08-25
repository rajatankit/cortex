import asyncio
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from core.cortex_bootstrap import build_cortex
from core.approval_gate import ApprovalStatus


async def main():
    print("CORTEX APPROVAL EXPIRATION SECURITY TEST")
    print("=" * 50)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]

    print("\nTEST 1: REQUEST HIGH-RISK TOOL")

    result = await gateway.execute(
        agent_id="ARIA",
        tool_name="create_tournament",
        task="Create expiration-test tournament",
        context={
            "tournament_name": "EXPIRATION TEST TOURNAMENT",
            "time": "22:30",
        },
    )

    print(result)

    request_id = result.data["request_id"]

    print("\nREQUEST ID:")
    print(request_id)

    request = approval_gate.get(request_id)

    if request is None:
        print("EXPIRATION TEST: FAIL")
        print("Approval request was not created.")
        return

    print("\nTEST 2: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.status != ApprovalStatus.APPROVED:
        print("APPROVAL: FAIL")
        return

    print("APPROVAL: PASS")

    print("\nTEST 3: FORCE APPROVAL TO EXPIRE")

    expired_time = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()

    expired_request = replace(
        approved,
        expires_at=expired_time,
    )

    approval_gate._requests[request_id] = expired_request

    print("Original expiry:", approved.expires_at)
    print("Forced expiry:", expired_request.expires_at)

    print("\nTEST 4: VERIFY EXPIRATION")

    current_request = approval_gate.get(request_id)

    now = datetime.now(timezone.utc)

    expires_at = datetime.fromisoformat(
        current_request.expires_at
    )

    is_expired = now >= expires_at

    print("Current time:", now.isoformat())
    print("Expires at:", current_request.expires_at)
    print("Expired:", is_expired)

    if is_expired:
        print("EXPIRATION DETECTION: PASS")
    else:
        print("EXPIRATION DETECTION: FAIL")
        return

    print("\nTEST 5: EXECUTION AFTER EXPIRATION")

    execution = await gateway.approve_and_execute(
        request_id=request_id,
        context={
            "tournament_name": "SHOULD NOT EXECUTE",
            "time": "23:59",
        },
    )

    print(execution)

    if not execution.success:
        print("POST-EXPIRATION BLOCK: PASS")
        print("Expired approval cannot be executed.")
    else:
        print("POST-EXPIRATION BLOCK: FAIL")
        print("SECURITY FAILURE: Expired approval was executed.")

    print("\nTEST 6: FINAL APPROVAL STATUS")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if final_request.status == ApprovalStatus.EXPIRED:
        print("EXPIRATION STATE: PASS")
    else:
        print(
            "EXPIRATION STATE: FAIL"
            f" | Current status: {final_request.status.value}"
        )

    print("\nSECURITY VERIFICATION")

    expiration_pass = (
        final_request.status == ApprovalStatus.EXPIRED
    )

    execution_blocked = not execution.success

    if expiration_pass:
        print("APPROVAL EXPIRATION: PASS")
    else:
        print("APPROVAL EXPIRATION: FAIL")

    if execution_blocked:
        print("EXPIRED EXECUTION BLOCK: PASS")
    else:
        print("EXPIRED EXECUTION BLOCK: FAIL")

    if expiration_pass and execution_blocked:
        print("\nAPPROVAL EXPIRATION SECURITY: PASS")
        print(
            "Expired approval was detected and could not be executed."
        )
    else:
        print("\nAPPROVAL EXPIRATION SECURITY: FAIL")

    print("\n" + "=" * 50)
    print("APPROVAL EXPIRATION SECURITY TEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())




