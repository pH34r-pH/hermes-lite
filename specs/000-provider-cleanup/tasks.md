# Tasks: Non-Allowlisted LM Provider Cleanup

**Input**: Design documents from `/specs/000-provider-cleanup/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline verification and tooling before destructive changes

- [x] T001 [P] Audit `agent/` directory — produce list of 100+ files and confirm deletion targets exist upstream
- [x] T002 [P] Audit `plugins/image_gen/` and `plugins/video_gen/` directories — confirm they exist upstream
- [ ] T003 Run current unit-test baseline for OpenAI, Copilot, and Claude adapter tests to capture pre-cleanup pass/fail state
- [ ] T004 Create a `python -c "import agent"` smoke-test script to verify post-cleanup import health

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting registry and import audit that MUST be complete before file deletions begin

**⚠️ CRITICAL**: No file deletions can begin until this phase is complete

- [x] T005 [P] Verify all provider adapter files to delete exist upstream:
  - `agent/azure_identity_adapter.py`
  - `agent/bedrock_adapter.py`
  - `agent/gemini_native_adapter.py`
  - `agent/gemini_cloudcode_adapter.py`
  - `agent/gemini_schema.py`
  - `agent/google_code_assist.py`
  - `agent/google_oauth.py`
  - `agent/codex_runtime.py`
  - `agent/codex_responses_adapter.py`
  - `agent/moonshot_schema.py`
  - `agent/models_dev.py`
  - `agent/portal_tags.py`
  - `agent/auxiliary_client.py`
- [x] T006 [P] Verify all media-generation files to delete exist upstream:
  - `agent/image_gen_provider.py`
  - `agent/image_gen_registry.py`
  - `agent/image_routing.py`
  - `agent/video_gen_provider.py`
  - `agent/video_gen_registry.py`
  - `plugins/image_gen/`
  - `plugins/video_gen/`
- [x] T007 [P] Verify all import sites that reference the above files (run `rg` across repo for `from agent\.(azure|bedrock|gemini|codex|moonshot|models_dev|portal_tags|auxiliary_client)` and `agent\.(image_gen|video_gen)`)
- [ ] T008 Document every import line that must be removed in `agent/__init__.py`, `agent/agent_init.py`, `agent/agent_runtime_helpers.py`, `agent/chat_completion_helpers.py`, `agent/conversation_loop.py`, `agent/context_compressor.py`, `agent/plugin_llm.py`, `agent/title_generator.py`, `model_tools.py`, `toolsets.py`, `hermes_cli/plugins.py`, `hermes_cli/tools_config.py`, `tools/image_generation_tool.py`, `tools/video_generation_tool.py`

**Checkpoint**: Every dangling import is identified and documented. File deletions can now begin.

---

## Phase 3: User Story 1 - Remove Non-Allowlisted Provider Modules (Priority: P1) 🎯 MVP

**Goal**: Delete all provider adapter modules, transport layers, and schema files for non-allowlisted LM providers

**Independent Test**: Run `python -c "import agent"` after deletions and confirm no ImportError from missing provider modules

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T009 [P] [US1] Add contract test: `python -c "import agent"` completes without ImportError
- [ ] T010 [P] [US1] Add smoke test: `find agent/ -name "*azure_identity*" -o -name "*bedrock*" -o -name "*gemini*" -o -name "*codex*" -o -name "*moonshot*" -o -name "*models_dev*" -o -name "*portal_tags*" -o -name "*auxiliary_client*"` returns zero files

### Implementation for User Story 1

- [x] T011 [P] [US1] Verify/Delete `agent/azure_identity_adapter.py`
- [x] T012 [P] [US1] Verify/Delete `agent/bedrock_adapter.py`
- [x] T013 [P] [US1] Verify/Delete `agent/gemini_native_adapter.py`
- [x] T014 [P] [US1] Verify/Delete `agent/gemini_cloudcode_adapter.py`
- [x] T015 [P] [US1] Verify/Delete `agent/gemini_schema.py`
- [x] T016 [P] [US1] Verify/Delete `agent/google_code_assist.py`
- [x] T017 [P] [US1] Verify/Delete `agent/google_oauth.py`
- [x] T018 [P] [US1] Verify/Delete `agent/codex_runtime.py`
- [x] T019 [P] [US1] Verify/Delete `agent/codex_responses_adapter.py`
- [x] T020 [P] [US1] Verify/Delete `agent/moonshot_schema.py`
- [x] T021 [P] [US1] Verify/Delete `agent/models_dev.py`
- [x] T022 [P] [US1] Verify/Delete `agent/portal_tags.py`
- [x] T023 [P] [US1] Verify/Delete `agent/auxiliary_client.py`
- [ ] T024 [US1] Remove Azure imports and branches from `agent/agent_init.py` (lines referencing `azure_identity_adapter`, `is_token_provider`, `_is_azure_openai_url`)
- [ ] T025 [US1] Remove Bedrock imports and branches from `agent/agent_init.py` (lines referencing `bedrock_adapter`, `build_anthropic_bedrock_client`, `_bedrock_region`, `_bedrock_guardrail_config`)
- [ ] T026 [US1] Remove Codex imports and branches from `agent/agent_init.py` (lines referencing `codex_responses_adapter`, `codex_runtime`, `raw_codex`, `openai-codex` api_mode)
- [ ] T027 [US1] Remove auxiliary_client imports from `agent/agent_runtime_helpers.py`
- [ ] T028 [US1] Remove auxiliary_client imports from `agent/chat_completion_helpers.py`
- [ ] T029 [US1] Remove auxiliary_client imports from `agent/conversation_loop.py`
- [ ] T030 [US1] Remove auxiliary_client imports from `agent/context_compressor.py` and replace `call_llm` with direct OpenAI-compatible helper
- [ ] T031 [US1] Remove auxiliary_client imports from `agent/plugin_llm.py`
- [ ] T032 [US1] Remove auxiliary_client imports from `agent/title_generator.py`
- [ ] T033 [US1] Remove xAI / Grok OAuth branches from `agent/credential_sources.py` (`_remove_xai_oauth_loopback_pkce`, `provider="xai-oauth"` entry)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Remove Image and Video Generation Providers (Priority: P2)

**Goal**: Delete all image-generation and video-generation provider modules, registries, and routing code

**Independent Test**: Verify `plugins/image_gen/`, `plugins/video_gen/`, and matching `agent/image_gen_*.py` / `agent/video_gen_*.py` files no longer exist and their registries no longer appear in `model_tools.py` or `toolsets.py`

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T034 [P] [US2] Smoke test: `find plugins/ -type d \( -name "image_gen" -o -name "video_gen" \)` returns zero directories

### Implementation for User Story 2

- [x] T035 [P] [US2] Verify/Delete `agent/image_gen_provider.py`
- [x] T036 [P] [US2] Verify/Delete `agent/image_gen_registry.py`
- [x] T037 [P] [US2] Verify/Delete `agent/image_routing.py`
- [x] T038 [P] [US2] Verify/Delete `agent/video_gen_provider.py`
- [x] T039 [P] [US2] Verify/Delete `agent/video_gen_registry.py`
- [x] T040 [P] [US2] Verify/Delete `plugins/image_gen/` directory
- [x] T041 [P] [US2] Verify/Delete `plugins/video_gen/` directory
- [ ] T042 [US2] Remove `image_gen_registry` and `video_gen_registry` imports from `hermes_cli/plugins.py`
- [ ] T043 [US2] Remove `image_gen_registry` and `video_gen_registry` imports from `hermes_cli/tools_config.py`
- [ ] T044 [US2] Remove `image_tools` / `image_generate` and `video_gen` / `video_generate` references from `model_tools.py`
- [ ] T045 [US2] Remove `image_gen` and `video_gen` toolset definitions from `toolsets.py`
- [ ] T046 [US2] Remove or stub `tools/image_generation_tool.py` (eliminate `agent.image_gen_registry` imports)
- [ ] T047 [US2] Remove or stub `tools/video_generation_tool.py` (eliminate `agent.video_gen_registry` imports)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Update Provider Routing and Credential Pool (Priority: P3)

**Goal**: Update provider routing tables, credential pool, and factory methods so only Ollama, OpenAI, Copilot, and Claude are resolvable at runtime

**Independent Test**: Start agent with a legacy config referencing a removed provider and observe `ConfigurationError` at startup

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T048 [P] [US3] Unit test: config referencing `bedrock` raises `ConfigurationError` within 2 seconds
- [ ] T049 [P] [US3] Unit test: config referencing `gemini` raises `ConfigurationError` within 2 seconds

### Implementation for User Story 3

- [ ] T050 [US3] Update `agent/credential_pool.py` enumeration to only contain `ollama`, `openai`, `copilot`, `claude`
- [ ] T051 [US3] Update transport layer factory in `agent/agent_init.py` to only map the four allowlisted provider names to adapter classes
- [ ] T052 [US3] Update `agent/chat_completion_helpers.py` provider routing to reject non-allowlisted providers
- [ ] T053 [US3] Update `hermes_cli/tools_config.py` provider picker to only show allowlisted providers
- [ ] T054 [US3] Add `ConfigurationError` guard in `agent/agent_init.py` (or `run_agent.py`) when config references a removed provider name (azure_foundry, bedrock, gemini, codex, xai, moonshot, minimax, huggingface, novitaai, nvidia_nim, mimo, openrouter, zai_glm, nous_portal, auxiliary)
- [ ] T055 [US3] Update `hermes-lite doctor` command (`hermes_cli/commands.py` or equivalent) to only probe Ollama, OpenAI, Copilot, and Claude endpoints
- [ ] T056 [US3] Update `pyproject.toml` extras: remove `bedrock`, `azure-identity`; prune `[all]` of related transitives

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Retain and Verify Allowlisted Provider Modules (Priority: P4)

**Goal**: Keep the four allowlisted provider modules intact and verify they still pass existing tests after the cleanup

**Independent Test**: Run provider-specific unit tests for OpenAI, Copilot, and Claude adapters; smoke-test Ollama connectivity after the new adapter lands (spec 002)

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T057 [P] [US4] Run existing unit tests for `agent/chat_completion_helpers.py`
- [ ] T058 [P] [US4] Run existing unit tests for `agent/copilot_acp_client.py` and `acp_adapter/`
- [ ] T059 [P] [US4] Run existing unit tests for `agent/anthropic_adapter.py`

### Implementation for User Story 4

- [x] T060 [US4] Verify `agent/chat_completion_helpers.py` is retained and has no imports from deleted modules
- [x] T061 [US4] Verify `agent/copilot_acp_client.py` is retained and has no imports from deleted modules
- [x] T062 [US4] Verify `acp_adapter/` directory is retained and has no imports from deleted modules
- [x] T063 [US4] Verify `acp_registry/` directory is retained and has no imports from deleted modules
- [x] T064 [US4] Verify `agent/anthropic_adapter.py` is retained and has no imports from deleted modules
- [x] T065 [US4] Verify `agent/lmstudio_reasoning.py` is retained (deleted later by spec 002 after `agent/ollama_adapter.py` integration)
- [ ] T066 [US4] Fix any broken imports in retained modules caused by deletion of shared utilities (e.g., if `agent/auxiliary_client.py` exports were used by retained code, inline or relocate the needed helpers)

**Checkpoint**: Allowlisted provider modules compile and pass tests with zero regression

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and verification

- [ ] T067 [P] Run full `python -c "from agent import *; load_providers()"` smoke test — must complete without ImportError in under 5 seconds
- [ ] T068 [P] Run `find agent/ -name "*azure_identity*" -o -name "*bedrock*" -o -name "*gemini*" -o -name "*codex*" -o -name "*moonshot*" -o -name "*models_dev*" -o -name "*portal_tags*" -o -name "*auxiliary_client*"` and confirm zero files
- [ ] T069 [P] Run `find plugins/ -type d \( -name "image_gen" -o -name "video_gen" \)` and confirm zero directories
- [ ] T070 Count Python files in `agent/` — verify at most 55 files remain
- [ ] T071 Update `REDESIGN.md` references to deleted modules if they are now obsolete
- [ ] T072 [P] Run retained provider unit-test suite and confirm zero regressions
- [ ] T073 Update `specs/000-provider-cleanup/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all file deletions
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) — Depends on files from US1 being deleted so factory no longer references them
- **User Story 4 (P4)**: Can start after US1/US2 deletions — Regression-prevention story, runs last

### Within Each User Story

- Deletion tasks (marked [x]) are verified upstream first, then executed
- Import removal tasks follow the corresponding file deletions
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All deletion tasks within a user story marked [P] can run in parallel
- Import cleanup tasks can run in parallel once all deletions are done
- Retained-module verification tasks marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
