"""workspace.apply_patch tool implementation."""

from __future__ import annotations

import json
import logging

from tools.registry import registry

from ..registry import WorkspaceRegistry
from ..models import ApprovalMode
from ..lib.git_runner import GitRunner
from ..lib.path_guard import PathGuard
from ..lib.change_budget import ChangeBudget
from ..lib.precommit_gate import PreCommitGate
from ..lib.change_journal import ChangeJournal

logger = logging.getLogger(__name__)


def _workspace_registry_path() -> Path:
    """Return the path to workspaces.yaml under HERMES_HOME."""
    from hermes_constants import get_hermes_home
    from pathlib import Path
    return get_hermes_home() / "workspaces.yaml"


def _get_registry() -> WorkspaceRegistry:
    return WorkspaceRegistry(_workspace_registry_path())


def _workspace_apply_patch(args: dict) -> str:
    """Validate and apply a patch to a workspace."""
    ws_id = args.get("workspace_id", "").strip()
    patch_text = args.get("patch", "")
    session_id = args.get("session_id", "unknown")
    step = args.get("step", 0)

    reg = _get_registry()
    ws = reg.get(ws_id)
    if not ws:
        return json.dumps({"error": f"Workspace '{ws_id}' not found. Register it first."})

    if ws.approval_mode == ApprovalMode.READ_ONLY:
        return json.dumps({"error": f"Workspace '{ws_id}' is read-only."})

    # Path guard: ensure patch targets stay inside workspace
    guard = PathGuard(ws.path, ws.allowed_file_globs)
    try:
        guard.validate_patch_paths(patch_text)
    except ValueError as exc:
        return json.dumps({"error": f"Path guard rejected patch: {exc}"})

    # Change budget
    budget = ChangeBudget(ws.max_files, ws.max_lines)
    try:
        budget.validate_patch(patch_text)
    except ValueError as exc:
        return json.dumps({"error": f"Change budget exceeded: {exc}. Re-approval required."})

    runner = GitRunner(ws.path, ssh_socket=ws.ssh_agent_socket)

    # Check dirty tree
    try:
        dirty = runner.run(["status", "--porcelain"]).strip() != ""
        if dirty:
            return json.dumps({"error": "Working tree is dirty. Stash or commit changes first."})
    except Exception as exc:
        return json.dumps({"error": f"Git status failed: {exc}"})

    # Apply patch
    try:
        runner.run_with_stdin(["apply", "--check"], input_data=patch_text)
        runner.run_with_stdin(["apply"], input_data=patch_text)
    except Exception as exc:
        journal = ChangeJournal()
        journal.write_rejection(session_id, step, ws_id, patch_text, str(exc))
        return json.dumps({"error": f"Patch application failed: {exc}"})

    # Stage result
    try:
        runner.run(["add", "-A"])
    except Exception as exc:
        return json.dumps({"error": f"Git add failed: {exc}"})

    # Pre-commit gate
    gate = PreCommitGate(ws.precommit_gate)
    gate_result = gate.run(ws.path)

    journal = ChangeJournal()
    diff_after = runner.run(["diff", "--cached", "--no-color"])
    journal.write_success(session_id, step, ws_id, diff_after, None, gate_result)

    return json.dumps({
        "status": "applied",
        "files_changed": budget.files_changed(patch_text),
        "lines_changed": budget.lines_changed(patch_text),
        "precommit_gate": gate_result.to_dict(),
    })


registry.register(
    name="workspace.apply_patch",
    toolset="workspace",
    schema={
        "description": "Apply a unified diff patch to a workspace with budget and gate enforcement.",
        "parameters": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "patch": {"type": "string", "description": "Unified diff text"},
                "session_id": {"type": "string"},
                "step": {"type": "integer"},
            },
            "required": ["workspace_id", "patch"],
        },
    },
    handler=_workspace_apply_patch,
    description="Apply patch to workspace",
    emoji="🔧",
)
