# Feature Specification: hermes-lite Top-Level Configuration Profile

**Feature Branch**: `005-lite-config`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New top-level lite-config.yaml profile: pins default model to ollama:ministral-3:3b, escalation order, enabled_gateways, iteration budget 25, tool-call-failure budget 3, deferred-queue curator mode, disable removed providers fail-closed. Read REDESIGN.md §5.1."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pin Default Model and Escalation Order (Priority: P1)

Hermes-lite must ship a canonical `lite-config.yaml` that pins the default inference model to `ollama:ministral-3:3b` and defines an escalation order (`ollama -> copilot -> openai -> claude`) so that local inference is always attempted first before burning cloud API quota.

**Why this priority**: The entire purpose of the fork is lightweight on-device operation. Without a pinned default, upstream agents may default to cloud providers and silently consume API keys or fail when offline.

**Independent Test**: Can be fully tested by starting `hermes-lite` with no user config and verifying that the active model resolves to `ollama:ministral-3:3b` and the escalation queue is populated in the correct order.

**Acceptance Scenarios**:

1. **Given** no user `config.yaml` exists, **When** hermes-lite starts, **Then** the default model is `ollama:ministral-3:3b`
2. **Given** an Ollama request fails (model not loaded, timeout), **When** the agent escalates, **Then** the next candidate is `copilot` (or whichever is next in the configured escalation order)
3. **Given** a user overrides `model` in their local config, **When** the agent initializes, **Then** the user override takes precedence but the escalation order still falls back through the lite profile chain
4. **Given** the escalation exhausts all providers, **When** the final provider fails, **Then** the agent surfaces a clear error to the user rather than looping infinitely

---

### User Story 2 - Declare Enabled Gateways and Disable Removed Providers Fail-Closed (Priority: P2)

Hermes-lite must declare the exact set of allowed gateways (`discord`, `openwebui`, `tui`) in `lite-config.yaml` and must fail closed at config-load time if any config key references a removed provider or gateway (e.g. `telegram`, `slack`, `whatsapp`).

**Why this priority**: The fork deletes many upstream platforms and providers. A stale user config that references them should be caught early with a clear error rather than causing a cryptic `ImportError` at runtime.

**Independent Test**: Can be fully tested by creating a config that sets `gateway: telegram` and verifying that `hermes-lite` exits with a `ConfigurationError` naming the disallowed gateway before any network calls are made.

**Acceptance Scenarios**:

1. **Given** `lite-config.yaml` sets `enabled_gateways: [discord, openwebui, tui]`, **When** the gateway loader initializes, **Then** only those three platforms are registered
2. **Given** a user config references `gateway: telegram`, **When** config validation runs, **Then** the process exits with `ConfigurationError: "Gateway 'telegram' has been removed in hermes-lite"`
3. **Given** a user config references `provider: alibaba` (kept) alongside `provider: yuanbao` (removed), **When** config validation runs, **Then** the yuanbao reference is rejected while the alibaba reference is accepted
4. **Given** a skill or plugin attempts to re-enable a removed provider at runtime, **When** the agent's provider resolver checks against the denylist, **Then** the attempt is blocked and logged at `ERROR` level

---

### User Story 3 - Cap Iteration Budget and Tool-Call-Failure Budget (Priority: P3)

Hermes-lite must set a per-session iteration budget of 25 (down from upstream defaults of 50–90) and a per-kit tool-call-failure budget of 3 before forced escalation to the next provider. This prevents runaway loops and forces the agent to escalate rather than repeating failed tool calls against a small model.

**Why this priority**: Small models hallucinate tool calls more often. Left uncapped, a 3B model can burn the entire iteration budget on malformed calls. After 3 failures the agent should escalate to a larger model or ask the user.

**Independent Test**: Can be fully tested by running a task that deliberately triggers tool-call failures and verifying that the agent escalates after the third failure rather than continuing to turn 25.

**Acceptance Scenarios**:

1. **Given** the agent is running with `lite-config.yaml`, **When** the conversation loop starts, **Then** `max_iterations` is capped at 25
2. **Given** a tool call returns an error, **When** the same tool is called again and fails, **Then** the failure counter increments per kit
3. **Given** the per-kit tool-call-failure counter reaches 3, **When** the next tool call is attempted, **Then** the agent escalates to the next provider in the escalation order before making the call
4. **Given** the agent escalates due to tool-call failures, **When** the new model processes the turn, **Then** the failure counter is reset to 0 for the new provider

---

### User Story 4 - Deferred-Queue Curator and Background Reviewer (Priority: P4)

Hermes-lite must run the curator and background reviewer in deferred-queue mode: each loop tick enqueues jobs into `~/.hermes-lite/queue/curator.jsonl` instead of executing them inline. A configurable threshold (default: 25 enqueued jobs or 4 hours of accumulated work) triggers a batched approval prompt in the originating gateway.

**Why this priority**: On-device small models have limited throughput. Running the curator inline adds latency to every turn. Deferring to a queue batch keeps the main loop fast while still catching mistakes.

**Independent Test**: Can be fully tested by observing that `~/.hermes-lite/queue/curator.jsonl` grows by one line per turn and that a prompt for batch approval is emitted when the file reaches 25 lines.

**Acceptance Scenarios**:

1. **Given** the agent completes a turn, **When** the curator job is generated, **Then** it is appended to `~/.hermes-lite/queue/curator.jsonl` rather than executed immediately
2. **Given** the queue reaches 25 entries, **When** the agent checks the threshold, **Then** it emits a message in the active gateway asking the user to authorize a batched curator pass
3. **Given** the user approves the batch, **When** the curator processes the queue, **Then** all 25 jobs are processed in a single subagent run and the queue file is truncated
4. **Given** 4 hours elapse without reaching the 25-job threshold, **When** the agent checks the threshold, **Then** a batched curator pass is still proposed to the user

---

### Edge Cases

- What happens when `lite-config.yaml` is missing from the install directory? The agent must refuse to start with a clear error rather than falling back to upstream defaults, because the lite profile is the canonical configuration for this fork.
- What happens when the user has both `~/.hermes/config.yaml` and `lite-config.yaml`? The merge order must be: `lite-config.yaml` base -> `~/.hermes/config.yaml` overlay -> command-line overrides. Removed-provider references in the overlay must still be rejected.
- How does the system handle an escalation when the next provider has no API key configured? It must skip that provider and move to the next in the order, logging the skip at `INFO` level.
- What happens when the iteration budget is exhausted mid-task? The agent must return a summary of what was accomplished and a note that the budget was reached, rather than silently truncating.
- What happens when the deferred queue file grows beyond disk capacity? A rotation limit (e.g. max 500 entries, oldest dropped) must prevent unbounded growth.
- What happens when the background reviewer is disabled in user config while deferred-queue mode is enabled in `lite-config.yaml`? Deferred-queue mode wins for the lite profile; the user can only disable the reviewer entirely by opting out of the lite profile.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a new top-level `lite-config.yaml` file at the repository root that serves as the canonical configuration profile for hermes-lite
- **FR-002**: `lite-config.yaml` MUST set `model: "ollama:ministral-3:3b"` as the default inference target
- **FR-003**: `lite-config.yaml` MUST define `escalation_order: [ollama, copilot, openai, claude]` as the provider fallback chain
- **FR-004**: `lite-config.yaml` MUST declare `enabled_gateways: [discord, openwebui, tui]`
- **FR-005**: `lite-config.yaml` MUST set `max_iterations: 25` (down from upstream 50/90)
- **FR-006**: `lite-config.yaml` MUST set `tool_call_failure_budget: 3` per kit before forced escalation
- **FR-007**: `lite-config.yaml` MUST enable `prompt_prefix_caching: true` by default
- **FR-008**: `lite-config.yaml` MUST enable `per_session_snapshots: true` by default
- **FR-009**: `lite-config.yaml` MUST configure `curator.mode: deferred_queue` and `curator.threshold_jobs: 25` and `curator.threshold_hours: 4`
- **FR-010**: `lite-config.yaml` MUST disable `image`, `video`, `voice`, and all removed providers at config load with a `fail_closed: true` flag
- **FR-011**: System MUST validate the merged config at startup and raise `ConfigurationError` with the exact offending key whenever a removed provider or gateway is referenced
- **FR-012**: System MUST implement config merging: `lite-config.yaml` is the base, `~/.hermes/config.yaml` overlays on top, and CLI flags overlay on top of both
- **FR-013**: System MUST log the effective configuration (model, gateways, iteration budget, active kit) at `INFO` level on startup
- **FR-014**: System MUST provide a `--profile lite` CLI flag that explicitly selects the lite profile; when omitted, the upstream default profile is used so the same binary can serve both forks

### Key Entities

- **LiteConfigProfile**: The `lite-config.yaml` file and its in-memory representation. Loaded by the config subsystem when `profile: lite` is active.
- **EscalationOrder**: An ordered list of provider names that the agent walks when the current provider fails or the tool-call-failure budget is exceeded.
- **ToolCallFailureBudget**: A per-kit counter that tracks consecutive tool-call errors. When it reaches the configured limit, the agent escalates.
- **DeferredQueue**: A JSONL file at `~/.hermes-lite/queue/curator.jsonl` that holds curator and background-reviewer jobs until a batch threshold is reached.
- **RemovedProviderDenylist**: The set of providers and gateways deleted by the fork. Checked at config-merge time and at runtime provider resolution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `hermes-lite --profile lite` with no user config resolves `model` to `ollama:ministral-3:3b`, verified by startup log output
- **SC-002**: A config file referencing `gateway: telegram` causes the agent to exit within 2 seconds with a clear `ConfigurationError`, verified by pytest
- **SC-003**: The iteration budget is capped at 25 for lite-profile sessions, verified by `assert agent.max_iterations == 25`
- **SC-004**: After 3 consecutive tool-call failures, the agent escalates to the next provider in the escalation order, verified by mock provider injection in a test
- **SC-005**: The deferred queue file `~/.hermes-lite/queue/curator.jsonl` grows by exactly one line per turn when curator jobs are generated, verified by line count before and after a test conversation
- **SC-006**: Lite-profile startup log contains the effective model, gateway list, and iteration budget at `INFO` level, verified by log capture in pytest
- **SC-007**: The same binary run without `--profile lite` uses upstream defaults (model empty, max_iterations 90, all gateways enabled), confirming backward compatibility

## Assumptions

- The upstream config loader (`hermes_cli.config`) supports layered config files and can be extended with a `profile` key without breaking existing users
- `~/.hermes-lite/` is the canonical home directory for the fork, distinct from `~/.hermes/`, and is created on first run
- Ollama is the primary inference backend for the cyberdeck; `ministral-3:3b` is pulled or available locally before the agent starts
- The removed-provider list is stable after `001-gateway-cleanup` and `000-provider-cleanup` are complete
- The deferred queue directory is created with appropriate permissions (0700) because it may contain conversation metadata
- `copilot`, `openai`, and `claude` providers are retained in the fork but only used as escalation targets; their API keys are optional and checked at escalation time
- The upstream `max_iterations` parameter in `AIAgent.__init__` is the control point for the iteration budget; no new loop logic is required
