"""workspace.push tool implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from tools.registry import registry

from ..registry import WorkspaceRegistry
from ..models import ApprovalMode
from ..lib.git_runner import GitRunner

logger = logging.getLogger(__name__)


def _workspace_registry_path() -> Path:
    """Return the path to workspaces.yaml under HERMES_HOME."""
    from hermes_constants import get_hermes_home
    from pathlib import Path
    return get_hermes_home() / "workspaces.yaml"


def _get_registry() -> WorkspaceRegistry:
    return WorkspaceRegistry(_workspace_registry_path())


def _workspace_push(args: dict) -> str:
    """Push topic branch to registered remote."""
    ws_id = args.get("workspace_id", "").strip()
    reg = _get_registry()
    ws = reg.get(ws_id)
    if not ws:
        return json.dumps({"error": f"Workspace '{ws_id}' not found."})

    if ws.approval_mode == ApprovalMode.READ_ONLY:
        return json.dumps({"error": f"Workspace '{ws_id}' is read-only."})

    runner = GitRunner(ws.path, ssh_socket=ws.ssh_agent_socket)

    # Verify remote URL
    try:
        actual_remote = runner.run(["remote", "get-url", "origin"]).strip()
        if ws.push_remote and actual_remote != ws.push_remote:
            return json.dumps({
                "error": f"Remote URL mismatch. Registry: {ws.push_remote}, Actual: {actual_remote}"
            })
    except Exception:
        pass

    branch = runner.run(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    remote = ws.push_remote or "origin"

    try:
        runner.run(["push", remote, branch])
        return json.dumps({"status": "pushed", "branch": branch, "remote": remote})
    except Exception as exc:
        err = str(exc)
        if "non-fast-forward" in err.lower() or " rejected " in err.lower():
            try:
                runner.run(["pull", "--rebase", remote, ws.default_branch])
                runner.run(["push", remote, branch])
                return json.dumps({"status": "pushed_after_rebase", "branch": branch, "remote": remote})
            except Exception as rebase_exc:
                return json.dumps({"error": f"Push rebase failed: {rebase_exc}"})
        if "ssh" in err.lower() or "agent" in err.lower():
            return json.dumps({"error": f"SSH agent error: {err}. Check ssh-agent socket."})
        return json.dumps({"error": f"Push failed: {err}"})


registry.register(
    name="workspace.push",
    toolset="workspace",
    schema={
        "description": "Push the current topic branch to the registered remote.",
        "parameters": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
            },
            "required": ["workspace_id"],
        },
    },
    handler=_workspace_push,
    description="Push topic branch",
    emoji="🚀",
)
