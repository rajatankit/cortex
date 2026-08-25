from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from uuid import uuid4
from copy import deepcopy


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    agent_id: str
    action: str
    task: str
    status: ApprovalStatus
    created_at: str
    tool_name: str | None = None
    context: dict | None = None
    expires_at: str | None = None


class ApprovalGate:
    """
    Manages human approval for CORTEX review-level actions.

    Security properties:
    - Every approval gets a unique request ID.
    - Approved requests can only be executed once.
    - Approved requests expire after a fixed time window.
    - Rejected requests cannot be re-approved.
    - Executed requests cannot be reused.
    - Approval agent binding is preserved.
    - Approval action binding is preserved.
    - Approval tool binding is preserved.
    - Approval context integrity is preserved.
    - Returned approval objects are isolated from internal state.
    """

    APPROVAL_TTL_SECONDS = 300  # 5 minutes

    def __init__(self):
        # Active approval records.
        self._requests: dict[str, ApprovalRequest] = {}

        # Trusted internal copy of every approval.
        #
        # This protects the authorization record even if some
        # internal object is accidentally modified.
        self._trusted_requests: dict[str, ApprovalRequest] = {}

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _copy_request(
        request: ApprovalRequest,
    ) -> ApprovalRequest:
        """
        Return a completely isolated copy of an approval request.

        This prevents callers from modifying the internal context
        dictionary through a returned object.
        """

        return ApprovalRequest(
            request_id=request.request_id,
            agent_id=request.agent_id,
            action=request.action,
            task=request.task,
            status=request.status,
            created_at=request.created_at,
            tool_name=request.tool_name,
            context=deepcopy(request.context),
            expires_at=request.expires_at,
        )

    def _store(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRequest:
        """
        Store the same authorization record in both the active
        and trusted stores.
        """

        active = self._copy_request(request)
        trusted = self._copy_request(request)

        self._requests[request.request_id] = active
        self._trusted_requests[request.request_id] = trusted

        return self._copy_request(trusted)

    def _restore_if_tampered(
        self,
        request_id: str,
    ) -> ApprovalRequest | None:
        """
        Verify the active approval against the trusted copy.

        If the active record has been modified, restore the trusted
        authorization record.

        This protects:
        - agent_id
        - action
        - task
        - tool_name
        - context
        - status
        - timestamps
        """

        active = self._requests.get(request_id)
        trusted = self._trusted_requests.get(request_id)

        if trusted is None:
            return None

        if active is None:
            restored = self._copy_request(trusted)
            self._requests[request_id] = restored
            return self._copy_request(restored)

        if active != trusted:
            restored = self._copy_request(trusted)
            self._requests[request_id] = restored
            return self._copy_request(restored)

        return self._copy_request(trusted)

    def _set_request(
        self,
        request: ApprovalRequest,
    ) -> ApprovalRequest:
        """
        Safely replace an approval record.

        Both the active and trusted authorization records are updated
        together so legitimate state transitions remain synchronized.
        """

        return self._store(request)

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    def create_request(
        self,
        agent_id: str,
        action: str,
        task: str,
        tool_name: str | None = None,
        context: dict | None = None,
    ) -> ApprovalRequest:

        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(
            seconds=self.APPROVAL_TTL_SECONDS
        )

        request = ApprovalRequest(
            request_id=str(uuid4()),
            agent_id=agent_id,
            action=action,
            task=task,
            status=ApprovalStatus.PENDING,
            created_at=now.isoformat(),
            tool_name=tool_name,
            context=deepcopy(context),
            expires_at=expires_at.isoformat(),
        )

        return self._store(request)

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    def get(
        self,
        request_id: str,
    ) -> ApprovalRequest | None:

        return self._restore_if_tampered(request_id)

    # ---------------------------------------------------------
    # PENDING
    # ---------------------------------------------------------

    def list_pending(self) -> list[ApprovalRequest]:
        requests = []

        for request_id in list(self._trusted_requests.keys()):
            request = self._restore_if_tampered(request_id)

            if (
                request is not None
                and request.status == ApprovalStatus.PENDING
            ):
                requests.append(request)

        return requests

    def pending_requests(self) -> list[ApprovalRequest]:
        return self.list_pending()

    # ---------------------------------------------------------
    # APPROVE
    # ---------------------------------------------------------

    def approve(
        self,
        request_id: str,
    ) -> ApprovalRequest:

        request = self._restore_if_tampered(request_id)

        if request is None:
            raise ValueError(
                f"Approval request not found: {request_id}"
            )

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request is already {request.status.value}"
            )

        if self.is_expired(request):

            expired = ApprovalRequest(
                request_id=request.request_id,
                agent_id=request.agent_id,
                action=request.action,
                task=request.task,
                status=ApprovalStatus.EXPIRED,
                created_at=request.created_at,
                tool_name=request.tool_name,
                context=deepcopy(request.context),
                expires_at=request.expires_at,
            )

            self._set_request(expired)

            raise ValueError(
                "Approval request has expired"
            )

        updated = ApprovalRequest(
            request_id=request.request_id,
            agent_id=request.agent_id,
            action=request.action,
            task=request.task,
            status=ApprovalStatus.APPROVED,
            created_at=request.created_at,
            tool_name=request.tool_name,
            context=deepcopy(request.context),
            expires_at=request.expires_at,
        )

        return self._set_request(updated)

    # ---------------------------------------------------------
    # REJECT
    # ---------------------------------------------------------

    def reject(
        self,
        request_id: str,
    ) -> ApprovalRequest:

        request = self._restore_if_tampered(request_id)

        if request is None:
            raise ValueError(
                f"Approval request not found: {request_id}"
            )

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Request is already {request.status.value}"
            )

        updated = ApprovalRequest(
            request_id=request.request_id,
            agent_id=request.agent_id,
            action=request.action,
            task=request.task,
            status=ApprovalStatus.REJECTED,
            created_at=request.created_at,
            tool_name=request.tool_name,
            context=deepcopy(request.context),
            expires_at=request.expires_at,
        )

        return self._set_request(updated)

    # ---------------------------------------------------------
    # EXPIRATION
    # ---------------------------------------------------------

    def is_expired(
        self,
        request: ApprovalRequest,
    ) -> bool:

        if not request.expires_at:
            return False

        expires_at = datetime.fromisoformat(
            request.expires_at
        )

        now = datetime.now(timezone.utc)

        return now >= expires_at

    def check_expiration(
        self,
        request_id: str,
    ) -> ApprovalRequest | None:

        request = self._restore_if_tampered(request_id)

        if request is None:
            return None

        if request.status not in (
            ApprovalStatus.PENDING,
            ApprovalStatus.APPROVED,
        ):
            return request

        if not self.is_expired(request):
            return request

        expired = ApprovalRequest(
            request_id=request.request_id,
            agent_id=request.agent_id,
            action=request.action,
            task=request.task,
            status=ApprovalStatus.EXPIRED,
            created_at=request.created_at,
            tool_name=request.tool_name,
            context=deepcopy(request.context),
            expires_at=request.expires_at,
        )

        return self._set_request(expired)

    # ---------------------------------------------------------
    # EXECUTION
    # ---------------------------------------------------------

    def mark_executed(
        self,
        request_id: str,
    ) -> ApprovalRequest:

        request = self._restore_if_tampered(request_id)

        if request is None:
            raise ValueError(
                f"Approval request not found: {request_id}"
            )

        if request.status != ApprovalStatus.APPROVED:
            raise ValueError(
                f"Request is not approved: {request.status.value}"
            )

        if self.is_expired(request):

            expired = ApprovalRequest(
                request_id=request.request_id,
                agent_id=request.agent_id,
                action=request.action,
                task=request.task,
                status=ApprovalStatus.EXPIRED,
                created_at=request.created_at,
                tool_name=request.tool_name,
                context=deepcopy(request.context),
                expires_at=request.expires_at,
            )

            self._set_request(expired)

            raise ValueError(
                "Approval request has expired"
            )

        updated = ApprovalRequest(
            request_id=request.request_id,
            agent_id=request.agent_id,
            action=request.action,
            task=request.task,
            status=ApprovalStatus.EXECUTED,
            created_at=request.created_at,
            tool_name=request.tool_name,
            context=deepcopy(request.context),
            expires_at=request.expires_at,
        )

        return self._set_request(updated)




