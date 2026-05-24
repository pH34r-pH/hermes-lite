"""workspace.diff tool implementation."""

from __future__ import annotations

import json
import logging

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


def _workspace_diff(args: dict) -> str:
    """Return unified diff of working tree or commit range."""
    ws_id = args.get("workspace_id", "").strip()
    commit_range = args.get("commit_range", "").strip()
    reg = _get_registry()
    ws = reg.get(ws_id)
    if not ws:
        return json.dumps({"error": f"Workspace '{ws_id}' not found."})

    runner = GitRunner(ws.path, ssh_socket=ws.ssh_agent_socket)
    cmd = ["diff", "--no-color"]
    if commit_range:
        cmd.append(commit_range)
    try:
        diff_text = runner.run(cmd)
        return diff_text or "(no changes)"
    except Exception as exc:
        return json.dumps({"error": f"Git diff failed: {exc}"})


registry.register(
    name="workspace.diff",
    toolset="workspace",
    schema={
        "description": "Get unified diff for a workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "commit_range": {"type": "string", "description": "Optional commit range (e.g., 'HEAD~1..HEAD')"},
            },
            "required": ["workspace_id"],
        },
    },
    handler=_workspace_diff,
    description="Workspace diff",
    emoji="📝",
)
