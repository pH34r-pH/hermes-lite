"""Pre-commit gate runner."""

from __future__ import annotations

import dataclasses
import logging
import os
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class GateResult:
    status: str  # "passed", "failed", "skipped"
    stdout: str = ""
    stderr: str = ""
    command: str = ""

    def to_dict(self):
        return {
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "command": self.command,
        }


class PreCommitGate:
    """Run a workspace-configured command before each commit."""

    def __init__(self, command: str = "") -> None:
        self.command = command.strip()

    def run(self, cwd: str) -> GateResult:
        if not self.command:
            return GateResult(status="skipped", command="")

        # If the command looks like a binary name, check it's installed
        first_word = self.command.split()[0]
        if not shutil.which(first_word):
            logger.warning("Pre-commit gate command '%s' not found; skipping", first_word)
            return GateResult(
                status="skipped",
                command=self.command,
                stderr=f"Command '{first_word}' not found in PATH",
            )

        try:
            result = subprocess.run(
                self.command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
            )
            if result.returncode == 0:
                return GateResult(status="passed", stdout=result.stdout, command=self.command)
            return GateResult(status="failed", stdout=result.stdout, stderr=result.stderr, command=self.command)
        except Exception as exc:
            return GateResult(status="failed", stderr=str(exc), command=self.command)
