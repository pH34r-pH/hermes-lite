---
name: arxiv-write
description: "Draft a research note with resolved local citations. Optionally emit a spec-seed.json envelope on explicit user confirmation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [arxiv, write, research-note, spec-seed, synthesis]
    related_skills: [arxiv-compare, spec-kit]
---

# arxiv-write

## Title
arxiv-write — Research Note Drafting

## Description
Accept a topic string from the user, synthesize findings from the active reading list (extracts, skims, and comparisons), and draft a research note saved to `~/repos/knowledge/notes/<topic-slug>.md`. All citations are resolved to local PDF paths. If the user explicitly confirms "propose a spec from this", emit `~/repos/knowledge/seeds/<feature-slug>.json` containing a structured spec-seed envelope (title, summary, problem statement, candidate approach, citations, acceptance criteria). No seed file is emitted without explicit confirmation.

## Trigger Conditions
- Sequential pipeline final step after `arxiv-compare`
- User invokes `/arxiv write <topic>`
- User replies "propose a spec from this" after a research note

## Inputs
- `topic` (str): Research note topic / title
- `arxiv_ids` (list[str], optional): Specific papers to include; defaults to active reading list
- `emit_seed` (bool): True only on explicit user confirmation

## Outputs
- `~/repos/knowledge/notes/<topic-slug>.md`
  - Inline citation links to `../papers/<arxiv-id>/paper.pdf`
- Optionally `~/repos/knowledge/seeds/<feature-slug>.json`
  - `title`, `summary`, `problem_statement`, `candidate_approach`, `citations`, `acceptance_criteria`

## Procedure
1. Gather `extract.json` and `skim.md` for selected papers
2. Prompt the model to synthesize a cohesive research note
3. Resolve citation placeholders to local PDF paths
4. Write note atomically (temp + rename) to avoid conflicts with hand-editing
5. If `emit_seed` is true:
   a. Prompt model to generate spec-seed JSON matching the spec-kit schema
   b. Write `seeds/<feature-slug>.json` atomically
   c. Notify user of the hand-off path to `/spec`
6. Return summary of written artifacts

## Notes
- If `LocalRepoWorkspace` (spec 010) is available, commit the note through it; otherwise write atomically and ask the user to commit manually.
- Hand-editing conflicts are handled by atomic writes; git surfaces the conflict on the next commit.
- **Full implementation is pending.** This stub establishes the skill shape and loading contract for the arxiv-research bundle.
