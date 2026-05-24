"""workspace.list tool implementation."""

from __future__ import annotations

import logging
from pathlib import Path

from tools.registry import registry

from ..registry import WorkspaceRegistry
from ..models import ApprovalMode

logger = logging.getLogger(__name__)


def _workspace_registry_path() -> Path:
    """Return the path to workspaces.yaml under HERMES_HOME."""
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "workspaces.yaml"


def _get_registry() -> WorkspaceRegistry:
    return WorkspaceRegistry(_workspace_registry_path())


def _workspace_list(args: dict) -> str:
    """Return all registered workspaces with metadata."""
    reg = _get_registry()
    if not reg.entries:
        return "No workspaces registered. Register one first."
    lines = []
    for e in reg.entries:
        lines.append(
            f"- {e.id}: {e.friendly_name}\n"
            f"  path: {e.path}\n"
            f"  default_branch: {e.default_branch}\n"
            f"  approval_mode: {e.approval_mode.value}\n"
            f"  allowed_prefixes: {', '.join(e.allowed_branch_prefixes)}"
        )
    return "\n".join(lines)


registry.register(
    name="workspace.list",
    toolset="workspace",
    schema={
        "description": "List all registered local repo workspaces with metadata.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    handler=_workspace_list,
    description="List registered workspaces",
    emoji="📁",
)
