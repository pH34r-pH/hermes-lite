# Tasks: Ollama Adapter

**Input**: Design documents from `/specs/002-ollama-adapter/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Environment verification and adapter scaffold

- [x] T001 Verify Ollama is installed and accessible at `http://127.0.0.1:11434` on the Jetson
- [x] T002 Verify `ministral-3:3b` is available or document `ollama pull` requirement
- [x] T003 Create `agent/ollama_adapter.py` scaffold with module docstring and imports (`httpx`, `json`, `logging`, `typing`)
- [ ] T004 [P] Verify `agent/stream_diag.py` streaming callback interface is sufficient for NDJSON token events (document the expected callback signature)
- [ ] T005 [P] Verify `agent/retry_utils.py` covers transient HTTP errors (connection refused, timeout) so the adapter does not need its own retry layer

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core request/response models and provider registration that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
- [x] T006 Create `OllamaRequest` dataclass in `agent/ollama_adapter.py` — normalized payload containing `messages`, `model`, `stream`, `options`, and `tools`
- [x] T007 Create `OllamaResponse` dataclass in `agent/ollama_adapter.py` — normalized payload containing `assistant_text`, `reasoning_text`, `tool_calls`, and `done`
- [x] T008 Create `OllamaAdapter` class skeleton in `agent/ollama_adapter.py` with `__init__(base_url, model, context_window=32768)`
- [x] T009 Implement `_probe_model()` method in `agent/ollama_adapter.py` — hits Ollama `/api/tags` to verify model availability before first request
- [ ] T010 Add Ollama provider branch to `agent/agent_init.py` — map `provider == "ollama"` to `api_mode == "ollama_chat"`
- [ ] T011 Add Ollama adapter import and routing to `agent/chat_completion_helpers.py` — wire `ollama_adapter.OllamaAdapter` into the transport factory
- [ ] T012 Add `ollama` to provider enumeration in `agent/credential_pool.py`
- [ ] T013 Update `run_agent.py` provider registry to include `ollama` as a valid provider name

**Checkpoint**: Foundation ready — `OllamaAdapter` class exists, provider is registered, and user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Direct Ollama Chat and Generate Endpoints (Priority: P1) 🎯 MVP

**Goal**: Implement the adapter's `/api/chat` and `/api/generate` endpoints so the cyberdeck can run `ministral-3:3b` offline

**Independent Test**: Start Ollama locally with `ministral-3:3b`, initialize the adapter, send a simple chat message, and receive a non-empty response within 10 seconds

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T014 [P] [US1] Unit test: `OllamaAdapter.chat(...)` builds correct `/api/chat` POST body
- [ ] T015 [P] [US1] Unit test: `OllamaAdapter.generate(...)` builds correct `/api/generate` POST body
- [ ] T016 [P] [US1] Integration test: non-streaming chat request returns at least 10 tokens in under 10 seconds

### Implementation for User Story 1
- [x] T017 [US1] Implement `OllamaAdapter.chat(messages: list, tools: list = None, stream: bool = False) -> OllamaResponse` in `agent/ollama_adapter.py`
  - POST to `{base_url}/api/chat`
  - Serialize OpenAI-format messages into Ollama's `messages` field
  - Set `model` and `stream` flags
- [x] T018 [US1] Implement `OllamaAdapter.generate(prompt: str, stream: bool = False) -> OllamaResponse` in `agent/ollama_adapter.py`
  - POST to `{base_url}/api/generate`
  - Set `prompt` and `model` fields
- [x] T019 [US1] Add remote `base_url` support (e.g., partner VM) — no hardcoded localhost beyond the default
- [x] T020 [US1] Implement clear error when the model is unavailable — suggest `ollama pull <model>`
- [x] T021 [US1] Handle empty `message.content` but populated `message.tool_calls` in `/api/chat` response — prioritize tool calls, do not emit blank assistant message

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Function-Calling via JSON-Schema Prompts (Priority: P2)

**Goal**: Support tool use by injecting JSON schemas into prompts and parsing structured model output back into Hermes' standard tool-call format

**Independent Test**: Load a single-kit tool surface (e.g. arXiv kit), send a user message that should trigger a tool call, and verify the adapter returns a valid `tool_calls` list that `agent/tool_executor.py` can dispatch

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T022 [P] [US2] Unit test: three JSON schemas are injected into the prompt in a stable, cache-friendly format
- [ ] T023 [P] [US2] Unit test: invalid schema (missing required fields) is rejected at prompt-build time with `ValueError`
- [ ] T024 [P] [US2] Unit test: model JSON output is parsed into OpenAI-compatible `tool_calls` with `name` and `arguments`

### Implementation for User Story 2
- [x] T025 [US2] Implement `ToolSchemaInjector` in `agent/ollama_adapter.py` — serializes active kit's tool schemas into a prompt section appended to the system or user message
- [x] T026 [US2] Implement schema pre-validation in `agent/ollama_adapter.py` — validate every injected schema has `name`, `description`, and `parameters`; raise descriptive `ValueError` if not
- [x] T027 [US2] Implement structured output parser in `agent/ollama_adapter.py` — detect JSON objects in assistant text, validate `name` against active toolset allowlist, parse `arguments` as dict
- [x] T028 [US2] Return parsed tool calls as OpenAI-compatible `tool_calls` list with `name` and `arguments` fields
- [x] T029 [US2] Handle non-JSON assistant text — return plain assistant message with empty `tool_calls`
- [x] T030 [US2] Handle partial or malformed JSON — surface parse error as a tool-result failure so the conversation loop can retry or escalate

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Token-Budget Estimator for Small Models (Priority: P3)

**Goal**: Prevent context overflow on the 8 GB Jetson by estimating prompt tokens and triggering compression before posting to Ollama

**Independent Test**: Construct a prompt of known token length, call the estimator, and verify the reported count is within 10 percent of `tiktoken`'s count for the same text

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T031 [P] [US3] Unit test: 500-token prompt returns count between 450 and 550
- [ ] T032 [P] [US3] Unit test: 30k prompt against 32k window reports 2k remaining headroom and emits warning
- [ ] T033 [P] [US3] Unit test: prompt with JSON schemas counts schema text as part of budget
- [ ] T034 [P] [US3] Unit test: tiktoken missing falls back to character heuristic and logs one-time warning

### Implementation for User Story 3

- [ ] T035 [US3] Implement `OllamaAdapter.estimate_token_budget(prompt: str, tools: list) -> dict` in `agent/ollama_adapter.py`
  - Use `tiktoken` encoding when available
  - Fall back to character-based heuristic (`len(text) / 4`) when unavailable, with a one-time `logging.warning`
- [ ] T036 [US3] Compare `prompt_tokens` against `context_window` (default 32768 for Ministral-3 3B, config-knob override) and return `remaining_tokens`
- [ ] T037 [US3] Set `warning = True` when `prompt_tokens > 0.8 * context_window`
- [ ] T038 [US3] When warning is triggered, call `agent/context_compressor.py` to compact the prompt before posting to Ollama
- [ ] T039 [US3] Ensure the estimator counts injected JSON-schema tool descriptions as part of the prompt budget

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Streaming Through Stream Diagnostics (Priority: P4)

**Goal**: Stream reasoning content and tool-call deltas through Hermes' existing `agent/stream_diag.py` plumbing

**Independent Test**: Initiate a chat request, observe that tokens arrive incrementally in the TUI or Discord, and verify the final assembled message matches the non-streaming response

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T040 [P] [US4] Unit test: first streaming token yielded within 2 seconds of HTTP request
- [ ] T041 [P] [US4] Unit test: reasoning tokens routed through reasoning channel, answer tokens through answer channel
- [ ] T042 [P] [US4] Unit test: simulated network dropout yields terminal error event through `stream_diag.py` within 1 second

### Implementation for User Story 4

- [ ] T043 [US4] Implement `OllamaAdapter.chat_stream(messages, tools)` generator in `agent/ollama_adapter.py` — parse NDJSON lines from Ollama `/api/chat` with `stream=True`
- [ ] T044 [US4] Yield each token through `agent/stream_diag.py` callback within 50 ms of receipt
- [ ] T045 [US4] Detect reasoning delimiters (e.g. `<think>`…`</think>`) and route reasoning tokens through the reasoning channel; route final answer tokens through the answer channel
- [ ] T046 [US4] Buffer tool-call deltas mid-stream until the complete JSON object is received, validate tool name against allowlist, then yield a structured tool-call event
- [ ] T047 [US4] Handle invalid NDJSON lines — skip the line, log a `logging.debug` warning, and continue streaming rather than crashing
- [ ] T048 [US4] Handle network errors / disconnects — yield a terminal error event through `stream_diag.py`; rely on `agent/retry_utils.py` for retry logic
- [ ] T049 [US4] Respect user config `stream=False` — wait for full response and return it as a single message without invoking the streaming path

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration, migration from lmstudio_reasoning.py, and final verification

- [ ] T050 Verify non-streaming chat request to local Ollama with `ministral-3:3b` returns a response of at least 10 tokens in under 10 seconds
- [ ] T051 Verify streaming chat request yields first token within 2 seconds
- [ ] T052 Verify tool-call parsing accuracy is at or above 95 percent in a 20-request test suite
- [ ] T053 Verify token-budget estimator output is within 10 percent of `tiktoken` for English text prompts between 100 and 10 000 tokens
- [ ] T054 Verify when estimated prompt size exceeds 80 percent of context window, `agent/context_compressor.py` is invoked and resulting prompt fits within the window
- [ ] T055 Verify a streaming session interrupted by a simulated network dropout yields a terminal error event through `stream_diag.py` within 1 second of disconnect
- [ ] T056 Remove or inline any remaining imports of `agent/lmstudio_reasoning.py` from `agent/agent_init.py`, `agent/chat_completion_helpers.py`, `run_agent.py`
- [ ] T057 Update `agent/agent_init.py` to set Ollama as the default local provider when `provider` is unset and `OLLAMA_HOST` or loopback Ollama is reachable
- [x] T058 [P] Verify/Delete `agent/lmstudio_reasoning.py` after all callers are migrated and unit-test suite passes with zero provider-related regressions
- [ ] T059 [P] Run retained provider unit-test suite (OpenAI, Copilot, Claude) and confirm zero regressions
- [ ] T060 Update `pyproject.toml` if an `ollama` extra is needed (e.g., for `tiktoken` or model-specific deps)
- [ ] T061 Update `specs/002-ollama-adapter/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — Builds on request/response models from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Independent of US1/US2 but integrates with `context_compressor.py`
- **User Story 4 (P4)**: Can start after US1 — Requires working `/api/chat` endpoint to stream from

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (smoke-test local Ollama chat)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (chat / generate endpoints)
   - Developer B: User Story 2 (JSON-schema tool calling)
   - Developer C: User Story 3 (token budget estimator)
   - Developer D: User Story 4 (streaming / stream_diag)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- `agent/lmstudio_reasoning.py` is retained until T058; do not delete it before all callers in `agent/agent_init.py`, `agent/chat_completion_helpers.py`, and `run_agent.py` are migrated
