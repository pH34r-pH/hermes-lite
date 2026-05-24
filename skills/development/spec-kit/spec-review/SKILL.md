---
name: spec-review
description: "Invoke the background reviewer over the diff set and surface findings before opening the PR."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, review, background-reviewer, quality-gate]
    related_skills: [spec-analyze, spec-implement]
---

# spec-review

## Title
 spec-review — Pre-PR Background Review

## Description
Invoke the background reviewer over the diff set produced by `spec-implement`. If the background reviewer is disabled, degrade gracefully to a self-check (diff stats, file count, test command presence) and note the degradation in the PR description. Write structured findings (severity, file, line, recommendation) into the workspace journal. Ensure the PR description includes `spec-analyze` results and background-reviewer findings.

## Trigger Conditions
- User invokes `/spec review`
- `spec-implement` completes and the user requests review before opening PR

## Inputs
- Workspace diff set (from `spec-implement` commits)
- `spec-analyze` results
- Background reviewer configuration (`curator.mode: deferred_queue`)

## Outputs
- Structured findings in workspace journal
- Updated PR description template

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the spec-kit bundle.
