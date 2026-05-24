# Implementation Plan: Tool-Surface Slimmer

**Branch**: `003-tool-surface-slimmer` | **Date**: 2026-05-24 | **Spec**: `specs/003-tool-surface-slimmer/spec.md`

**Input**: Feature specification from `/specs/003-tool-surface-slimmer/spec.md`

## Summary

Create `agent/tool_surface.py` as the canonical tool-surface filter for hermes-lite. The module consumes tool schemas from `tools.registry`, exposes only tools required by the active kit, validates every schema against a per-kit allowlist, emits a deterministic SHA-256 digest for prefix-cache keying, and refuses to load any tool whose module transitively imports a removed provider. It reduces the schema token footprint from 40+ tools to at most 12 per kit so that 3B models fit inside their context window.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: `tools.registry` (existing), `hashlib` (stdlib), `json` (stdlib), `importlib.util` / `ast` (stdlib for static import scanning), `yaml` (PyYAML for allowlist file)

**Storage**: `agent/tool_surface_allowlists.yaml` — static allowlist mapping; `lite-config.yaml` — denylist patterns for removed providers (managed by spec 005)

**Testing**: pytest

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: CLI agent / provider adapter library

**Performance Goals**: `tool_surface.get_definitions("arxiv")` returns in under 5 ms; digest computation returns in under 1 ms when cached

**Constraints**: Must not import `model_tools.py` or `run_agent.py`; must be imported by them, not the reverse. Must work when `lite-config.yaml` (spec 005) is already loadable.

**Scale/Scope**: Single module (`agent/tool_surface.py`, ~400–600 LOC) plus one YAML allowlist file and unit tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Import-scanning rejection prevents reintroduction of deleted provider dependencies that could expand attack surface or cause runtime `ImportError`.
- **Defense in Depth**: Per-kit allowlist acts as a second gate after registry discovery; unknown tools are dropped with a warning even if they register successfully.
- **Secure Defaults**: When `active_kit` is missing or unknown, the module falls back to `hermes-lite-core` rather than exposing the upstream full tool surface.
- **Dependency Management**: No new heavy dependencies; `yaml` is already required by the upstream config loader.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/003-tool-surface-slimmer/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
agent/
├── tool_surface.py              # CREATE — canonical tool-surface filter and digest emitter
├── tool_surface_allowlists.yaml # CREATE — per-kit ordered allowlists
├── system_prompt.py             # READ-ONLY — will consume digest for cache keying
├── ollama_adapter.py            # READ-ONLY — will consume filtered schemas
└── retry_utils.py               # RETAIN

tools/
├── registry.py                  # RETAIN — consumed by tool_surface.py
└── environments/                # RETAIN

tests/
├── unit/test_tool_surface.py              # CREATE
└── unit/test_tool_surface_allowlists.py   # CREATE
```

**Structure Decision**: Single project layout. The primary deliverable is `agent/tool_surface.py`. Cross-cutting consumers (`run_agent.py`, `model_tools.py`, `agent/ollama_adapter.py`) import it rather than the reverse. The allowlist file lives alongside the module for locality.

## Complexity Tracking

> No violations. The module is a single self-contained filter that reuses the existing registry. No new subprojects or persistence layers introduced.
