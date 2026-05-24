# Implementation Plan: arXiv Research Skill Bundle

**Branch**: `006-arxiv-research-bundle` | **Date**: 2026-05-24 | **Spec**: `specs/006-arxiv-research-bundle/spec.md`

**Input**: Feature specification from `/specs/006-arxiv-research-bundle/spec.md`

## Summary

Ship a complete `skills/research/arxiv/` skill bundle exposed through a single `/arxiv` slash command. The bundle implements a sequential, 3B-model-friendly research pipeline with six skills: `arxiv-discover`, `arxiv-fetch`, `arxiv-skim`, `arxiv-extract`, `arxiv-compare`, and `arxiv-write`. A strict rate-limiting layer guards the arXiv API (1 req / 3 s, jittered backoff, 1000-results-per-day soft cap). Fetched PDFs and metadata are content-addressed and cached in the knowledge repo (`~/repos/knowledge`). The final skill can emit a `spec-seed.json` envelope that hands off to the spec-kit bundle, closing the research → spec → implement loop. All skills bind to the `research` memory profile for isolation.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: `feedparser` (Atom/XML parsing), `requests` (arXiv API + PDF download), existing `tools/registry.py`, existing `agent/skill_commands.py`, existing `agent/tool_surface.py` (spec 003), existing memory-profile subsystem (spec 013)

**Storage**: `~/repos/knowledge/papers/<arxiv-id>/paper.pdf`, `~/repos/knowledge/papers/<arxiv-id>/metadata.json`, `~/repos/knowledge/papers/<arxiv-id>/skim.md`, `~/repos/knowledge/papers/<arxiv-id>/extract.json`, `~/repos/knowledge/notes/<topic>.md`, `~/repos/knowledge/seeds/<feature>.json`, `~/.hermes-lite/cache/arxiv/` (24-hour TTL query cache), `~/.hermes-lite/cache/arxiv/rate-limit-state.json`

**Testing**: pytest

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: Skill bundle — six markdown skill definitions plus Python support modules

**Performance Goals**: Discovery query served from cache in under 5 seconds; fresh query (including rate-limit delay) in under 10 seconds; `arxiv-fetch` downloads a 10-page PDF and writes `metadata.json` within 30 seconds; `arxiv-skim` processes a 50-page paper in under 5 minutes on Jetson 25 W power mode without context overflow

**Constraints**: Must degrade gracefully when the cyberdeck is offline; must never re-download a paper with the same arXiv ID; must chunk long papers so no single inference call exceeds the 3B model ~32k token context window (target 16k token chunks); must honor the per-kit tool-call-failure budget of 3 (spec 005)

**Scale/Scope**: Six SKILL.md files, one bundle manifest YAML, one Python rate-limiter module, one Python cache module, one Python arXiv client module, and integration wiring into `agent/tool_surface.py` for sequential skill surfacing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Rate limiting and identifying `User-Agent` prevent abuse of the arXiv API. Content-addressed storage prevents cache-poisoning via path manipulation.
- **Defense in Depth**: The bundle loads and unloads skills sequentially through `agent/tool_surface.py`, exposing only the active skill's toolset to the model at any turn, minimizing the attack surface.
- **Secure Defaults**: Offline degradation returns cached results or clear empty-result messages rather than crashing. Daily 1000-result soft cap prevents runaway discovery loops.
- **Dependency Management**: `feedparser` and `requests` are lightweight and widely available; no heavy ML frameworks added.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/006-arxiv-research-bundle/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
skills/research/arxiv/
├── SKILL.md                    # Root skill bundle descriptor (sequential pipeline overview)
├── arxiv-discover/SKILL.md     # Skill 1 — query arXiv API, rate limit, cache, deduplicate
├── arxiv-fetch/SKILL.md        # Skill 2 — download PDF + metadata into knowledge repo
├── arxiv-skim/SKILL.md         # Skill 3 — section-by-section markdown skim with page citations
├── arxiv-extract/SKILL.md      # Skill 4 — structured JSON extraction (claims, methods, datasets, results, limitations)
├── arxiv-compare/SKILL.md      # Skill 5 — markdown comparison table across reading list
├── arxiv-write/SKILL.md        # Skill 6 — research note with resolved citations + optional spec-seed.json
├── manifest.yaml               # Bundle manifest registering /arxiv slash command
└── lib/
    ├── __init__.py
    ├── rate_limiter.py         # ArxivRateLimiter — token bucket, jittered backoff, daily cap
    ├── query_cache.py          # ArxivQueryCache — TTL disk cache with 24-hour expiration
    ├── client.py               # ArxivClient — API requests, XML parsing, defensive error handling
    ├── paper_store.py          # ArxivPaper — content-addressed knowledge-repo I/O
    └── reading_list.py         # ReadingList — research memory profile integration

~/.hermes-lite/cache/arxiv/     # Runtime query cache directory (created on first use)
~/.hermes-lite/skill-bundles/arxiv.yaml  # Bundle alias (optional, or use manifest.yaml)

agent/
└── tool_surface.py             # UPDATE — register arxiv kit allowlist (spec 003 integration point)
```

**Structure Decision**: Single skill bundle under `skills/research/arxiv/`. Each skill is a self-contained `SKILL.md` invoked sequentially by the master `SKILL.md`. Python support modules live in `lib/` adjacent to the skills. The bundle manifest registers `/arxiv` as a slash command that loads the sequential pipeline.

## Complexity Tracking

> No violations. The feature introduces one skill bundle with six markdown skill files and a small Python support library (~400–600 LOC total). No new subprojects, persistence layers, or service boundaries introduced beyond the knowledge repo and a disk cache.
