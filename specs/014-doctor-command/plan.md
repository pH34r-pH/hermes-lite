# Implementation Plan: `hermes-lite doctor` Command

**Branch**: `014-doctor-command` | **Date**: 2026-05-24 | **Spec**: `specs/014-doctor-command/spec.md`

**Input**: Feature specification from `/specs/014-doctor-command/spec.md`

## Summary

Ship a reduced `hermes-lite doctor` command that checks only the surfaces and dependencies required for the cyberdeck fork. The command lives in `hermes_cli/doctor_lite.py` and reuses upstream output primitives (`check_ok`, `check_warn`, `check_fail`, `_section`) from `hermes_cli/doctor.py` where possible. It probes Ollama reachability and model presence, checks credential presence (warning, not failure, for offline-first operation), verifies Discord and Open WebUI gateway bindings, validates TUI availability, checks `state.db` schema version, validates the skills index, reports disk space and thermal state, and verifies registered local repo workspaces. The command completes in under 10 seconds on a Jetson Orin Nano, exits 0 for warnings only, and exits non-zero for actual failures. A `--fix` flag attempts safe auto-remediation.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Standard library (`os`, `sys`, `subprocess`, `shutil`, `pathlib`, `sqlite3`, `json`, `re`), existing `hermes_cli/doctor.py` (output primitives), existing `hermes_cli/cli_output.py` (`print_success`, `print_warning`, `print_error`), existing `hermes_state.py` (schema version), existing `hermes_constants.py` (`get_hermes_home()`), existing `cli.py` or `hermes_cli/commands.py` (subcommand registration)

**Storage**: `~/.hermes-lite/lite-config.yaml` (config), `~/.hermes-lite/state.db` (schema version), `~/.hermes-lite/workspaces.yaml` (workspace registry), `skills/` and `optional-skills/` (bundle index)

**Testing**: pytest, plus integration tests requiring git repos, Ollama daemon mocks, and filesystem state manipulation

**Target Platform**: Linux (Jetson Orin Nano) for thermal checks; gracefully degrades on non-Jetson and in containers

**Project Type**: CLI subcommand with focused health checks

**Performance Goals**: Complete execution under 10 seconds on Jetson Orin Nano with no network; each individual check under 2 seconds

**Constraints**: No live API calls for credential validation (presence-only checks to avoid rate limits); no import of removed providers or platforms; container detection skips systemd/thermal checks; `ripgrep` missing degrades to `os.walk` fallback

**Scale/Scope**: One new Python module (`hermes_cli/doctor_lite.py`, ~400-600 LOC), subcommand registration, no changes to upstream `doctor.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Credential checks are presence-only; no live API calls that could leak or consume keys; workspace git auth checks use non-destructive probes (`ssh -T`, `gh auth status`).
- **Defense in Depth**: Malformed `lite-config.yaml` parsed defensively; missing Ollama reported with remediation command; state.db schema mismatch reported with migration hint.
- **Secure Defaults**: `--fix` limited to safe, idempotent operations (schema migration, `ollama pull`); does not modify user code or config files.
- **Dependency Management**: No new external packages; reuses existing CLI output primitives and hermes-lite infrastructure; `ripgrep` is optional with `os.walk` fallback.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/014-doctor-command/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
hermes_cli/
├── doctor_lite.py                 # NEW — DoctorLite command implementation
├── doctor.py                      # EXISTING — upstream doctor (~2000 LOC); output primitives reused
├── cli_output.py                  # EXISTING — print_success / print_warning / print_error primitives
├── commands.py                    # UPDATE — register `doctor` subcommand invoking DoctorLite
└── config.py                      # EXISTING — lite-config.yaml parsing; schema validation

hermes_state.py                    # EXISTING — SQLite session store; PRAGMA user_version check
hermes_constants.py                # EXISTING — get_hermes_home() path resolution
plugins/local_repo_workspace/
└── registry.py                    # EXISTING — workspaces.yaml reader (optional reuse)

gateway/platforms/discord/         # EXISTING — discord.py import check
ui-tui/                            # EXISTING — TUI entry point and compiled bundle check
skills/                            # EXISTING — skill bundle directories
optional-skills/                   # EXISTING — optional skill bundle directories
```

**Structure Decision**: Single new module `hermes_cli/doctor_lite.py` rather than modifying the upstream `doctor.py`, because the upstream file is large (~2000 LOC) and contains many checks for removed providers/platforms. Keeping the reduced doctor separate makes maintenance easier and ensures no accidental imports of removed code. The new module imports or reimplements only the output primitives it needs.

## Complexity Tracking

> No constitution violations. The feature is a single CLI subcommand that performs read-only or safe health checks; it does not introduce new runtime systems, network listeners, or external dependencies. It reuses existing state.db, config, and workspace infrastructure.
