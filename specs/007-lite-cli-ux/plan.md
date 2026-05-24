# Plan: Lite CLI Command Group (SPEC-007)

## Overview

Create a new `lite` CLI command group with four subcommands, integrating with the existing argparse setup in `hermes_cli/main.py`.

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `hermes_cli/lite_cmd.py` | Create | Command group wiring and dispatch |
| `hermes_cli/logs_lite.py` | Create | JSONL log query engine |
| `hermes_cli/main.py` | Modify | Register `lite` subparser and `cmd_lite` |

## Subcommand Details

### `lite logs`
- `--stream` — one of the 7 diagnostics streams (default `agent`)
- `--since` — time filter (`today`, `1h`, `30m`, ISO date)
- `--tail` — last N lines only
- `--grep` — key:value or substring match
- `--export` — dump all streams (respects `--exclude`)
- `--exclude` — skip streams during export

### `lite workspaces`
- Reads `~/.hermes-lite/workspaces.yaml`
- Prints name and path per workspace
- Handles missing file gracefully

### `lite profiles`
- Loads `lite-config.yaml` via `hermes_cli/lite_config.load_lite_config()`
- Prints profile name, default model, enabled gateways, max_iterations

### `lite doctor`
- Delegates to `hermes_cli/doctor_lite.DoctorLite` (see SPEC-014)
- Supports `--fix` flag

## Integration Points

- `_BUILTIN_SUBCOMMANDS` in `main.py` must include `"lite"` to avoid expensive plugin discovery.
- `add_lite_subparser(subparsers)` is called near the `doctor` parser registration.

## Testing

1. `python -m hermes_cli.main lite --help` renders without error.
2. `hermes lite logs --stream agent` returns JSON lines or empty.
3. `hermes lite doctor` exits 0 or 1 and prints check results.

## Rollback

Removing the `lite` subparser registration and `_BUILTIN_SUBCOMMANDS` entry restores upstream behavior.
