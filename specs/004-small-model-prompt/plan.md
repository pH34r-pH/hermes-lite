# Implementation Plan: Small-Model System Prompt Profile

**Branch**: `004-small-model-prompt` | **Date**: 2026-05-24 | **Spec**: `specs/004-small-model-prompt/spec.md`

**Input**: Feature specification from `/specs/004-small-model-prompt/spec.md`

## Summary

Add a new `prompt_profile="small"` to `agent/system_prompt.py` that produces a drastically shortened stable tier (<300 tokens) for small on-device models. The profile strips the verbose `TOOL_USE_ENFORCEMENT_GUIDANCE`, `OPENAI_MODEL_EXECUTION_GUIDANCE`, and `COMPUTER_USE_GUIDANCE` blocks, omits platform hints for all deleted platforms, limits per-tool guidance to one-sentence condensations only when the corresponding tool is in the active kit, and ensures byte-identical output across turns so that Ollama / llama.cpp prefix caches stay warm. The upstream `build_system_prompt_parts()` function remains intact for `"default"` profile users.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: tiktoken (optional — already in environment for token budget measurement), existing `agent/system_prompt.py` three-tier architecture (`stable`, `context`, `volatile`)

**Storage**: N/A (prompt assembly is stateless per call; caching is in-memory on `agent._cached_system_prompt`)

**Testing**: pytest

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: CLI agent / prompt assembly library

**Performance Goals**: `build_system_prompt()` completes in under 2 ms when the cached prompt is valid; small-profile stable tier token count is under 300 tokens for all supported kits

**Constraints**: Must preserve upstream `"default"` profile behavior exactly; must not break existing SOUL.md, Alibaba model-identity workaround, or kanban worker paths; must be byte-stable across turns

**Scale/Scope**: Modifications to a single file (`agent/system_prompt.py`, ~200–400 delta LOC) plus unit tests. No new modules.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Prompt truncation does not weaken tool-use enforcement; it replaces verbose guidance with a concise mandatory sentence so the model still knows it must act.
- **Defense in Depth**: Deleted platform hints are fully removed, preventing a small model from hallucinating Telegram or Slack behaviors when those platforms are no longer present.
- **Secure Defaults**: When a kit has zero allowlisted tools, the small profile still produces a valid system prompt with identity and no tool guidance rather than crashing.
- **Dependency Management**: tiktoken is already required upstream; no new dependencies.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/004-small-model-prompt/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
agent/
├── system_prompt.py       # UPDATE — add small-profile branch to prompt assembly
├── prompt_builder.py      # READ-ONLY — may contain retained platform hints
├── tool_surface.py        # READ-ONLY — provides active kit tool names for conditional guidance
└── run_agent.py           # UPDATE — add `prompt_profile` parameter to `AIAgent.__init__`

tests/
├── unit/test_system_prompt.py           # UPDATE / CREATE — add small-profile assertions
└── unit/test_small_profile_tokens.py    # CREATE — parameterized token-budget test
```

**Structure Decision**: Single project layout. All changes are localized to `agent/system_prompt.py` and `run_agent.py`. `agent/tool_surface.py` (spec 003) is read to determine which tools are active for conditional guidance inclusion.

## Complexity Tracking

> No violations. The small profile is a conditional content branch inside an existing module. No new subprojects, persistence layers, or service boundaries introduced.
