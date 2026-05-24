# Tasks: Non-Allowlisted Gateway and Web Dashboard Cleanup

**Input**: Design documents from `/specs/001-gateway-cleanup/`

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

- [x] T001 [P] Audit `gateway/platforms/` directory — produce list of files and confirm deletion targets exist upstream
- [x] T002 [P] Audit `website/`, `web/`, `plugins/web/`, `plugins/spotify/`, `plugins/google_meet/`, `plugins/teams_pipeline/`, `plugins/hermes-achievements/` — confirm they exist upstream
- [ ] T003 Run current gateway smoke test to capture pre-cleanup pass/fail state
- [ ] T004 Create `python -c "from gateway.platforms import load_platforms; p=load_platforms()"` smoke-test script

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cross-cutting registry and import audit that MUST be complete before platform deletions begin

**⚠️ CRITICAL**: No file deletions can begin until this phase is complete

- [x] T005 [P] Verify all platform adapter files to delete exist upstream:
  - `gateway/platforms/telegram.py`
  - `gateway/platforms/telegram_network.py`
  - `gateway/platforms/slack.py`
  - `gateway/platforms/whatsapp.py`
  - `gateway/platforms/signal.py`
  - `gateway/platforms/signal_rate_limit.py`
  - `gateway/platforms/email.py`
  - `gateway/platforms/yuanbao.py`
  - `gateway/platforms/yuanbao_proto.py`
  - `gateway/platforms/yuanbao_sticker.py`
  - `gateway/platforms/yuanbao_media.py`
  - `gateway/platforms/weixin.py`
  - `gateway/platforms/wecom.py`
  - `gateway/platforms/wecom_callback.py`
  - `gateway/platforms/wecom_crypto.py`
  - `gateway/platforms/feishu.py`
  - `gateway/platforms/feishu_comment.py`
  - `gateway/platforms/feishu_comment_rules.py`
  - `gateway/platforms/dingtalk.py`
  - `gateway/platforms/qqbot/` (directory)
  - `gateway/platforms/matrix.py`
  - `gateway/platforms/mattermost.py`
  - `gateway/platforms/homeassistant.py`
  - `gateway/platforms/bluebubbles.py`
  - `gateway/platforms/sms.py`
  - `gateway/platforms/msgraph_webhook.py`
  - `gateway/platforms/webhook.py`
- [x] T006 [P] Verify bundled web dashboard and plugin directories to delete exist upstream:
  - `website/`
  - `web/`
  - `plugins/spotify/`
  - `plugins/google_meet/`
  - `plugins/teams_pipeline/`
  - `plugins/hermes-achievements/`
- [x] T007 [P] Verify `plugins/web/` exists upstream; determine whether to fully delete or reduce to web-search-provider components per REDESIGN.md §4.3
- [x] T008 [P] Run `rg` across repo for imports of each platform above, and for `website/`, `web/`, `plugins/web/` references in `gateway/run.py`, `gateway/config.py`, `gateway/platform_registry.py`, `hermes_cli/plugins.py`, `hermes_cli/commands.py`
- [ ] T009 Document every import line and config enum that must be removed

**Checkpoint**: Every dangling import and config reference is identified and documented. File deletions can now begin.

---

## Phase 3: User Story 1 - Remove Non-Allowlisted Chat Platforms (Priority: P1) 🎯 MVP

**Goal**: Delete all gateway platform modules, adapters, and identity helpers for non-allowlisted chat surfaces, leaving only Discord, TUI, and Open WebUI

**Independent Test**: Run `python -c "from gateway.platforms import *; load_platforms()"` after deletion and confirm only Discord, TUI, and Open WebUI adapters load

### Tests for User Story 1 (OPTIONAL) ⚠️

- [ ] T010 [P] [US1] Contract test: `load_platforms()` returns only `discord`, `tui`, `openwebui`
- [ ] T011 [P] [US1] Smoke test: `find gateway/platforms/ -maxdepth 1 -name "*.py" | wc -l` returns at most 5 files after cleanup

### Implementation for User Story 1

- [x] T012 [P] [US1] Verify/Delete `gateway/platforms/telegram.py`
- [x] T013 [P] [US1] Verify/Delete `gateway/platforms/telegram_network.py`
- [x] T014 [P] [US1] Verify/Delete `gateway/platforms/slack.py`
- [x] T015 [P] [US1] Verify/Delete `gateway/platforms/whatsapp.py`
- [x] T016 [P] [US1] Verify/Delete `gateway/platforms/signal.py`
- [x] T017 [P] [US1] Verify/Delete `gateway/platforms/signal_rate_limit.py`
- [x] T018 [P] [US1] Verify/Delete `gateway/platforms/email.py`
- [x] T019 [P] [US1] Verify/Delete `gateway/platforms/yuanbao.py`
- [x] T020 [P] [US1] Verify/Delete `gateway/platforms/yuanbao_proto.py`
- [x] T021 [P] [US1] Verify/Delete `gateway/platforms/yuanbao_sticker.py`
- [x] T022 [P] [US1] Verify/Delete `gateway/platforms/yuanbao_media.py`
- [x] T023 [P] [US1] Verify/Delete `gateway/platforms/weixin.py`
- [x] T024 [P] [US1] Verify/Delete `gateway/platforms/wecom.py`
- [x] T025 [P] [US1] Verify/Delete `gateway/platforms/wecom_callback.py`
- [x] T026 [P] [US1] Verify/Delete `gateway/platforms/wecom_crypto.py`
- [x] T027 [P] [US1] Verify/Delete `gateway/platforms/feishu.py`
- [x] T028 [P] [US1] Verify/Delete `gateway/platforms/feishu_comment.py`
- [x] T029 [P] [US1] Verify/Delete `gateway/platforms/feishu_comment_rules.py`
- [x] T030 [P] [US1] Verify/Delete `gateway/platforms/dingtalk.py`
- [x] T031 [P] [US1] Verify/Delete `gateway/platforms/qqbot/` directory
- [x] T032 [P] [US1] Verify/Delete `gateway/platforms/matrix.py`
- [x] T033 [P] [US1] Verify/Delete `gateway/platforms/mattermost.py`
- [x] T034 [P] [US1] Verify/Delete `gateway/platforms/homeassistant.py`
- [x] T035 [P] [US1] Verify/Delete `gateway/platforms/bluebubbles.py`
- [x] T036 [P] [US1] Verify/Delete `gateway/platforms/sms.py`
- [x] T037 [P] [US1] Verify/Delete `gateway/platforms/msgraph_webhook.py`
- [x] T038 [P] [US1] Verify/Delete `gateway/platforms/webhook.py`
- [ ] T039 [US1] Remove platform enums from `gateway/config.py` (TELEGRAM, WHATSAPP, SLACK, SIGNAL, MATTERMOST, MATRIX, HOMEASSISTANT, EMAIL, SMS, DINGTALK, WEBHOOK, MSGRAPH_WEBHOOK, FEISHU, WECOM, WECOM_CALLBACK, WEIXIN, BLUEBUBBLES, QQBOT, YUANBAO)
- [ ] T040 [US1] Remove platform-specific config bridging from `gateway/config.py` (slack_cfg, telegram_cfg, etc.)
- [ ] T041 [US1] Update `gateway/platforms/__init__.py`: remove `QQAdapter` and `YuanbaoAdapter` from `__all__` and `__getattr__`; do not import deleted modules
- [ ] T042 [US1] Update `gateway/run.py`: remove all Telegram-specific logic (`_telegramize_command_mentions`, `_telegram_topic_mode_enabled`, `_is_telegram_topic_root_lobby`, `_is_telegram_topic_lane`, etc.), WhatsApp identity imports, msgraph webhook binding, and adapter instantiation blocks for deleted platforms
- [ ] T043 [US1] Update `gateway/platform_registry.py` if it references deleted platforms
- [ ] T044 [US1] Audit `gateway/platforms/helpers.py`: excise any helpers only used by deleted platforms; retain helpers used by `discord.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Remove Bundled Web Dashboard and Related Plugins (Priority: P2)

**Goal**: Delete the bundled web dashboard and related media/achievement plugins

**Independent Test**: Verify `website/`, `web/`, `plugins/web/`, `plugins/spotify/`, `plugins/google_meet/`, `plugins/teams_pipeline/`, and `plugins/hermes-achievements/` no longer exist

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T045 [P] [US2] Smoke test: `ls website/ web/ plugins/web/ plugins/spotify/ plugins/google_meet/ plugins/teams_pipeline/ plugins/hermes-achievements/ 2>&1 | grep "No such file" | wc -l` returns 7

### Implementation for User Story 2

- [x] T046 [P] [US2] Verify/Delete `website/` directory
- [x] T047 [P] [US2] Verify/Delete `web/` directory
- [x] T048 [P] [US2] Verify/Delete `plugins/spotify/` directory
- [x] T049 [P] [US2] Verify/Delete `plugins/google_meet/` directory
- [x] T050 [P] [US2] Verify/Delete `plugins/teams_pipeline/` directory
- [x] T051 [P] [US2] Verify/Delete `plugins/hermes-achievements/` directory
- [x] T052 [US2] Verify/Reduce `plugins/web/` — either fully delete or reduce to web-search-provider components only per REDESIGN.md §4.3
- [ ] T053 [US2] Remove `plugins/web/` imports and registry entries from `hermes_cli/plugins.py` if fully deleted
- [ ] T054 [US2] Remove dashboard-related package-data entries from `pyproject.toml` (`hermes_cli/web_dist`, `plugins/*/dashboard/dist`)
- [ ] T055 [US2] Remove `web` extra from `pyproject.toml` if `plugins/web/` is fully deleted (or retain if reduced to search-provider only)
- [ ] T056 [US2] Remove any gateway session initializer references to web-dashboard URLs in `gateway/session.py` or `gateway/run.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Introduce Open WebUI Gateway (Priority: P3)

**Goal**: Create a new `gateway/platforms/openwebui/` package that registers as an Open WebUI pipeline

**Independent Test**: Run an Open WebUI instance, install the Hermes-Lite pipeline, send a message, and verify the response appears in the Hermes session history

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T057 [P] [US3] Contract test: pipeline registers under name "Hermes-Lite" in Open WebUI's pipeline list
- [ ] T058 [P] [US3] Integration test: send message, verify session created in `state.db`

### Implementation for User Story 3

- [ ] T059 [US3] Create `gateway/platforms/openwebui/__init__.py` with package exports
- [ ] T060 [US3] Create `gateway/platforms/openwebui/pipeline.py` implementing Open WebUI pipeline protocol (inlet/outlet hooks)
- [ ] T061 [US3] Create `gateway/platforms/openwebui/session_mapper.py` mapping Open WebUI conversation IDs to Hermes session IDs bidirectionally, storing in `state.db`
- [ ] T062 [US3] Implement user allowlist enforcement in `gateway/platforms/openwebui/pipeline.py` — reject disallowed users with HTTP 403 and log attempt
- [ ] T063 [US3] Implement streaming response logic in `gateway/platforms/openwebui/pipeline.py` — forward assistant markdown, code blocks, and citations correctly
- [ ] T064 [US3] Add `OpenWebUIAdapter` class inheriting from `gateway/platforms/base.py` if needed for gateway integration
- [ ] T065 [US3] Update `gateway/platforms/__init__.py` to expose Open WebUI adapter
- [ ] T066 [US3] Update `gateway/config.py` to add `OPENWEBUI = "openwebui"` platform enum
- [ ] T067 [US3] Update `gateway/platform_registry.py` to register the Open WebUI entry

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Converge All Surfaces on Shared Agent Loop and State (Priority: P4)

**Goal**: Ensure TUI, Discord, and Open WebUI all feed into the same agent conversation loop, skill surface, and `state.db`

**Independent Test**: Start a session in Discord, send a directive, then open the TUI for the same session ID and verify history and agent state are consistent

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T068 [P] [US4] Integration test: Discord session turn count visible in TUI within 1 second of state commit
- [ ] T069 [P] [US4] Integration test: Open WebUI session visible in Discord bot quote

### Implementation for User Story 4

- [ ] T070 [US4] Verify `gateway/session.py` is platform-agnostic and unchanged — shared state layer intact
- [ ] T071 [US4] Verify `gateway/session_context.py` is platform-agnostic and unchanged
- [ ] T072 [US4] Verify `hermes_state.py` is platform-agnostic and unchanged
- [ ] T073 [US4] Update `gateway/run.py` to ensure Open WebUI adapter uses the same `AIAgent.chat()` / `run_conversation()` entry point as Discord and TUI
- [ ] T074 [US4] Update `gateway/run.py` to ensure all three surfaces share the same `agent/tool_surface.py` rebuild events
- [ ] T075 [US4] Update `gateway/run.py` to ensure `~/.hermes-lite/queue/curator.jsonl` jobs are surfaced by any gateway when batch threshold is reached
- [ ] T076 [US4] Add session serialization lock per session ID in `gateway/run.py` or `gateway/session.py` to prevent concurrent Discord + Open WebUI turns on the same session (queue or return 409 busy)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, and verification

- [ ] T077 [P] Run `python -c "from gateway.platforms import load_platforms; p=load_platforms(); assert set(p) == {'discord','tui','openwebui'}"` — must complete successfully
- [ ] T078 [P] Run `find gateway/platforms/ -maxdepth 1 -name "*.py" | wc -l` — must return at most 5 files
- [ ] T079 [P] Verify `gateway/platforms/helpers.py` contains only helpers used by retained platforms
- [ ] T080 [P] Verify `gateway/config.py` raises `ConfigurationError` when a removed platform is referenced
- [ ] T081 Run retained gateway tests (Discord-focused) and confirm zero regressions
- [ ] T082 Update `REDESIGN.md` references to deleted platforms if they are now obsolete
- [ ] T083 Update `gateway/platforms/ADDING_A_PLATFORM.md` to document the three-surface allowlist policy
- [ ] T084 Update `specs/001-gateway-cleanup/` status to Complete

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P3)**: Can start after US1 (deleted platforms won't collide with new adapter) — Creates new code
- **User Story 4 (P4)**: Can start after US1 and US3 — Requires both deletions and new adapter to be in place

### Within Each User Story

- Deletion tasks (marked [x]) are verified upstream first, then executed
- Import/config removal follows the corresponding file deletions
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All deletion tasks within US1 and US2 can run in parallel
- Open WebUI adapter creation tasks (T059–T067) can run in parallel where they touch different files

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
