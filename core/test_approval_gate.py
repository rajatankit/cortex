from core.approval_gate import ApprovalGate, ApprovalStatus


gate = ApprovalGate()


request = gate.create_request(
    agent_id="ARIA",
    action="modify_data",
    task="Modify player data",
)


print("CREATED:")
print(request)

print("\nPENDING:")
print(gate.list_pending())


approved = gate.approve(request.request_id)

print("\nAPPROVED:")
print(approved)

print("\nSTATUS:")
print(approved.status == ApprovalStatus.APPROVED)




