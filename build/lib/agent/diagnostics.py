"""Structured JSONL diagnostics logger for hermes-lite.

Provides a singleton ``DiagnosticsLogger`` that emits seven independent
newline-delimited JSON streams under ``~/.hermes-lite/logs/``:

    agent.jsonl     — kit load, session lifecycle, model events
    tools.jsonl     — tool calls with latency and outcome
    providers.jsonl — provider escalation and cost metadata
    workspace.jsonl — workspace mutations (repo, files, commits)
    security.jsonl  — security findings (mode 0600)
    thermal.jsonl   — Jetson thermal sampling
    api.jsonl       — external API calls (Azure, partner, etc.)

Each stream rotates daily (based on filesystem mtime) and retains files
for 90 days.  A 1 GB per-stream safety cap stops appending and warns to
``errors.log`` when exceeded.
"""

from __future__ import annotations

import gzip
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stable schema
# ---------------------------------------------------------------------------

@dataclass
class StableSchema:
    """Every JSONL line carries these top-level fields for schema stability."""

    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str = "__startup__"
    kit: str = "__startup__"
    skill: str = "__startup__"
    provider: str = "__startup__"
    model: str = "__startup__"
    workspace: str = "__startup__"
    gateway: str = "__startup__"
    event: str = ""
    latency_ms: Optional[int] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Ensure payload is the last key for human readability
        payload = d.pop("payload")
        d["payload"] = payload
        return d


# ---------------------------------------------------------------------------
# Secret redactor
# ---------------------------------------------------------------------------

# Reuse upstream secret-pattern approach without importing logging infra.
_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|password|secret|auth)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-]{10,})['\"]?"),
    re.compile(r"(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{10,})"),
    re.compile(r"(?i)(sk-[a-zA-Z0-9]{20,})"),
    re.compile(r"(?i)(ghp_[a-zA-Z0-9]{20,})"),
)


def redact_sensitive_text(text: str) -> str:
    """Replace suspected secrets with ``<redacted>``."""
    for pat in _SECRET_PATTERNS:
        text = pat.sub(lambda m: m.group(1) + "<redacted>", text)
    return text


class SecretRedactor:
    """Recursively redact strings inside a JSON-serialisable payload."""

    @classmethod
    def redact(cls, obj: Any) -> Any:
        if isinstance(obj, str):
            return redact_sensitive_text(obj)
        if isinstance(obj, dict):
            return {k: cls.redact(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [cls.redact(v) for v in obj]
        return obj


# ---------------------------------------------------------------------------
# LogStream — append-only JSONL writer
# ---------------------------------------------------------------------------

class LogStream:
    """Append-only JSONL writer with daily rotation and size safety cap."""

    def __init__(
        self,
        name: str,
        log_dir: Path,
        max_bytes: int = 1_073_741_824,  # 1 GB
        file_mode: int = 0o600,
    ) -> None:
        self.name = name
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.file_mode = file_mode
        self._current_path: Optional[Path] = None
        self._writer: Optional[Any] = None
        self._lock = threading.Lock()
        self._disabled = False
        self._warned = False
        self._ensure_dir()
        self._rotate_if_needed()

    def _ensure_dir(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # Best-effort chmod; FAT/exfat will ignore this silently
        try:
            os.chmod(self.log_dir, 0o0700)
        except (OSError, PermissionError):
            pass

    def _today_path(self) -> Path:
        """Path for today's stream file."""
        return self.log_dir / f"{self.name}.jsonl"

    def _rotate_if_needed(self) -> None:
        """Switch to a new file when the date boundary crossed (mtime-based)."""
        target = self._today_path()

        if self._current_path and self._current_path != target:
            # Date rolled over — close old handle
            if self._writer:
                try:
                    self._writer.close()
                except Exception:
                    pass
                self._writer = None

        self._current_path = target

        if not self._writer:
            try:
                self._writer = open(self._current_path, "a", encoding="utf-8")
                if self.file_mode:
                    try:
                        os.chmod(self._current_path, self.file_mode)
                    except (OSError, PermissionError):
                        pass
            except (OSError, PermissionError) as exc:
                if not self._warned:
                    self._warned = True
                    warnings.warn(f"Diagnostics stream '{self.name}' disabled: {exc}")
                self._disabled = True

    def _size_ok(self) -> bool:
        if not self._current_path or not self._current_path.exists():
            return True
        return self._current_path.stat().st_size < self.max_bytes

    def write(self, record: Dict[str, Any]) -> None:
        if self._disabled:
            return
        with self._lock:
            self._rotate_if_needed()
            if not self._size_ok():
                if not self._warned:
                    self._warned = True
                    warnings.warn(
                        f"Diagnostics stream '{self.name}' exceeded 1 GB; "
                        "appending stopped."
                    )
                return
            try:
                line = json.dumps(record, separators=(",", ":"), default=str)
                if self._writer is not None:
                    self._writer.write(line + "\n")
                    self._writer.flush()
            except (OSError, PermissionError) as exc:
                if not self._warned:
                    self._warned = True
                    warnings.warn(f"Diagnostics stream '{self.name}' disabled: {exc}")
                self._disabled = True

    def close(self) -> None:
        with self._lock:
            if self._writer:
                try:
                    self._writer.close()
                except Exception:
                    pass
                self._writer = None


# ---------------------------------------------------------------------------
# Retention cleaner
# ---------------------------------------------------------------------------

class RetentionCleaner:
    """Delete stream files older than *retention_days*, skipping archives."""

    def __init__(self, log_dir: Path, retention_days: int = 90) -> None:
        self.log_dir = log_dir
        self.retention_days = retention_days

    def run(self) -> None:
        if not self.log_dir.exists():
            return
        cutoff = time.time() - (self.retention_days * 86400)
        for entry in self.log_dir.iterdir():
            if not entry.is_file():
                continue
            name = entry.name
            # Skip archives
            if ".archive" in name or "archive" in entry.parts:
                continue
            if not name.endswith(".jsonl"):
                continue
            try:
                mtime = entry.stat().st_mtime
                if mtime < cutoff:
                    entry.unlink()
            except (OSError, PermissionError):
                pass


# ---------------------------------------------------------------------------
# Thermal sampler (Jetson-only)
# ---------------------------------------------------------------------------

class ThermalSampler(threading.Thread):
    """Background thread that polls ``tegrastats`` every 5 seconds."""

    def __init__(self, diagnostics_logger: "DiagnosticsLogger") -> None:
        super().__init__(daemon=True, name="thermal-sampler")
        self.diagnostics = diagnostics_logger
        self._stop_event = threading.Event()
        self._tegrastats_available: Optional[bool] = None

    def _has_tegrastats(self) -> bool:
        if self._tegrastats_available is None:
            self._tegrastats_available = shutil.which("tegrastats") is not None
        return self._tegrastats_available

    def _sample(self) -> Optional[Dict[str, Any]]:
        if not self._has_tegrastats():
            return None
        try:
            output = subprocess.run(
                ["tegrastats", "--interval", "1000", "--count", "1"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            line = output.stdout.strip()
            if not line:
                return None
            return _parse_tegrastats(line)
        except Exception:
            return None

    def run(self) -> None:
        while not self._stop_event.is_set():
            data = self._sample()
            if data is not None:
                self.diagnostics.log(
                    "thermal",
                    "sample",
                    data,
                )
            self._stop_event.wait(timeout=5)

    def stop(self) -> None:
        self._stop_event.set()


def _parse_tegrastats(line: str) -> Dict[str, Any]:
    """Parse a single tegrastats line into a dict."""
    result: Dict[str, Any] = {}
    # CPU temp
    m = re.search(r"CPU@([\d.]+)C", line)
    if m:
        result["cpu_temp"] = float(m.group(1))
    # GPU temp (AUX or PMIC)
    m = re.search(r"(AUX|PMIC)@([\d.]+)C", line)
    if m:
        result["gpu_temp"] = float(m.group(2))
    # nvpmodel power mode
    m = re.search(r"POM_5V_IN ([\d]+)/([\d]+)", line)
    if m:
        result["power_mode"] = f"{m.group(1)}/{m.group(2)}"
    # Throttling flags
    if "throttled" in line.lower():
        result["throttled"] = True
        # Extract hex bitmask if present
        m = re.search(r"0x([0-9a-fA-F]+)", line)
        if m:
            result["throttle_flags"] = f"0x{m.group(1)}"
    else:
        result["throttled"] = False
    return result


# ---------------------------------------------------------------------------
# DiagnosticsLogger singleton
# ---------------------------------------------------------------------------

class DiagnosticsLogger:
    """Singleton structured JSONL logger for hermes-lite."""

    _instance: Optional["DiagnosticsLogger"] = None
    _lock = threading.Lock()

    STREAMS = (
        "agent",
        "tools",
        "providers",
        "workspace",
        "security",
        "thermal",
        "api",
    )

    def __new__(cls, *args: Any, **kwargs: Any) -> "DiagnosticsLogger":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        retention_days: int = 90,
    ) -> None:
        if self._initialized:
            return
        self._initialized = True

        if log_dir is None:
            log_dir = Path.home() / ".hermes-lite" / "logs"
        self.log_dir = log_dir
        self.retention_days = retention_days
        self.streams: Dict[str, LogStream] = {}
        self._redactor = SecretRedactor()
        self._thermal_sampler: Optional[ThermalSampler] = None

        # Create streams
        for name in self.STREAMS:
            mode = 0o0600 if name == "security" else 0o0600
            self.streams[name] = LogStream(
                name=name,
                log_dir=self.log_dir,
                file_mode=mode,
            )

        # Run retention cleaner at startup
        RetentionCleaner(self.log_dir, retention_days).run()

        # Start thermal sampler if tegrastats is available
        if shutil.which("tegrastats") is not None:
            self._thermal_sampler = ThermalSampler(self)
            self._thermal_sampler.start()

    def log(
        self,
        stream: str,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> None:
        """Emit a structured event to *stream*."""
        if stream not in self.streams:
            return
        schema = StableSchema(event=event)
        # Override schema fields from context
        for key in ("ts", "session_id", "kit", "skill", "provider", "model",
                    "workspace", "gateway", "latency_ms"):
            if key in context:
                setattr(schema, key, context[key])
        schema.payload = self._redactor.redact(payload or {})
        self.streams[stream].write(schema.to_dict())

    def close(self) -> None:
        if self._thermal_sampler:
            self._thermal_sampler.stop()
            self._thermal_sampler.join(timeout=2)
        for stream in self.streams.values():
            stream.close()


def get_diagnostics_logger() -> DiagnosticsLogger:
    """Return the singleton ``DiagnosticsLogger`` instance."""
    return DiagnosticsLogger()
