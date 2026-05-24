"""workspace.status tool implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from tools.registry import registry

from ..registry import WorkspaceRegistry
from ..lib.git_runner import GitRunner

logger = logging.getLogger(__name__)


def _workspace_registry_path() -> Path:
    """Return the path to workspaces.yaml under HERMES_HOME."""
    from hermes_constants import get_hermes_home
    from pathlib import Path
    return get_hermes_home() / "workspaces.yaml"


def _get_registry() -> WorkspaceRegistry:
    return WorkspaceRegistry(_workspace_registry_path())


def _workspace_status(args: dict) -> str:
    """Report current branch, dirty state, and ahead/behind counts."""
    ws_id = args.get("workspace_id", "").strip()
    reg = _get_registry()
    ws = reg.get(ws_id)
    if not ws:
        return json.dumps({"error": f"Workspace '{ws_id}' not found."})

    runner = GitRunner(ws.path, ssh_socket=ws.ssh_agent_socket)
    try:
        branch = runner.run(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        dirty = runner.run(["status", "--porcelain"]).strip() != ""
        remote = ws.push_remote or "origin"
        ahead_behind = "0, 0"
        try:
            ahead_behind = runner.run(["rev-list", "--left-right", "--count", f"{remote}/{ws.default_branch}...HEAD"]).strip()
        except Exception:
            pass
        return json.dumps({
            "workspace_id": ws_id,
            "branch": branch,
            "dirty": dirty,
            "ahead_behind": ahead_behind,
        })
    except Exception as exc:
        return json.dumps({"error": f"Git status failed: {exc}"})


registry.register(
    name="workspace.status",
    toolset="workspace",
    schema={
        "description": "Get git status for a workspace (branch, dirty, ahead/behind).",
        "parameters": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
            },
            "required": ["workspace_id"],
        },
    },
    handler=_workspace_status,
    description="Workspace git status",
    emoji="📊",
)
