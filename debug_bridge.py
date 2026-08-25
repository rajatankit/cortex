import json
import os
import urllib.request

TOKEN = os.getenv("BATTLE_CROWN_BRIDGE_TOKEN", "")
URL = "http://localhost:3000/api/cortex/rooms"

def call(action, context):
    payload = json.dumps({"action": action, "context": context}).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"status": "error", "message": str(e)}


print("--- STORE (tournament_id=2) ---")
store = call("store_room_data", {
    "room_id": "DEBUG-1",
    "tournament_id": "2",
    "password": "debugpass",
    "game": "BGMI",
})
print(store)

print("\n--- IMMEDIATE READ ---")
read = call("read_room_data", {"room_id": "DEBUG-1"})
print(read)