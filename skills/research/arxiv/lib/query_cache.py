"""ArXiv query cache with TTL and offline stale returns.

Stores gzip-compressed Atom/XML feed responses under
`~/.hermes-lite/cache/arxiv/` with a 24-hour expiration.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Tuple


class ArxivQueryCache:
    """TTL-based disk cache for arXiv discovery queries.

    - 24-hour expiration per query key
    - gzip-compressed storage
    - Offline mode returns stale entries with a warning flag
    """

    _TTL_SECONDS = 24 * 3600  # 24 hours

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.hermes-lite/cache/arxiv")
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def get(
        self, query: str, max_results: int = 10
    ) -> Tuple[Optional[str], bool]:
        """Return cached feed XML (or None) and a stale flag.

        If the entry is within TTL, ``stale`` is ``False``.
        If the entry exists but is expired, it is still returned with
        ``stale=True`` so that offline callers have something to show.
        """
        path = self._path(query, max_results)
        meta_path = path.with_suffix(".json")
        if not path.exists() or not meta_path.exists():
            return None, False

        try:
            with meta_path.open("r", encoding="utf-8") as fh:
                meta = json.load(fh)
            timestamp: float = meta.get("timestamp", 0)
        except (json.JSONDecodeError, OSError):
            return None, False

        age = time.monotonic() - timestamp
        stale = age > self._TTL_SECONDS

        try:
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                data = fh.read()
        except (OSError, gzip.BadGzipFile):
            return None, False

        return data, stale

    def set(self, query: str, max_results: int, feed_xml: str) -> None:
        """Store *feed_xml* under the query key."""
        path = self._path(query, max_results)
        meta_path = path.with_suffix(".json")
        try:
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                fh.write(feed_xml)
            with meta_path.open("w", encoding="utf-8") as fh:
                json.dump({"timestamp": time.monotonic()}, fh)
        except OSError:
            pass

    def clear(self) -> int:
        """Remove all cached entries. Returns number of files removed."""
        count = 0
        for f in self._cache_dir.iterdir():
            if f.is_file() and (f.suffix == ".gz" or f.suffix == ".json"):
                try:
                    f.unlink()
                    count += 1
                except OSError:
                    pass
        return count

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _path(self, query: str, max_results: int) -> Path:
        key = f"{query.strip().lower()}|{max_results}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return self._cache_dir / f"{digest}.xml.gz"
