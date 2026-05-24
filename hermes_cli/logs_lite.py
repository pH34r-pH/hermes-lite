"""CLI helper for querying hermes-lite structured JSONL log streams.

Implements ``hermes lite logs`` with filters for stream, tail, since, and grep.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


def _resolve_log_dir() -> Path:
    """Return the canonical diagnostics log directory."""
    return Path.home() / ".hermes-lite" / "logs"


def _parse_since(since: str | None) -> Optional[datetime]:
    """Parse a --since string (e.g. 'today', '1h', '30m', '2025-05-24') into UTC datetime."""
    if since is None:
        return None
    since = since.strip().lower()
    if since == "today":
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Relative durations
    if since.endswith("h"):
        try:
            hours = int(since[:-1])
            return datetime.now(timezone.utc) - timedelta(hours=hours)
        except ValueError:
            pass
    if since.endswith("m"):
        try:
            minutes = int(since[:-1])
            return datetime.now(timezone.utc) - timedelta(minutes=minutes)
        except ValueError:
            pass
    if since.endswith("d"):
        try:
            days = int(since[:-1])
            return datetime.now(timezone.utc) - timedelta(days=days)
        except ValueError:
            pass
    # ISO date
    try:
        return datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    return None


def _line_matches(line_obj: Dict[str, Any], grep: str | None) -> bool:
    """Return True when *line_obj* contains the grep key:value pair."""
    if not grep:
        return True
    if ":" not in grep:
        # Simple substring search across the JSON representation
        return grep.lower() in json.dumps(line_obj).lower()
    key, val = grep.split(":", 1)
    key = key.strip()
    val = val.strip()
    # Nested key support (e.g. payload.outcome)
    current: Any = line_obj
    for part in key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False
    return str(current).lower() == val.lower()


def _iter_lines(stream_path: Path, since_dt: Optional[datetime]) -> Iterator[Dict[str, Any]]:
    """Yield JSONL records from *stream_path*, optionally filtered by timestamp."""
    open_fn = gzip.open if str(stream_path).endswith(".gz") else open
    try:
        with open_fn(stream_path, "rt", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if since_dt is not None:
                    ts_str = obj.get("ts")
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str)
                            if ts < since_dt:
                                continue
                        except ValueError:
                            pass
                yield obj
    except (OSError, FileNotFoundError):
        return


def _export_stream(
    stream_name: str,
    log_dir: Path,
    since_dt: Optional[datetime],
    grep: str | None,
    exclude: bool = False,
) -> Iterator[str]:
    """Yield JSONL text lines for a single stream."""
    if exclude:
        return
    stream_path = log_dir / f"{stream_name}.jsonl"
    for obj in _iter_lines(stream_path, since_dt):
        if _line_matches(obj, grep):
            yield json.dumps(obj, separators=(",", ":"), default=str)


def run_logs_query(args: argparse.Namespace) -> None:
    """Execute a ``lite logs`` query and print results."""
    log_dir = _resolve_log_dir()
    stream = getattr(args, "stream", "agent") or "agent"
    since = getattr(args, "since", None)
    tail = getattr(args, "tail", 0)
    grep = getattr(args, "grep", None)
    export = getattr(args, "export", False)
    exclude = getattr(args, "exclude", [])
    if exclude is None:
        exclude = []

    since_dt = _parse_since(since)

    if export:
        # Export all streams (or all except excluded)
        all_streams = ["agent", "tools", "providers", "workspace", "security", "thermal", "api"]
        excluded_set = set(exclude)
        for sname in all_streams:
            if sname in excluded_set:
                continue
            for line in _export_stream(sname, log_dir, since_dt, grep, exclude=False):
                print(line)
        return

    # Single stream query
    stream_path = log_dir / f"{stream}.jsonl"
    lines: List[str] = []
    for obj in _iter_lines(stream_path, since_dt):
        if _line_matches(obj, grep):
            lines.append(json.dumps(obj, separators=(",", ":"), default=str))

    if tail and tail > 0:
        lines = lines[-tail:]

    for line in lines:
        print(line)


def add_logs_subparser(subparsers: Any) -> None:
    """Register ``logs`` subcommand under ``lite``."""
    logs_parser = subparsers.add_parser(
        "logs",
        help="Query structured JSONL diagnostic logs",
        description=(
            "View and filter hermes-lite structured JSONL log streams. "
            "Each stream is a daily-rotated newline-delimited JSON file."
        ),
    )
    logs_parser.add_argument(
        "--stream",
        default="agent",
        choices=["agent", "tools", "providers", "workspace", "security", "thermal", "api"],
        help="Which log stream to query (default: agent)",
    )
    logs_parser.add_argument(
        "--since",
        metavar="WHEN",
        help="Filter by time: today, 1h, 30m, 1d, or ISO date",
    )
    logs_parser.add_argument(
        "--tail",
        type=int,
        metavar="N",
        help="Show only the last N lines",
    )
    logs_parser.add_argument(
        "--grep",
        metavar="FILTER",
        help="Filter by key:value or substring match",
    )
    logs_parser.add_argument(
        "--export",
        action="store_true",
        help="Export all streams as JSONL (respects --exclude)",
    )
    logs_parser.add_argument(
        "--exclude",
        action="append",
        metavar="STREAM",
        choices=["agent", "tools", "providers", "workspace", "security", "thermal", "api"],
        help="Exclude a stream from export (can be given multiple times)",
    )
    logs_parser.set_defaults(func=run_logs_query)
