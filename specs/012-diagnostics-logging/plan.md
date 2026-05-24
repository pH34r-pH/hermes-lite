# Implementation Plan: Diagnostics Logging — Structured JSONL Streams

**Branch**: `012-diagnostics-logging` | **Date**: 2026-05-24 | **Spec**: `specs/012-diagnostics-logging/spec.md`

**Input**: Feature specification from `/specs/012-diagnostics-logging/spec.md`

## Summary

Ship `agent/diagnostics.py`, a singleton structured logger that emits seven independent newline-delimited JSON streams under `~/.hermes-lite/logs/`: `agent.jsonl`, `tools.jsonl`, `providers.jsonl`, `workspace.jsonl`, `security.jsonl`, `thermal.jsonl`, and `api.jsonl`. Every line carries a stable top-level schema (`ts`, `session_id`, `kit`, `skill`, `provider`, `model`, `workspace`, `gateway`, `event`, `latency_ms`, plus a `payload` object). Each stream rotates daily and retains files for 90 days. `security.jsonl` is created with mode `0600` and excluded from generic exports. A CLI helper (`hermes-lite logs --stream <name> --since <date> --tail <n> --grep <expr>`) allows filtering and tailing. The upstream plain-text logs remain unchanged; the JSONL layer is purely additive.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Standard library (`logging`, `json`, `threading`, `pathlib`, `os`, `shutil`, `datetime`, `re`, `subprocess`), existing `hermes_logging.py` (for plain-text log warnings and `RedactingFormatter` pattern), existing `hermes_constants.py` (`get_hermes_home()`)

**Storage**: `~/.hermes-lite/logs/*.jsonl` (daily-rotated, 90-day retention), `~/.hermes-lite/logs/archive/` (excluded from retention cleanup)

**Testing**: pytest, plus integration tests requiring filesystem operations and `tegrastats` mocks

**Target Platform**: Linux (Jetson Orin Nano) for thermal sampling; gracefully degrades on non-Jetson hosts

**Project Type**: Agent internal module with CLI subcommand helper

**Performance Goals**: JSONL append latency under 5 ms per line; CLI query on 10,000-line stream returns in under 1 second; agent startup time increase under 200 ms

**Constraints**: Synchronous buffered writes flushed at end of each agent loop iteration; 1 GB per-stream daily safety cap; read-only filesystem degradation to `/dev/null` equivalent with single warning; secrets redacted via upstream `RedactingFormatter` pattern

**Scale/Scope**: One Python module (`agent/diagnostics.py`, ~400-600 LOC), small CLI helper in `hermes_cli/logs_lite.py` or `cli.py`, background thermal sampler thread, retention cleaner at startup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: `security.jsonl` created with mode `0600`; excluded from generic exports; secret redaction applied to all payloads before write.
- **Defense in Depth**: Directory created with `0700`; per-stream safety cap prevents unbounded growth; archive suffix / subdirectory preserves user-migrated files from deletion.
- **Secure Defaults**: Empty allowlist for log exports defaults to excluding `security.jsonl`; retention cleaner skips `.archive` files and `archive/` subdirectories.
- **Dependency Management**: No new external packages; fully standard-library plus existing hermes-lite infrastructure.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/012-diagnostics-logging/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
agent/
├── diagnostics.py                 # NEW — DiagnosticsLogger singleton, LogStream, StableSchema, ThermalSampler, RetentionCleaner, SecretRedactor
└── redact.py                      # EXISTING — reused for secret pattern redaction before JSONL serialization

hermes_cli/
├── logs_lite.py                   # NEW — CLI helper: hermes-lite logs --stream --since --tail --grep + export --exclude security
├── cli_output.py                  # EXISTING — check_ok / check_warn / check_fail primitives reused for CLI output
└── commands.py                    # EXISTING — register `logs` subcommand in COMMAND_REGISTRY

run_agent.py                       # EXISTING — initialize DiagnosticsLogger at startup; flush at end of loop iteration
model_tools.py                     # EXISTING — emit tool_call events to tools.jsonl via DiagnosticsLogger
cli.py                             # EXISTING — route CLI-initiated events to agent.jsonl
gateway/
├── run.py                         # EXISTING — emit gateway events to agent.jsonl / api.jsonl
└── session.py                     # EXISTING — emit session lifecycle events to agent.jsonl

hermes_logging.py                  # EXISTING — plain-text agent.log / errors.log / gateway.log retained unchanged
hermes_constants.py                # EXISTING — get_hermes_home() returns ~/.hermes-lite path
```

**Structure Decision**: Single module `agent/diagnostics.py` because all stream management, schema enforcement, rotation, retention, and redaction are tightly coupled. The CLI helper is a small separate file under `hermes_cli/` analogous to other subcommands. All consumers import a singleton `DiagnosticsLogger` instance rather than managing file handles directly.

## Complexity Tracking

> No constitution violations. The feature is a single agent module with additive logging; it does not introduce new runtime systems, network listeners, or external dependencies. It reuses existing redaction and path primitives.
