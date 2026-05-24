# Implementation Plan: Ollama Adapter

**Branch**: `002-ollama-adapter` | **Date**: 2026-05-24 | **Spec**: `specs/002-ollama-adapter/spec.md`

**Input**: Feature specification from `/specs/002-ollama-adapter/spec.md`

## Summary

Create `agent/ollama_adapter.py` as the canonical local provider adapter for the cyberdeck. The adapter sends requests directly to Ollama's `/api/chat` and `/api/generate` endpoints, supports function-calling via JSON-schema prompts pre-validated against the active toolset, exposes a token-budget estimator using `tiktoken` heuristics (with character-based fallback), and streams reasoning plus tool-call deltas through the existing `agent/stream_diag.py` plumbing. After integration, the adapter replaces `agent/lmstudio_reasoning.py` as the default local provider, and all references to `lmstudio_reasoning.py` are removed.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: httpx (already core), tiktoken (optional — lazy-install or graceful fallback), pydantic

**Storage**: N/A (stateless per request; context window tracked in-memory)

**Testing**: pytest, pytest-asyncio

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: CLI agent / provider adapter library

**Performance Goals**: Non-streaming chat request to local Ollama with `ministral-3:3b` returns a response of at least 10 tokens in under 10 seconds; first streaming token within 2 seconds of HTTP request

**Constraints**: Offline-first; 8 GB device; model-agnostic (swapping models is a config change); no retry layer (handled by `agent/retry_utils.py`)

**Scale/Scope**: Single adapter file (~500–1000 LOC) plus integration touches in `agent/agent_init.py`, `agent/chat_completion_helpers.py`, and `run_agent.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Adapter validates tool names against the active toolset before yielding tool-call events, preventing hallucinated tool invocations.
- **Defense in Depth**: Token-budget estimator pre-empts context overflow that could degrade model behavior into repetitive or leaking output.
- **Secure Defaults**: Configurable `base_url` defaults to loopback (`127.0.0.1:11434`); no remote exposure by default.
- **Dependency Management**: `tiktoken` is optional; absence is handled gracefully with a one-time warning and character-based fallback.

**Result**: PASS — adapter design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/002-ollama-adapter/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
agent/
├── ollama_adapter.py         # CREATE — canonical Ollama provider adapter
├── lmstudio_reasoning.py     # DELETE after integration (retained until T058)
├── stream_diag.py            # RETAIN — streaming plumbing reused verbatim
├── retry_utils.py            # RETAIN — transient HTTP errors handled here
├── context_compressor.py     # RETAIN — triggered when token budget > 80%
├── model_metadata.py         # RETAIN — context window lookups
├── agent_init.py             # UPDATE — add ollama provider branch
├── chat_completion_helpers.py # UPDATE — route to ollama_adapter
└── tool_executor.py          # RETAIN — dispatches tool_calls parsed by adapter

run_agent.py                  # UPDATE — provider registry, default local provider

pyproject.toml                # UPDATE — add ollama extra if needed (or keep core httpx)

tests/
├── unit/test_ollama_adapter.py         # CREATE — unit tests for adapter
└── integration/test_ollama_chat.py     # CREATE — integration tests against local Ollama
```

**Structure Decision**: Single project layout. The primary deliverable is `agent/ollama_adapter.py`. Cross-cutting integration touches `agent/agent_init.py`, `agent/chat_completion_helpers.py`, and `run_agent.py` to register the adapter as a provider. `agent/lmstudio_reasoning.py` is deleted only after all callers are migrated.

## Complexity Tracking

> No violations. The adapter is a single self-contained module that reuses existing infrastructure (`stream_diag.py`, `retry_utils.py`, `context_compressor.py`). No new subprojects or persistence layers introduced.
