"""workspace.locate tool implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from tools.registry import registry

from ..registry import WorkspaceRegistry

logger = logging.getLogger(__name__)


def _workspace_registry_path() -> Path:
    """Return the path to workspaces.yaml under HERMES_HOME."""
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "workspaces.yaml"


def _get_registry() -> WorkspaceRegistry:
    return WorkspaceRegistry(_workspace_registry_path())


def _workspace_locate(args: dict) -> str:
    """Resolve a natural-language target to a registered workspace."""
    reg = _get_registry()
    query = args.get("query", "").strip().lower()
    if not query:
        return json.dumps({"error": "Missing query parameter"})

    matches = []
    for e in reg.entries:
        score = 0
        if query in e.id.lower():
            score += 3
        if query in e.friendly_name.lower():
            score += 3
        if query in Path(e.path).name.lower():
            score += 2
        if e.push_remote and query in e.push_remote.lower():
            score += 1
        if score > 0:
            matches.append((score, e))

    if not matches:
        return json.dumps({"error": f"No workspace matches '{query}'. Register it first."})

    matches.sort(key=lambda x: (-x[0], x[1].id))
    top_score = matches[0][0]
    top_matches = [m for m in matches if m[0] == top_score]

    if len(top_matches) > 1:
        ids = [m[1].id for m in top_matches]
        return json.dumps({
            "error": f"Ambiguous query '{query}'. Multiple matches: {', '.join(ids)}. Please clarify."
        })

    e = top_matches[0][1]
    return json.dumps({
        "id": e.id,
        "friendly_name": e.friendly_name,
        "path": e.path,
        "default_branch": e.default_branch,
        "approval_mode": e.approval_mode.value,
        "push_remote": e.push_remote,
    })


registry.register(
    name="workspace.locate",
    toolset="workspace",
    schema={
        "description": "Locate a workspace by natural-language query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language target (name, path fragment, remote URL)"},
            },
            "required": ["query"],
        },
    },
    handler=_workspace_locate,
    description="Locate a workspace",
    emoji="🔍",
)
