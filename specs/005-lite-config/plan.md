# Implementation Plan: hermes-lite Top-Level Configuration Profile

**Branch**: `005-lite-config` | **Date**: 2026-05-24 | **Spec**: `specs/005-lite-config/spec.md`

**Input**: Feature specification from `/specs/005-lite-config/spec.md`

## Summary

Create a canonical `lite-config.yaml` at the repository root that serves as the base configuration profile for hermes-lite. It pins the default model to `ollama:ministral-3:3b`, defines an escalation order (`ollama -> copilot -> openai -> claude`), declares enabled gateways (`discord`, `openwebui`, `tui`), caps the iteration budget at 25, sets a tool-call-failure budget of 3, enables prefix caching and per-session snapshots, and runs the curator in deferred-queue mode. The config subsystem must validate the merged config at startup, fail closed on removed-provider references, and log the effective configuration at `INFO` level.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: PyYAML (already core), Pydantic (already core for upstream config validation), existing `hermes_cli.config` loader

**Storage**: `lite-config.yaml` (repo root, version-controlled); `~/.hermes-lite/queue/curator.jsonl` (runtime deferred queue); `~/.hermes/config.yaml` (user overlay, existing)

**Testing**: pytest

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: CLI agent with layered configuration

**Performance Goals**: Config validation and merge completes in under 100 ms at startup; agent exits within 2 seconds when a removed provider is referenced

**Constraints**: Must support `--profile lite` CLI flag while maintaining backward compatibility when the flag is omitted; must merge configs in the order `lite-config.yaml` base → `~/.hermes/config.yaml` overlay → CLI overrides; removed-provider references in any layer must be rejected

**Scale/Scope**: One new YAML file (`lite-config.yaml`, ~80–120 lines) plus modifications to the config loader (`hermes_cli/config.py` or equivalent) and `run_agent.py` to accept profile selection; deferred-queue implementation touches `agent/curator.py` or a new queue module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Removed-provider references are rejected at config-load time rather than causing a cryptic runtime `ImportError`, preventing accidental reintroduction of deleted dependencies.
- **Defense in Depth**: `fail_closed: true` ensures that any unrecognized or removed provider/gateway reference causes immediate startup failure rather than silent omission.
- **Secure Defaults**: Default model is local (`ollama:ministral-3:3b`); cloud providers are only used after explicit escalation; deferred-queue mode prevents runaway inline curation.
- **Dependency Management**: No new heavy dependencies; config loader already uses PyYAML and Pydantic.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/005-lite-config/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
hermes_cli/
├── config.py            # UPDATE — add profile-aware merge logic, removed-provider denylist
├── commands.py          # UPDATE — add `--profile lite` CLI flag
└── plugins.py           # READ-ONLY

agent/
├── tool_surface.py      # UPDATE — read `tool_surface.removed_provider_patterns` from merged config
└── run_agent.py         # UPDATE — pass `profile` through to config loader; respect iteration budget

lite-config.yaml         # CREATE — canonical hermes-lite profile

~/.hermes-lite/queue/    # CREATE — deferred queue directory

tests/
├── unit/test_lite_config.py           # CREATE
└── integration/test_config_startup.py # CREATE
```

**Structure Decision**: Single project layout. `lite-config.yaml` lives at the repository root for visibility. The config loader in `hermes_cli/config.py` is extended with profile-aware merging and a removed-provider denylist. The deferred queue directory is created under `~/.hermes-lite/` on first run.

## Complexity Tracking

> No violations. The feature introduces one config file and extends an existing loader. No new subprojects or persistence layers introduced beyond a JSONL queue file.
