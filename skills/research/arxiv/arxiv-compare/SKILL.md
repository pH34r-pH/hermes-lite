---
name: arxiv-compare
description: "Generate a markdown comparison table across papers in the active reading list. Store cross-references in the research memory profile."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arxiv, compare, synthesis, reading-list, cross-reference]
    related_skills: [arxiv-extract, arxiv-write]
---

# arxiv-compare

## Title
arxiv-compare — Paper Comparison

## Description
Accept a list of arXiv IDs from the active reading list, read their `extract.json` files, and produce a markdown comparison table comparing claims, methods, datasets, results, and limitations across the selected papers. Cross-references (e.g. "Paper A agrees with Paper B on X") are stored in the `research` memory profile via `ReadingList.add_cross_ref()`.

## Trigger Conditions
- User asks "compare these papers" after extraction
- User invokes `/arxiv compare <arxiv-id> <arxiv-id> ...`
- Sequential pipeline step after `arxiv-extract`

## Inputs
- `arxiv_ids` (list[str]): Two or more arXiv IDs to compare

## Outputs
- Markdown comparison table (returned in conversation or saved to `compare.md`)
- Cross-references stored in `ReadingList`

## Procedure
1. Verify each ID has `extract.json`; abort with missing-paper note if not
2. Load `extract.json` for each paper
3. Build comparison dimensions: claims, methods, datasets, results, limitations
4. Prompt the model to produce a markdown table with papers as columns
5. Extract cross-reference sentences and register them via `ReadingList.add_cross_ref()`
6. Return the comparison table to the user

## Notes
- Works with as few as two papers; no upper limit, but very large sets should be chunked.
- **Full implementation is pending.** This stub establishes the skill shape and loading contract for the arxiv-research bundle.
