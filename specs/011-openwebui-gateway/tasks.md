# Tasks: Open WebUI Gateway

**Input**: Design documents from `/specs/011-openwebui-gateway/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structure, module scaffolds, schema files, and upstream integration points

- [x] T001 Create `gateway/platforms/openwebui/` directory tree: `schemas/`
- [x] T002 Create `gateway/platforms/openwebui/__init__.py` with package init and pipeline registration stub
- [x] T003 Create `gateway/platforms/openwebui/schemas/openwebui_payload.schema.json`
  - Document expected payload fields: `conversation_id`, `message_id`, `user`, `content`, `metadata`
- [x] T004 Verify `gateway/platforms/base.py` exists; document inheritance point for `OpenWebUIAdapter`
- [x] T005 Verify `gateway/session.py` exists; document session creation and reuse integration point
- [x] T006 Verify `gateway/session_context.py` exists; document `OpenWebUISessionContext` extension point
- [x] T007 Verify `agent/redact.py` exists; document redaction before streaming integration point
- [x] T008 Verify `state.db` schema supports external conversation-ID mapping; document required migration if any
- [x] T009 [P] Add `__init__.py` and module docstring scaffolds for all new modules

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Python support modules that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T010 Implement `ConversationMapping` functionality in `gateway/platforms/openwebui.py`
  - Persist Open WebUI conversation ID → hermes session ID mapping in `state.db` via `SessionMapper._ensure_db()` and `set_meta`
  - Reuse existing session on known conversation ID
  - Detect stale mapping (session deleted) and create new session, overwriting mapping
  - Handle mapping lookup within 500 ms
- [x] T011 Implement `UserAllowlist` in `gateway/platforms/openwebui.py`
  - Load allowlist from `~/.hermes-lite/lite-config.yaml` or dedicated allowlist file
  - Empty allowlist defaults to deny-all
  - Check performed on every message intake
  - If user removed mid-conversation, subsequent messages are refused
- [x] T012 Implement `PipelineStream` (`OpenWebUISSEStream`) in `gateway/platforms/openwebui.py`
  - Convert agent output into Open WebUI-compatible SSE markdown chunks
  - Wrap code blocks in triple backticks with language tag
  - Format arXiv citations as markdown links
  - Format markdown tables with pipe syntax
  - Support chunking for long responses
- [x] T013 Implement `MarkdownSanitizer` (`OpenWebUIMarkdownFormatter`) in `gateway/platforms/openwebui.py`
  - Escape raw HTML
  - Repair unclosed backticks
  - Cleanup malformed table syntax
  - Preserve intended markdown formatting
- [x] T014 Implement `OpenWebUIAdapter` skeleton in `gateway/platforms/openwebui.py`
  - Wire `SessionMapper`, `UserAllowlist`, `OpenWebUISSEStream`, `OpenWebUIMarkdownFormatter`
  - Route Open WebUI payloads into `AIAgent.chat()` / `run_conversation()`
  - Handle intake, mapping, allowlist check, agent loop invocation, and response streaming
- [x] T015 [P] Add docstrings and type stubs for all new public methods/classes

**Checkpoint**: Foundation ready — conversation mapping, user allowlist, pipeline stream, markdown sanitizer, and adapter skeleton exist; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Register as an Open WebUI Pipeline and Map Conversations (Priority: P1) 🎯 MVP

**Goal**: Conversation-to-session mapping makes Open WebUI a first-class gateway

**Independent Test**: Send two messages in the same Open WebUI conversation and verify in `state.db` that both are attached to the same hermes session ID

### Tests for User Story 1

- [ ] T016 [P] [US1] Unit test: `ConversationMapping` creates new mapping on first conversation ID in `tests/unit/test_conversation_mapping.py`
- [ ] T017 [P] [US1] Unit test: `ConversationMapping` reuses existing session on second message in `tests/unit/test_conversation_mapping.py`
- [ ] T018 [P] [US1] Unit test: `ConversationMapping` detects stale mapping and creates new session in `tests/unit/test_conversation_mapping.py`
- [ ] T019 [P] [US1] Unit test: different conversation ID creates independent mapping in `tests/unit/test_conversation_mapping.py`
- [ ] T020 [P] [US1] Integration test: two messages in same Open WebUI conversation share session in `tests/integration/test_openwebui_mapping.py`

### Implementation for User Story 1

- [x] T021 [US1] Complete `OpenWebUIAdapter.intake()` via `Pipeline.inlet()` in `gateway/platforms/openwebui.py`
  - Parse Open WebUI payload
  - Call `SessionMapper` to get or create hermes session ID
  - Persist mapping and session origin (`source='openwebui'`) to `state.db`
- [x] T022 [US1] Complete `OpenWebUIAdapter.route()` via `Pipeline._run_agent()` in `gateway/platforms/openwebui.py`
  - Pass message into agent loop (`AIAgent.chat()`)
  - Append agent response to session history in `state.db`
- [x] T023 [US1] Register adapter as Open WebUI pipeline named "Hermes-Lite"
  - Already present in `gateway/platforms/__init__.py`
- [ ] T024 [US1] Verify pipeline appears in Open WebUI pipeline list when configured

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Enforce User Allowlist (Priority: P1)

**Goal**: Prevent unauthorized users from consuming agent quota or triggering workspace mutations

**Independent Test**: Configure allowlist with one user, send messages from allowed and disallowed users, and verify responses

### Tests for User Story 2

- [ ] T025 [P] [US2] Unit test: `UserAllowlist` allows listed user in `tests/unit/test_allowlist.py`
- [ ] T026 [P] [US2] Unit test: `UserAllowlist` denies non-listed user with polite refusal in `tests/unit/test_allowlist.py`
- [ ] T027 [P] [US2] Unit test: empty allowlist denies all users in `tests/unit/test_allowlist.py`
- [ ] T028 [P] [US2] Unit test: `/spec` command rejected for non-allowlisted user before agent loop in `tests/unit/test_allowlist.py`
- [ ] T029 [P] [US2] Integration test: allowlist enforced within 200 ms in `tests/integration/test_openwebui_allowlist.py`

### Implementation for User Story 2

- [x] T030 [US2] Integrate `UserAllowlist.check()` into `Pipeline.inlet()` in `gateway/platforms/openwebui.py`
  - Check on every message intake
  - Non-allowlisted user receives polite refusal: "This agent is restricted. Contact the admin to request access."
  - Refusal returned at gateway layer before agent loop is reached
- [ ] T031 [US2] Add allowlist configuration documentation to `~/.hermes-lite/lite-config.yaml` schema
- [ ] T032 [US2] Verify allowlist status change mid-conversation is respected on next message

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Stream Markdown, Code Blocks, and Citations (Priority: P2)

**Goal**: Agent output is readable and professional in the Open WebUI browser interface

**Independent Test**: Ask for a code example and an arXiv citation, then verify rendered HTML in Open WebUI

### Tests for User Story 3

- [ ] T033 [P] [US3] Unit test: `PipelineStream` wraps Python code in triple-backtick fences with `python` tag in `tests/unit/test_pipeline_stream.py`
- [ ] T034 [P] [US3] Unit test: `PipelineStream` formats arXiv citation as markdown link in `tests/unit/test_pipeline_stream.py`
- [ ] T035 [P] [US3] Unit test: `PipelineStream` formats comparison table with pipe syntax in `tests/unit/test_pipeline_stream.py`
- [ ] T036 [P] [US3] Unit test: `MarkdownSanitizer` escapes raw HTML and repairs unclosed backticks in `tests/unit/test_markdown_sanitizer.py`
- [ ] T037 [P] [US3] Unit test: reasoning content collapsed into `<details>` block per config in `tests/unit/test_pipeline_stream.py`
- [ ] T038 [P] [US3] Integration test: long response chunked without truncation in `tests/integration/test_openwebui_streaming.py`

### Implementation for User Story 3

- [x] T039 [US3] Complete `PipelineStream.format()` via `OpenWebUIMarkdownFormatter.format()` in `gateway/platforms/openwebui.py`
  - Wrap code blocks in triple backticks with language tag
  - Format arXiv citations as markdown links to local knowledge repo or arXiv URL
  - Format markdown tables with pipe syntax
  - Chunk long responses gracefully
- [x] T040 [US3] Complete `MarkdownSanitizer.sanitize()` via `OpenWebUIMarkdownFormatter.sanitize()` in `gateway/platforms/openwebui.py`
  - Escape raw HTML
  - Repair unclosed backticks
  - Cleanup malformed table syntax
- [x] T041 [US3] Handle reasoning content in `gateway/platforms/openwebui.py`
  - Collapse into `<details>` block or strip, per config
  - Never mix reasoning with final answer
- [x] T042 [US3] Integrate `PipelineStream` and `MarkdownSanitizer` into adapter response path

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Cross-Gateway Session Visibility (Priority: P2)

**Goal**: Sessions created in Open WebUI are visible in TUI and vice versa

**Independent Test**: Create a session in Open WebUI, open TUI, and verify session appears in TUI session list with same messages

### Tests for User Story 4

- [ ] T043 [P] [US4] Unit test: session created via Open WebUI appears in session list with `openwebui` origin in `tests/unit/test_session_visibility.py`
- [ ] T044 [P] [US4] Unit test: TUI continuation appends to same session in `state.db` in `tests/unit/test_session_visibility.py`
- [ ] T045 [P] [US4] Unit test: FTS5 search recalls messages from all gateways in `tests/unit/test_session_visibility.py`
- [ ] T046 [P] [US4] Integration test: cross-gateway session continuity verified end-to-end in `tests/integration/test_openwebui_visibility.py`

### Implementation for User Story 4

- [x] T047 [US4] Ensure `OpenWebUIAdapter` writes session metadata with `gateway: openwebui` origin to `state.db`
- [ ] T048 [US4] Verify TUI session list queries include sessions from all gateways
- [ ] T049 [US4] Verify FTS5 search indexes messages regardless of gateway origin
- [ ] T050 [US4] Verify background curator review pass sees full conversation regardless of gateway
- [x] T051 [US4] Ensure agent responses written to `state.db` are immediately visible to other gateway queries

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge-case handling, safety, logging, and final integration

- [x] T052 Verify adapter redacts absolute file paths via `agent/redact.py` before streaming tool results to browser
- [ ] T053 Verify adapter handles streaming error mid-response: sends partial message, closes stream cleanly, logs failure to `logs/agent.jsonl`
- [x] T054 Verify adapter handles concurrent messages per session by queuing or returning busy indicator; no interleaved agent loops
- [ ] T055 Verify adapter handles HTTP-served Open WebUI with admin log warning but still functions
- [ ] T056 Verify adapter supports `/arxiv`, `/spec`, `/sec`, and other slash commands same as Discord and TUI
- [x] T057 Verify adapter logs all intake, mapping, and streaming events to `logs/agent.jsonl`
- [ ] T058 Verify adapter completes a simple greeting chat-turn in under 5 seconds on Jetson 25 W mode
- [ ] T059 Verify 10,000-token response is handled without truncation or rendering errors
- [ ] T060 Verify empty allowlist defaults to deny-all
- [ ] T061 [P] Run retained unit-test suite and confirm zero regressions in gateway loading, session management, or platform adapters
- [x] T062 Update gateway platform registration to include `openwebui` in known platforms list
- [ ] T063 Update `REDESIGN.md` §5.3 references to reflect completed implementation
- [ ] T064 Update `specs/011-openwebui-gateway/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on US1 intake path but can be tested standalone
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Builds on US1 response path but can be tested standalone with mocked agent output
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Depends on `state.db` integration from US1 but is a visibility concern, not a functional dependency

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Support modules before adapter integration
- Core adapter path before polish
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US1 (mapping) and US3 (streaming) are orthogonal and can proceed in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (pipeline registration and conversation mapping)
4. **STOP and VALIDATE**: Test conversation mapping independently — send two messages, verify same session ID in `state.db`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Polish and final validation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (mapping) + User Story 2 (allowlist)
   - Developer B: User Story 3 (streaming + markdown)
   - Developer C: User Story 4 (cross-gateway visibility)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Non-allowlisted users MUST be refused at the gateway layer before reaching the agent loop
- Empty allowlist MUST default to deny-all
- Raw HTML, unclosed backticks, and malformed table syntax MUST be sanitized before streaming
- Absolute file paths and secrets MUST be redacted via `agent/redact.py`
- Concurrent messages to the same session MUST be queued; interleaved agent loops are prohibited
- The adapter MUST converge on the same `state.db`, memory profiles, and kits as all other gateways
- If Open WebUI is unreachable, the adapter MUST fail gracefully and log without crashing hermes-lite
