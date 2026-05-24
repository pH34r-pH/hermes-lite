"""Workspace model dataclasses and enums."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ApprovalMode(Enum):
    AUTO = "auto"
    CONFIRM = "confirm"
    PR_ONLY = "pr-only"
    READ_ONLY = "read-only"


@dataclass
class WorkspaceEntry:
    """A single workspace registry entry."""

    id: str
    friendly_name: str
    path: str
    default_branch: str = "main"
    allowed_branch_prefixes: List[str] = field(default_factory=lambda: ["hermes/"])
    push_remote: str = ""
    commit_author: str = ""
    allowed_file_globs: List[str] = field(default_factory=lambda: ["*"])
    required_reviewers: List[str] = field(default_factory=list)
    approval_mode: ApprovalMode = ApprovalMode.PR_ONLY
    ssh_agent_socket: str = ""
    precommit_gate: str = ""
    max_files: int = 2
    max_lines: int = 30

    def __post_init__(self):
        if not self.id or not re.match(r"^[a-zA-Z0-9_\-]+$", self.id):
            raise ValueError(f"Invalid workspace id: {self.id}")
        p = Path(self.path)
        if not p.is_absolute():
            raise ValueError(f"Workspace path must be absolute: {self.path}")
        if not self.default_branch:
            raise ValueError("default_branch must not be empty")
        if isinstance(self.approval_mode, str):
            self.approval_mode = ApprovalMode(self.approval_mode)
