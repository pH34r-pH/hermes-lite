"""Reduced doctor command for hermes-lite.

Checks: Ollama, credentials, Discord, OpenWebUI, TUI, state.db, skills, disk,
thermal, workspaces.  Designed to complete in under 10 seconds on Jetson.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Output primitives
# ---------------------------------------------------------------------------

def check_ok(text: str, detail: str = "") -> None:
    print(f"  \033[32m✓\033[0m {text}" + (f" \033[2m{detail}\033[0m" if detail else ""))


def check_warn(text: str, detail: str = "") -> None:
    print(f"  \033[33m⚠\033[0m {text}" + (f" \033[2m{detail}\033[0m" if detail else ""))


def check_fail(text: str, detail: str = "") -> None:
    print(f"  \033[31m✗\033[0m {text}" + (f" \033[2m{detail}\033[0m" if detail else ""))


def check_info(text: str) -> None:
    print(f"    \033[36m→\033[0m {text}")


def _section(title: str) -> None:
    print()
    print(f"\033[1;36m◆ {title}\033[0m")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_container() -> bool:
    """Detect if running inside a container."""
    return (Path("/.dockerenv").exists() or
            Path("/proc/1/cgroup").exists() and "container" in Path("/proc/1/cgroup").read_text(encoding="utf-8"))


def _has_cmd(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _run(cmd: list[str], timeout: float = 5, **kwargs: Any) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)


# ---------------------------------------------------------------------------
# Ollama probe
# ---------------------------------------------------------------------------

class OllamaProbe:
    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        """Return (status, message, remediation)."""
        try:
            r = _run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                      "http://127.0.0.1:11434"], timeout=3)
            if r.stdout.strip() != "200":
                return ("fail", "Ollama daemon not reachable at 127.0.0.1:11434",
                        "sudo systemctl start ollama  (or  ollama serve  in another terminal)")
        except Exception as exc:
            return ("fail", f"Ollama health check failed: {exc}",
                    "sudo systemctl start ollama")

        # Verify default model presence
        try:
            r = _run(["ollama", "list"], timeout=5)
            if r.returncode != 0:
                return ("warn", "Ollama daemon up but `ollama list` failed", None)
            lines = r.stdout.strip().splitlines()
            if len(lines) <= 1:
                return ("warn", "Ollama daemon up but no models downloaded",
                        "ollama pull ministral-3:3b")
            return ("ok", f"Ollama daemon up ({len(lines)-1} model(s))", None)
        except Exception as exc:
            return ("warn", f"Ollama daemon up but probe failed: {exc}", None)


# ---------------------------------------------------------------------------
# Credential presence check
# ---------------------------------------------------------------------------

class CredentialPresenceCheck:
    _ENV_VARS = (
        "OPENAI_API_KEY",
        "GITHUB_COPILOT_TOKEN",
        "ANTHROPIC_API_KEY",
    )

    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        missing: List[str] = []
        present: List[str] = []
        for var in self._ENV_VARS:
            if os.getenv(var):
                present.append(var)
            else:
                missing.append(var)
        if not present:
            return ("warn", "No API credentials found in environment",
                    "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in ~/.hermes/.env")
        if missing:
            return ("ok", f"Credentials present: {', '.join(present)}; missing: {', '.join(missing)}", None)
        return ("ok", f"All checked credentials present ({len(present)})", None)


# ---------------------------------------------------------------------------
# State DB schema check
# ---------------------------------------------------------------------------

class StateDbSchemaCheck:
    EXPECTED_VERSION = 1

    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        db_path = Path.home() / ".hermes-lite" / "state.db"
        if not db_path.exists():
            return ("warn", "state.db does not exist yet (will be created on first run)", None)
        try:
            r = _run(["sqlite3", str(db_path), "PRAGMA user_version;"], timeout=3)
            version = int(r.stdout.strip()) if r.returncode == 0 else 0
            if version == self.EXPECTED_VERSION:
                return ("ok", f"state.db schema version {version}", None)
            if fix:
                _run(["sqlite3", str(db_path),
                      f"PRAGMA user_version = {self.EXPECTED_VERSION};"], timeout=3)
                return ("ok", f"state.db schema migrated to version {self.EXPECTED_VERSION}", None)
            return ("fail", f"state.db schema version {version} (expected {self.EXPECTED_VERSION})",
                    f"sqlite3 {db_path} 'PRAGMA user_version = {self.EXPECTED_VERSION};'")
        except Exception as exc:
            return ("warn", f"Could not read state.db: {exc}", None)


# ---------------------------------------------------------------------------
# Disk space check
# ---------------------------------------------------------------------------

class DiskSpaceCheck:
    WARN_GB = 10

    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        path = Path.home() / ".hermes-lite"
        path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(path)
        free_gb = usage.free / (1024 ** 3)
        if free_gb < self.WARN_GB:
            return ("warn", f"Disk space low: {free_gb:.1f} GB free (below {self.WARN_GB} GB)",
                    "Free up disk space or expand the filesystem")
        return ("ok", f"Disk space OK: {free_gb:.1f} GB free", None)


# ---------------------------------------------------------------------------
# Thermal check
# ---------------------------------------------------------------------------

class ThermalCheck:
    ALARM_C = 85

    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        if _is_container():
            return ("ok", "Thermal check skipped in container", None)
        if not _has_cmd("tegrastats"):
            return ("ok", "Thermal check skipped (non-Jetson host)", None)
        try:
            r = _run(["tegrastats", "--interval", "1000", "--count", "1"], timeout=3)
            line = r.stdout.strip()
            cpu_temp = self._extract(line, r"CPU@([\d.]+)C")
            gpu_temp = self._extract(line, r"(?:AUX|PMIC)@([\d.]+)C")
            power_mode = self._extract(line, r"POM_5V_IN (\d+/\d+)")
            temps = []
            if cpu_temp is not None:
                temps.append(f"CPU {cpu_temp}°C")
            if gpu_temp is not None:
                temps.append(f"GPU {gpu_temp}°C")
            temp_str = ", ".join(temps) if temps else "(no temps parsed)"
            if cpu_temp is not None and cpu_temp > self.ALARM_C:
                return ("warn", f"CPU thermal alarm: {cpu_temp}°C (threshold {self.ALARM_C}°C)",
                        "Consider switching to 25 W power mode or adding cooling")
            if gpu_temp is not None and gpu_temp > self.ALARM_C:
                return ("warn", f"GPU thermal alarm: {gpu_temp}°C (threshold {self.ALARM_C}°C)",
                        "Consider switching to 25 W power mode or adding cooling")
            mode_str = f" [{power_mode}]" if power_mode else ""
            return ("ok", f"Thermal OK: {temp_str}{mode_str}", None)
        except Exception as exc:
            return ("warn", f"Thermal check failed: {exc}", None)

    @staticmethod
    def _extract(line: str, pattern: str) -> Optional[str]:
        import re
        m = re.search(pattern, line)
        return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Workspace health check
# ---------------------------------------------------------------------------

class WorkspaceHealthCheck:
    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        ws_path = Path.home() / ".hermes-lite" / "workspaces.yaml"
        if not ws_path.exists():
            return ("ok", "No workspaces registered", None)
        try:
            import yaml
            data = yaml.safe_load(ws_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            return ("warn", f"Could not parse workspaces.yaml: {exc}", None)
        workspaces = data.get("workspaces", data if isinstance(data, list) else [])
        if not workspaces:
            return ("ok", "No workspaces registered", None)
        missing: List[str] = []
        ok: List[str] = []
        for ws in workspaces:
            if isinstance(ws, dict):
                name = ws.get("name", "unnamed")
                wpath = ws.get("path", "")
            else:
                name = str(ws)
                wpath = str(ws)
            if wpath and Path(wpath).exists():
                ok.append(name)
            else:
                missing.append(name)
        if missing:
            return ("fail", f"Workspace paths missing: {', '.join(missing)}",
                    "Clone or recreate the missing workspace directories")
        return ("ok", f"All {len(ok)} workspace(s) present", None)


# ---------------------------------------------------------------------------
# Skills index check
# ---------------------------------------------------------------------------

class SkillsIndexCheck:
    REQUIRED_BUNDLES = (
        "research",
        "spec",
        "dev",
        "web",
        "azure",
        "infra",
        "api",
        "security",
    )

    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        repo_root = Path(__file__).parent.parent.resolve()
        skills_dir = repo_root / "skills"
        optional_dir = repo_root / "optional-skills"
        missing: List[str] = []
        found: List[str] = []
        for bundle in self.REQUIRED_BUNDLES:
            if (skills_dir / bundle).exists() or (optional_dir / bundle).exists():
                found.append(bundle)
            else:
                missing.append(bundle)
        if missing:
            return ("fail", f"Missing skill bundles: {', '.join(missing)}",
                    "Ensure the repo is fully checked out")
        return ("ok", f"All {len(found)} required skill bundles present", None)


# ---------------------------------------------------------------------------
# TUI availability check
# ---------------------------------------------------------------------------

class TuiAvailabilityCheck:
    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        repo_root = Path(__file__).parent.parent.resolve()
        tui_dir = repo_root / "ui-tui"
        if not tui_dir.exists():
            return ("warn", "ui-tui/ directory not found", None)
        pkg_json = tui_dir / "package.json"
        if not pkg_json.exists():
            return ("warn", "ui-tui/package.json missing", "npm install && npm run build in ui-tui/")
        node_modules = tui_dir / "node_modules"
        if not node_modules.exists():
            return ("warn", "ui-tui dependencies not installed", "npm install in ui-tui/")
        # Check for compiled bundle
        bundle = tui_dir / "dist" / "index.js"
        if not bundle.exists():
            return ("warn", "ui-tui compiled bundle missing", "npm run build in ui-tui/")
        return ("ok", "TUI dependencies and bundle present", None)


# ---------------------------------------------------------------------------
# Gateway binding check
# ---------------------------------------------------------------------------

class GatewayBindingCheck:
    def check(self, fix: bool = False) -> Tuple[str, str, Optional[str]]:
        # Load lite config to see which gateways are enabled
        try:
            from hermes_cli.lite_config import load_lite_config
            cfg = load_lite_config()
            enabled = set(g.lower() for g in cfg.get("enabled_gateways", []))
        except Exception:
            enabled = {"discord", "openwebui", "tui"}

        issues: List[str] = []

        if "discord" in enabled:
            try:
                import discord  # noqa: F401
                if not os.getenv("DISCORD_BOT_TOKEN"):
                    issues.append("Discord gateway enabled but DISCORD_BOT_TOKEN not set")
            except ImportError:
                issues.append("Discord gateway enabled but discord.py not installed")

        if "openwebui" in enabled:
            openwebui_module = Path(__file__).parent.parent / "gateway" / "platforms" / "openwebui.py"
            if not openwebui_module.exists():
                issues.append("Open WebUI adapter missing")
            # Pipeline adapter import check
            pipe_mod = Path(__file__).parent.parent / "gateway" / "platforms" / "openwebui.py"
            if pipe_mod.exists():
                try:
                    spec = __import__("importlib.util").util.spec_from_file_location(
                        "openwebui_adapter", str(pipe_mod)
                    )
                    if spec and spec.loader:
                        mod = __import__("importlib.util").util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                except Exception as exc:
                    issues.append(f"Open WebUI pipeline adapter not importable: {exc}")

        if issues:
            return ("warn", "; ".join(issues), "Check gateway configuration and env vars")
        return ("ok", "Gateway bindings OK", None)


# ---------------------------------------------------------------------------
# DoctorLite orchestration
# ---------------------------------------------------------------------------

class DoctorLite:
    def __init__(self, fix: bool = False) -> None:
        self.fix = fix
        self.warnings = 0
        self.failures = 0

    def run(self) -> int:
        print()
        print("\033[36m┌─────────────────────────────────────────────────────────┐\033[0m")
        print("\033[36m│              🩺 Hermes Lite Doctor                       │\033[0m")
        print("\033[36m└─────────────────────────────────────────────────────────┘\033[0m")

        checks = [
            ("Ollama", OllamaProbe()),
            ("Credentials", CredentialPresenceCheck()),
            ("State DB", StateDbSchemaCheck()),
            ("Disk Space", DiskSpaceCheck()),
            ("Thermal", ThermalCheck()),
            ("Workspaces", WorkspaceHealthCheck()),
            ("Skills Index", SkillsIndexCheck()),
            ("TUI", TuiAvailabilityCheck()),
            ("Gateway Bindings", GatewayBindingCheck()),
        ]

        for title, checker in checks:
            _section(title)
            status, message, remediation = checker.check(fix=self.fix)
            if status == "ok":
                check_ok(message)
            elif status == "warn":
                check_warn(message)
                self.warnings += 1
                if remediation:
                    check_info(remediation)
            else:
                check_fail(message)
                self.failures += 1
                if remediation:
                    check_info(remediation)

        print()
        print("─" * 59)
        if self.failures:
            print(f"\033[31m{self.failures} failure(s), {self.warnings} warning(s)\033[0m")
            return 1
        if self.warnings:
            print(f"\033[33m{self.warnings} warning(s)\033[0m")
            return 0
        print("\033[32mAll checks passed.\033[0m")
        return 0
