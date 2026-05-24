# Implementation Plan: Non-Allowlisted LM Provider Cleanup

**Branch**: `000-provider-cleanup` | **Date**: 2026-05-24 | **Spec**: `specs/000-provider-cleanup/spec.md`

**Input**: Feature specification from `/specs/000-provider-cleanup/spec.md`

## Summary

Delete all non-allowlisted LM provider adapter modules, transport layers, schema files, and media-generation modules from the agent surface. Update provider routing tables, credential pool, transport factory, and pyproject.toml extras so that only Ollama (new adapter in spec 002), OpenAI, GitHub Copilot, and Claude (Anthropic) remain resolvable at runtime. This shrinks the dependency tree, reduces prompt noise, and eliminates dead code paths on the cyberdeck.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: openai, httpx, anthropic (optional), agent-client-protocol (optional), pydantic, PyJWT

**Storage**: SQLite (state.db — historical session data left intact)

**Testing**: pytest, pytest-asyncio, pytest-xdist

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: CLI agent / library

**Performance Goals**: Agent startup (`python -c "import agent"`) under 5 seconds after cleanup

**Constraints**: Offline-first cyberdeck fork; no media generation; no cloud providers beyond OpenAI/Claude/Copilot

**Scale/Scope**: Reduce `agent/` directory from 100+ Python files to at most 55

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Deletion of unused providers reduces attack surface; removed OAuth paths (xAI/Grok) eliminate dangling credential refresh loops.
- **Defense in Depth**: Narrowing provider enumeration to four allowlisted entries prevents runtime injection of disallowed backends.
- **Secure Defaults**: Legacy configs referencing removed providers fail closed with `ConfigurationError` at startup.
- **Dependency Management**: Unused provider extras (`bedrock`, `azure-identity`) removed from pyproject.toml to shrink blast radius.

**Result**: PASS — cleanup aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/000-provider-cleanup/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
agent/
├── __init__.py
├── agent_init.py
├── agent_runtime_helpers.py
├── chat_completion_helpers.py
├── conversation_loop.py
├── context_compressor.py
├── credential_sources.py
├── credential_pool.py
├── plugin_llm.py
├── model_tools.py
├── model_metadata.py
├── toolsets.py
├── stream_diag.py
├── retry_utils.py
├── title_generator.py
├── anthropic_adapter.py         # RETAIN
├── copilot_acp_client.py        # RETAIN
├── chat_completion_helpers.py   # RETAIN
├── lmstudio_reasoning.py        # RETAIN until 002-ollama-adapter replaces it
├── ollama_adapter.py            # CREATED by spec 002
├── transports/
│   ├── base.py
│   ├── chat_completions.py
│   └── anthropic.py
└── (... files to delete — see tasks.md)

gateway/
├── run.py
├── config.py
├── platform_registry.py
└── platforms/
    ├── base.py
    ├── discord.py               # RETAIN
    └── helpers.py

plugins/
├── image_gen/                   # DELETE
├── video_gen/                   # DELETE
├── model-providers/             # Audit — remove non-allowlisted
├── web/                         # Handled in spec 001
└── (...)

tools/
├── image_generation_tool.py     # Remove or stub
├── video_generation_tool.py     # Remove or stub
└── (...)

hermes_cli/
├── plugins.py                   # Remove image_gen/video_gen registry imports
└── tools_config.py              # Remove image_gen/video_gen registry imports

pyproject.toml                   # Remove non-allowlisted extras
```

**Structure Decision**: Single project layout. The `agent/` directory is the primary target. Cross-cutting deletions touch `tools/`, `hermes_cli/`, `plugins/`, and `pyproject.toml`. No new subprojects introduced.

## Complexity Tracking

> No violations. Cleanup reduces complexity by deleting code rather than adding it.
