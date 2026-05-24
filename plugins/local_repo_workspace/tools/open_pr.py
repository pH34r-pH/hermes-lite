"""workspace.open_pr tool implementation."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess

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


def _workspace_open_pr(args: dict) -> str:
    """Open a PR using GitHub CLI or REST API fallback."""
    ws_id = args.get("workspace_id", "").strip()
    title = args.get("title", "").strip()
    body = args.get("body", "").strip()
    session_id = args.get("session_id", "unknown")
    gateway_link = args.get("gateway_link", "")

    reg = _get_registry()
    ws = reg.get(ws_id)
    if not ws:
        return json.dumps({"error": f"Workspace '{ws_id}' not found."})

    runner = GitRunner(ws.path, ssh_socket=ws.ssh_agent_socket)
    branch = runner.run(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    diff_stat = runner.run(["diff", "--stat", f"{ws.default_branch}...{branch}"]).strip()

    pr_body = body or f"\nDiff summary:\n```\n{diff_stat}\n```\nSession: {session_id}"
    if gateway_link:
        pr_body += f"\nOriginating gateway: {gateway_link}"

    # Try gh CLI first
    if shutil.which("gh"):
        try:
            result = subprocess.run(
                ["gh", "pr", "create", "--title", title or f"Update from {session_id}", "--body", pr_body],
                cwd=ws.path,
                capture_output=True,
                text=True,
                env={**os.environ, "GIT_DIR": os.path.join(ws.path, ".git")},
            )
            if result.returncode == 0:
                return json.dumps({"status": "pr_created", "url": result.stdout.strip()})
        except Exception:
            pass

    # Fallback to REST API
    try:
        import requests
        # Derive owner/repo from push_remote
        remote = ws.push_remote or ""
        if remote.startswith("git@github.com:"):
            repo = remote.replace("git@github.com:", "").replace(".git", "")
        elif "github.com/" in remote:
            repo = remote.split("github.com/")[-1].replace(".git", "")
        else:
            return json.dumps({"error": "Cannot derive GitHub repo from push_remote. Create PR manually."})

        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            return json.dumps({"error": "GITHUB_TOKEN not set and gh CLI failed. Create PR manually."})

        url = f"https://api.github.com/repos/{repo}/pulls"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        payload = {
            "title": title or f"Update from {session_id}",
            "body": pr_body,
            "head": branch,
            "base": ws.default_branch,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201):
            return json.dumps({"status": "pr_created", "url": resp.json().get("html_url", "")})
        return json.dumps({"error": f"GitHub API error: {resp.status_code} {resp.text}"})
    except Exception as exc:
        return json.dumps({"error": f"PR creation failed: {exc}. Create PR manually."})


registry.register(
    name="workspace.open_pr",
    toolset="workspace",
    schema={
        "description": "Open a pull request for the current topic branch.",
        "parameters": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "session_id": {"type": "string"},
                "gateway_link": {"type": "string", "description": "Link to originating gateway message"},
            },
            "required": ["workspace_id"],
        },
    },
    handler=_workspace_open_pr,
    description="Open pull request",
    emoji="🔀",
)
