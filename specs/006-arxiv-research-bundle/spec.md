# Feature Specification: arXiv Research Skill Bundle

**Feature Branch**: `006-arxiv-research-bundle`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New skills/research/arxiv/ bundle with 6 sequential skills (arxiv-discover, arxiv-fetch, arxiv-skim, arxiv-extract, arxiv-compare, arxiv-write). Rate limits, caching, knowledge repo integration. Read REDESIGN.md §5.4, §8, §12.5."

## Current State

Upstream Hermes Agent ships a broad `skills/research/` tree with general web search, news aggregation, and domain-specific lookup skills. There is **no arXiv-specific research bundle**, no dedicated rate-limited arXiv API client, no structured paper-extraction pipeline, and no integration with a local knowledge repository. Papers found via generic web search are not cached locally, not deduplicated against a local store, and do not produce structured `spec-seed.json` envelopes that can feed a downstream spec-driven development loop. The upstream agent has no concept of a `research` memory profile scoped to academic literature.

## Target State

Hermes-lite ships a complete `skills/research/arxiv/` skill bundle exposed through a single `/arxiv` slash command. The bundle implements a sequential, 3B-model-friendly research pipeline: discover papers, fetch and cache them, skim section-by-section, extract structured claims and methods, compare across a reading list, and write a research note with resolved citations. All artifacts live in the dedicated **knowledge repo** (`~/repos/knowledge`) registered as a first-class workspace. A strict rate-limiting layer (1 request / 3 s, jittered backoff, 1000-results-per-day soft cap, identifying `User-Agent`) guards the arXiv API. Fetched PDFs and metadata are content-addressed and never re-downloaded. The final skill (`arxiv-write`) can emit a `spec-seed.json` envelope that hands off to the spec-kit bundle (§5.10), closing the research → spec → implement loop.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and Cache Papers Offline (Priority: P1)

A user on the cyberdeck (potentially offline) issues `/arxiv "small model alignment 2026"` and receives a deduplicated list of candidate papers, with hits already present in the local knowledge repo marked as cached.

**Why this priority**: Discovery is the entry point of the research loop. Without it, no downstream skills have input. Offline-awareness is critical to the cyberdeck use case.

**Independent Test**: Can be fully tested by running `/arxiv` with a query, verifying that results appear, and confirming that a repeated query within 24 hours does not hit the network.

**Acceptance Scenarios**:

1. **Given** the user types `/arxiv "quantum error correction"`, **When** `arxiv-discover` runs, **Then** it returns a markdown list of candidate papers with title, authors, arXiv ID, and cached indicator
2. **Given** the same query is repeated within 24 hours, **When** `arxiv-discover` runs, **Then** it serves results from the local cache without making an API request
3. **Given** the cyberdeck is offline, **When** the user repeats a previously cached query, **Then** cached results are still returned with a note that the network is unreachable
4. **Given** a new query is issued while offline, **When** `arxiv-discover` runs, **Then** it returns an empty result with a clear offline message and no network errors

---

### User Story 2 - Fetch and Persist Papers in the Knowledge Repo (Priority: P1)

After selecting papers from the discovery list, the user confirms a subset and `arxiv-fetch` downloads PDFs and metadata into `~/repos/knowledge/papers/<arxiv-id>/`, extracts metadata, and registers the paper in the `research` memory profile.

**Why this priority**: Local persistence is what makes the research loop usable offline and what enables downstream skim/extract/compare operations without repeated downloads.

**Independent Test**: Can be fully tested by selecting a paper, running `arxiv-fetch`, and verifying the directory structure, file presence, and memory profile entry.

**Acceptance Scenarios**:

1. **Given** the user selects `arXiv:2501.12345`, **When** `arxiv-fetch` runs, **Then** the PDF is saved to `~/repos/knowledge/papers/2501.12345/paper.pdf` and metadata to `metadata.json`
2. **Given** the same paper is fetched again, **When** `arxiv-fetch` runs, **Then** it detects the content-addressed cache hit and skips the download
3. **Given** the arXiv API returns a 503 error, **When** `arxiv-fetch` retries, **Then** it applies the configured jittered backoff and surfaces the failure after max retries
4. **Given** the paper is successfully fetched, **When** the `research` memory profile is queried, **Then** the paper appears in the active reading list with title, ID, and fetch timestamp

---

### User Story 3 - Skim and Extract Structured Data (Priority: P2)

The user asks for a summary of a fetched paper. `arxiv-skim` produces a stable, section-by-section skim with page-aware citations. `arxiv-extract` then writes a structured JSON (`extract.json`) containing claims, methods, datasets, and results.

**Why this priority**: Skimming and extraction transform raw PDFs into usable research artifacts. The structured JSON is the input to comparison and spec-seed generation.

**Independent Test**: Can be fully tested by running `arxiv-skim` and `arxiv-extract` against a cached paper and verifying that the output files exist and conform to the expected schema.

**Acceptance Scenarios**:

1. **Given** a cached paper at `papers/2501.12345/`, **When** `arxiv-skim` runs, **Then** it produces a markdown skim with section headings and page citations, saved as `skim.md`
2. **Given** the same paper, **When** `arxiv-extract` runs, **Then** it writes `extract.json` with keys `claims`, `methods`, `datasets`, `results`, `limitations`
3. **Given** a very long paper (>50 pages), **When** `arxiv-skim` runs, **Then** it processes the paper in chunked sections, never loading the full text into the 3B model context window at once
4. **Given** the paper contains tables and figures, **When** `arxiv-extract` runs, **Then** it attempts to reference table/figure numbers in the `results` array without hallucinating values

---

### User Story 4 - Compare Papers and Write a Research Note (Priority: P2)

The user asks to compare multiple papers on their reading list. `arxiv-compare` generates a markdown comparison table with cross-references stored in memory. `arxiv-write` then drafts a research note with citations resolved to local PDFs, saved in the knowledge repo.

**Why this priority**: Comparison and synthesis are the value-add of the research bundle. The research note is the artifact that can be shared, version-controlled, and converted into a spec seed.

**Independent Test**: Can be fully tested by selecting two papers, running `arxiv-compare`, then running `arxiv-write`, and verifying the output files and memory state.

**Acceptance Scenarios**:

1. **Given** two papers with `extract.json` files, **When** `arxiv-compare` runs, **Then** it produces a markdown table comparing claims, methods, and results across both papers
2. **Given** the comparison exists, **When** `arxiv-write` runs with topic "alignment survey", **Then** it writes `~/repos/knowledge/notes/alignment-survey.md` with inline citation links to local PDFs
3. **Given** the user replies "propose a spec from this", **When** `arxiv-write` completes, **Then** it emits `~/repos/knowledge/seeds/alignment-survey.json` containing title, summary, problem statement, candidate approach, citations, and acceptance criteria draft
4. **Given** the user does not request a spec seed, **When** `arxiv-write` completes, **Then** only the note is written and no seed file is emitted

---

### Edge Cases

- What happens when the arXiv API returns malformed XML/Atom feeds? The client must parse defensively and log the malformed payload for curator review, rather than crashing the agent loop.
- How does the system handle PDFs that fail to download (404, paywall redirect, corrupted file)? It must retry once, then mark the paper as `fetch_failed` in the reading list and surface the issue to the user.
- What happens when the daily 1000-result soft cap is reached? Subsequent discovery queries must return cached results only and emit a rate-limit warning to the user.
- What happens when the knowledge repo disk budget (§7.4, ~60 GB) is exhausted? The agent must emit a disk-full warning and refuse new fetches until the user frees space.
- How does `arxiv-skim` handle papers with no clear section boundaries? It must fall back to a fixed-page chunking strategy with overlap to preserve context.
- What happens when `arxiv-extract` encounters trailing commas or invalid JSON from the 3B model? The JSON parser must use a permissive recovery mode and surface the parse error for hand-correction.
- What happens when the user hand-edits a note in the knowledge repo while `arxiv-write` is working? `arxiv-write` must create the note atomically (write to temp, then rename) and rely on git to surface the conflict on commit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a new `skills/research/arxiv/` directory with a manifest entry exposing `/arxiv` as a single slash command
- **FR-002**: `arxiv-discover` MUST query the arXiv API with a strict rate limit of 1 request per 3 seconds with jittered exponential backoff
- **FR-003**: `arxiv-discover` MUST enforce a 1000-results-per-day soft cap and emit a warning when the cap is reached
- **FR-004**: `arxiv-discover` MUST send an identifying `User-Agent` header containing the cyberdeck identifier and a contact address
- **FR-005**: `arxiv-discover` MUST deduplicate results against the local knowledge repo and mark cached papers
- **FR-006**: `arxiv-discover` MUST cache query results for 24 hours to prevent redundant API calls
- **FR-007**: `arxiv-fetch` MUST download PDFs and metadata into `~/repos/knowledge/papers/<arxiv-id>/`
- **FR-008**: `arxiv-fetch` MUST use content-addressed storage so the same `<arxiv-id>` is never re-downloaded
- **FR-009**: `arxiv-fetch` MUST extract metadata (title, authors, abstract, categories, published, updated) into `metadata.json`
- **FR-010**: `arxiv-skim` MUST produce a section-by-section markdown skim (`skim.md`) with page-aware citations
- **FR-011**: `arxiv-skim` MUST chunk long papers so that no single inference call exceeds the 3B model context window
- **FR-012**: `arxiv-extract` MUST write `extract.json` with the keys `claims`, `methods`, `datasets`, `results`, and `limitations`
- **FR-013**: `arxiv-compare` MUST generate a markdown comparison table across papers in the active reading list
- **FR-014**: `arxiv-compare` MUST store cross-references in the `research` memory profile
- **FR-015**: `arxiv-write` MUST write research notes to `~/repos/knowledge/notes/<topic>.md` with citations resolved to local PDF paths
- **FR-016**: `arxiv-write` MUST commit notes through the `LocalRepoWorkspace` tool set so they are subject to the same audit log as code changes
- **FR-017**: `arxiv-write` MUST emit `spec-seed.json` to `~/repos/knowledge/seeds/<feature>.json` only on explicit user confirmation
- **FR-018**: The bundle MUST load and unload skills sequentially through `agent/tool_surface.py`, exposing only the active skill's toolset to the model
- **FR-019**: The bundle MUST bind to the `research` memory profile so reading lists, extracts, and notes are isolated from other workflows
- **FR-020**: All skills MUST honor the per-kit tool-call-failure budget (3 failures before escalation, per `lite-config.yaml`)

### Key Entities

- **ArxivPaper**: Represents a cached paper with arXiv ID, metadata, local PDF path, skim markdown, and structured extract JSON.
- **ReadingList**: The active set of papers bound to the `research` memory profile. Contains references to ArxivPaper entities and their processing status.
- **ResearchNote**: A markdown document produced by `arxiv-write`, containing synthesized findings with local citation links.
- **SpecSeed**: A structured JSON envelope emitted by `arxiv-write` that bridges research output into the spec-kit bundle. Contains title, summary, problem statement, candidate approach, citations, and acceptance criteria.
- **ArxivQueryCache**: A TTL-based cache of discovery query results, stored under `~/.hermes-lite/cache/arxiv/` with 24-hour expiration.
- **ArxivRateLimiter**: A client-side rate-limiting token bucket enforcing 1 req/3 s, jittered backoff, and a daily 1000-result soft cap.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A discovery query returns results within 5 seconds when served from cache, and within 10 seconds (including rate-limit delay) for a fresh query
- **SC-002**: Repeating the same query within 24 hours produces zero network requests to the arXiv API, verified by intercepting HTTP traffic
- **SC-003**: `arxiv-fetch` successfully downloads a standard 10-page paper PDF and writes `metadata.json` within 30 seconds
- **SC-004**: `arxiv-skim` processes a 50-page paper in under 5 minutes on the Jetson 25 W power mode, without a single inference context overflow
- **SC-005**: `arxiv-extract` produces a valid `extract.json` matching the required schema in at least 90% of tested papers
- **SC-006**: `arxiv-write` produces a research note with all citation links resolving to local PDF paths, and no broken relative paths
- **SC-007**: The rate limiter enforces at least 3 seconds between successive API requests, verified by timestamp deltas in `logs/tools.jsonl`
- **SC-008**: When the daily 1000-result cap is reached, `arxiv-discover` surfaces a clear warning and continues to serve cached results

## Assumptions

- The knowledge repo (`~/repos/knowledge`) is already cloned and registered in `~/.hermes-lite/workspaces.yaml` as a first-class workspace
- The arXiv API remains freely accessible with the same Atom/XML feed format and bulk PDF links
- The cyberdeck has intermittent or no internet connectivity; the bundle must degrade gracefully to cached content
- Papers are assumed to be standard arXiv preprints with accessible PDFs; papers behind external paywalls or with corrupted PDFs are handled as edge cases
- The `research` memory profile is created by the memory subsystem and available before the arXiv bundle loads
- LocalRepoWorkspace (§5.9) is available for commits to the knowledge repo; if not, `arxiv-write` falls back to writing files and notifying the user to commit manually
- The 3B model context window is approximately 32k tokens; the chunking strategy in `arxiv-skim` targets 16k token chunks to leave room for system prompt and tool schemas
- `spec-seed.json` format is stable and parseable by `spec-specify` in the spec-kit bundle
