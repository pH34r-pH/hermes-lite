---
name: arxiv-discover
description: "Query arXiv API with rate limiting, cache results for 24h, deduplicate against local knowledge repo, and return a markdown candidate list."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arxiv, discover, search, rate-limit, cache, offline]
    related_skills: [arxiv-fetch]
---

# arxiv-discover

## Title
arxiv-discover — ArXiv Paper Discovery

## Description
Accept a user query string, call the arXiv API through `lib/client.py`, and return a deduplicated markdown list of candidate papers. Papers already present in `~/repos/knowledge/papers/<arxiv-id>/` are marked as cached. Results are served from the 24-hour TTL disk cache when available. If the daily 1000-result cap is reached, a warning is emitted and only cached results are returned. When offline, stale cache entries are returned with a note.

## Trigger Conditions
- User invokes `/arxiv "<query>"` (first step of the sequential pipeline)
- User invokes `/arxiv discover "<query>"`

## Inputs
- `query` (str): Free-text search query
- `max_results` (int, optional): Number of results to fetch (default 10)

## Outputs
- Markdown list of candidate papers with:
  - Title
  - Authors
  - arXiv ID
  - Categories
  - Cached indicator ✓ if already in knowledge repo
- Rate-limit warning when daily cap reached
- Offline note when serving stale cache

## Procedure
1. Normalize query string and compute cache key
2. Check `ArxivQueryCache`; return fresh cached results immediately if hit
3. Check `ArxivRateLimiter.cap_reached()`; emit warning and serve stale cache if capped
4. Call `ArxivClient.search(query, max_results)`:
   - Wait for rate-limit token
   - Retry up to 3× with jittered backoff on 5xx
   - On persistent failure, return stale cache or empty result
5. For each result, check `PaperStore.exists(arxiv_id)`; mark cached papers
6. Add each result to `ReadingList` with status `discovered`
7. Return markdown candidate list

## Notes
- Malformed XML responses are logged to `~/.hermes-lite/cache/arxiv/malformed/` for curator review rather than crashing the agent loop.
- Offline new queries return an empty result with a clear message and no network errors.
- **Full implementation is pending.** This stub establishes the skill shape and loading contract for the arxiv-research bundle.
