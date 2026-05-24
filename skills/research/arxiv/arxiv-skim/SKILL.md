---
name: arxiv-skim
description: "Produce a section-by-section markdown skim with page-aware citations. Chunk long papers to fit the 3B model context window."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arxiv, skim, summary, pdf, chunking, markdown]
    related_skills: [arxiv-fetch, arxiv-extract]
---

# arxiv-skim

## Title
arxiv-skim — Section-by-Section Paper Skim

## Description
Read a cached PDF from `~/repos/knowledge/papers/<arxiv-id>/paper.pdf`, extract text, and produce `skim.md` with section headings and page-aware citations. Long papers (>50 pages or >16k tokens) are processed in chunks; the full text is never loaded into the 3B model context window at once. When section boundaries are unclear, fall back to fixed-page chunking with a 2-page overlap to preserve context.

## Trigger Conditions
- User asks "summarize this paper" after a fetch
- User invokes `/arxiv skim <arxiv-id>`
- Sequential pipeline step after `arxiv-fetch`

## Inputs
- `arxiv_id` (str): arXiv ID of a previously fetched paper

## Outputs
- `~/repos/knowledge/papers/<arxiv-id>/skim.md`
  - Section headings
  - Condensed per-section summaries
  - Page citations in parentheses, e.g. `(p. 7)`

## Procedure
1. Verify `PaperStore.exists(arxiv_id)`; abort with clear message if not fetched
2. Extract text from `paper.pdf` using lightweight PDF text extraction
3. Detect section boundaries (Introduction, Methods, Results, ...)
4. If text fits in ~16k tokens:
   a. Generate full skim in one inference call
5. Else:
   a. Chunk by section (or fixed 8-page chunks with 2-page overlap)
   b. Generate partial skims per chunk
   c. Synthesize final `skim.md` from partial outputs
6. Write result via `PaperStore.write_skim()`
7. Update `ReadingList.update_status(arxiv_id, "skimmed")`

## Notes
- Prefer existing environment PDF libraries; add new dependencies only if necessary.
- **Full implementation is pending.** This stub establishes the skill shape and loading contract for the arxiv-research bundle.
