# SPEC-007: Lite CLI Command Group

**Status**: Complete  
**Scope**: CLI only  
**Owner**: hermes-lite

## Summary

Introduce a new top-level CLI command group `lite` that provides hermes-lite-specific utilities: querying diagnostic JSONL logs, listing registered workspaces, showing profile info, and running a reduced doctor.

## Motivation

The upstream `hermes` CLI is large and cross-platform. hermes-lite needs a curated subset of commands that are relevant to the lite profile (edge-device, Linux-only, local-Ollama-first). A dedicated `lite` group keeps these utilities namespaced and discoverable.

## User Stories

- **US-1**: As a user, I want to query structured diagnostic logs with filters so that I can debug agent behavior without parsing plain text.
- **US-2**: As a user, I want to see my registered workspaces so that I know which repos the agent can operate on.
- **US-3**: As a user, I want to verify my lite profile configuration so that I understand the active model and gateways.
- **US-4**: As a user, I want a reduced doctor that completes in under 10 seconds on Jetson so that I can quickly verify my setup.

## Requirements

1. Add `lite` as a top-level argparse subcommand in `hermes_cli/main.py`.
2. Subcommands:
   - `lite logs` — query JSONL diagnostic streams (`agent`, `tools`, `providers`, `workspace`, `security`, `thermal`, `api`). Supports `--stream`, `--since`, `--tail`, `--grep`, `--export`, `--exclude`.
   - `lite workspaces` — show registered workspaces from `~/.hermes-lite/workspaces.yaml`.
   - `lite profiles` — show lite profile info (model, gateways, max_iterations).
   - `lite doctor` — run reduced health checks (Ollama, credentials, state.db, disk, thermal, workspaces, skills, TUI, gateway bindings). Supports `--fix`.
3. Register `lite` in `_BUILTIN_SUBCOMMANDS` so plugin discovery is skipped.

## Design

- `hermes_cli/lite_cmd.py` — argparse wiring and dispatch.
- `hermes_cli/logs_lite.py` — log query engine (shared with `lite logs`).
- `hermes_cli/doctor_lite.py` — reduced doctor implementation (see SPEC-014).
- `agent/diagnostics.py` — structured logger (see SPEC-012).

## Acceptance Criteria

- `hermes lite --help` shows the four subcommands.
- `hermes lite logs --stream agent --since today --tail 20` prints valid JSON lines.
- `hermes lite doctor` completes in <10s on Jetson Orin Nano.
- `hermes lite workspaces` and `hermes lite profiles` produce human-readable output.
