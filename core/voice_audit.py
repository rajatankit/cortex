from __future__ import annotations

from typing import Any

from core.audit_logger import AuditLogger


class VoiceAudit:
    """
    Voice-facing audit layer for CORTEX.

    VoiceAudit does not execute tools and does not bypass the
    existing security pipeline. It provides a safe, structured
    view of audit events for future voice/UI consumers.
    """

    def __init__(self, audit_logger: AuditLogger):
        if audit_logger is None:
            raise ValueError("audit_logger is required.")

        self.audit_logger = audit_logger

    def record(
        self,
        agent_id: str,
        action: str,
        decision: str,
        success: bool,
        message: str,
    ):
        """
        Record an event through the existing AuditLogger.
        """
        return self.audit_logger.log(
            agent_id=agent_id,
            action=action,
            decision=decision,
            success=success,
            message=message,
        )

    def events(self) -> list[Any]:
        """
        Return a snapshot of all audit events.
        """
        return self.audit_logger.list_events()

    def count(self) -> int:
        """
        Return the number of audit events.
        """
        return self.audit_logger.count()

    def clear(self) -> None:
        """
        Clear audit events.
        """
        self.audit_logger.clear()

    def latest(self):
        """
        Return the latest audit event, or None if no events exist.
        """
        events = self.audit_logger.list_events()

        if not events:
            return None

        return events[-1]

    def status(self) -> dict[str, Any]:
        """
        Return a compact status snapshot suitable for
        voice/UI consumers.
        """
        latest_event = self.latest()

        return {
            "available": True,
            "event_count": self.count(),
            "latest_event": latest_event,
        }
