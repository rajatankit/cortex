from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    timestamp: str
    agent_id: str
    action: str
    decision: str
    success: bool
    message: str


class AuditLogger:
    """
    Records CORTEX decisions and execution results.

    Optional voice notification support is provided through an
    injected notifier.

    IMPORTANT:
    - Audit logging remains the source of truth.
    - Voice notification never controls permissions.
    - Voice notification never changes decisions.
    - Voice notification failures never break execution.
    - Existing AuditLogger() usage remains fully compatible.
    """

    def __init__(self, voice_notifier: Any | None = None):
        self._events: list[AuditEvent] = []
        self._voice_notifier = voice_notifier

    def log(
        self,
        agent_id: str,
        action: str,
        decision: str,
        success: bool,
        message: str,
    ) -> AuditEvent:

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_id=agent_id,
            action=action,
            decision=decision,
            success=success,
            message=message,
        )

        # ----------------------------------------------------
        # PRIMARY AUDIT RECORD
        # ----------------------------------------------------

        self._events.append(event)

        # ----------------------------------------------------
        # OPTIONAL VOICE AUDIT
        # ----------------------------------------------------
        #
        # Voice is strictly observational.
        # It must NEVER affect the audit result or execution flow.
        #

        if self._voice_notifier is not None:
            try:
                self._voice_notifier.notify(event)
            except Exception:
                # Voice must never break CORTEX execution.
                pass

        return event

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()

    def voice_enabled(self) -> bool:
        """
        Return whether a voice notifier is attached and enabled.
        """

        if self._voice_notifier is None:
            return False

        try:
            return bool(self._voice_notifier.enabled)
        except Exception:
            return False