"""ArXiv API rate limiter.

Token bucket enforcing 1 request per 3 seconds, jittered exponential backoff,
and a 1000-results-per-day soft cap.
"""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Dict, Optional


class ArxivRateLimiter:
    """Client-side rate limiter for the arXiv API.

    Rules:
    - 1 request per 3 seconds (token bucket)
    - Jittered exponential backoff on 503 / connection errors (base 2, max 30 s)
    - Daily 1000-result soft cap persisted to disk
    - Identifying User-Agent header
    """

    _REQUEST_INTERVAL = 3.0
    _MAX_BACKOFF = 30.0
    _DAILY_CAP = 1000

    def __init__(
        self,
        state_path: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        if state_path is None:
            state_path = os.path.expanduser(
                "~/.hermes-lite/cache/arxiv/rate-limit-state.json"
            )
        self._state_path = Path(state_path)
        self._state_path.parent.mkdir(parents=True, exist_ok=True)

        self._user_agent = user_agent or self._default_user_agent()
        self._last_request_time: float = 0.0
        self._load_state()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def user_agent(self) -> str:
        """Return the identifying User-Agent string."""
        return self._user_agent

    def wait_if_needed(self) -> None:
        """Block until at least `_REQUEST_INTERVAL` seconds have elapsed
        since the last request.
        """
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self._REQUEST_INTERVAL:
            time.sleep(self._REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.monotonic()

    def backoff(self, attempt: int) -> float:
        """Compute jittered exponential sleep time for *attempt* (0-based).
        Returns the number of seconds slept.
        """
        delay = min((2 ** attempt), self._MAX_BACKOFF)
        jitter = random.uniform(0, delay)
        final = delay + jitter
        time.sleep(final)
        return final

    def cap_reached(self) -> bool:
        """True if the daily 1000-result soft cap has been reached."""
        self._maybe_reset_daily_counter()
        return int(self._state.get("daily_count", 0)) >= self._DAILY_CAP

    def record_results(self, count: int) -> None:
        """Increment the daily result counter by *count*."""
        self._maybe_reset_daily_counter()
        current = int(self._state.get("daily_count", 0))
        self._state["daily_count"] = current + count
        self._save_state()

    def cap_warning(self) -> str:
        """Human-readable warning when the cap is reached."""
        return (
            "Daily arXiv result cap (1000) reached. "
            "Subsequent discovery will serve cached results only."
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _default_user_agent(self) -> str:
        ident = os.environ.get("CYBERDECK_ID", "hermes-lite")
        contact = os.environ.get("CYBERDECK_CONTACT", "hermes@example.com")
        return f"HermesAgent/{__version__} ({ident}; contact: {contact})"

    def _maybe_reset_daily_counter(self) -> None:
        today = time.strftime("%Y-%m-%d")
        if self._state.get("date") != today:
            self._state["date"] = today
            self._state["daily_count"] = 0

    def _load_state(self) -> None:
        default: Dict[str, object] = {
            "date": time.strftime("%Y-%m-%d"),
            "daily_count": 0,
        }
        if self._state_path.exists():
            try:
                with self._state_path.open("r", encoding="utf-8") as fh:
                    loaded = json.load(fh)
                if isinstance(loaded, dict):
                    self._state: Dict[str, object] = loaded
                else:
                    self._state = default
            except (json.JSONDecodeError, OSError):
                self._state = default
        else:
            self._state = default
        self._maybe_reset_daily_counter()

    def _save_state(self) -> None:
        try:
            with self._state_path.open("w", encoding="utf-8") as fh:
                json.dump(self._state, fh, indent=2)
        except OSError:
            pass


# N.B. __init__ imports this, so define __version__ locally to avoid circularity.
__version__ = "1.0.0"
