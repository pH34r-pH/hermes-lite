"""Path guard: resolve inputs against workspace root, reject traversal/escapes."""

from __future__ import annotations

import fnmatch
import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class PathGuard:
    """Reject path-traversal and symlink escapes."""

    def __init__(self, root: str, allowed_globs: List[str]) -> None:
        self.root = Path(root).resolve()
        self.allowed_globs = allowed_globs or ["*"]

    def resolve(self, rel: str) -> Path:
        """Return absolute path, or raise ValueError if it escapes root."""
        target = (self.root / rel).resolve()
        try:
            target.relative_to(self.root)
        except ValueError:
            raise ValueError(f"Path '{rel}' escapes workspace root '{self.root}'") from None
        # Follow symlinks — if the resolved real path is outside root, reject
        real = target.resolve(strict=False)
        try:
            real.relative_to(self.root)
        except ValueError:
            raise ValueError(f"Path '{rel}' symlinks outside workspace root '{self.root}'") from None
        return target

    def is_allowed(self, rel: str) -> bool:
        """Check if path matches allowed file globs."""
        return any(fnmatch.fnmatch(rel, g) for g in self.allowed_globs)

    def validate_patch_paths(self, patch_text: str) -> None:
        """Parse unified diff and verify all target paths are allowed."""
        for line in patch_text.splitlines():
            if line.startswith("--- ") or line.startswith("+++ "):
                raw = line.split()[1]
                # Strip a/ or b/ prefix
                if raw.startswith("a/") or raw.startswith("b/"):
                    raw = raw[2:]
                # Ignore /dev/null
                if raw == "/dev/null":
                    continue
                # Ensure no traversal
                self.resolve(raw)
                if not self.is_allowed(raw):
                    raise ValueError(f"File '{raw}' is not in allowed_file_globs: {self.allowed_globs}")
