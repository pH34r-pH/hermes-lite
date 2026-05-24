"""Content-addressed paper storage in the knowledge repo.

Papers live at ``~/repos/knowledge/papers/<arxiv-id>/`` with:
- ``paper.pdf``
- ``metadata.json``
- ``skim.md``
- ``extract.json``
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional


# Budget guard: refuse new fetches when knowledge repo exceeds ~60 GB
_KB_BUDGET_BYTES = 60 * 1024 * 1024 * 1024


def _dir_size(path: Path) -> int:
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
    except OSError:
        pass
    return total


class PaperStore:
    """Content-addressed storage for fetched arXiv papers."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.path.expanduser("~/repos/knowledge/papers")
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Cache / existence
    # ------------------------------------------------------------------ #

    def exists(self, arxiv_id: str) -> bool:
        """Return ``True`` if the paper directory and ``paper.pdf`` exist."""
        return (self._base / arxiv_id / "paper.pdf").exists()

    def dir_for(self, arxiv_id: str) -> Path:
        """Return the paper directory, creating it if necessary."""
        d = self._base / arxiv_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ------------------------------------------------------------------ #
    # PDF
    # ------------------------------------------------------------------ #

    def pdf_path(self, arxiv_id: str) -> Path:
        return self.dir_for(arxiv_id) / "paper.pdf"

    def write_pdf(self, arxiv_id: str, data: bytes) -> Path:
        """Write PDF bytes atomically (temp + rename)."""
        self._guard_budget()
        dest = self.pdf_path(arxiv_id)
        tmp = dest.with_suffix(".tmp")
        with tmp.open("wb") as fh:
            fh.write(data)
        tmp.rename(dest)
        return dest

    # ------------------------------------------------------------------ #
    # Metadata
    # ------------------------------------------------------------------ #

    def metadata_path(self, arxiv_id: str) -> Path:
        return self.dir_for(arxiv_id) / "metadata.json"

    def write_metadata(self, arxiv_id: str, metadata: Dict[str, Any]) -> Path:
        """Write metadata dict as JSON."""
        dest = self.metadata_path(arxiv_id)
        tmp = dest.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(metadata, fh, indent=2, ensure_ascii=False)
        tmp.rename(dest)
        return dest

    def read_metadata(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """Read metadata dict, or ``None`` if missing."""
        path = self.metadata_path(arxiv_id)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return None

    # ------------------------------------------------------------------ #
    # Skim
    # ------------------------------------------------------------------ #

    def skim_path(self, arxiv_id: str) -> Path:
        return self.dir_for(arxiv_id) / "skim.md"

    def write_skim(self, arxiv_id: str, text: str) -> Path:
        dest = self.skim_path(arxiv_id)
        tmp = dest.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            fh.write(text)
        tmp.rename(dest)
        return dest

    def read_skim(self, arxiv_id: str) -> Optional[str]:
        path = self.skim_path(arxiv_id)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return None

    # ------------------------------------------------------------------ #
    # Extract
    # ------------------------------------------------------------------ #

    def extract_path(self, arxiv_id: str) -> Path:
        return self.dir_for(arxiv_id) / "extract.json"

    def write_extract(self, arxiv_id: str, data: Dict[str, Any]) -> Path:
        dest = self.extract_path(arxiv_id)
        tmp = dest.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        tmp.rename(dest)
        return dest

    def read_extract(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        path = self.extract_path(arxiv_id)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return None

    # ------------------------------------------------------------------ #
    # Budget guard
    # ------------------------------------------------------------------ #

    def _guard_budget(self) -> None:
        size = _dir_size(self._base)
        if size > _KB_BUDGET_BYTES:
            raise OSError(
                f"Knowledge repo paper store exceeds 60 GB budget "
                f"({size / (1024**3):.1f} GB used). "
                f"Free space before fetching new papers."
            )


__all__ = ["PaperStore"]
