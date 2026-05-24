"""Branch hygiene: never mutate main/master directly."""

from __future__ import annotations

import logging
import uuid
from typing import List

from .git_runner import GitRunner

logger = logging.getLogger(__name__)

PROTECTED_BRANCHES = {"main", "master"}


class BranchHygiene:
    """Enforce topic-branch workflow."""

    def __init__(self, default_branch: str, allowed_prefixes: List[str]) -> None:
        self.default_branch = default_branch
        self.allowed_prefixes = allowed_prefixes or ["hermes/"]

    def never_mutate_default(self, runner: GitRunner) -> None:
        """Raise if the current branch is a protected default branch."""
        current = runner.run(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        if current in PROTECTED_BRANCHES:
            raise RuntimeError(
                f"Currently on protected branch '{current}'. "
                f"Switch to a topic branch before committing."
            )

    def ensure_topic_branch(self, runner: GitRunner, topic_hint: str = "") -> str:
        """Create or switch to a topic branch matching allowed prefixes."""
        current = runner.run(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        for prefix in self.allowed_prefixes:
            if current.startswith(prefix):
                return current

        # Need a new topic branch
        prefix = self.allowed_prefixes[0]
        slug = topic_hint or uuid.uuid4().hex[:8]
        branch = f"{prefix}{slug}"
        runner.run(["checkout", "-b", branch, self.default_branch])
        return branch

    def validate_branch_name(self, name: str) -> None:
        """Raise if the branch name does not match allowed prefixes."""
        if not any(name.startswith(p) for p in self.allowed_prefixes):
            raise ValueError(
                f"Branch '{name}' does not match allowed prefixes: {self.allowed_prefixes}"
            )
