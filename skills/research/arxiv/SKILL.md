---
name: arxiv-research
description: "Root bundle descriptor for the arXiv research pipeline. Exposes /arxiv slash command with 6 sequential skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arxiv-research, bundle, pipeline, academic, offline]
    related_skills: [spec-kit, local-repo-workspace]
    memory_profiles: [research]
---

# ArXiv Research Skill Bundle

The `arxiv-research` bundle implements a complete offline-capable academic literature review pipeline. It exposes the `/arxiv` slash command and provides six sequential skills, each sized for a 3B model context.

## Sequential Pipeline

1. **arxiv-discover** — Query the arXiv API, apply rate limits and 24h caching, deduplicate against the local knowledge repo
2. **arxiv-fetch** — Download PDF and metadata into `~/repos/knowledge/papers/<arxiv-id>/`, skip if already cached
3. **arxiv-skim** — Read the cached PDF and produce `skim.md` with section headings and page-aware citations
4. **arxiv-extract** — Read `skim.md` and produce `extract.json` with claims, methods, datasets, results, and limitations
5. **arxiv-compare** — Read `extract.json` from multiple papers and produce a markdown comparison table
6. **arxiv-write** — Draft a research note in `~/repos/knowledge/notes/<topic>.md` with local citation links; optionally emit `spec-seed.json`

## Approval Gates

- **research→spec**: Mandatory user confirmation before `arxiv-write` emits a `spec-seed.json` envelope

## Delegation Rules

- Each skill is loaded/unloaded one at a time via `agent/tool_surface.py`
- Only the active skill's toolset is exposed per turn
- The bundle binds to the `research` memory profile on load
- All network calls route through `lib/client.py` which enforces rate limits (1 req / 3 s, jittered backoff, 1000-result daily cap)
- Offline mode returns cached results or clear empty-result messages rather than crashing

## Artifacts

| Artifact | Producer | Consumers |
|----------|----------|-----------|
| Query results (cached) | arxiv-discover | arxiv-fetch |
| `paper.pdf` | arxiv-fetch | arxiv-skim |
| `metadata.json` | arxiv-fetch | arxiv-skim, arxiv-extract, arxiv-compare |
| `skim.md` | arxiv-skim | arxiv-extract |
| `extract.json` | arxiv-extract | arxiv-compare, arxiv-write |
| `compare.md` | arxiv-compare | arxiv-write |
| `notes/<topic>.md` | arxiv-write | user |
| `seeds/<feature>.json` | arxiv-write | spec-kit |

## Rate Limits & Caching

- **Rate limit**: 1 request per 3 seconds with jittered exponential backoff (base 2, max 30 s)
- **Daily cap**: 1000 results per day; subsequent queries serve from cache only
- **Query cache**: 24-hour TTL under `~/.hermes-lite/cache/arxiv/`, gzip-compressed, stale returns allowed when offline
- **User-Agent**: Identifying header with cyberdeck identifier and contact address

## Notes

This bundle requires `requests` and optionally `feedparser`. If `feedparser` is unavailable, `lib/client.py` falls back to `xml.etree.ElementTree` for Atom/XML parsing.
