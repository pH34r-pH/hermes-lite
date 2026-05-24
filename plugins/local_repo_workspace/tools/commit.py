"""workspace.commit tool implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from tools.registry import registry

from ..registry import WorkspaceRegistry
from ..models import ApprovalMode
from ..lib.git_runner import GitRunner
from ..lib.branch_hygiene import BranchHygiene

logger = logging.getLogger(__name__)


def _workspace_registry_path() -> Path:
    """Return the path to workspaces.yaml under HERMES_HOME."""
    from hermes_constants import get_hermes_home
    from pathlib import Path
    return get_hermes_home() / "workspaces.yaml"


def _get_registry() -> WorkspaceRegistry:
    return WorkspaceRegistry(_workspace_registry_path())


def _workspace_commit(args: dict) -> str:
    """Create or reuse a topic branch and commit staged changes."""
    ws_id = args.get("workspace_id", "").strip()
    message = args.get("message", "").strip()
    session_id = args.get("session_id", "unknown")
    source = args.get("source", "unknown")
    author_identity = args.get("author_identity", "")

    reg = _get_registry()
    ws = reg.get(ws_id)
    if not ws:
        return json.dumps({"error": f"Workspace '{ws_id}' not found."})

    if ws.approval_mode == ApprovalMode.READ_ONLY:
        return json.dumps({"error": f"Workspace '{ws_id}' is read-only."})

    if not message:
        return json.dumps({"error": "Commit message is required."})

    runner = GitRunner(ws.path, ssh_socket=ws.ssh_agent_socket)
    hygiene = BranchHygiene(ws.default_branch, ws.allowed_branch_prefixes)

    topic_branch = hygiene.ensure_topic_branch(runner)
    hygiene.never_mutate_default(runner)

    # Schema-validated commit message
    full_message = f"{message}\n\nSource: {source}\nSession: {session_id}\n"
    if author_identity or ws.commit_author:
        full_message += f"Author-Identity: {author_identity or ws.commit_author}\n"

    try:
        runner.run(["commit", "-m", full_message])
        sha = runner.run(["rev-parse", "HEAD"]).strip()
        return json.dumps({
            "status": "committed",
            "branch": topic_branch,
            "sha": sha,
        })
    except Exception as exc:
        return json.dumps({"error": f"Commit failed: {exc}"})


registry.register(
    name="workspace.commit",
    toolset="workspace",
    schema={
        "description": "Commit staged changes on a topic branch with schema-validated message.",
        "parameters": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "message": {"type": "string", "description": "Commit summary line"},
                "session_id": {"type": "string"},
                "source": {"type": "string", "description": "Gateway source (e.g., 'discord', 'openwebui')"},
                "author_identity": {"type": "string", "description": "Override commit author identity"},
            },
            "required": ["workspace_id", "message"],
        },
    },
    handler=_workspace_commit,
    description="Commit changes on topic branch",
    emoji="💾",
)
