"""
tools/vercel_monitor.py

Polls Vercel's Deployments API for a specific commit SHA's build
status, and can revert a file to its previous content via GitHub
if that build failed. Called by CORTEX's monitor cron
(app/api/cortex/monitor/atlas-builds) - not by the LLM directly.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

VERCEL_API_TOKEN = os.getenv("VERCEL_API_TOKEN", "")
VERCEL_PROJECT_NAME = os.getenv("VERCEL_PROJECT_NAME", "battle-crown")


def _vercel_request(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {VERCEL_API_TOKEN}"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


async def check_deployment_status(commit_sha: str) -> dict[str, Any]:
    """
    Looks up the Vercel deployment tied to a git commit SHA.
    Returns state: "READY" (success), "ERROR" (failed), "BUILDING"/
    "QUEUED" (still pending), or "not_found" if Vercel hasn't picked
    it up yet.
    """
    if not VERCEL_API_TOKEN:
        return {"status": "error", "message": "VERCEL_API_TOKEN not configured"}

    url = f"https://api.vercel.com/v6/deployments?projectId={VERCEL_PROJECT_NAME}&limit=10"

    try:
        data = _vercel_request(url)
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    for deployment in data.get("deployments", []):
        meta = deployment.get("meta", {})
        sha = meta.get("githubCommitSha") or meta.get("gitCommitSha")
        if sha and sha.startswith(commit_sha[:7]):
            state = deployment.get("readyState") or deployment.get("state")
            return {"status": "found", "state": state, "url": deployment.get("url")}

    return {"status": "not_found"}