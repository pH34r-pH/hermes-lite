"""Workspace registry: read/write ~/.hermes-lite/workspaces.yaml."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

import yaml

from .models import WorkspaceEntry, ApprovalMode

logger = logging.getLogger(__name__)


_TEMPLATE = """# Hermes-lite Workspace Registry
# Register local repos hermes may mutate.
#
# Each entry requires:
#   id: short alphanumeric identifier
#   friendly_name: human-readable name
#   path: absolute path to repo root
#   default_branch: main (or master)
#   allowed_branch_prefixes: [hermes/]
#   approval_mode: pr-only  (auto | confirm | pr-only | read-only)
#
workspaces:
  - id: example
    friendly_name: Example Repo
    path: /home/user/repos/example
    default_branch: main
    allowed_branch_prefixes:
      - hermes/
    push_remote: git@github.com:owner/example.git
    commit_author: Hermes Lite <hermes@localhost>
    allowed_file_globs:
      - "*"
    required_reviewers: []
    approval_mode: pr-only
"""


class WorkspaceRegistry:
    """Parses and validates workspaces.yaml."""

    def __init__(self, path: Optional[Path | str] = None) -> None:
        self.path = Path(path) if path else Path.home() / ".hermes-lite" / "workspaces.yaml"
        self.entries: List[WorkspaceEntry] = []
        self._error: Optional[str] = None
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._error = (
                f"Workspace registry not found at {self.path}. "
                f"Create it from the template: {_TEMPLATE}"
            )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            template_path = self.path.parent / "workspaces.yaml.template"
            if not template_path.exists():
                template_path.write_text(_TEMPLATE, encoding="utf-8")
            return

        try:
            data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            self._error = f"Malformed workspace registry at {self.path}: {exc}"
            return

        if not isinstance(data, dict):
            self._error = f"Workspace registry must be a YAML mapping: {self.path}"
            return

        raw_list = data.get("workspaces", [])
        if not isinstance(raw_list, list):
            self._error = f"'workspaces' key must be a list: {self.path}"
            return

        for idx, raw in enumerate(raw_list):
            try:
                self.entries.append(WorkspaceEntry(**raw))
            except Exception as exc:
                logger.warning("Skipping malformed workspace entry #%d: %s", idx, exc)

    def get(self, ws_id: str) -> Optional[WorkspaceEntry]:
        for e in self.entries:
            if e.id == ws_id:
                return e
        return None

    def error(self) -> Optional[str]:
        return self._error

    def add(self, entry: WorkspaceEntry) -> None:
        if self.get(entry.id):
            raise ValueError(f"Workspace id '{entry.id}' already exists")
        self.entries.append(entry)
        self._save()

    def _save(self) -> None:
        data = {
            "workspaces": [
                {
                    "id": e.id,
                    "friendly_name": e.friendly_name,
                    "path": e.path,
                    "default_branch": e.default_branch,
                    "allowed_branch_prefixes": e.allowed_branch_prefixes,
                    "push_remote": e.push_remote,
                    "commit_author": e.commit_author,
                    "allowed_file_globs": e.allowed_file_globs,
                    "required_reviewers": e.required_reviewers,
                    "approval_mode": e.approval_mode.value,
                }
                for e in self.entries
            ]
        }
        self.path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
