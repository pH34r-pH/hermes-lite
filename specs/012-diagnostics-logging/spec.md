# Feature Specification: Diagnostics Logging — Structured JSONL Streams

**Feature Branch**: `012-diagnostics-logging`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New agent/diagnostics.py structured logger. Log streams: agent.jsonl, tools.jsonl, providers.jsonl, workspace.jsonl, security.jsonl (mode 0600), thermal.jsonl, api.jsonl. Daily rotation, 90-day retention. Stable schema. Read REDESIGN.md §5.14."

## Current State

Upstream Hermes Agent uses `hermes_logging.py` to produce three plain-text log files under `~/.hermes/logs/`:

- `agent.log` — INFO+ catch-all for agent, tool, and session activity.
- `errors.log` — WARNING+ for quick triage.
- `gateway.log` — INFO+ gateway-only events (created when `mode="gateway"`).

These files use `RotatingFileHandler` (size-based, default 5 MB × 3 backups) with a `RedactingFormatter` to strip secrets. Session context is injected via a custom `LogRecord` factory using `threading.local()`. Upstream also retains:

- `state.db` — SQLite session store with FTS5 indexing (canonical tool-call and recall record).
- Trajectory capture under `~/.hermes/trajectories/` — turn-by-turn session serialization for replay and curator review.
- Per-session JSON snapshots for diffing and collaboration.
- Curator and background-reviewer outputs under `~/.hermes/queue/`.
- `journalctl` records for the hermes systemd unit.

There is **no structured JSONL diagnostics layer**, no per-event-type log streams, no daily rotation, no 90-day retention policy, no thermal sampling, and no restricted-permission security log stream. The upstream logger is not kit- or profile-aware; it does not emit stable-schema JSON suitable for downstream analysis, self-improvement signal mining, or partner-model cost sharing.

## Target State

Hermes-lite ships `agent/diagnostics.py`, a single structured logger that emits newline-delimited JSON to `~/.hermes-lite/logs/`. Every log line carries a stable top-level schema: `ts`, `session_id`, `kit`, `skill`, `provider`, `model`, `workspace`, `gateway`, `event`, `latency_ms`, plus an event-specific payload object. The logger supports seven independent streams, each with **daily rotation** and a **90-day retention window**:

- `logs/agent.jsonl` — loop ticks, kit loads/unloads, memory profile switches, iteration counts, session lifecycle.
- `logs/tools.jsonl` — every tool call with schema validation result, latency, and outcome (`success`, `parse-fail`, `semantic-fail`, `refusal`, `timeout`).
- `logs/providers.jsonl` — every LM call: provider, model, request size, response size, latency, cost (when known), cache-hit indicator, and which escalation-chain node answered.
- `logs/workspace.jsonl` — every `workspace.*` call: target repo, files touched, byte delta, change-budget remaining, pre-commit gate result, commit SHA.
- `logs/security.jsonl` — every `/sec` probe and finding; created with filesystem mode `0600` and rotated separately so it can be archived without leaking into shared diagnostic dumps.
- `logs/thermal.jsonl` — 5-second `tegrastats` samples: CPU temp, GPU temp, current `nvpmodel` power mode, throttling flags.
- `logs/api.jsonl` — calls hermes-lite makes to its own deployed `azure-api` endpoint (including the partner small model): request id, route, status, latency, partner-vs-paid routing decision, and self-pentest probe results.

The upstream plain-text logs (`agent.log`, `errors.log`, `gateway.log`) are retained unchanged; the JSONL diagnostics layer is additive. A small CLI helper (`hermes-lite logs --stream <name> --since <date> --tail`) allows filtering and tailing each stream.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit and Query Agent Lifecycle Events (Priority: P1)

A user starts a session with the arXiv kit. The diagnostics layer writes kit load, model resolution, and iteration counts to `agent.jsonl`. Later, the user runs `hermes-lite logs --stream agent --since today --tail 20` to see recent session transitions.

**Why this priority**: The agent stream is the backbone of the self-improvement loop. Without it, the agent cannot correlate session behavior with kit configuration.

**Independent Test**: Can be fully tested by starting a session, verifying `agent.jsonl` contains the kit-load event, and querying the stream via the CLI helper.

**Acceptance Scenarios**:

1. **Given** the agent loads the `arxiv` kit, **When** the session begins, **Then** `agent.jsonl` contains a line with `event: "kit_load"`, `kit: "arxiv"`, and a valid ISO-8601 `ts`
2. **Given** the agent switches from the `arxiv` kit to the `spec-kit`, **When** the switch occurs, **Then** `agent.jsonl` records `event: "kit_switch"` with both the old and new kit names in the payload
3. **Given** the user runs `hermes-lite logs --stream agent --since today`, **When** the CLI helper executes, **Then** it returns only lines from `agent.jsonl` whose `ts` is within the current calendar day
4. **Given** a session ends, **When** the final turn completes, **Then** `agent.jsonl` records `event: "session_end"` with total iteration count and elapsed time

---

### User Story 2 - Capture Tool Calls with Outcomes and Latency (Priority: P1)

A user sends a directive that triggers a tool call. The diagnostics layer writes the tool name, arguments hash, validation result, latency, and outcome to `tools.jsonl`. A failed tool call is recorded with an error classification.

**Why this priority**: Tool-call signal is the primary feedback for refining the tool surface and prompt templates. Accurate outcome classification (parse vs semantic vs timeout) is required for automated analysis.

**Independent Test**: Can be fully tested by invoking a tool and inspecting `tools.jsonl` for the corresponding event line.

**Acceptance Scenarios**:

1. **Given** the agent calls `workspace.status`, **When** the call succeeds, **Then** `tools.jsonl` contains `event: "tool_call"`, `tool: "workspace.status"`, `outcome: "success"`, and `latency_ms > 0`
2. **Given** the agent issues a tool call with malformed JSON arguments, **When** parsing fails, **Then** `tools.jsonl` records `outcome: "parse-fail"` and includes the validation error in the payload
3. **Given** a tool call times out after 60 seconds, **When** the timeout fires, **Then** `tools.jsonl` records `outcome: "timeout"` and `latency_ms` is approximately the timeout threshold
4. **Given** the user runs `hermes-lite logs --stream tools --grep outcome:semantic-fail`, **When** the query executes, **Then** it returns only lines matching the filter

---

### User Story 3 - Record Provider Escalation and Cost Metadata (Priority: P2)

A user sends a hard prompt that escalates from Ollama to Claude. The diagnostics layer writes each LM attempt to `providers.jsonl`, including the final responder, token counts, and estimated cost.

**Why this priority**: The partner-model adapter and cost-sharing logic depend on this stream. It also provides the telemetry needed to optimize escalation thresholds.

**Independent Test**: Can be fully tested by configuring multiple providers, triggering an escalation, and inspecting `providers.jsonl` for the chain of attempts.

**Acceptance Scenarios**:

1. **Given** Ollama returns a 500 error, **When** the agent escalates to Claude, **Then** `providers.jsonl` contains two lines: one for the failed Ollama attempt with `outcome: "error"`, and one for the successful Claude attempt with `outcome: "success"`
2. **Given** a response is served from the prompt cache, **When** the LM call completes, **Then** the line includes `cache_hit: true` and correct request/response size fields
3. **Given** the model is `ministral-3:3b` on Ollama, **When** the call succeeds, **Then** `cost` is `null` (local) but `latency_ms` and `model` are populated
4. **Given** the user runs a nightly batch job, **When** the job finishes, **Then** a summary query over `providers.jsonl` yields total cost and call count per provider for that day

---

### User Story 4 - Thermal Sampling and Security Stream Isolation (Priority: P3)

On a Jetson Orin Nano, the diagnostics layer polls `tegrastats` every 5 seconds and writes samples to `thermal.jsonl`. A security probe run by the `/sec` kit writes findings to `security.jsonl` with mode `0600`.

**Why this priority**: Thermal data is essential for the power-mode watchdog and for correlating throttling with model latency. Isolating the security stream prevents sensitive findings from leaking into shared diagnostic exports.

**Independent Test**: Can be fully tested by verifying `thermal.jsonl` grows at 5-second intervals and that `security.jsonl` permissions are `0600`.

**Acceptance Scenarios**:

1. **Given** the device is running at `nvpmodel -m 1`, **When** 30 seconds elapse, **Then** `thermal.jsonl` contains 6 lines with monotonically increasing timestamps, each including `cpu_temp`, `gpu_temp`, and `power_mode`
2. **Given** the device throttles due to temperature, **When** `tegrastats` reports throttling flags, **Then** the corresponding `thermal.jsonl` line includes `throttled: true` and the flag bitmask
3. **Given** the `/sec` kit writes a finding, **When** the write occurs, **Then** `security.jsonl` exists and its filesystem mode is `0600` (readable/writable only by owner)
4. **Given** a user exports diagnostics with `hermes-lite logs export --exclude security`, **When** the export runs, **Then** the resulting tarball does not contain `security.jsonl` or any lines with `stream: "security"`

---

### Edge Cases

- What happens when `~/.hermes-lite/logs/` is on a read-only filesystem? The logger must degrade gracefully, writing to `/dev/null` equivalents and emitting a single warning to `errors.log`.
- How does the system handle a clock jump backward across a daily rotation boundary? Rotation must use filesystem mtime, not monotonic time, to avoid overwriting the same day’s file.
- What happens when `security.jsonl` is created on a filesystem that ignores POSIX permissions (e.g., some FAT exfat mounts)? The logger must warn at startup and rely on directory-level `0700` for isolation.
- How does the logger behave when a stream file grows beyond a safety cap (e.g., 1 GB) within a single day? It must stop appending and emit a warning to `errors.log` per stream, preserving prior lines.
- What happens when `tegrastats` is unavailable (not a Jetson)? `thermal.jsonl` must be silently omitted; the logger must not crash.
- How are secrets redacted from JSONL payloads? The diagnostics layer reuses the upstream `RedactingFormatter` pattern: any value matching a known secret pattern (API keys, tokens) is replaced with `<redacted>` before serialization.
- What happens when a session ID is not yet set (early startup)? Top-level fields must still be present with `null` or `"__startup__"` defaults so the schema remains stable.
- How does 90-day retention interact with user manual archiving? The retention cleaner runs at agent startup and removes files whose mtime is older than 90 days, but files with an `.archive` suffix or inside an `archive/` subdirectory are skipped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The diagnostics layer MUST be implemented as `agent/diagnostics.py` and expose a single structured logger interface usable by `run_agent.py`, `model_tools.py`, `cli.py`, and `gateway/`.
- **FR-002**: Every JSONL line MUST contain the stable top-level fields: `ts` (ISO-8601 UTC), `session_id`, `kit`, `skill`, `provider`, `model`, `workspace`, `gateway`, `event`, `latency_ms`, plus a `payload` object.
- **FR-003**: The logger MUST write to seven independent streams under `~/.hermes-lite/logs/`: `agent.jsonl`, `tools.jsonl`, `providers.jsonl`, `workspace.jsonl`, `security.jsonl`, `thermal.jsonl`, `api.jsonl`.
- **FR-004**: Each stream MUST rotate daily (new file at 00:00 UTC) and retain files for 90 days; files older than 90 days MUST be deleted at startup.
- **FR-005**: `security.jsonl` MUST be created with filesystem mode `0600` and MUST never be included in generic log exports unless explicitly requested.
- **FR-006**: `thermal.jsonl` MUST sample `tegrastats` every 5 seconds when running on a Jetson; when `tegrastats` is unavailable, the stream MUST be silently skipped.
- **FR-007**: The tool-call stream MUST classify outcomes as one of: `success`, `parse-fail`, `semantic-fail`, `refusal`, `timeout`.
- **FR-008**: The provider stream MUST record the full escalation chain: each attempted provider, its outcome, and the final responder.
- **FR-009**: The workspace stream MUST record every `workspace.*` call, including the target repo, files touched, byte delta, change-budget remaining, pre-commit gate result, and commit SHA.
- **FR-010**: The API stream MUST record every call to the deployed `azure-api` endpoint, including request id, route, status, latency, partner-vs-paid routing decision, and self-pentest probe results.
- **FR-011**: Secret redaction MUST be applied to all JSONL payloads before write; API keys, tokens, and passwords MUST be replaced with `<redacted>`.
- **FR-012**: The logger MUST degrade gracefully on read-only or full filesystems, emitting a single warning to `errors.log` and disabling the affected stream.
- **FR-013**: A CLI helper `hermes-lite logs --stream <name> --since <date> --tail <n> --grep <expr>` MUST allow filtering and tailing each stream.
- **FR-014**: Retention cleanup MUST skip files with an `.archive` suffix or residing in an `archive/` subdirectory.
- **FR-015**: The upstream plain-text logs (`agent.log`, `errors.log`, `gateway.log`) MUST remain unchanged; the JSONL layer MUST be purely additive.

### Key Entities

- **DiagnosticsLogger**: The singleton structured logger in `agent/diagnostics.py` that routes events to the appropriate JSONL stream.
- **LogStream**: A per-event-type append-only newline-delimited JSON file under `~/.hermes-lite/logs/` with daily rotation and 90-day retention.
- **StableSchema**: The fixed top-level JSON object shape shared across all streams, ensuring downstream analysis and partner-model ingestion are schema-stable.
- **ThermalSampler**: A background thread (or asyncio task) that polls `tegrastats` every 5 s and emits to `thermal.jsonl`.
- **RetentionCleaner**: A startup-time janitor that deletes stream files older than 90 days, respecting archive exclusions.
- **SecretRedactor**: A pre-write filter that replaces known secret patterns with `<redacted>`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `agent.jsonl` contains a valid `kit_load` event within 1 second of session start in integration testing.
- **SC-002**: `tools.jsonl` records at least one tool call with `latency_ms > 0` and a valid `outcome` enum value per test run.
- **SC-003**: `providers.jsonl` accurately captures an escalation chain (≥2 providers) during a simulated failure test.
- **SC-004**: `security.jsonl` is created with mode `0600` verified by `stat` in CI.
- **SC-005**: Daily rotation creates a new file at 00:00 UTC; the old file is closed and no longer written to.
- **SC-006**: Retention cleanup removes a synthetic 91-day-old file at startup while preserving a 1-day-old file.
- **SC-007**: Thermal sampling produces one line per 5-second interval on Jetson hardware; on non-Jetson hosts the stream is absent and the agent does not crash.
- **SC-008**: Secret redaction prevents any raw API key from appearing in any JSONL stream, verified by grep over all streams in CI.
- **SC-009**: The CLI helper returns filtered results in under 1 second for a 10,000-line stream.
- **SC-010**: Agent startup time increases by less than 200 ms when the diagnostics layer is initialized.

## Assumptions

- The Jetson Orin Nano runs JetPack 6.x with `tegrastats` available in `$PATH`.
- `~/.hermes-lite/logs/` resides on a POSIX filesystem that supports `chmod` (e.g., ext4 on the microSD card).
- Daily rotation boundaries are aligned to UTC; local timezone offsets are not required because the cyberdeck may change timezones.
- The upstream `hermes_logging.py` plain-text logs continue to serve human-readable tailing; JSONL streams are for machines and self-improvement loops.
- Downstream analysis (curator, partner-model quota sharing) reads JSONL directly via Python `json` or `jq`; no secondary database is required.
- Event volume is low enough (<10k lines/day) that plain JSONL is sufficient; no compression or columnar format is needed for v1.
- The 90-day retention window is a hard default; users who need longer retention can manually archive files before the cleaner runs.
- Log lines are written synchronously (buffered) but flushed at the end of every agent loop iteration to balance durability and I/O overhead.
