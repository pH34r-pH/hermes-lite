"""Git subprocess wrapper with environment scrubbing."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import List, Optional

logger = logging.getLogger(__name__)


class GitRunner:
    """Run git commands with scrubbed environment and per-workspace overrides."""

    def __init__(self, cwd: str, ssh_socket: str = "") -> None:
        self.cwd = cwd
        self.ssh_socket = ssh_socket

    def _env(self) -> dict:
        """Return a scrubbed environment with only safe variables."""
        keep = {
            "PATH", "HOME", "USER", "SHELL", "LANG", "LC_ALL",
            "TERM", "EDITOR", "VISUAL",
        }
        env = {k: v for k, v in os.environ.items() if k in keep or not k.startswith("GIT_")}
        if self.ssh_socket:
            env["SSH_AUTH_SOCK"] = self.ssh_socket
        # Working-copy-only config
        env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        env["GIT_CONFIG_SYSTEM"] = "/dev/null"
        return env

    def run(self, args: List[str]) -> str:
        cmd = ["git", "-C", self.cwd] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=self._env(),
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"git {' '.join(args)} failed: {exc.stderr}") from exc

    def run_with_stdin(self, args: List[str], input_data: str) -> str:
        cmd = ["git", "-C", self.cwd] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=self._env(),
                input=input_data,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"git {' '.join(args)} failed: {exc.stderr}") from exc
