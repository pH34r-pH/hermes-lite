---
name: arxiv-extract
description: "Extract structured claims, methods, datasets, results, and limitations into extract.json. Use permissive JSON recovery mode."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arxiv, extract, structured-data, json, claims, methods]
    related_skills: [arxiv-skim, arxiv-compare]
---

# arxiv-extract

## Title
arxiv-extract — Structured Data Extraction

## Description
Read `skim.md` (and/or the raw PDF text) for a cached paper and produce `extract.json` containing structured research artifacts. The expected keys are `claims`, `methods`, `datasets`, `results`, and `limitations`. Table and figure numbers are referenced in `results` without hallucinating values. The JSON parser operates in a permissive recovery mode to handle trailing commas or minor syntax errors from the 3B model; unrecoverable parse errors are surfaced for hand-correction.

## Trigger Conditions
- Sequential pipeline step after `arxiv-skim`
- User invokes `/arxiv extract <arxiv-id>`

## Inputs
- `arxiv_id` (str): arXiv ID of a previously skimmed paper

## Outputs
- `~/repos/knowledge/papers/<arxiv-id>/extract.json`
  - `claims`: list of textual claims made by the paper
  - `methods`: list of methods or techniques described
  - `datasets`: list of datasets used or introduced
  - `results`: list of result summaries with table/figure references where applicable
  - `limitations`: list of stated or inferred limitations

## Procedure
1. Verify `PaperStore.skim_path(arxiv_id)` exists; abort if missing
2. Load skim text and chunk if necessary to fit context budget
3. Prompt the model to emit structured JSON with the five required keys
4. Parse model output:
   a. Try strict `json.loads()` first
   b. On failure, strip trailing commas and retry
   c. On persistent failure, log error and return raw model text for hand-correction
5. Write valid JSON via `PaperStore.write_extract()`
6. Update `ReadingList.update_status(arxiv_id, "extracted")`

## Notes
- Never fabricate table or figure values; cite their numbers only when visible in the text.
- **Full implementation is pending.** This stub establishes the skill shape and loading contract for the arxiv-research bundle.
