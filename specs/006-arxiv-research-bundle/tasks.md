# Tasks: arXiv Research Skill Bundle

**Input**: Design documents from `/specs/006-arxiv-research-bundle/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structure, module scaffold, and upstream integration points

- [x] T001 Create `skills/research/arxiv/` directory tree: `arxiv-discover/`, `arxiv-fetch/`, `arxiv-skim/`, `arxiv-extract/`, `arxiv-compare/`, `arxiv-write/`, `lib/`
- [x] T002 Create `skills/research/arxiv/manifest.yaml` — bundle manifest exposing `/arxiv` slash command with sequential skill list
- [ ] T003 Verify `agent/tool_surface.py` (spec 003) kit allowlist infrastructure exists; document `arxiv` kit registration point
- [ ] T004 Verify `plugins/memory/` (spec 013) exposes `research` memory profile; document profile binding hook
- [x] T005 Verify `~/.hermes-lite/` directory exists (spec 005); create `~/.hermes-lite/cache/arxiv/` with `0700` permissions
- [x] T006 Add `skills/research/arxiv/lib/__init__.py` scaffold with module docstring and version constant

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Python support modules that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Implement `ArxivRateLimiter` class in `skills/research/arxiv/lib/rate_limiter.py`
  - Token bucket enforcing 1 request per 3 seconds
  - Jittered exponential backoff (base 2, max 30 seconds)
  - Daily 1000-result soft cap with persistent counter in `~/.hermes-lite/cache/arxiv/rate-limit-state.json`
  - Identifying `User-Agent` header containing cyberdeck identifier and contact address
- [x] T008 Implement `ArxivQueryCache` class in `skills/research/arxiv/lib/query_cache.py`
  - TTL-based disk cache under `~/.hermes-lite/cache/arxiv/`
  - 24-hour expiration per query key (normalized query string + max_results)
  - Store Atom/XML feed response as gzip-compressed text
  - Offline-aware: return stale entries with a warning flag when network is unreachable
- [x] T009 Implement `ArxivClient` class in `skills/research/arxiv/lib/client.py`
  - Query arXiv API via `requests` with `feedparser` for Atom/XML parsing
  - Defensive parsing: malformed XML logs payload for curator review rather than crashing
  - Return structured list of `{arxiv_id, title, authors, abstract, categories, published, updated, pdf_url}`
  - Integrate `ArxivRateLimiter` and `ArxivQueryCache`
- [x] T010 Implement `ArxivPaper` dataclass and `PaperStore` in `skills/research/arxiv/lib/paper_store.py`
  - Content-addressed storage at `~/repos/knowledge/papers/<arxiv-id>/`
  - Files: `paper.pdf`, `metadata.json`, `skim.md`, `extract.json`
  - `exists(arxiv_id) -> bool` cache-hit check
  - `write_metadata(arxiv_id, metadata)` and `read_metadata(arxiv_id)` helpers
  - Disk-budget guard: refuse new fetches when `~/repos/knowledge/` exceeds ~60 GB
- [x] T011 Implement `ReadingList` class in `skills/research/arxiv/lib/reading_list.py`
  - Bind to `research` memory profile via `plugins/memory/` adapter
  - Store active papers with status: `discovered`, `fetched`, `skimmed`, `extracted`, `fetch_failed`
  - Methods: `add()`, `get()`, `list_active()`, `update_status()`, `get_cross_refs()`
- [x] T012 Implement `skills/research/arxiv/SKILL.md` — root bundle descriptor that documents the sequential pipeline and delegates to each sub-skill

**Checkpoint**: Foundation ready — rate limiter, cache, client, paper store, and reading list exist; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Discover and Cache Papers Offline (Priority: P1) 🎯 MVP

**Goal**: Entry-point research loop that queries arXiv, deduplicates against the knowledge repo, caches results for 24 hours, and degrades gracefully offline

**Independent Test**: Run `/arxiv "quantum error correction"`, verify results appear, repeat within 24 hours and confirm zero network requests via HTTP traffic intercept

### Tests for User Story 1

- [ ] T013 [P] [US1] Unit test: `ArxivQueryCache` stores and retrieves a query result within TTL in `tests/unit/test_arxiv_query_cache.py`
- [ ] T014 [P] [US1] Unit test: `ArxivRateLimiter` enforces at least 3 seconds between API requests in `tests/unit/test_arxiv_rate_limiter.py`
- [ ] T015 [P] [US1] Unit test: offline mode returns cached results with a warning flag in `tests/unit/test_arxiv_client.py`
- [ ] T016 [P] [US1] Integration test: repeated query within 24 hours produces zero HTTP requests in `tests/integration/test_arxiv_discover.py`

### Implementation for User Story 1

- [x] T017 [US1] Write `skills/research/arxiv/arxiv-discover/SKILL.md` — skill definition for querying arXiv
  - Accept user query string
  - Call `ArxivClient.search(query)` with rate limit and cache
  - Deduplicate against `PaperStore.exists()` and mark cached papers
  - Return markdown list of candidates with title, authors, arXiv ID, and cached indicator
  - Emit rate-limit warning when daily 1000-result cap is reached
- [x] T018 [US1] Wire `arxiv-discover` into root `SKILL.md` as the first sequential step
- [ ] T019 [US1] Add `arxiv` kit allowlist entry to `agent/tool_surface_allowlists.yaml` (or equivalent spec 003 artifact)
- [ ] T020 [US1] Handle malformed XML: log malformed payload path under `~/.hermes-lite/cache/arxiv/malformed/` for curator review
- [ ] T021 [US1] Handle offline new query: return empty result with clear offline message and no network errors

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fetch and Persist Papers in the Knowledge Repo (Priority: P1)

**Goal**: Download PDFs and metadata into the knowledge repo with content-addressed deduplication and memory profile registration

**Independent Test**: Select `arXiv:2501.12345`, run `arxiv-fetch`, verify directory structure, file presence, and `research` memory profile entry

### Tests for User Story 2

- [ ] T022 [P] [US2] Unit test: `PaperStore.write_metadata()` creates `~/repos/knowledge/papers/2501.12345/metadata.json` in `tests/unit/test_paper_store.py`
- [ ] T023 [P] [US2] Unit test: duplicate fetch detects cache hit and skips download in `tests/unit/test_paper_store.py`
- [ ] T024 [P] [US2] Unit test: 503 response triggers jittered backoff and surfaces failure after max retries in `tests/unit/test_arxiv_client.py`
- [ ] T025 [P] [US2] Integration test: fetch registers paper in `research` memory profile in `tests/integration/test_arxiv_fetch.py`

### Implementation for User Story 2

- [x] T026 [US2] Write `skills/research/arxiv/arxiv-fetch/SKILL.md` — skill definition for downloading papers
  - Accept selected arXiv ID(s) from user or prior `arxiv-discover` result
  - Download PDF to `~/repos/knowledge/papers/<arxiv-id>/paper.pdf`
  - Write `metadata.json` with keys: `title`, `authors`, `abstract`, `categories`, `published`, `updated`
  - Skip download if `paper.pdf` already exists (content-addressed by arXiv ID)
  - On 503: retry once with jittered backoff, then mark as `fetch_failed` in reading list
  - On disk-full: emit warning and refuse new fetches
- [x] T027 [US2] Wire `arxiv-fetch` into root `SKILL.md` as the second sequential step
- [ ] T028 [US2] Integrate `ReadingList.update_status(arxiv_id, "fetched")` and `ReadingList.update_status(arxiv_id, "fetch_failed")` on outcomes
- [ ] T029 [US2] Add fetch-failure edge-case handling: corrupted PDF detection via PyPDF2 or pdfminer header check (optional, log warning if unavailable)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Skim and Extract Structured Data (Priority: P2)

**Goal**: Transform raw PDFs into usable research artifacts — section-by-section skim and structured JSON extraction

**Independent Test**: Run `arxiv-skim` and `arxiv-extract` against a cached paper and verify output files exist and conform to expected schema

### Tests for User Story 3

- [ ] T030 [P] [US3] Unit test: `arxiv-skim` chunking strategy splits a 50-page text into ≤16k token chunks in `tests/unit/test_arxiv_skim.py`
- [ ] T031 [P] [US3] Unit test: `arxiv-extract` produces valid `extract.json` with required keys in `tests/unit/test_arxiv_extract.py`
- [ ] T032 [P] [US3] Unit test: fallback fixed-page chunking with overlap when no clear section boundaries exist in `tests/unit/test_arxiv_skim.py`
- [ ] T033 [P] [US3] Integration test: end-to-end skim + extract produces `skim.md` and `extract.json` in `tests/integration/test_arxiv_skim_extract.py`

### Implementation for User Story 3

- [x] T034 [US3] Write `skills/research/arxiv/arxiv-skim/SKILL.md` — skill definition for section-by-section skimming
  - Read cached PDF from `~/repos/knowledge/papers/<arxiv-id>/paper.pdf`
  - Extract text (use existing `tools/read_file.py` or lightweight PDF text extraction)
  - Produce `skim.md` with section headings and page-aware citations
  - Chunk long papers (>50 pages) into ≤16k token sections; never load full text into 3B context at once
  - Fallback: fixed-page chunking with 2-page overlap when section boundaries are unclear
- [x] T035 [US3] Write `skills/research/arxiv/arxiv-extract/SKILL.md` — skill definition for structured extraction
  - Read `skim.md` and/or PDF text
  - Produce `extract.json` with keys: `claims`, `methods`, `datasets`, `results`, `limitations`
  - Reference table/figure numbers in `results` without hallucinating values
  - Permissive JSON recovery mode for trailing commas or invalid JSON from the 3B model
  - Surface parse errors for hand-correction
- [x] T036 [US3] Wire `arxiv-skim` and `arxiv-extract` into root `SKILL.md` as steps three and four
- [ ] T037 [US3] Update `ReadingList.update_status()` for `skimmed` and `extracted` states

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Compare Papers and Write a Research Note (Priority: P2)

**Goal**: Synthesize findings across multiple papers, produce a research note with resolved citations, and optionally emit a `spec-seed.json` envelope

**Independent Test**: Select two papers, run `arxiv-compare`, then `arxiv-write`, verify output files and memory state

### Tests for User Story 4

- [ ] T038 [P] [US4] Unit test: `arxiv-compare` produces markdown table comparing claims, methods, and results across two `extract.json` files in `tests/unit/test_arxiv_compare.py`
- [ ] T039 [P] [US4] Unit test: `arxiv-write` produces `~/repos/knowledge/notes/<topic>.md` with local PDF citation links in `tests/unit/test_arxiv_write.py`
- [ ] T040 [P] [US4] Unit test: explicit user confirmation triggers `spec-seed.json` emission; absence suppresses it in `tests/unit/test_arxiv_write.py`
- [ ] T041 [P] [US4] Integration test: end-to-end compare + write + seed emission in `tests/integration/test_arxiv_compare_write.py`

### Implementation for User Story 4

- [x] T042 [US4] Write `skills/research/arxiv/arxiv-compare/SKILL.md` — skill definition for paper comparison
  - Accept list of arXiv IDs from active reading list
  - Read `extract.json` for each paper
  - Produce markdown comparison table with claims, methods, and results cross-references
  - Store comparison cross-references in `research` memory profile
- [x] T043 [US4] Write `skills/research/arxiv/arxiv-write/SKILL.md` — skill definition for research note drafting
  - Accept topic string from user
  - Write `~/repos/knowledge/notes/<topic-slug>.md` with inline citation links to local PDF paths
  - Use `LocalRepoWorkspace` (spec 010) for commits if available; otherwise write atomically (temp + rename) and notify user to commit manually
  - On explicit user confirmation "propose a spec from this": emit `~/repos/knowledge/seeds/<feature-slug>.json` containing `title`, `summary`, `problem_statement`, `candidate_approach`, `citations`, `acceptance_criteria`
  - No seed emitted without explicit confirmation
- [x] T044 [US4] Wire `arxiv-compare` and `arxiv-write` into root `SKILL.md` as steps five and six
- [ ] T045 [US4] Integrate `LocalRepoWorkspace` commit path for notes when available (spec 010)
- [ ] T046 [US4] Document hand-editing conflict handling: atomic write (temp + rename); git surfaces conflict on next commit

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration, sequential skill surfacing, memory profile binding, and final verification

- [ ] T047 Wire sequential skill loading/unloading through `agent/tool_surface.py` — only the active skill's toolset is exposed per turn
- [ ] T048 Bind the `arxiv` kit to the `research` memory profile on load (spec 013 integration)
- [ ] T049 Verify rate limiter enforces at least 3 seconds between API requests via timestamp deltas in `logs/tools.jsonl`
- [ ] T050 Verify daily 1000-result cap surfaces a clear warning and continues to serve cached results
- [ ] T051 Verify `arxiv-write` spec-seed JSON conforms to schema expected by `spec-specify` (spec 007)
- [ ] T052 [P] Run retained unit-test suite and confirm zero regressions in skill loading or tool registry
- [ ] T053 Update `agent/tool_surface_allowlists.yaml` with finalized `arxiv` kit tool names after skill audit
- [ ] T054 Update `REDESIGN.md` §5.4, §8, §12.5 references to reflect completed implementation
- [ ] T055 Update `specs/006-arxiv-research-bundle/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on discovery output; can be tested with hardcoded IDs
- **User Story 3 (P2)**: Can start after US2 delivers a working fetch — Needs cached papers
- **User Story 4 (P2)**: Can start after US3 delivers skim/extract — Needs `extract.json` files

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Support library before skill markdown
- Core skill before integration into root SKILL.md
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel
- All tests for a user story marked [P] can run in parallel
- US3 and US4 sequential processing can be drafted in parallel but integration-tested sequentially

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (`/arxiv "query"` returns results, cache works, offline degrades gracefully)
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
   - Developer A: User Story 1 (discover + cache)
   - Developer B: User Story 2 (fetch + persist)
3. Once US2 is done:
   - Developer C: User Story 3 (skim + extract)
   - Developer D: User Story 4 (compare + write)
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
- The `arxiv` kit MUST honor the per-kit tool-call-failure budget of 3 (spec 005)
- The `research` memory profile MUST be bound on kit load and unbound on kit unload (spec 013)
- All PDF text extraction should prefer lightweight libraries already in the environment; add new dependencies only if absolutely necessary and document in `plan.md` Technical Context
