---
name: arxiv-fetch
description: "Download PDF and metadata into the knowledge repo. Skip if already cached. Handle 503 retries, disk-full guards, and reading-list status updates."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arxiv, fetch, download, pdf, metadata, knowledge-repo]
    related_skills: [arxiv-discover, arxiv-skim]
---

# arxiv-fetch

## Title
arxiv-fetch — Paper Fetch & Persistence

## Description
Accept one or more arXiv IDs (from user selection or `arxiv-discover` output), download the PDF and metadata, and persist them to `~/repos/knowledge/papers/<arxiv-id>/`. Skip download if `paper.pdf` already exists (content-addressed by arXiv ID). On 503 errors, retry once with jittered backoff, then mark the paper as `fetch_failed` in the reading list. Refuse new fetches if the knowledge repo disk budget (~60 GB) is exhausted.

## Trigger Conditions
- User replies with arXiv IDs after `/arxiv "<query>"`
- User invokes `/arxiv fetch <arxiv-id> ...`

## Inputs
- `arxiv_ids` (list[str]): One or more arXiv IDs to fetch

## Outputs
- `~/repos/knowledge/papers/<arxiv-id>/paper.pdf`
- `~/repos/knowledge/papers/<arxiv-id>/metadata.json` with keys:
  - `title`, `authors`, `abstract`, `categories`, `published`, `updated`
- Reading-list status updated to `fetched` or `fetch_failed`

## Procedure
1. For each arXiv ID:
   a. If `PaperStore.exists(id)` is true, skip with "already cached" note
   b. Resolve PDF URL from metadata (or construct `https://arxiv.org/pdf/<id>.pdf`)
   c. Download PDF via `requests`, respecting `ArxivRateLimiter`
   d. On 503: retry once with backoff; on repeated failure, mark `fetch_failed`
   e. Write PDF atomically via `PaperStore.write_pdf()`
   f. Write metadata via `PaperStore.write_metadata()`
   g. Update `ReadingList.update_status(id, "fetched")`
2. Return summary: fetched, skipped, failed counts

## Notes
- PDF download is done through `requests` with the same identifying `User-Agent`.
- Corrupted PDF detection is optional; if `PyPDF2` or `pdfminer` is available, log a warning on malformed headers.
- **Full implementation is pending.** This stub establishes the skill shape and loading contract for the arxiv-research bundle.
