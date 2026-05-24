# Implementation Plan: Memory Profiles per Workflow

**Branch**: `013-memory-profiles` | **Date**: 2026-05-24 | **Spec**: `specs/013-memory-profiles/spec.md`

**Input**: Feature specification from `/specs/013-memory-profiles/spec.md`

## Summary

Reuse the existing `plugins/memory/` infrastructure to add eight per-workflow memory profiles (`research`, `spec`, `dev`, `web`, `azure`, `infra`, `api`, `security`). Profile activation is a first-class kit transition: loading a kit switches the active memory namespace(s), logged to `agent.jsonl`. Composite kits bind to multiple profiles simultaneously (e.g., `azure-ops` → `azure + infra`). The `security` profile is writeable only by the `/sec` kit; all other kits receive read-only access. Profile isolation is enforced in code regardless of the underlying provider (Honcho, mem0, supermemory, retaindb). The implementation stays compatible with the existing memory-provider adapter interface so no provider-specific changes are required.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Existing `plugins/memory/__init__.py`, existing provider adapters under `plugins/memory/honcho/`, `plugins/memory/mem0/`, `plugins/memory/supermemory/`, `plugins/memory/retaindb/`, existing `agent/tool_surface.py`, existing `hermes_cli/config.py` (`cfg_get`), existing `agent/diagnostics.py` (for `profile_switch` events)

**Storage**: Provider-specific namespaces (Honcho projects, mem0 namespaces, SQLite tables prefixed with profile name), `~/.hermes-lite/lite-config.yaml` (`memory_profiles.bindings`)

**Testing**: pytest, plus integration tests requiring real or mocked memory providers

**Target Platform**: Linux (Jetson Orin Nano) for agent; memory provider backends may be local SQLite or HTTP APIs

**Project Type**: Plugin extension with namespace isolation, access control, and config-driven kit bindings

**Performance Goals**: Profile switch within 500 ms; cross-profile pollution test returns zero foreign entries; composite recall query under 2 seconds for 1,000-entry dataset; curator all-profile read under 3 seconds

**Constraints**: In-flight queries complete against the profile they were started with; invalid kit→profile mappings rejected at startup with fallback to `dev`; profile names are lower-case alphanumeric; writes to `security` from non-`/sec` kits raise `MemoryWriteDenied`

**Scale/Scope**: Modifications to `plugins/memory/__init__.py` and a new `plugins/memory/profiles.py` module (~300-400 LOC), updates to kit loader and agent loop for profile switching, config schema extension

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: `security` profile write isolation is enforced at the memory layer before any provider write; all non-`/sec` kits are blocked with `MemoryWriteDenied`.
- **Defense in Depth**: Profile isolation enforced in code even if the underlying provider does not natively support namespaces; provider-namespace mapping ensures no accidental cross-profile leakage.
- **Secure Defaults**: Default profile at startup is `dev`; invalid config mappings fall back to `dev` with a warning; unknown kits default to `dev`.
- **Dependency Management**: No new external packages; reuses existing memory-provider adapter interface.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/013-memory-profiles/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
plugins/memory/
├── __init__.py                     # UPDATE — add profile-aware load/save wrappers, ProviderNamespaceMap, discover_memory_providers update
├── profiles.py                     # NEW — MemoryProfile, ProfileBinding, ProfileSwitchEvent, SecurityProfileGuard, CompositeRecallQuery
├── honcho/
│   └── __init__.py                 # EXISTING — no changes required (adapter interface compatible)
├── mem0/
│   └── __init__.py                 # EXISTING — no changes required
├── supermemory/
│   └── __init__.py                 # EXISTING — no changes required
├── retaindb/
│   └── __init__.py                 # EXISTING — no changes required
└── ...                             # EXISTING — other provider adapters unchanged

agent/
├── tool_surface.py                 # UPDATE — invoke profile switch on kit load/unload
└── diagnostics.py                  # EXISTING — emit profile_switch events to agent.jsonl

run_agent.py                        # EXISTING — pass active profile set into memory calls; flush in-flight queries on switch
hermes_cli/
├── config.py                       # EXISTING — validate memory_profiles.bindings schema
└── commands.py                     # UPDATE — register `memory --profile` and `memory --list-profiles` subcommands

~/.hermes-lite/lite-config.yaml     # UPDATE — memory_profiles.bindings section
```

**Structure Decision**: A single new module `plugins/memory/profiles.py` rather than splitting per profile, because all eight profiles share the same access-control, binding, and recall-merging logic. `plugins/memory/__init__.py` is updated to wrap provider calls with profile namespace translation and security guard checks. The existing provider subdirectories require no modifications because the adapter interface is preserved.

## Complexity Tracking

> No constitution violations. The feature adds one module and updates the memory plugin init to wrap existing provider calls, rather than introducing new runtime systems. Tool surface is unchanged — memory is an internal layer.
