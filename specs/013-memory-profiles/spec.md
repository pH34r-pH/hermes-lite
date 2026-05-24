# Feature Specification: Memory Profiles per Workflow

**Feature Branch**: `013-memory-profiles`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Reuse plugins/memory/ for per-workflow namespaces. 8 profiles: research, spec, dev, web, azure, infra, api, security. Kit→profile binding. Security profile write-only to /sec kit. Read REDESIGN.md §5.7."

## Current State

Upstream Hermes Agent ships a `plugins/memory/` directory containing multiple memory-provider plugins: `honcho/`, `mem0/`, `supermemory/`, `hindsight/`, `byterover/`, `holographic/`, `openviking/`, and `retaindb/`. These are managed by `plugins/memory/__init__.py` and configured via `config.yaml`. Memory is global or per-conversation-user; there is **no per-workflow namespace isolation**. The active memory backend (e.g., Honcho) stores all recall context in a single flat space regardless of whether the user is researching arXiv papers, writing specs, deploying Azure resources, or running security probes. There is **no kit→profile binding**: loading the arXiv kit does not switch the memory namespace, and loading the security kit does not restrict memory writes. All kits share the same recall surface, which causes context pollution and increases retrieval noise for small models. The `plugins/kanban/` plugin demonstrates dispatcher/worker isolation but does not extend to memory namespaces.

## Target State

Hermes-lite reuses the existing `plugins/memory/` infrastructure but adds **per-workflow memory profiles**. Eight profiles are defined:

| Profile   | Kit(s) bound                     | What lives here                                                                                                                          |
| --------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `research`| arxiv                            | Reading list, paper extracts, comparison tables, written notes, open questions.                                                          |
| `spec`    | spec-kit                         | Spec proposals (`spec.md`), plans (`plan.md`), task lists (`tasks.md`), constitution, review notes, approvals.                           |
| `dev`     | spec-kit, web-ops, security      | Repo conventions, build commands, code-review patterns, lint/test invocations, branch hygiene rules.                                     |
| `web`     | web-ops                          | Frontend conventions for the SWA target (routing, components, styles, deploy config, SWA `staticwebapp.config.json`).                    |
| `azure`   | azure-ops                        | Azure CLI patterns, Bicep modules for SWA + VM, RBAC, key vault references, deploy slots, networking rules.                              |
| `infra`   | azure-ops, dev, security         | Linux VM host knowledge — systemd, reverse proxy (`caddy`/`nginx`), TLS, DNS, firewall, egress allowlist, log rotation, Tailscale mesh.  |
| `api`     | dev, web-ops, security           | The OpenAI/Copilot back-end API contract — routes, auth, rate limits, MCP exposure, observability.                                       |
| `security`| security (write); others read-only | Threat models, findings reports, baselines, scope allowlist, credential rotation history. Only the `/sec` kit may write here.            |

Profile selection is a first-class kit transition: loading the arXiv kit points memory at `research`; loading the spec-kit points memory at `spec + dev`; loading azure-ops points memory at `azure + infra`; loading the security kit points memory at `security` (write) plus `web + api + infra` (read). When a profile transition occurs, the diagnostics layer logs it to `agent.jsonl`. The security profile enforces write-only access for the `/sec` kit; all other kits receive read-only access to `security`.

The implementation should be compatible with the existing memory-provider adapter interface so that enabling Honcho, mem0, or supermemory continues to work without provider-specific changes.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load a Kit and Switch Memory Profile (Priority: P1)

A user starts the arXiv kit. The agent loads the `research` memory profile so that recall returns only paper extracts and reading-list entries, not Azure CLI snippets or threat-model notes.

**Why this priority**: Isolating memory by workflow is the primary mechanism for reducing retrieval noise on a 3B model. Without it, the model is distracted by irrelevant context.

**Independent Test**: Can be fully tested by loading the arXiv kit, storing a note, switching to the azure-ops kit, and verifying the note is not visible in recall.

**Acceptance Scenarios**:

1. **Given** the agent loads the `arxiv` kit, **When** the kit transition completes, **Then** the active memory profile is `research` and `agent.jsonl` records `event: "profile_switch"` with `profile: "research"`
2. **Given** the user stores a paper note while in `research`, **When** the agent later recalls context in the same session, **Then** the note is returned with high relevance
3. **Given** the agent switches from `arxiv` to `azure-ops`, **When** recall runs, **Then** the paper note is not returned because the active profile is now `azure`
4. **Given** no kit is active (startup), **When** memory is queried, **Then** the default profile is `dev` to support general development tasks

---

### User Story 2 - Security Profile Write Isolation (Priority: P1)

A user runs a security scan with the `/sec` kit. The agent writes findings to the `security` profile. Later, the user switches to the spec-kit and attempts a recall query; the spec-kit can read security findings but cannot mutate them.

**Why this priority**: Preventing accidental or malicious overwrite of security findings by non-security kits is a hard trust-boundary requirement.

**Independent Test**: Can be fully tested by writing a finding from `/sec`, switching kits, and asserting the write operation is rejected for non-security kits.

**Acceptance Scenarios**:

1. **Given** the `/sec` kit runs a probe, **When** it writes a finding, **Then** the write succeeds and the `security` profile contains the finding
2. **Given** the agent switches to the `spec-kit`, **When** it attempts to write a memory entry tagged `security`, **Then** the memory layer raises `MemoryWriteDenied` and the agent logs a refusal
3. **Given** the `spec-kit` performs a recall query, **When** the query matches a `security` profile entry, **Then** the entry is returned read-only without side effects
4. **Given** the `/sec` kit is unloaded and the `web-ops` kit is loaded, **When** `web-ops` recalls context, **Then** security findings are visible but marked with `source_profile: "security"` in the metadata

---

### User Story 3 - Multi-Profile Binding for Composite Kits (Priority: P2)

A user loads the azure-ops kit. The agent binds memory to both `azure` and `infra` profiles simultaneously, so recall includes Azure CLI patterns and Linux VM host knowledge.

**Why this priority**: Composite kits need context from multiple domains. Explicit multi-profile binding prevents ad-hoc mixing and keeps the retrieval surface bounded.

**Independent Test**: Can be fully tested by loading azure-ops, storing distinct notes in both `azure` and `infra`, and verifying recall returns both.

**Acceptance Scenarios**:

1. **Given** the `azure-ops` kit is active, **When** the agent stores a Bicep snippet, **Then** it is written to the `azure` profile
2. **Given** the `azure-ops` kit is active, **When** the agent stores a systemd service note, **Then** it is written to the `infra` profile
3. **Given** the agent performs a recall query for "deploy slot", **When** the query executes, **Then** results from `azure` rank higher than results from `infra`
4. **Given** the agent performs a recall query for "reverse proxy", **When** the query executes, **Then** results from `infra` are returned, and no unrelated `web` or `api` entries pollute the results

---

### User Story 4 - Profile Persistence and Cross-Session Recall (Priority: P2)

A user reboots the cyberdeck and restarts hermes-lite. The previous session used the spec-kit with the `spec` profile. The user resumes work and expects prior spec drafts and review notes to be available.

**Why this priority**: Memory is only valuable if it persists across restarts. The profile namespace must be durable in the underlying provider (e.g., Honcho project, mem0 namespace, SQLite file).

**Independent Test**: Can be fully tested by storing a note in `spec`, restarting the agent, loading the spec-kit, and verifying the note is still recallable.

**Acceptance Scenarios**:

1. **Given** a note is stored in the `spec` profile, **When** the agent restarts and loads the `spec-kit`, **Then** the note is present in recall results
2. **Given** the cyberdeck reboots, **When** the agent starts and the user requests recall from the `research` profile, **Then** the query returns only research-profile entries, not spec or dev entries
3. **Given** the underlying provider is Honcho, **When** a profile switch occurs, **Then** the Honcho client uses the profile name as the project/namespace identifier
4. **Given** the underlying provider is `retaindb` (local SQLite), **When** a profile switch occurs, **Then** the SQLite table or namespace is prefixed with the profile name (e.g., `research_messages`)

---

### Edge Cases

- What happens when a memory provider does not support namespaces (e.g., a simple flat-file backend)? The adapter must emulate namespaces by prefixing keys or storing a `profile` column; isolation must still be enforced in code.
- How does the system handle a kit transition while a long-running recall query is in flight? In-flight queries complete against the profile they were started with; new queries use the new profile.
- What happens when the user manually edits `config.yaml` to bind an unsupported kit→profile mapping? The config validator rejects unknown profiles or kits at startup, defaulting to the `dev` profile.
- How are profile names handled when the user switches memory providers (e.g., from Honcho to mem0)? Profile names are alphanumeric lower-case and are mapped to provider-specific namespace identifiers via a translation table in `plugins/memory/__init__.py`.
- What happens when the `/sec` kit attempts to write to a read-only profile? The write is refused with a clear error message surfaced to the gateway, and the agent asks the user for direction.
- How does memory profile isolation interact with the curator and background reviewer? The curator reads from all profiles during its review pass but writes its findings only to the `spec` profile (or session-specific scratch space), never to `security`.
- What happens when two kits claim the same primary profile (e.g., both spec-kit and web-ops bind to `dev`)? Shared profiles are allowed; the binding table supports multiple kits per profile. Writes from any bound kit go to the same namespace.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin MUST expose eight named memory profiles: `research`, `spec`, `dev`, `web`, `azure`, `infra`, `api`, `security`.
- **FR-002**: Profile activation MUST be a first-class kit transition event emitted to `agent.jsonl` with `event: "profile_switch"` and the new profile list.
- **FR-003**: The kit→profile binding MUST be declared in `lite-config.yaml` under `memory_profiles.bindings`.
- **FR-004**: The `security` profile MUST be writeable ONLY by the `/sec` kit; all other kits MUST receive read-only access.
- **FR-005**: A write attempt to `security` from a non-`/sec` kit MUST raise `MemoryWriteDenied` and log a `security_refusal` event.
- **FR-006**: Composite kits (e.g., `azure-ops`) MUST bind to multiple profiles simultaneously; recall MUST query all bound profiles and return merged, ranked results.
- **FR-007**: Writes from a composite kit MUST route to the primary profile of that kit unless explicitly annotated (e.g., `infra` for systemd notes under `azure-ops`).
- **FR-008**: Profile isolation MUST be enforced regardless of the underlying memory provider (Honcho, mem0, supermemory, retaindb, etc.).
- **FR-009**: Profile names MUST be lower-case alphanumeric and mapped to provider-specific namespace identifiers via a translation table in `plugins/memory/__init__.py`.
- **FR-010**: Profile state MUST persist across agent restarts and reboots via the underlying provider's persistence mechanism.
- **FR-011**: In-flight memory queries MUST complete against the profile they were started with, even if a kit switch occurs mid-query.
- **FR-012**: Unknown kit→profile mappings in `config.yaml` MUST be rejected at startup, falling back to the `dev` profile with a warning.
- **FR-013**: The memory profile switch MUST be observable from the CLI via `hermes-lite memory --profile` and `hermes-lite memory --list-profiles`.
- **FR-014**: Curator and background-reviewer reads MUST span all profiles, but their writes MUST be restricted to `spec` or session-scratch space, never `security`.

### Key Entities

- **MemoryProfile**: A named namespace (`research`, `spec`, `dev`, `web`, `azure`, `infra`, `api`, `security`) that isolates recall context per workflow.
- **ProfileBinding**: The mapping from a kit name to one or more memory profiles, declared in `lite-config.yaml`.
- **ProfileSwitchEvent**: A diagnostics event logged when the active profile changes, carrying the old and new profile lists.
- **SecurityProfileGuard**: An access-control layer that enforces write-only permissions for the `/sec` kit on the `security` profile.
- **ProviderNamespaceMap**: A translation table mapping canonical profile names to provider-specific identifiers (e.g., Honcho project names, mem0 namespaces).
- **CompositeRecallQuery**: A recall operation that queries multiple bound profiles and merges results with per-profile relevance weighting.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Switching from the `arxiv` kit to the `azure-ops` kit changes the active profile set within 500 ms.
- **SC-002**: A recall query in the `research` profile does not return entries from the `azure` profile, verified by synthetic cross-profile pollution test.
- **SC-003**: The `/sec` kit successfully writes to `security`; a non-security kit is blocked with `MemoryWriteDenied` in integration testing.
- **SC-004**: A composite kit (`azure-ops`) recall query returns results from both `azure` and `infra` profiles, with no results from `research`, `spec`, or `web`.
- **SC-005**: Profile-persisted notes survive an agent restart and are recallable within 2 seconds of profile reload.
- **SC-006**: Invalid kit→profile mappings in `config.yaml` trigger a startup warning and fallback to `dev`, verified by config validation test.
- **SC-007**: Memory profile switch events appear in `agent.jsonl` with correct `event`, `kit`, and `profile` fields.
- **SC-008**: Curator reads span all profiles in under 3 seconds for a 1,000-entry test dataset.
- **SC-009**: Security profile entries are never mutated by non-security kits in a 24-hour randomized stress test.
- **SC-010**: The CLI helper `hermes-lite memory --list-profiles` returns the eight canonical profiles and their active kit bindings in under 1 second.

## Assumptions

- The underlying memory provider (Honcho, mem0, etc.) supports namespace or project isolation, or can be wrapped to emulate it.
- The cyberdeck has sufficient disk I/O to handle profile-scoped SQLite or HTTP-backed memory without introducing visible latency.
- Kits are loaded one at a time via `agent/tool_surface.py`; profile switches occur only at kit boundaries, not mid-turn.
- The `security` profile will contain sensitive findings; its write isolation is a hard requirement, not a best-effort feature.
- Small models benefit from smaller, bounded recall surfaces; therefore, profiles are intentionally narrow and do not default to a global "all" profile.
- Profile names are stable and will not change between releases; if new profiles are needed, they are additive.
- The upstream `plugins/memory/__init__.py` plugin loader is the integration point; no changes to individual provider SDKs are required.
