"""Per-directive change budget tracker."""

from __future__ import annotations

import re
from typing import Optional


class ChangeBudget:
    """Enforce max files and max lines per patch."""

    def __init__(self, max_files: int = 2, max_lines: int = 30) -> None:
        self.max_files = max_files
        self.max_lines = max_lines

    @staticmethod
    def files_changed(patch_text: str) -> int:
        """Count number of files touched by a unified diff."""
        files = set()
        for line in patch_text.splitlines():
            if line.startswith("--- a/") or line.startswith("--- "):
                files.add(line.split()[1].lstrip("a/"))
            elif line.startswith("+++ b/") or line.startswith("+++ "):
                files.add(line.split()[1].lstrip("b/"))
        return len(files)

    @staticmethod
    def lines_changed(patch_text: str) -> int:
        """Count added+deleted lines in a unified diff."""
        count = 0
        for line in patch_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                count += 1
            elif line.startswith("-") and not line.startswith("---"):
                count += 1
        return count

    def validate_patch(self, patch_text: str) -> None:
        """Raise ValueError if the patch exceeds budget."""
        files = self.files_changed(patch_text)
        lines = self.lines_changed(patch_text)
        if files > self.max_files:
            raise ValueError(f"Patch touches {files} files, max allowed is {self.max_files}")
        if lines > self.max_lines:
            raise ValueError(f"Patch changes {lines} lines, max allowed is {self.max_lines}")
