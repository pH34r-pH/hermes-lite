# Implementation Plan: Spec-Kit Skill Bundle

**Branch**: `007-spec-kit-bundle` | **Date**: 2026-05-24 | **Spec**: `specs/007-spec-kit-bundle/spec.md`

**Input**: Feature specification from `/specs/007-spec-kit-bundle/spec.md`

## Summary

Ship a complete `skills/development/spec-kit/` skill bundle exposed through a single `/spec` slash command. The bundle implements 10 sequential skills — `spec-constitution`, `spec-specify`, `spec-clarify`, `spec-plan`, `spec-tasks`, `spec-test`, `spec-analyze`, `spec-checklist`, `spec-implement`, and `spec-review` — each sized for a 3B model context, each producing or consuming standard spec-kit artifacts (`spec.md`, `plan.md`, `tasks.md`, `analyze.md`, `checklist.md`, `tests.md`, `constitution.md`). The bundle integrates with `LocalRepoWorkspace` (spec 010) for all file mutations and git operations. Two mandatory approval gates protect auto-promotion: one at the `arxiv-write → spec-specify` boundary (research to spec) and one at the `spec-tasks → spec-implement` boundary (planning to implementation). Cross-repo plans are explicitly disallowed. The bundle binds to the `spec` and `dev` memory profiles.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: PyYAML (already core), Pydantic (already core), Jinja2 (optional — for spec templates), existing `agent/skill_commands.py`, existing `agent/tool_surface.py` (spec 003), existing `plugins/local_repo_workspace/` (spec 010), existing memory-profile subsystem (spec 013)

**Storage**: `<workspace>/specs/constitution.md`, `<workspace>/specs/<feature>/spec.md`, `<workspace>/specs/<feature>/plan.md`, `<workspace>/specs/<feature>/tasks.md`, `<workspace>/specs/<feature>/analyze.md`, `<workspace>/specs/<feature>/checklist.md`, `<workspace>/specs/<feature>/tests.md`, `~/repos/knowledge/seeds/<feature>.json` (input), `~/.hermes-lite/journal/<session-id>/` (spec 010 change journal)

**Testing**: pytest

**Target Platform**: Linux (Jetson Orin Nano)

**Project Type**: Skill bundle — ten markdown skill definitions plus template scaffolding and integration wiring

**Performance Goals**: `spec-specify` produces a `spec.md` passing template schema validation in 95% of cases; `spec-plan` produces `plan.md` within 120 seconds for single-sub-tree features; `spec-tasks` produces a cyclic-free dependency graph; a complete spec→plan→tasks→implement cycle for a 3-task feature completes end-to-end in under 15 minutes on Jetson 25 W power mode

**Constraints**: Each skill must fit in a 3B model context window; cross-repo plans are disallowed; every commit must land on a topic branch (never `main`/`master` directly); pre-commit gate blocks on failure; change budget pauses for re-approval on overflow; unattended auto-promotion is never allowed

**Scale/Scope**: Ten SKILL.md files, one bundle manifest YAML, artifact templates directory (~8 Jinja2/markdown templates), approval gate helper module, and integration wiring into `agent/tool_surface.py` and `LocalRepoWorkspace`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Approval gates prevent unattended auto-promotion from research to spec and from planning to implementation. Cross-repo plan disallowment prevents scope-creep attacks that span multiple repos.
- **Defense in Depth**: Branch-hygiene enforcement (never commit to `main`/`master`) is wired through `LocalRepoWorkspace`, which is the only sanctioned mutation path. Pre-commit gates catch lint/test failures before code enters version control.
- **Secure Defaults**: `LocalRepoWorkspace` default `approval_mode` is `confirm` or `pr-only`; auto mode is not the default. The background reviewer degrades to self-check when disabled rather than silently skipping review.
- **Dependency Management**: No new heavy dependencies; PyYAML, Pydantic, and optional Jinja2 are already present.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/007-spec-kit-bundle/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
skills/development/spec-kit/
├── SKILL.md                      # Root skill bundle descriptor (sequential pipeline overview)
├── spec-constitution/SKILL.md    # Skill 1 — create/update `<workspace>/specs/constitution.md`
├── spec-specify/SKILL.md         # Skill 2 — read seed, produce `<workspace>/specs/<feature>/spec.md`
├── spec-clarify/SKILL.md         # Skill 3 — generate clarification questions, await answers
├── spec-plan/SKILL.md            # Skill 4 — produce `<workspace>/specs/<feature>/plan.md`
├── spec-tasks/SKILL.md           # Skill 5 — produce dependency-ordered `<workspace>/specs/<feature>/tasks.md`
├── spec-test/SKILL.md            # Skill 6 — optionally emit `<workspace>/specs/<feature>/tests.md`
├── spec-analyze/SKILL.md         # Skill 7 — cross-artifact consistency analysis
├── spec-checklist/SKILL.md       # Skill 8 — generate verification checklist
├── spec-implement/SKILL.md       # Skill 9 — execute tasks via `LocalRepoWorkspace`
├── spec-review/SKILL.md          # Skill 10 — invoke background reviewer, surface findings
├── manifest.yaml                 # Bundle manifest registering `/spec` slash command
├── templates/
│   ├── constitution.md.j2        # Constitution template
│   ├── spec.md.j2                # Spec template (matches upstream specify CLI shape)
│   ├── plan.md.j2                # Plan template
│   ├── tasks.md.j2               # Tasks template
│   ├── analyze.md.j2             # Analysis report template
│   ├── checklist.md.j2           # Checklist template
│   └── tests.md.j2               # Tests description template
└── lib/
    ├── __init__.py
    ├── approval_gate.py          # ApprovalGate — user-confirmation checkpoints with gateway integration
    ├── seed_parser.py            # SpecSeed — parse `spec-seed.json` and validate schema
    ├── task_validator.py         # TaskRecord validator — DAG cycle detection, plan-section reference check
    └── workspace_resolver.py     # Resolve target workspace from seed or user input against `workspaces.yaml`

~/.hermes-lite/skill-bundles/spec.yaml  # Bundle alias (optional, or use manifest.yaml)

agent/
└── tool_surface.py             # UPDATE — register spec-kit kit allowlist (spec 003 integration point)
```

**Structure Decision**: Single skill bundle under `skills/development/spec-kit/`. Each skill is a self-contained `SKILL.md` invoked sequentially by the master `SKILL.md`. Templates live in `templates/` and are rendered by the skills. Python support modules handle approval gates, seed parsing, task validation, and workspace resolution. The bundle manifest registers `/spec` as a slash command.

## Complexity Tracking

> No violations. The feature introduces one skill bundle with ten markdown skill files, a small template library, and a Python support library (~500–700 LOC total). No new subprojects, persistence layers, or service boundaries introduced beyond the workspace journal and spec artifacts.
