from core.permissions import RiskLevel

# ... execute() method ke andar, REVIEW block ko replace karo:

if decision.decision == Decision.REVIEW:

    if decision.risk == RiskLevel.HIGH:
        required_verification = "fingerprint+face"
    elif decision.risk == RiskLevel.MEDIUM:
        required_verification = "fingerprint"
    else:
        required_verification = "none"

    request = self.approval_gate.create_request(
        agent_id=agent_id,
        action=action,
        task=task,
        tool_name=tool_name,
        context=context,
        required_verification=required_verification,
    )

    return self._record(
        ControlResult(
            success=False,
            agent_id=agent_id,
            action=action,
            decision=Decision.REVIEW,
            message=(
                f"VERIFICATION_REQUIRED:{required_verification}:"
                f"{request.request_id}"
            ),
        )
    )