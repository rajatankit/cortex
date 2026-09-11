"""
tools/atlas_tools.py

ATLAS engineering tools for CORTEX.

read_code now reads REAL files from two places:
- repo="cortex" -> the local filesystem this Python process is
  running from (Cortex's own source).
- repo="battlecrown" -> the battle-crown GitHub repo, fetched via
  the GitHub REST API (requires GITHUB_TOKEN + GITHUB_BATTLECROWN_REPO).

If a bare filename is given (no "/" in it, e.g. "tournament_tools.py")
instead of a full path, both branches search for the first matching
file by name before reading it - "code ka naam lu, vo mujhe de de".

modify_code is still a placeholder. The plan (once GITHUB_TOKEN is
confirmed working for reads) is a PR-based flow: ATLAS drafts the
change, opens a branch + pull request on GitHub instead of pushing
straight to main, so Boss reviews and merges it manually - not wired
up yet.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

from core.tools.tool import Tool, ToolRisk

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_BATTLECROWN_REPO = os.getenv("GITHUB_BATTLECROWN_REPO", "")
GITHUB_BRANCH = os.getenv("GITHUB_DEFAULT_BRANCH", "main")

# Cap so a huge file doesn't blow up the response/context.
MAX_CHARS = 8000

_SKIP_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".next",
    "core_backup_86_passed", "core_backup_before_import_fix",
}


def _project_root() -> str:
    # atlas_tools.py lives in core/tools/, so the project root is two
    # levels up (core/tools -> core -> project root).
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _find_cortex_file_by_name(filename: str) -> str | None:
    root = _project_root()
    for current_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        if filename in files:
            rel = os.path.relpath(os.path.join(current_dir, filename), root)
            return rel.replace("\\", "/")
    return None


def _read_cortex_file(path: str) -> dict[str, Any]:
    root = _project_root()
    full_path = os.path.normpath(os.path.join(root, path))

    # Safety: never allow escaping the project root via "..".
    if not full_path.startswith(root):
        return {"status": "error", "message": "Path escapes project root - not allowed."}

    if not os.path.isfile(full_path):
        return {"status": "not_found", "repo": "cortex", "path": path}

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    truncated = len(content) > MAX_CHARS
    return {
        "status": "ok",
        "repo": "cortex",
        "path": path,
        "content": content[:MAX_CHARS],
        "truncated": truncated,
    }


def _github_request(url: str):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "cortex-atlas",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _find_battlecrown_file_by_name(filename: str) -> str | None:
    url = (
        f"https://api.github.com/repos/{GITHUB_BATTLECROWN_REPO}"
        f"/git/trees/{GITHUB_BRANCH}?recursive=1"
    )
    try:
        data = _github_request(url)
    except Exception:
        return None

    for entry in data.get("tree", []):
        if entry.get("type") == "blob" and entry["path"].split("/")[-1] == filename:
            return entry["path"]
    return None


def _read_battlecrown_file(path: str) -> dict[str, Any]:
    if not GITHUB_TOKEN:
        return {"status": "error", "message": "GITHUB_TOKEN is not configured"}
    if not GITHUB_BATTLECROWN_REPO:
        return {"status": "error", "message": "GITHUB_BATTLECROWN_REPO is not configured"}

    url = (
        f"https://api.github.com/repos/{GITHUB_BATTLECROWN_REPO}"
        f"/contents/{path}?ref={GITHUB_BRANCH}"
    )

    try:
        data = _github_request(url)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return {"status": "not_found", "repo": "battle-crown", "path": path}
        return {"status": "error", "message": f"GitHub HTTP {error.code}: {error.reason}"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    if data.get("type") != "file" or "content" not in data:
        return {"status": "error", "message": "Path is not a readable file (maybe a folder)."}

    try:
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception as exc:
        return {"status": "error", "message": f"Failed to decode file: {exc}"}

    truncated = len(content) > MAX_CHARS
    return {
        "status": "ok",
        "repo": "battle-crown",
        "path": path,
        "content": content[:MAX_CHARS],
        "truncated": truncated,
    }


def _normalize_repo(repo_raw: str) -> str:
    r = (repo_raw or "").strip().lower()
    if r in ("battlecrown", "battle-crown", "battle crown", "bc"):
        return "battlecrown"
    return "cortex"


# ============================================================
# READ CODE  (REAL DATA - both repos)
# ============================================================

async def read_code(
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:

    context = context or {}
    repo = _normalize_repo(context.get("repo", ""))
    path = context.get("path") or context.get("file") or context.get("filename")

    if not path:
        return {
            "status": "error",
            "message": "path (or filename) is required, e.g. 'tournament_tools.py'",
        }

    path = str(path).strip().lstrip("/")

    # Bare filename (no folder in it) - search for it first.
    if "/" not in path and "\\" not in path:
        if repo == "cortex":
            found = _find_cortex_file_by_name(path)
        else:
            found = _find_battlecrown_file_by_name(path)

        if not found:
            return {"status": "not_found", "repo": repo, "path": path}
        path = found

    if repo == "cortex":
        return _read_cortex_file(path)
    return _read_battlecrown_file(path)


# ============================================================
# MODIFY CODE  (still placeholder - see module docstring)
# ============================================================

async def modify_code(
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High-risk engineering operation.

    Actual code modification must only occur after
    authorization and approval through CORTEX.
    """

    context = context or {}

    return {
        "operation": "modify_code",
        "status": "accepted",
        "context": context,
    }


# ============================================================
# REGISTRATION
# ============================================================

def register_atlas_tools(tool_registry) -> None:

    if not tool_registry.exists("read_code"):
        tool_registry.register(
            Tool(
                name="read_code",
                description=(
                    "Reads a real source file from the Cortex or battle-crown "
                    "codebase, by full path or bare filename."
                ),
                required_action="read_code",
                risk=ToolRisk.LOW,
                handler=read_code,
            )
        )

    if not tool_registry.exists("modify_code"):
        tool_registry.register(
            Tool(
                name="modify_code",
                description=(
                    "Modify source code through an authorized "
                    "and approved engineering operation."
                ),
                required_action="modify_code",
                risk=ToolRisk.HIGH,
                handler=modify_code,
            )
        )