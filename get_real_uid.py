import os
import urllib.request
import json

TOKEN = os.getenv("BATTLE_CROWN_BRIDGE_TOKEN", "")
URL = "http://localhost:3000/api/cortex/notifications"

payload = json.dumps({"action": "read_notification_logs", "context": {}}).encode("utf-8")
req = urllib.request.Request(
    URL, data=payload,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=15) as resp:
    print(resp.read().decode("utf-8")[:500])
