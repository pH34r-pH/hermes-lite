---
name: spec-kit
description: "Root bundle descriptor for the spec-driven development pipeline. Exposes /spec slash command with 10 sequential skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec-kit, bundle, pipeline, spec-driven-development]
    related_skills: [arxiv-research, local-repo-workspace]
    memory_profiles: [spec, dev]
---

# Spec-Kit Skill Bundle

The `spec-kit` bundle implements the **spec → plan → tasks → implement** pattern for offline development on the Jetson. It exposes the `/spec` slash command and provides 10 sequential skills, each sized for a 3B model context.

## Sequential Pipeline

1. **spec-constitution** — Create or update `specs/constitution.md` (governance, tone, non-negotiables)
2. **spec-specify** — Convert research seed or user ask into `specs/<feature>/spec.md`
3. **spec-clarify** — Generate up to 5 clarification questions; record answers in `spec.md`
4. **spec-plan** — Produce `specs/<feature>/plan.md` (architecture, contracts, risks)
5. **spec-tasks** — Produce dependency-ordered `specs/<feature>/tasks.md`
6. **spec-test** — Optionally emit `specs/<feature>/tests.md` (TDD step)
7. **spec-analyze** — Cross-artifact consistency analysis (non-destructive)
8. **spec-checklist** — Generate verification `checklist.md`
9. **spec-implement** — Execute tasks via `LocalRepoWorkspace` (gated commits)
10. **spec-review** — Background reviewer over diff set before PR

## Approval Gates

- **research→spec**: Mandatory user confirmation before `spec-specify` writes `spec.md`
- **tasks→implement**: Mandatory user confirmation before `spec-implement` begins execution

## Delegation Rules

- Each skill is loaded/unloaded one at a time via `agent/tool_surface.py`
- Only the active skill's toolset is exposed per turn
- The bundle binds to the `spec` and `dev` memory profiles on load
- Cross-repo plans are disallowed; split into coordinated specs with linked IDs

## Artifacts

| Artifact | Producer | Consumers |
|----------|----------|-----------|
| `constitution.md` | spec-constitution | all |
| `spec.md` | spec-specify | spec-clarify, spec-plan, spec-analyze |
| `plan.md` | spec-plan | spec-tasks, spec-analyze, spec-test |
| `tasks.md` | spec-tasks | spec-analyze, spec-implement |
| `tests.md` | spec-test | spec-implement |
| `checklist.md` | spec-checklist | spec-review |
| `analyze.md` | spec-analyze | spec-review |

## Notes

This is a skeleton bundle. Full skill logic implementation is pending per `specs/007-spec-kit-bundle/`.
