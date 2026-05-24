# arxiv-research bundle

A sequential, offline-capable academic literature review pipeline for Hermes-lite.

## Quick Start

```
/arxiv "quantum error correction"
```

This runs `arxiv-discover` to search arXiv, then walks through fetch, skim, extract, compare, and write steps.

## Structure

- `manifest.yaml` — Bundle manifest exposing `/arxiv` slash command
- `SKILL.md` — Root bundle descriptor documenting the sequential pipeline
- `arxiv-*/SKILL.md` — Six skill definitions (discover, fetch, skim, extract, compare, write)
- `lib/` — Python support modules (rate limiter, cache, client, paper store, reading list)

## Dependencies

- `requests`
- `feedparser` (optional; falls back to `xml.etree.ElementTree`)

## Storage

- Papers: `~/repos/knowledge/papers/<arxiv-id>/`
- Notes: `~/repos/knowledge/notes/<topic>.md`
- Seeds: `~/repos/knowledge/seeds/<feature>.json`
- Query cache: `~/.hermes-lite/cache/arxiv/`
