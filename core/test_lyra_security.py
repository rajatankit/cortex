"""
core/test_lyra_security.py

Adversarial security test suite for LYRA (send_notification).

NO PRODUCTION FILE IS MODIFIED BY THIS TEST. Every check below either
calls a real public method on the existing architecture, or - where
explicitly noted - reaches into a private store ONLY to simulate an
external condition (time passing, a tampered record) that the
production code is then asked to detect/handle on its own. This test
never weakens, patches around, or fakes a security decision.

------------------------------------------------------------------
ARCHITECTURAL FINDINGS
------------------------------------------------------------------

UPDATE: an earlier version of this test assumed no Tool was
registered for "send_notification" (based on a repository snapshot
that only showed register_tournament_tools() and
register_player_tools() being called). Running this suite against
the real repository showed that assumption was outdated - a real
"send_notification" tool IS registered and executes successfully
end-to-end, returning {"status": "sent", "notification": {...}}.
Every test below reflects that reality; nothing here fakes or
assumes success/failure that wasn't actually observed.

One finding DOES still hold, and is verified directly by TEST 8
rather than assumed: ToolGateway.approve_and_execute() never calls
AuditLogger on any of its own rejection branches (agent mismatch,
expired, wrong status, disabled/unknown agent, permission revoked) -
only AgentController-driven paths (like a normal execute_intent()
call) generate audit events. This is a real gap in today's audit
coverage, not a test bug - flagged, not silently worked around.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from core.cortex_bootstrap import bootstrap_cortex
from core.approval_gate import ApprovalRequest, ApprovalStatus


# ============================================================
# TEST RESULT TRACKING
# ============================================================

_RESULTS: list[tuple[str, str]] = []  # (test_name, "PASS" | "FAIL" | "SKIPPED")


def _record(name: str, status: str) -> None:
    _RESULTS.append((name, status))
    print(f"{name}: {status}")


def _fresh_runtime():
    """
    Every test gets its own fully bootstrapped CORTEX runtime, so
    that one test's tampering (revoked permission, disabled agent,
    expired/executed approval) can never leak into another test.
    """
    return bootstrap_cortex()


# ============================================================
# TEST 1 - WRONG AGENT APPROVAL EXECUTION
# ============================================================

async def test_1_wrong_agent_execution():
    print("\nTEST 1: WRONG AGENT APPROVAL EXECUTION")

    runtime = _fresh_runtime()

    request = runtime.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1 about tournament start",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Original approved message"},
    )

    runtime.approval_gate.approve(request.request_id)

    # A different, real, enabled agent attempts to execute LYRA's
    # approval.
    result = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="ELARA",
    )

    print(result)

    assert result.success is False, "Wrong-agent execution must fail."
    assert "does not match" in result.message.lower(), (
        "Failure must be due to agent binding mismatch, not something else."
    )

    stored = runtime.approval_gate.get(request.request_id)
    assert stored.status == ApprovalStatus.APPROVED, (
        "Approval must remain APPROVED, not EXECUTED, after a "
        "rejected wrong-agent attempt."
    )

    _record("TEST 1 (WRONG AGENT EXECUTION)", "PASS")


# ============================================================
# TEST 2 - CONTEXT TAMPERING
# ============================================================

async def test_2_context_tampering():
    print("\nTEST 2: CONTEXT TAMPERING")
    print(
        "send_notification is a real, working tool. This test proves "
        "the full end-to-end security property: even though a "
        "tampered context (P2 / 'Tampered message') is supplied to "
        "approve_and_execute(), the notification actually sent uses "
        "ONLY the original approved context (P1 / 'Original approved "
        "message'). The tampered values must never appear anywhere "
        "in the result."
    )

    runtime = _fresh_runtime()

    original_context = {
        "player_id": "nh5RRoYNmZab5AzblUxq7NipjBi1",
        "message": "Original approved message",
    }

    request = runtime.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context=dict(original_context),
    )

    runtime.approval_gate.approve(request.request_id)

    tampered_context = {"player_id": "P2", "message": "Tampered message"}

    result = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="LYRA",
        context=tampered_context,
    )

    print(result)

    assert result.success is True, "Legitimate approved execution must succeed."
    assert result.tool_name == "send_notification"

    result_data = result.data or {}
    assert result_data.get("status") == "sent"

    notification = result_data.get("notification", {})
    assert notification.get("userId") == "nh5RRoYNmZab5AzblUxq7NipjBi1", (
        "Notification must use the ORIGINAL approved player_id."
    )
    assert notification.get("message") == "Original approved message", (
        "Notification must use the ORIGINAL approved message."
    )

    payload_str = str(result_data)
    assert "P2" not in payload_str, "Tampered player_id must never appear."
    assert "Tampered message" not in payload_str, (
        "Tampered message must never appear."
    )

    stored = runtime.approval_gate.get(request.request_id)
    assert stored.status == ApprovalStatus.EXECUTED
    assert stored.context == original_context, (
        "Approval's stored context must never be mutated by the "
        "tampered execution attempt."
    )

    _record("TEST 2 (CONTEXT TAMPERING)", "PASS")


# ============================================================
# TEST 3 - EXPIRED APPROVAL
# ============================================================

async def test_3_expired_approval():
    print("\nTEST 3: EXPIRED APPROVAL")
    print(
        "Approval is created and approved normally (full 300s TTL), "
        "then its stored expires_at is rewritten to a past timestamp "
        "to deterministically simulate time passing - no sleep, and "
        "the production ApprovalGate/ToolGateway code makes every "
        "actual decision."
    )

    runtime = _fresh_runtime()

    request = runtime.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Hello"},
    )

    approved = runtime.approval_gate.approve(request.request_id)
    assert approved.status == ApprovalStatus.APPROVED

    # Simulate time passing: rewrite the stored expiry into the past,
    # in BOTH the active and trusted stores (so this isn't detected
    # as "tampering" and reverted by _restore_if_tampered - we are
    # simulating the clock, not an attacker).
    past_expiry = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()

    expired_record = ApprovalRequest(
        request_id=approved.request_id,
        agent_id=approved.agent_id,
        action=approved.action,
        task=approved.task,
        status=approved.status,
        created_at=approved.created_at,
        tool_name=approved.tool_name,
        context=dict(approved.context or {}),
        expires_at=past_expiry,
    )

    runtime.approval_gate._requests[request.request_id] = expired_record
    runtime.approval_gate._trusted_requests[request.request_id] = expired_record

    result = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="LYRA",
    )

    print(result)

    assert result.success is False, "Expired approval must not execute."

    stored = runtime.approval_gate.get(request.request_id)
    assert stored.status == ApprovalStatus.EXPIRED, (
        "Approval status must become EXPIRED."
    )

    _record("TEST 3 (EXPIRED APPROVAL)", "PASS")


# ============================================================
# TEST 4 - PERMISSION REVOKED AFTER APPROVAL
# ============================================================

async def test_4_permission_revoked_after_approval():
    print("\nTEST 4: PERMISSION REVOKED AFTER APPROVAL")

    runtime = _fresh_runtime()

    request = runtime.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Hello"},
    )

    runtime.approval_gate.approve(request.request_id)

    removed = runtime.permission_engine.revoke("LYRA", "send_notification")
    assert removed is True, "Permission must have existed to revoke."

    result = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="LYRA",
    )

    print(result)

    assert result.success is False
    assert "permission" in result.message.lower(), (
        "Failure message must indicate permission was removed."
    )
    assert (
        "removed" in result.message.lower()
        or "revoked" in result.message.lower()
    )

    _record("TEST 4 (PERMISSION REVOKED AFTER APPROVAL)", "PASS")


# ============================================================
# TEST 5 - TOOL/ACTION BINDING
# ============================================================

async def test_5_tool_action_binding():
    print("\nTEST 5: TOOL/ACTION BINDING")
    print(
        "Directly tampers the ACTIVE approval store (not the trusted "
        "one) to point at a different, real, existing tool/action "
        "('modify_code'), then confirms ApprovalGate's own tamper "
        "detection (_restore_if_tampered, triggered by .get()/"
        "check_expiration()) reverts it BEFORE execution - and that "
        "the RESTORED tool ('send_notification') is what actually "
        "runs, never the tampered one."
    )

    runtime = _fresh_runtime()

    request = runtime.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Hello"},
    )

    approved = runtime.approval_gate.approve(request.request_id)

    tampered_record = ApprovalRequest(
        request_id=approved.request_id,
        agent_id=approved.agent_id,
        action="modify_code",
        task=approved.task,
        status=approved.status,
        created_at=approved.created_at,
        tool_name="modify_code",
        context=dict(approved.context or {}),
        expires_at=approved.expires_at,
    )

    # Tamper ONLY the active store - the trusted store still holds
    # the real, original record.
    runtime.approval_gate._requests[request.request_id] = tampered_record

    restored = runtime.approval_gate.get(request.request_id)

    print(restored)

    assert restored.action == "send_notification", (
        "Tampered action must be reverted by ApprovalGate's own "
        "integrity check before anything else sees it."
    )
    assert restored.tool_name == "send_notification"

    # Execution must proceed against the RESTORED action - and, since
    # send_notification is a real working tool, it succeeds normally.
    result = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="LYRA",
    )

    print(result)

    assert result.success is True, (
        "Restored (real) binding must execute normally."
    )
    assert result.tool_name == "send_notification", (
        "Must execute the RESTORED tool - never the tampered one."
    )

    payload_str = str(result.data).lower()
    assert "modify_code" not in payload_str, (
        "Result must never reference the tampered tool in any form - "
        "proves the tampered substitution never took effect."
    )

    _record("TEST 5 (TOOL/ACTION BINDING)", "PASS")


# ============================================================
# TEST 6 - REPLAY PROTECTION
# ============================================================

async def test_6_replay_protection():
    print("\nTEST 6: REPLAY PROTECTION")
    print(
        "send_notification is a real, working tool, so this exercises "
        "the FULL pipeline: first execution succeeds and consumes the "
        "approval; a second attempt with the SAME request_id must be "
        "rejected."
    )

    runtime = _fresh_runtime()

    request = runtime.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Hello"},
    )

    runtime.approval_gate.approve(request.request_id)

    first_attempt = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="LYRA",
    )
    print(first_attempt)
    assert first_attempt.success is True, (
        "First legitimate execution must succeed."
    )

    stored_after_first = runtime.approval_gate.get(request.request_id)
    assert stored_after_first.status == ApprovalStatus.EXECUTED, (
        "Approval must be consumed (EXECUTED) after a successful run."
    )

    second_attempt = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="LYRA",
    )
    print(second_attempt)

    assert second_attempt.success is False, "Replayed execution must fail."
    assert "executed" in second_attempt.message.lower(), (
        "Failure must indicate the approval was already executed."
    )

    # Belt-and-suspenders: the underlying ApprovalGate mechanism
    # itself also refuses to mark an already-EXECUTED approval as
    # executed again.
    try:
        runtime.approval_gate.mark_executed(request.request_id)
        raise AssertionError(
            "mark_executed() must reject an already-executed approval."
        )
    except ValueError as exc:
        print(f"mark_executed() correctly rejected replay: {exc}")

    _record("TEST 6 (REPLAY PROTECTION)", "PASS")


# ============================================================
# TEST 7 - DISABLED / INVALID AGENT
# ============================================================

async def test_7_disabled_invalid_agent():
    print("\nTEST 7: DISABLED / INVALID AGENT")

    # --- 7a: the bound agent exists but is disabled ---------------
    runtime_a = _fresh_runtime()

    request_a = runtime_a.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Hello"},
    )
    runtime_a.approval_gate.approve(request_a.request_id)

    lyra_agent = runtime_a.agent_registry.get("LYRA")
    assert lyra_agent is not None
    lyra_agent.enabled = False  # existing public attribute, no new API

    result_a = await runtime_a.tool_gateway.approve_and_execute(
        request_id=request_a.request_id,
        agent_id="LYRA",
    )
    print(result_a)

    assert result_a.success is False
    assert "disabled" in result_a.message.lower()

    # --- 7b: the bound agent_id does not exist at all --------------
    runtime_b = _fresh_runtime()

    request_b = runtime_b.approval_gate.create_request(
        agent_id="GHOST",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Hello"},
    )
    runtime_b.approval_gate.approve(request_b.request_id)

    assert runtime_b.agent_registry.get("GHOST") is None

    result_b = await runtime_b.tool_gateway.approve_and_execute(
        request_id=request_b.request_id,
        agent_id="GHOST",
    )
    print(result_b)

    assert result_b.success is False
    assert "not registered" in result_b.message.lower()

    _record("TEST 7 (DISABLED / INVALID AGENT)", "PASS")


# ============================================================
# TEST 8 - AUDIT VERIFICATION
# ============================================================

async def test_8_audit_verification():
    print("\nTEST 8: AUDIT VERIFICATION")

    runtime = _fresh_runtime()

    before_count = runtime.audit_count()

    # A blocked ToolGateway.approve_and_execute() attempt (wrong
    # agent) - per the architectural finding above, this path does
    # NOT call AuditLogger anywhere.
    request = runtime.approval_gate.create_request(
        agent_id="LYRA",
        action="send_notification",
        task="Notify player P1",
        tool_name="send_notification",
        context={"player_id": "P1", "message": "Hello"},
    )
    runtime.approval_gate.approve(request.request_id)

    blocked_result = await runtime.tool_gateway.approve_and_execute(
        request_id=request.request_id,
        agent_id="ELARA",
    )
    assert blocked_result.success is False

    after_blocked_count = runtime.audit_count()

    print(
        f"Audit events before blocked attempt: {before_count}, "
        f"after: {after_blocked_count}"
    )

    assert after_blocked_count == before_count, (
        "ToolGateway.approve_and_execute() rejections are NOT "
        "audited by the current architecture - confirming the "
        "finding, not assuming it either way."
    )

    # A normal, successful, low-risk execution via the real pipeline
    # (execute_intent -> ... -> AgentController -> AuditLogger) DOES
    # get audited - proving AuditLogger integration genuinely works
    # elsewhere, just not on the ToolGateway.approve_and_execute()
    # code path exercised above.
    normal_result = await runtime.execute_intent("Check tournament")
    assert normal_result.success is True

    after_normal_count = runtime.audit_count()

    print(f"Audit events after a normal execute_intent(): {after_normal_count}")

    assert after_normal_count > after_blocked_count, (
        "A normal AgentController-routed execution must generate an "
        "audit event."
    )

    events = runtime.audit_events()
    last_event = events[-1]

    print(last_event)

    assert last_event.agent_id == "ARIA"
    assert last_event.action == "read_tournament"
    assert last_event.success is True

    _record("TEST 8 (AUDIT VERIFICATION)", "PASS")


# ============================================================
# RUNNER
# ============================================================

async def main():
    print("CORTEX LYRA ADVERSARIAL SECURITY TEST SUITE")
    print("=" * 60)

    await test_1_wrong_agent_execution()
    await test_2_context_tampering()
    await test_3_expired_approval()
    await test_4_permission_revoked_after_approval()
    await test_5_tool_action_binding()
    await test_6_replay_protection()
    await test_7_disabled_invalid_agent()
    await test_8_audit_verification()

    print("\n" + "=" * 60)
    print("RESULT SUMMARY")
    print("-" * 60)

    failed = [name for name, status in _RESULTS if status == "FAIL"]

    for name, status in _RESULTS:
        print(f"  {name}: {status}")

    print("=" * 60)

    if not failed:
        print("\nCORTEX LYRA ADVERSARIAL SECURITY TEST: PASS")
    else:
        print(
            f"\nCORTEX LYRA ADVERSARIAL SECURITY TEST: FAIL "
            f"({len(failed)} failed)"
        )
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())




