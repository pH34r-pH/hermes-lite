# Implementation Plan: Non-Allowlisted Gateway and Web Dashboard Cleanup

**Branch**: `001-gateway-cleanup` | **Date**: 2026-05-24 | **Spec**: `specs/001-gateway-cleanup/spec.md`

**Input**: Feature specification from `/specs/001-gateway-cleanup/spec.md`

## Summary

Delete all gateway platform modules, adapters, and identity helpers for non-allowlisted chat surfaces, retaining only Discord, TUI, and the new Open WebUI gateway. Remove the bundled web dashboard (`website/`, `web/`, `plugins/web/`) and related media/achievement plugins. Create a new `gateway/platforms/openwebui/` package that registers as an Open WebUI pipeline, maps conversation IDs to Hermes session IDs, enforces a user allowlist, and streams responses. Converge all three remaining surfaces on the same agent loop and `state.db`.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: discord.py, httpx, fastapi/uvicorn (for Open WebUI pipeline), prompt_toolkit (TUI)

**Storage**: SQLite (state.db — session ID mapping table additive, no migration required)

**Testing**: pytest, pytest-asyncio

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: CLI agent with messaging gateway

**Performance Goals**: Gateway platform loader (`python -c "from gateway.platforms import load_platforms; p=load_platforms()"`) completes successfully with only Discord, TUI, and Open WebUI

**Constraints**: Jetson disk space is limited; bundled Docusaurus/React dashboard is out of scope

**Scale/Scope**: Reduce `gateway/platforms/` from 30+ files to at most 5 (`__init__.py`, `base.py`, `discord.py`, `helpers.py`, `openwebui/`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Removing unused platform adapters shrinks attack surface; Open WebUI allowlist enforces explicit user authorization.
- **Defense in Depth**: Platform loader uses explicit allowlist rather than filesystem discovery, preventing injection of rogue adapters.
- **Secure Defaults**: Config referencing removed platforms fails closed with `ConfigurationError` at startup.
- **Dependency Management**: Deleting bundled dashboard and media plugins removes large, unmaintained dependency trees.

**Result**: PASS — cleanup aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/001-gateway-cleanup/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
gateway/
├── run.py
├── config.py
├── session.py
├── session_context.py
├── platform_registry.py
├── stream_consumer.py
└── platforms/
    ├── __init__.py
    ├── base.py
    ├── discord.py           # RETAIN
    ├── helpers.py           # Audit — excise unused helpers
    └── openwebui/           # CREATE
        ├── __init__.py
        ├── pipeline.py
        └── session_mapper.py

plugins/
├── web/                   # DELETE (or reduce to web-search-provider only)
├── spotify/               # DELETE
├── google_meet/           # DELETE
├── teams_pipeline/        # DELETE
├── hermes-achievements/   # DELETE
├── image_gen/             # Handled in spec 000
└── video_gen/             # Handled in spec 000

ui-tui/                    # RETAIN
└── src/

tui_gateway/               # RETAIN

website/                   # DELETE
web/                       # DELETE

hermes_cli/
├── plugins.py             # Remove web/achievement plugin registry imports
└── commands.py            # Update platform picker / doctor command
```

**Structure Decision**: Single project layout. Primary targets are `gateway/platforms/` (deletion + new stub), `plugins/` (deletion), and root-level `website/` / `web/` directories. Open WebUI gateway is a new package under `gateway/platforms/openwebui/`.

## Complexity Tracking

> No violations. Cleanup reduces complexity by deleting code rather than adding it.
