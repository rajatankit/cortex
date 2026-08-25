import os
import json
import urllib.request

TOKEN = os.getenv("CORTEX_BRIDGE_TOKEN", "")

req = urllib.request.Request(
    "http://localhost:8000/dispatch",
    data=json.dumps({"task": "Check tournament"}).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    },
    method="POST",
)

with urllib.request.urlopen(req, timeout=15) as resp:
    print(resp.read().decode("utf-8"))