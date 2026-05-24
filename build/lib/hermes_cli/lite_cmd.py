"""Lite command group for hermes CLI.

Provides ``hermes lite`` with subcommands:
    logs        — Query structured JSONL diagnostic logs
    workspaces  — Show registered lite workspaces
    profiles    — Show lite profile info
    doctor      — Run reduced health checks for hermes-lite
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


def cmd_lite(args: argparse.Namespace) -> None:
    """Dispatch ``hermes lite <subcommand>``."""
    # If no subcommand, print help
    parser = getattr(args, "_parser", None)
    if parser and not getattr(args, "lite_command", None):
        parser.print_help()
        return

    # Subcommands are wired via set_defaults(func=...) in add_lite_subparser.
    # If we reach here without a func, argparse already handled the dispatch
    # or the user gave an unknown subcommand.
    func = getattr(args, "func", None)
    if func:
        func(args)
    else:
        print("Error: unknown lite subcommand.", file=sys.stderr)
        sys.exit(1)


def _cmd_lite_logs(args: argparse.Namespace) -> None:
    """Bridge to logs_lite query handler."""
    from hermes_cli.logs_lite import run_logs_query
    run_logs_query(args)


def _cmd_lite_workspaces(args: argparse.Namespace) -> None:
    """Show registered lite workspaces."""
    ws_path = Path.home() / ".hermes-lite" / "workspaces.yaml"
    if not ws_path.exists():
        print("No workspaces registered.")
        return
    try:
        import yaml
        data = yaml.safe_load(ws_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"Could not read workspaces: {exc}")
        return

    workspaces = data.get("workspaces", data if isinstance(data, list) else [])
    if not workspaces:
        print("No workspaces registered.")
        return

    print(f"Registered workspaces ({len(workspaces)}):")
    for ws in workspaces:
        if isinstance(ws, dict):
            name = ws.get("name", " unnamed")
            path = ws.get("path", "")
            print(f"  • {name}: {path}")
        else:
            print(f"  • {ws}")


def _cmd_lite_profiles(args: argparse.Namespace) -> None:
    """Show lite profile information."""
    from hermes_cli.lite_config import load_lite_config
    from hermes_constants import get_hermes_home

    print("Profile: lite")
    print(f"HERMES_LITE_PROFILE=1")
    hermes_home = get_hermes_home()
    print(f"HERMES_HOME={hermes_home}")

    try:
        cfg = load_lite_config()
        model = cfg.get("model", "<unset>")
        print(f"Default model: {model}")
        gateways = cfg.get("enabled_gateways", [])
        print(f"Enabled gateways: {', '.join(gateways) if gateways else 'none'}")
        max_iter = cfg.get("max_iterations", "<unset>")
        print(f"Max iterations: {max_iter}")
    except Exception as exc:
        print(f"(lite-config.yaml not readable: {exc})")


def _cmd_lite_doctor(args: argparse.Namespace) -> None:
    """Run reduced hermes-lite doctor checks."""
    from hermes_cli.doctor_lite import DoctorLite
    doctor = DoctorLite(fix=getattr(args, "fix", False))
    exit_code = doctor.run()
    sys.exit(exit_code)


def add_lite_subparser(subparsers: Any) -> None:
    """Register the ``lite`` command group with argparse."""
    lite_parser = subparsers.add_parser(
        "lite",
        help="hermes-lite utilities (logs, workspaces, profiles, doctor)",
        description="lightweight hermes-lite command group for edge-device workflows",
    )
    lite_subparsers = lite_parser.add_subparsers(dest="lite_command")

    # logs
    logs_parser = lite_subparsers.add_parser(
        "logs",
        help="Query structured JSONL diagnostic logs",
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
        help="Export all streams as JSONL",
    )
    logs_parser.add_argument(
        "--exclude",
        action="append",
        metavar="STREAM",
        choices=["agent", "tools", "providers", "workspace", "security", "thermal", "api"],
        help="Exclude a stream from export (can be given multiple times)",
    )
    logs_parser.set_defaults(func=_cmd_lite_logs)

    # workspaces
    ws_parser = lite_subparsers.add_parser(
        "workspaces",
        help="Show registered lite workspaces",
    )
    ws_parser.set_defaults(func=_cmd_lite_workspaces)

    # profiles
    prof_parser = lite_subparsers.add_parser(
        "profiles",
        help="Show lite profile information",
    )
    prof_parser.set_defaults(func=_cmd_lite_profiles)

    # doctor
    doctor_parser = lite_subparsers.add_parser(
        "doctor",
        help="Run reduced health checks for hermes-lite",
    )
    doctor_parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt safe auto-remediation",
    )
    doctor_parser.set_defaults(func=_cmd_lite_doctor)

    lite_parser.set_defaults(func=cmd_lite)
