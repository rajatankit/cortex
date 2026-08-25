import asyncio
from core.cortex_bootstrap import build_cortex


async def main():
    print("CORTEX APPROVAL PERMISSION-REVOCATION SECURITY TEST")
    print("=" * 60)

    cortex = build_cortex()

    gateway = cortex["tool_gateway"]
    approval_gate = cortex["approval_gate"]
    permissions = cortex["permissions"]

    agent_id = "ARIA"
    tool_name = "create_tournament"
    action = "create_tournament"

    context = {
        "tournament_name": "PERMISSION REVOCATION TEST TOURNAMENT",
        "time": "22:00",
    }

    print("\nTEST 1: CREATE HIGH-RISK APPROVAL REQUEST")

    result = await gateway.execute(
        agent_id=agent_id,
        tool_name=tool_name,
        task="Create permission-revocation test tournament",
        context=context,
    )

    print(result)

    request_id = None

    if result.data:
        request_id = result.data.get("request_id")

    if not request_id:
        print("TEST FAILED: No approval request ID returned.")
        return

    print("\nREQUEST ID:")
    print(request_id)

    request = approval_gate.get(request_id)

    if request is None:
        print("TEST FAILED: Approval request not found.")
        return

    print("\nORIGINAL APPROVAL REQUEST:")
    print(request)

    print("\nTEST 2: VERIFY PERMISSION EXISTS")

    permission_before = permissions.is_allowed(
        agent_id,
        action,
    )

    print(f"Permission before revocation: {permission_before}")

    if permission_before:
        print("ORIGINAL PERMISSION: PASS")
    else:
        print("ORIGINAL PERMISSION: FAIL")
        print(
            "ARIA does not currently have the required "
            "permission for this test."
        )
        return

    print("\nTEST 3: APPROVE REQUEST")

    approved = approval_gate.approve(request_id)

    print(approved)

    if approved.status.value == "approved":
        print("APPROVAL: PASS")
    else:
        print("APPROVAL: FAIL")
        return

    print("\nTEST 4: REVOKE PERMISSION AFTER APPROVAL")

    permission_removed = False

    try:
        if hasattr(permissions, "revoke"):
            permissions.revoke(
                agent_id,
                action,
            )
            permission_removed = True

        elif hasattr(permissions, "remove_permission"):
            permissions.remove_permission(
                agent_id,
                action,
            )
            permission_removed = True

        elif hasattr(permissions, "deny"):
            permissions.deny(
                agent_id,
                action,
            )
            permission_removed = True

    except Exception as exc:
        print(f"Permission revocation error: {exc}")

    if not permission_removed:
        print(
            "PERMISSION REVOCATION: FAIL"
        )
        print(
            "No supported permission-revocation method "
            "was found in PermissionEngine."
        )
        return

    permission_after = permissions.is_allowed(
        agent_id,
        action,
    )

    print(f"Permission after revocation: {permission_after}")

    if not permission_after:
        print("PERMISSION REVOCATION: PASS")
    else:
        print("PERMISSION REVOCATION: FAIL")
        print(
            "Permission is still active after revocation."
        )
        return

    print("\nTEST 5: ATTEMPT EXECUTION AFTER REVOCATION")

    execution = await gateway.approve_and_execute(
        request_id=request_id,
        agent_id=agent_id,
        context=context,
    )

    print(execution)

    if not execution.success:
        print("POST-REVOCATION BLOCK: PASS")
        print(
            "Execution was blocked because permission "
            "was removed after approval."
        )
    else:
        print("POST-REVOCATION BLOCK: FAIL")
        print(
            "CORTEX executed an approved action even though "
            "the permission had been revoked."
        )

    print("\nTEST 6: VERIFY APPROVAL WAS NOT CONSUMED")

    final_request = approval_gate.get(request_id)

    print(final_request)

    if final_request is None:
        print("APPROVAL STATE: FAIL")
        return

    if final_request.status.value == "approved":
        print("APPROVAL REMAINS APPROVED: PASS")
        print(
            "Failed execution did not consume the approval."
        )
    else:
        print(
            "APPROVAL REMAINS APPROVED: FAIL"
        )
        print(
            f"Current approval state: "
            f"{final_request.status.value}"
        )

    print("\nTEST 7: VERIFY NO TOURNAMENT WAS CREATED")

    created_tournament = None

    if execution.data:
        data = execution.data

        if isinstance(data, dict):
            created_tournament = data.get("tournament")

    if execution.success and created_tournament is not None:
        print("UNAUTHORIZED CREATION: FAIL")
        print(
            "A tournament was created despite permission revocation."
        )
    else:
        print("UNAUTHORIZED CREATION BLOCK: PASS")
        print(
            "No tournament was created after permission revocation."
        )

    print("\nSECURITY VERIFICATION")
    print("-" * 60)

    permission_pass = not permission_after
    execution_block_pass = not execution.success
    approval_state_pass = (
        final_request.status.value == "approved"
    )
    no_creation_pass = (
        not execution.success
        and created_tournament is None
    )

    if (
        permission_pass
        and execution_block_pass
        and approval_state_pass
        and no_creation_pass
    ):
        print("APPROVAL PERMISSION-REVOCATION: PASS")
        print(
            "Permission revoked after approval prevented "
            "execution and preserved the approval state."
        )
    else:
        print("APPROVAL PERMISSION-REVOCATION: FAIL")

    print("\n" + "=" * 60)
    print(
        "APPROVAL PERMISSION-REVOCATION SECURITY TEST COMPLETE"
    )


if __name__ == "__main__":
    asyncio.run(main())




