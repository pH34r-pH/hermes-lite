"""Structured change journal under ~/.hermes-lite/journal/<session-id>/<step>.json."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .precommit_gate import GateResult

logger = logging.getLogger(__name__)


class ChangeJournal:
    """Write JSON journal entries for every workspace mutation step."""

    def __init__(self, base_dir: Optional[Path | str] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path.home() / ".hermes-lite" / "journal"

    def _write(self, session_id: str, step: int, data: Dict[str, Any]) -> None:
        out = self.base_dir / session_id
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{step}.json"
        payload = {
            "step": step,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def write_success(
        self,
        session_id: str,
        step: int,
        workspace_id: str,
        diff: str,
        commit_sha: Optional[str],
        gate_result: GateResult,
        pr_url: str = "",
    ) -> None:
        self._write(session_id, step, {
            "workspace_id": workspace_id,
            "diff": diff,
            "commit_sha": commit_sha,
            "precommit_gate_result": gate_result.to_dict(),
            "pr_url": pr_url,
            "rejection_reason": None,
        })

    def write_rejection(
        self,
        session_id: str,
        step: int,
        workspace_id: str,
        diff: str,
        reason: str,
    ) -> None:
        self._write(session_id, step, {
            "workspace_id": workspace_id,
            "diff": diff,
            "commit_sha": None,
            "precommit_gate_result": None,
            "pr_url": "",
            "rejection_reason": reason,
        })

    def query_session(self, session_id: str) -> str:
        """Return a summary of files touched, lines changed, and PR links."""
        out = self.base_dir / session_id
        if not out.exists():
            return "No journal entries for this session."
        entries = sorted(out.glob("*.json"), key=lambda p: int(p.stem))
        lines = [f"Session {session_id} — {len(entries)} step(s):"]
        for e in entries:
            data = json.loads(e.read_text(encoding="utf-8"))
            ws = data.get("workspace_id", "?")
            sha = data.get("commit_sha")
            pr = data.get("pr_url", "")
            reason = data.get("rejection_reason")
            if reason:
                lines.append(f"  Step {data['step']} [{ws}]: REJECTED — {reason}")
            else:
                info = f"sha={sha or 'n/a'}"
                if pr:
                    info += f" pr={pr}"
                lines.append(f"  Step {data['step']} [{ws}]: {info}")
        return "\n".join(lines)
