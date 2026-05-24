# Implementation Plan: Open WebUI Gateway

**Branch**: `011-openwebui-gateway` | **Date**: 2026-05-24 | **Spec**: `specs/011-openwebui-gateway/spec.md`

**Input**: Feature specification from `/specs/011-openwebui-gateway/spec.md`

## Summary

Ship a `gateway/platforms/openwebui/` package that registers as an Open WebUI pipeline named "Hermes-Lite". The adapter accepts Open WebUI conversation payloads, maps each Open WebUI conversation ID to a hermes session ID in `state.db`, enforces a user allowlist, and streams responses as markdown with fenced code blocks and citation references. It converges on the same agent loop (`run_agent.py`) and the same `state.db` as Discord and TUI, so a directive issued in Open WebUI can be inspected in the TUI and vice versa. The adapter supports the same slash commands and kit loading as other gateways. It is the experimentation endpoint that runs alongside Discord, not a replacement for it.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: `requests` (REST API fallback for PR creation), `sseclient` or built-in asyncio SSE (streaming to Open WebUI), existing `gateway/platforms/base.py`, existing `gateway/session.py`, existing `gateway/session_context.py`, existing `agent/redact.py`, existing `agent/display.py`, existing `agent/markdown_tables.py`, existing `run_agent.py`

**Storage**: `state.db` (session store and conversation mapping), `~/.hermes-lite/lite-config.yaml` or dedicated allowlist file (user allowlist), `logs/agent.jsonl` (structured gateway events)

**Testing**: pytest, plus integration tests requiring a running Open WebUI instance or mocked pipeline interface

**Target Platform**: Linux (Jetson Orin Nano) for agent; Open WebUI instance on local network or VM for pipeline target

**Project Type**: Gateway platform adapter with conversation ID mapping, user allowlist enforcement, SSE streaming, and markdown formatting

**Performance Goals**: Conversation ID mapping created/reused within 500 ms; non-allowlisted user refused within 200 ms; full chat-turn (intake → agent loop → stream) completes in under 5 seconds for a simple greeting on Jetson 25 W mode; 10,000-token response handled without truncation

**Constraints**: Non-allowlisted users receive polite refusal and never reach the agent loop; absolute file paths and secrets are redacted before streaming; concurrent messages per session are queued, never interleaved; raw HTML, unclosed backticks, and malformed tables are sanitized; reasoning content is collapsed or stripped per user config

**Scale/Scope**: One gateway platform package (~4-6 Python modules, ~600-800 LOC), conversation mapping logic, allowlist loader, SSE stream formatter, markdown sanitizer, integration with existing gateway session and agent loop infrastructure

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: User allowlist enforced at the gateway layer before messages reach the agent loop; empty allowlist defaults to deny-all; absolute paths and secrets redacted via `agent/redact.py` before streaming to browser.
- **Defense in Depth**: Allowlist check performed on every message intake; if user status changes mid-conversation, subsequent messages are refused; concurrent session messages are queued to prevent interleaved agent loops.
- **Secure Defaults**: Empty allowlist defaults to deny-all; adapter issues warning when Open WebUI is served over HTTP but still functions.
- **Dependency Management**: No heavy web framework added; uses existing gateway and agent infrastructure; Open WebUI is an external system dependency.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/011-openwebui-gateway/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
gateway/platforms/openwebui/
├── __init__.py                     # Package init and pipeline registration
├── adapter.py                      # OpenWebUIAdapter class — intake, mapping, allowlist, routing
├── conversation_mapping.py         # Open WebUI conversation ID ↔ hermes session ID persistence in state.db
├── allowlist.py                    # UserAllowlist loader from lite-config.yaml or dedicated file
├── pipeline_stream.py              # PipelineStream — SSE formatter with markdown/code/citation formatting
├── markdown_sanitizer.py           # Raw HTML escape, unclosed backtick repair, malformed table cleanup
└── schemas/
    └── openwebui_payload.schema.json   # Expected payload shape from Open WebUI

gateway/platforms/
└── base.py                         # EXISTING — OpenWebUIAdapter inherits from base platform adapter

gateway/
├── session.py                      # EXISTING — session creation and reuse
└── session_context.py              # EXISTING — session context including gateway origin

agent/
├── redact.py                       # EXISTING — secrets and path redaction
├── display.py                      # EXISTING — response formatting
└── markdown_tables.py              # EXISTING — table formatting helpers

~/.hermes-lite/lite-config.yaml     # User allowlist configuration (or dedicated allowlist file)
```

**Structure Decision**: Single package under `gateway/platforms/openwebui/` because all functionality is scoped to the Open WebUI pipeline adapter. The adapter delegates to existing gateway session management and agent loop infrastructure rather than duplicating it. Separate modules for conversation mapping, allowlist, stream formatting, and markdown sanitization keep concerns isolated and testable.

## Complexity Tracking

> No constitution violations. The feature is a single gateway platform adapter that reuses existing agent and gateway infrastructure rather than introducing new runtime systems. The tool surface is unchanged — the adapter is an intake and output formatting layer.
