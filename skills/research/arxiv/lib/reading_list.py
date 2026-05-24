"""Reading list tracking for the `research` memory profile.

Tracks the active set of papers and their processing status:
``discovered``, ``fetched``, ``skimmed``, ``extracted``, ``fetch_failed``.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional


class ReadingList:
    """Lightweight reading list backed by a JSON file.

    In production this binds to the ``research`` memory profile via the
    memory subsystem (spec 013).  The file-backed implementation ensures
    the bundle works standalone and offline.
    """

    _VALID_STATUSES = {
        "discovered",
        "fetched",
        "skimmed",
        "extracted",
        "fetch_failed",
    }

    def __init__(self, state_path: Optional[str] = None) -> None:
        if state_path is None:
            state_path = os.path.expanduser(
                "~/.hermes-lite/cache/arxiv/reading-list.json"
            )
        self._path = Path(state_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Dict[str, object]] = {}
        self._load()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def add(self, arxiv_id: str, title: str = "", **meta: object) -> None:
        """Add a paper to the reading list with status ``discovered``."""
        if arxiv_id not in self._data:
            self._data[arxiv_id] = {
                "arxiv_id": arxiv_id,
                "title": title,
                "status": "discovered",
                "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self._data[arxiv_id].update(meta)
            self._save()

    def get(self, arxiv_id: str) -> Optional[Dict[str, object]]:
        """Return the reading-list entry for *arxiv_id*, or ``None``."""
        return self._data.get(arxiv_id)

    def list_active(self) -> List[Dict[str, object]]:
        """Return all active (non-failed) entries."""
        return [
            dict(entry)
            for entry in self._data.values()
            if entry.get("status") != "fetch_failed"
        ]

    def list_all(self) -> List[Dict[str, object]]:
        """Return all entries including failures."""
        return [dict(entry) for entry in self._data.values()]

    def update_status(self, arxiv_id: str, status: str) -> bool:
        """Set the paper's status.  Returns ``True`` on success."""
        if status not in self._VALID_STATUSES:
            return False
        entry = self._data.get(arxiv_id)
        if entry is None:
            return False
        entry["status"] = status
        entry["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self._save()
        return True

    def get_cross_refs(self) -> Dict[str, List[str]]:
        """Return a map of arXiv IDs to lists of related IDs stored in
        cross-references.
        """
        refs: Dict[str, List[str]] = {}
        for arxiv_id, entry in self._data.items():
            related = entry.get("cross_refs")
            if isinstance(related, list):
                refs[arxiv_id] = [str(r) for r in related]
        return refs

    def add_cross_ref(self, arxiv_id: str, related_id: str) -> None:
        """Add a cross-reference between two papers."""
        entry = self._data.get(arxiv_id)
        if entry is None:
            return
        existing = entry.setdefault("cross_refs", [])
        if isinstance(existing, list) and related_id not in existing:
            existing.append(related_id)
            self._save()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def _load(self) -> None:
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    self._data = data
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        try:
            with self._path.open("w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2, ensure_ascii=False)
        except OSError:
            pass


__all__ = ["ReadingList"]
