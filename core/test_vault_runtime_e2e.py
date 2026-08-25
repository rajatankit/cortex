"""
CORTEX VAULT Runtime End-to-End Test Suite.

Verifies the real VAULT pipeline:

    IntentEngine
        ->
    TaskPlanner
        ->
    AgentController
        ->
    PermissionEngine
        ->
    ApprovalGate
        ->
    ToolGateway
        ->
    VAULT Tool

No production code is modified by this test.
"""

from __future__ import annotations

import asyncio
from core.cortex_bootstrap import bootstrap_cortex


def fresh_runtime():
    return bootstrap_cortex()


async def test_1_vault_intent_routing():
    print("\nTEST 1: VAULT INTENT ROUTING")

    runtime = fresh_runtime()

    result = runtime.intent_engine.parse(
        "store room data",
        context={
            "room_id": "ROOM-001",
            "password": "SECRET-123",
            "tournament_id": "1",
            "game": "BGMI",
        },
    )

    print(result)

    assert result.success is True
    assert result.agent_id == "VAULT"
    assert result.action == "store_room_data"

    print("TEST 1 (VAULT INTENT ROUTING): PASS")


async def test_2_store_room_data():
    print("\nTEST 2: STORE ROOM DATA")

    runtime = fresh_runtime()

    result = await runtime.tool_gateway.execute(
        agent_id="VAULT",
        tool_name="store_room_data",
        task="Store protected room data",
        context={
            "room_id": "ROOM-001",
            "password": "SECRET-123",
            "tournament_id": "1",
            "game": "BGMI",
        },
    )

    print(result)

    if not result.success:
        print(
            "Execution requires approval. "
            "Request data:",
            result.data,
        )

        request_id = (result.data or {}).get("request_id")

        assert request_id is not None, (
            "HIGH-risk VAULT execution must create an approval request."
        )

        approved = runtime.approval_gate.approve(request_id)
        assert approved is not None

        result = await runtime.tool_gateway.approve_and_execute(
            request_id=request_id,
            agent_id="VAULT",
        )

        print(result)

    assert result.success is True
    assert result.tool_name == "store_room_data"

    data = result.data or {}

    assert data.get("status") == "stored"

    room = data.get("room", {})

    assert room.get("room_id") == "ROOM-001"
    assert room.get("password") == "SECRET-123"
    assert room.get("tournament_id") == 1
    assert room.get("game") == "BGMI"

    print("TEST 2 (STORE ROOM DATA): PASS")


async def test_3_read_room_data():
    print("\nTEST 3: READ ROOM DATA")

    runtime = fresh_runtime()

    store_result = await runtime.tool_gateway.execute(
        agent_id="VAULT",
        tool_name="store_room_data",
        task="Store room before reading",
        context={
            "room_id": "ROOM-READ-001",
            "password": "READ-SECRET",
            "tournament_id": "1",
            "game": "Free Fire",
        },
    )

    print("Store:", store_result)

    request_id = (store_result.data or {}).get("request_id")

    if request_id:
        runtime.approval_gate.approve(request_id)

        store_result = await runtime.tool_gateway.approve_and_execute(
            request_id=request_id,
            agent_id="VAULT",
        )

    assert store_result.success is True

    read_result = await runtime.tool_gateway.execute(
        agent_id="VAULT",
        tool_name="read_room_data",
        task="Read protected room data",
        context={
            "room_id": "ROOM-READ-001",
        },
    )

    print("Read:", read_result)

    if not read_result.success:
        request_id = (read_result.data or {}).get("request_id")

        assert request_id is not None

        runtime.approval_gate.approve(request_id)

        read_result = await runtime.tool_gateway.approve_and_execute(
            request_id=request_id,
            agent_id="VAULT",
        )

        print("Approved read:", read_result)

    assert read_result.success is True
    assert read_result.tool_name == "read_room_data"

    data = read_result.data or {}

    assert data.get("status") == "ok"

    room = data.get("room", {})

    assert room.get("room_id") == "ROOM-READ-001"
    assert room.get("password") == "READ-SECRET"

    print("TEST 3 (READ ROOM DATA): PASS")


async def test_4_update_room_data():
    print("\nTEST 4: UPDATE ROOM DATA")

    runtime = fresh_runtime()

    store_result = await runtime.tool_gateway.execute(
        agent_id="VAULT",
        tool_name="store_room_data",
        task="Create room for update test",
        context={
            "room_id": "ROOM-UPDATE-001",
            "password": "OLD-PASSWORD",
            "tournament_id": "1",
            "game": "BGMI",
        },
    )

    request_id = (store_result.data or {}).get("request_id")

    if request_id:
        runtime.approval_gate.approve(request_id)

        store_result = await runtime.tool_gateway.approve_and_execute(
            request_id=request_id,
            agent_id="VAULT",
        )

    assert store_result.success is True

    update_result = await runtime.tool_gateway.execute(
        agent_id="VAULT",
        tool_name="update_room_data",
        task="Update protected room password",
        context={
            "room_id": "ROOM-UPDATE-001",
            "updates": {
                "password": "NEW-PASSWORD",
            },
        },
    )

    print("Update:", update_result)

    if not update_result.success:
        request_id = (update_result.data or {}).get("request_id")

        assert request_id is not None

        runtime.approval_gate.approve(request_id)

        update_result = await runtime.tool_gateway.approve_and_execute(
            request_id=request_id,
            agent_id="VAULT",
        )

        print("Approved update:", update_result)

    assert update_result.success is True
    assert update_result.tool_name == "update_room_data"

    data = update_result.data or {}

    assert data.get("status") == "updated"

    room = data.get("room", {})

    assert room.get("room_id") == "ROOM-UPDATE-001"
    assert room.get("password") == "NEW-PASSWORD"

    print("TEST 4 (UPDATE ROOM DATA): PASS")


async def test_5_wrong_agent():
    print("\nTEST 5: WRONG AGENT")

    runtime = fresh_runtime()

    result = await runtime.tool_gateway.execute(
        agent_id="VAULT",
        tool_name="store_room_data",
        task="Store protected room",
        context={
            "room_id": "ROOM-SECURITY-001",
            "password": "SECRET",
        },
    )

    print(result)

    request_id = (result.data or {}).get("request_id")

    assert request_id is not None

    runtime.approval_gate.approve(request_id)

    attack = await runtime.tool_gateway.approve_and_execute(
        request_id=request_id,
        agent_id="ELARA",
    )

    print(attack)

    assert attack.success is False
    assert "does not match" in attack.message.lower()

    stored = runtime.approval_gate.get(request_id)

    assert stored.status.value == "approved"

    print("TEST 5 (WRONG AGENT): PASS")


async def test_6_unknown_room():
    print("\nTEST 6: UNKNOWN ROOM")

    runtime = fresh_runtime()

    result = await runtime.tool_gateway.execute(
        agent_id="VAULT",
        tool_name="read_room_data",
        task="Read unknown protected room",
        context={
            "room_id": "ROOM-DOES-NOT-EXIST",
        },
    )

    print(result)

    if not result.success:
        request_id = (result.data or {}).get("request_id")

        assert request_id is not None

        runtime.approval_gate.approve(request_id)

        result = await runtime.tool_gateway.approve_and_execute(
            request_id=request_id,
            agent_id="VAULT",
        )

        print(result)

    assert result.success is True

    data = result.data or {}

    assert data.get("status") == "not_found"
    assert data.get("room_id") == "ROOM-DOES-NOT-EXIST"

    print("TEST 6 (UNKNOWN ROOM): PASS")


async def main():
    print("CORTEX VAULT RUNTIME E2E TEST SUITE")
    print("=" * 60)

    await test_1_vault_intent_routing()
    await test_2_store_room_data()
    await test_3_read_room_data()
    await test_4_update_room_data()
    await test_5_wrong_agent()
    await test_6_unknown_room()

    print("\n" + "=" * 60)
    print("CORTEX VAULT RUNTIME E2E TEST: PASS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())




