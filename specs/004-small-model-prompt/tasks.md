# Tasks: Small-Model System Prompt Profile

**Input**: Design documents from `/specs/004-small-model-prompt/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline measurement and scaffold

- [x] T001 Audit current `agent/system_prompt.py` — capture token counts for `stable`, `context`, and `volatile` tiers with `prompt_profile="default"` for each supported kit
- [x] T002 Verify tiktoken `cl100k_base` is available in the hermes-lite environment; document fallback if missing
- [x] T003 Read `agent/system_prompt.py` to identify all guidance blocks (`TOOL_USE_ENFORCEMENT_GUIDANCE`, `OPENAI_MODEL_EXECUTION_GUIDANCE`, `GOOGLE_MODEL_OPERATIONAL_GUIDANCE`, `COMPUTER_USE_GUIDANCE`, `MEMORY_GUIDANCE`, `SESSION_SEARCH_GUIDANCE`, `SKILLS_GUIDANCE`, `KANBAN_GUIDANCE`, `PLATFORM_HINTS`) and record their upstream line ranges

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Profile selection infrastructure and token-budget measurement that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add `prompt_profile` parameter to `AIAgent.__init__` in `run_agent.py` (default `"default"`, accept `"small"`); store on `self.prompt_profile`
- [x] T005 Create `build_small_system_prompt_parts(agent, system_message)` function skeleton in `agent/system_prompt.py` that returns the same three-tier dict shape (`stable`, `context`, `volatile`)
- [x] T006 Implement `_count_tokens(text: str) -> int` helper in `agent/system_prompt.py` using tiktoken `cl100k_base`; fall back to character heuristic with one-time warning if tiktoken is missing
- [x] T007 Implement `_assert_budget(stable_tier: str, max_tokens: int = 300)` helper in `agent/system_prompt.py` — raises `ValueError` if budget is exceeded during development/testing
- [x] T008 Branch `build_system_prompt_parts()` in `agent/system_prompt.py` — if `agent.prompt_profile == "small"`, delegate to `build_small_system_prompt_parts()`; otherwise use the existing upstream path

**Checkpoint**: Foundation ready — profile selection works, token counter exists, and user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Remove Verbose Tool-Use Preamble (Priority: P1) 🎯 MVP

**Goal**: Strip the lengthy tool-use enforcement guidance, model-family operational directives, and computer-use blocks; replace with a single concise paragraph

**Independent Test**: Construct an `AIAgent` with `prompt_profile="small"` and assert that the stable tier token count is under 300 tokens

### Tests for User Story 1 (OPTIONAL) ⚠️

- [x] T009 [P] [US1] Unit test: `build_small_system_prompt_parts()` stable tier does not contain full `TOOL_USE_ENFORCEMENT_GUIDANCE` block
- [x] T010 [P] [US1] Unit test: stable tier is strictly fewer than 300 tokens for kit `arxiv`
- [x] T011 [P] [US1] Unit test: stable tier contains a single concise tool-use sentence (e.g., "Use available tools to act; do not describe intentions without acting.")
- [x] T012 [P] [US1] Unit test: default upstream profile retains full verbose guidance unchanged

### Implementation for User Story 1

- [x] T013 [US1] Omit `TOOL_USE_ENFORCEMENT_GUIDANCE` entirely from small-profile stable tier in `agent/system_prompt.py`
- [x] T014 [US1] Omit `OPENAI_MODEL_EXECUTION_GUIDANCE` entirely from small-profile stable tier in `agent/system_prompt.py`
- [x] T015 [US1] Omit `GOOGLE_MODEL_OPERATIONAL_GUIDANCE` entirely from small-profile stable tier in `agent/system_prompt.py`
- [x] T016 [US1] Omit `COMPUTER_USE_GUIDANCE` entirely from small-profile stable tier in `agent/system_prompt.py`
- [x] T017 [US1] Add a single concise tool-use sentence to small-profile stable tier in `agent/system_prompt.py`
- [x] T018 [US1] Ensure the default profile path is untouched — upstream `build_system_prompt_parts()` continues to include all guidance blocks when `prompt_profile != "small"`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Remove Irrelevant Platform Guidance (Priority: P2)

**Goal**: Omit `PLATFORM_HINTS` for deleted platforms and inject only the hint relevant to the current gateway

**Independent Test**: Set `agent.platform="discord"`, build the small profile, and grep the stable tier for deleted platform names; none must appear

### Tests for User Story 2 (OPTIONAL) ⚠️

- [x] T019 [P] [US2] Unit test: `platform="discord"` small profile contains only Discord hint; Telegram, Slack, WhatsApp, Signal, Yuanbao, Feishu, etc. are absent
- [x] T020 [P] [US2] Unit test: `platform="openwebui"` small profile contains Open WebUI hint and no others
- [x] T021 [P] [US2] Unit test: `platform="cli"` (TUI) small profile contains concise CLI hint with `MEDIA:/path` reference
- [x] T022 [P] [US2] Unit test: deleted platform names return zero matches across the small-profile stable tier

### Implementation for User Story 2

- [x] T023 [US2] Define `PLATFORM_HINT_ALLOWLIST = {"discord", "cli", "tui", "openwebui"}` in `agent/system_prompt.py`
- [x] T024 [US2] In small-profile stable tier, include at most one platform hint: the hint matching `agent.platform` if it is in `PLATFORM_HINT_ALLOWLIST`; otherwise omit platform hints entirely
- [x] T025 [US2] In small-profile stable tier, explicitly exclude all deleted platform hints: Telegram, Slack, WhatsApp, Signal, Email, Yuanbao, Weixin, WeCom, Feishu, DingTalk, QQBot, Matrix, Mattermost, HomeAssistant, BlueBubbles, SMS, Webhook
- [x] T026 [US2] Ensure the CLI/TUI hint is concise — reference `MEDIA:/path` interception in one sentence rather than a paragraph
- [x] T027 [US2] Handle leaked old config values gracefully: if `agent.platform` is set to a deleted platform string, emit no platform hint rather than crashing

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Limit Active Toolset to One Kit at a Time (Priority: P3)

**Goal**: Include per-tool guidance blocks only when the corresponding tool is present in the active kit's allowlist; condense to one sentence when included

**Independent Test**: Activate the `arxiv` kit with the small profile and assert that `kanban_show`, `memory`, and `session_search` guidance blocks are absent from the stable tier

### Tests for User Story 3 (OPTIONAL) ⚠️

- [x] T028 [P] [US3] Unit test: `active_kit="arxiv"` and `prompt_profile="small"` stable tier does not contain `KANBAN_GUIDANCE`
- [x] T029 [P] [US3] Unit test: `active_kit="spec-kit"` stable tier shows only spec-relevant skills (or omits skills index entirely)
- [x] T030 [P] [US3] Unit test: `computer_use` tool absent from active kit omits `COMPUTER_USE_GUIDANCE`
- [ ] T031 [P] [US3] Unit test: `memory` tool present in active kit shows a condensed single-sentence `MEMORY_GUIDANCE` instead of the multi-paragraph block

### Implementation for User Story 3

- [ ] T032 [US3] Integrate with `agent/tool_surface.py` (spec 003) to read the active kit's allowlisted tool names at prompt-build time
- [ ] T033 [US3] Conditionally include `MEMORY_GUIDANCE` in small-profile stable tier only if `memory` is in the active kit; when included, use a one-sentence condensation
- [ ] T034 [US3] Conditionally include `SESSION_SEARCH_GUIDANCE` in small-profile stable tier only if `session_search` is in the active kit; when included, use a one-sentence condensation
- [ ] T035 [US3] Conditionally include `SKILLS_GUIDANCE` / skills index in small-profile stable tier only if the active kit explicitly requires skill awareness; otherwise omit or drastically shorten
- [ ] T036 [US3] Conditionally include `KANBAN_GUIDANCE` in small-profile stable tier only if kanban tools are in the active kit; when included, use a one-sentence condensation
- [ ] T037 [US3] Omit `COMPUTER_USE_GUIDANCE` from small-profile stable tier when `computer_use` is not in the active kit

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Rely on Byte-Stable Prefix Caching (Priority: P4)

**Goal**: Ensure the small-profile system prompt is byte-identical across turns when agent state is unchanged

**Independent Test**: Call `build_system_prompt()` twice in a row with identical agent state and assert byte equality

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T038 [P] [US4] Unit test: two successive calls with identical state produce byte-identical strings
- [ ] T039 [P] [US4] Unit test: context compression changes only the volatile tier; stable tier remains byte-identical
- [ ] T040 [P] [US4] Unit test: kit switch changes stable tier, and the new stable tier is itself byte-identical on subsequent turns
- [ ] T041 [P] [US4] Unit test: `agent._cached_system_prompt` is populated at init and not rebuilt unless invalidated

### Implementation for User Story 4

- [ ] T042 [US4] Ensure timestamp line in small profile remains date-only (no time component) to match upstream behavior
- [ ] T043 [US4] Ensure kit-specific text is rendered deterministically (sorted tool names, stable string formatting, no unordered set iteration)
- [ ] T044 [US4] Cache the assembled system prompt on `agent._cached_system_prompt` in `run_agent.py`
- [ ] T045 [US4] Implement invalidation logic: rebuild the cache on kit switch, platform change, compression event, or SOUL.md modification; otherwise reuse
- [ ] T046 [US4] Ensure the stable tier is assembled from static strings and allowlist data only — no random identifiers, no timestamps, no memory summaries

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge-case handling, SOUL.md budget enforcement, and final verification

- [ ] T047 Verify small-profile stable tier token count is under 300 tokens for all supported kits (`arxiv`, `spec-kit`, `dev`, `web-ops`, `azure-ops`, `security`), parameterized pytest
- [ ] T048 Verify grep for deleted platform names across small-profile stable tier returns zero matches for every deleted platform
- [ ] T049 Verify two successive calls to `build_system_prompt()` with identical state produce byte-identical strings
- [ ] T050 Verify switching from `"default"` to `"small"` profile reduces stable tier token count by at least 60%
- [ ] T051 Verify agent startup smoke test (`python -c "from agent.system_prompt import build_system_prompt_parts; ..."`) passes for both `"default"` and `"small"` profiles without import errors
- [ ] T052 Verify kanban worker path (`HERMES_KANBAN_TASK` env set) with `"small"` profile still includes a condensed kanban guidance block
- [ ] T053 Implement SOUL.md fallback: if SOUL.md would cause the stable tier to exceed the 300-token budget, fall back to `DEFAULT_AGENT_IDENTITY` in small profile
- [ ] T054 Verify Alibaba model-identity workaround is still injected in small profile when `provider == "alibaba"`
- [ ] T055 Verify environment hints are still injected in small profile because they are required for correct operation
- [ ] T056 Run retained unit-test suite and confirm zero regressions in upstream `"default"` profile
- [ ] T057 Update `specs/004-small-model-prompt/` status to Complete

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Builds on US1's concise stable tier; requires `agent/tool_surface.py` (spec 003) for active kit tool names
- **User Story 4 (P4)**: Can start after US1–US3 — Requires stable tier content to be finalized before byte-stability can be guaranteed

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Content omission before content replacement
- Stable tier assembly before caching/invalidation logic
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel
- US3 can start in parallel once spec 003 delivers active kit API
- US4 can start once US1–US3 settle the stable tier content
- All tests for a user story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (token count < 300)
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
   - Developer A: User Story 1 (strip verbose guidance)
   - Developer B: User Story 2 (platform hint curation)
3. Once US1 and US2 are done:
   - Developer C: User Story 3 (conditional tool guidance)
   - Developer D: User Story 4 (byte stability / caching)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- The upstream `build_system_prompt_parts()` function must remain intact; branch, do not mutate the default path in place
- SOUL.md is optional; when present it may be large, so the small profile must be willing to ignore it to meet the 300-token budget
- The skills index is considered optional for small-model operation because the user can explicitly load a skill via slash command when needed
