# Feature Specification: Tool-Surface Slimmer

**Feature Branch**: `003-tool-surface-slimmer`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New agent/tool_surface.py module that exposes only tools required by the active kit, validates schemas against allow-list, emits static cache-friendly digest, refuses to load tools importing removed providers. Read REDESIGN.md §5.6."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Expose Only Active Kit Tools (Priority: P1)

Hermes-lite must construct the tool schema sent to the model from exactly one active kit (e.g. arxiv, dev, spec-kit) rather than the full Hermes core tool surface. This reduces the schema token footprint so a 3B model can fit the prompt inside its context window.

**Why this priority**: This is the foundational behavior of the tool-surface slimmer. Without kit-scoped tooling, small models see 40+ tool schemas and either overflow context or ignore instructions.

**Independent Test**: Can be fully tested by starting an agent with `active_kit="arxiv"`, requesting tool definitions, and verifying that only tools listed in the arxiv kit allowlist are present.

**Acceptance Scenarios**:

1. **Given** the agent is initialized with `active_kit="arxiv"`, **When** `tool_surface.get_definitions()` is called, **Then** the returned list contains only the tools registered in the `arxiv` kit allowlist
2. **Given** the agent is initialized with `active_kit="dev"`, **When** `tool_surface.get_definitions()` is called, **Then** tools such as `arxiv-discover`, `arxiv-fetch`, and `arxiv-skim` are absent from the schema
3. **Given** no active kit is specified, **When** `tool_surface.get_definitions()` is called, **Then** it falls back to a minimal safe default kit (e.g. `hermes-lite-core`) rather than exposing the full upstream tool surface
4. **Given** the active kit changes mid-session from `arxiv` to `spec-kit`, **When** the agent rebuilds the tool surface, **Then** the new schema reflects the `spec-kit` allowlist and the old arxiv-only tools are removed

---

### User Story 2 - Validate Tool Schemas Against Per-Kit Allowlist (Priority: P2)

Hermes-lite must validate every tool schema that is about to be exposed to the model against a hand-curated allowlist defined per kit. Unknown or newly-registered tools that are not explicitly allowlisted for the current kit must be dropped with a warning log.

**Why this priority**: Prevents accidentally leaking tools into a small model's context when a plugin or skill registers something outside the kit's intended scope.

**Independent Test**: Can be fully tested by registering a mock tool at runtime and confirming it does not appear in the schema when the active kit's allowlist does not contain it.

**Acceptance Scenarios**:

1. **Given** a tool `mock_tool` is registered in the global registry but is absent from the `arxiv` kit allowlist, **When** the agent requests definitions for kit `arxiv`, **Then** `mock_tool` is excluded and a warning is logged
2. **Given** the `spec-kit` allowlist explicitly names `read_file`, `write_file`, `patch`, and `search_files`, **When** the agent requests definitions for kit `spec-kit`, **Then** exactly those four tools are present and no others
3. **Given** a tool's schema fails structural validation (e.g. missing required `name` field), **When** the allowlist validator inspects it, **Then** the tool is rejected and an error is logged naming the offending schema
4. **Given** the allowlist is updated on disk and the agent hot-reloads it, **When** the next turn requests tool definitions, **Then** the updated allowlist is applied without requiring a process restart

---

### User Story 3 - Emit Static Cache-Friendly Digest (Priority: P3)

Hermes-lite must compute a deterministic, byte-stable digest of the active tool schema so that upstream prompt-prefix caches (Ollama, vLLM, llama.cpp) can reuse the KV state across turns. The digest must change only when the kit or the allowlisted tool schemas change.

**Why this priority**: Small-model inference on-device is latency-sensitive. Rebuilding the tool schema differently on every turn invalidates the prefix cache and doubles per-turn latency.

**Independent Test**: Can be fully tested by calling `tool_surface.digest()` twice with the same kit and comparing the digests; then mutating a tool description and confirming the digest changes.

**Acceptance Scenarios**:

1. **Given** the same active kit and unchanged tool schemas, **When** `tool_surface.digest()` is called on successive turns, **Then** the returned digest string is identical across calls
2. **Given** a tool description is patched in the registry, **When** `tool_surface.digest()` is called again, **Then** the digest changes to reflect the new schema bytes
3. **Given** the agent switches from kit `A` to kit `B`, **When** `tool_surface.digest()` is called, **Then** the digest is different from the kit-`A` digest
4. **Given** the digest is emitted, **When** the agent builds the API request, **Then** the digest is attached as a stable identifier (e.g. header or metadata) so that external cache layers can key on it

---

### User Story 4 - Refuse to Load Tools Importing Removed Providers (Priority: P4)

Hermes-lite must inspect each tool module's import graph at load time and refuse to surface any tool that transitively imports a provider or platform module that has been removed by the fork (e.g. Telegram, Slack, WhatsApp, Signal, Yuanbao, etc.).

**Why this priority**: The fork deletes many upstream providers. A stray tool that still imports a deleted module would cause an `ImportError` at runtime or, worse, reintroduce a removed dependency into the Jetson image.

**Independent Test**: Can be fully tested by attempting to register a tool that imports `gateway.platforms.telegram` and confirming it is rejected before any schema is emitted.

**Acceptance Scenarios**:

1. **Given** a tool implementation contains `import gateway.platforms.telegram`, **When** `tool_surface` scans the module's imports during registration, **Then** the tool is rejected and a `ProviderRemovedError` is raised
2. **Given** a tool implementation transitively imports a removed provider via a utility module, **When** `tool_surface` performs a depth-limited transitive import scan, **Then** the tool is rejected and the log names the offending import chain
3. **Given** a tool imports only allowed modules (e.g. `tools.registry`, `agent.ollama_adapter`), **When** the import scan runs, **Then** the tool is accepted and surfaced normally
4. **Given** the removed-provider denylist is configurable in `lite-config.yaml`, **When** an admin adds a new pattern, **Then** tools matching that pattern are rejected on the next agent init

---

### Edge Cases

- What happens when a kit allowlist references a tool name that does not exist in the registry? The validator must log a clear warning and continue with the remaining allowed tools rather than crashing.
- How does the system handle two kits with identical allowlists but different digest salts? The digests must still be distinct so cache layers do not conflate them.
- What happens when a tool's `check_fn` (dynamic availability predicate) returns `False` at runtime? The tool must be omitted from the schema even if it is on the allowlist, and the digest must reflect the runtime-available subset.
- What happens when the registry is mutated mid-turn by a plugin? The digest for the next turn must incorporate the mutation, but the current turn must not be affected.
- How does the import scanner behave with lazy imports (`importlib.import_module` inside a function)? Static top-level import scanning is sufficient for v1; lazy imports are out of scope but should be documented as a known gap.
- What happens when the active kit is changed while a long-running subagent is using the old kit? The subagent must retain its original tool surface; only new agent instances pick up the new kit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a new `agent/tool_surface.py` module that exposes `get_definitions(active_kit: str) -> list`, `validate(tool_schema, kit_allowlist)`, `digest() -> str`, and `scan_imports(module) -> list`
- **FR-002**: System MUST define per-kit allowlists in a structured format (e.g. `agent/tool_surface_allowlists.yaml` or JSON) mapping kit names to ordered lists of permitted tool names
- **FR-003**: System MUST reject any tool whose name is not present in the active kit's allowlist, logging the rejection at `WARNING` level
- **FR-004**: System MUST compute a SHA-256 or similar deterministic digest over the canonical JSON serialization of the filtered tool schemas, sorted by tool name, with deterministic key ordering and no timestamps
- **FR-005**: System MUST cache the digest per `(active_kit, registry_generation)` and invalidate the cache when the registry generation counter changes
- **FR-006**: System MUST scan the top-level import statements of each tool module and reject tools importing modules matching a denylist of removed providers (e.g. `gateway.platforms.telegram`, `gateway.platforms.slack`)
- **FR-007**: System MUST provide a configurable denylist in `lite-config.yaml` under `tool_surface.removed_provider_patterns`
- **FR-008**: System MUST integrate with the existing `tools.registry` so that `agent/tool_surface.py` consumes registry schemas rather than reimplementing discovery
- **FR-009**: System MUST fall back to a `hermes-lite-core` default kit when `active_kit` is missing or unrecognised
- **FR-010**: System MUST return an empty tool schema rather than crashing when the active kit allowlist is empty or all allowed tools fail their `check_fn`

### Key Entities

- **ToolSurface**: The runtime object that holds the active kit, the filtered schema list, and the cached digest. Lives in `agent/tool_surface.py`.
- **KitAllowlist**: The static mapping from kit name to permitted tool names. Loaded once at startup and reloadable via a public method.
- **ToolSchemaDigest**: A deterministic hash string representing the exact byte content of the active tool schema. Used for prefix-cache keying.
- **ProviderDenylist**: A list of Python module path patterns (e.g. `gateway.platforms.telegram`) that must not appear in a tool module's import graph.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With `active_kit="arxiv"`, the tool schema passed to the model contains no more than 12 tools (the arxiv kit scope), verified by `len(tool_surface.get_definitions("arxiv")) <= 12`
- **SC-002**: The digest for the same kit on two successive turns is identical, verified by `digest_turn_1 == digest_turn_2` with a pytest assertion
- **SC-003**: A tool importing `gateway.platforms.telegram` is rejected before its schema is ever emitted, verified by unit test asserting `ProviderRemovedError` on registration
- **SC-004**: Switching kits from `arxiv` to `spec-kit` changes the digest, verified by `digest_arxiv != digest_spec`
- **SC-005**: The `agent/tool_surface.py` module has no direct dependency on `model_tools.py` or `run_agent.py` — it is imported by them, not the reverse, verified by static import graph analysis
- **SC-006**: Agent startup with `active_kit="dev"` completes in under 500 ms on Jetson Orin Nano, measured by `time hermes-lite --kit dev --dry-run`

## Assumptions

- The upstream `tools.registry` module remains intact and continues to provide `get_definitions()`, `register()`, and `_generation` counter semantics
- Tool modules use top-level imports for their provider dependencies; lazy imports inside functions are not scanned in v1
- The list of removed providers matches the platforms deleted in `001-gateway-cleanup` (Telegram, Slack, WhatsApp, Signal, Email, Yuanbao, Weixin, WeCom, Feishu, DingTalk, QQBot, Matrix, Mattermost, HomeAssistant, BlueBubbles, SMS, Webhook)
- Kits are selected before the agent loop starts and do not change more than once per session in normal usage
- The Ollama / llama.cpp prefix cache implementation keys on the full messages array including the tool schema; a stable digest is therefore sufficient for cache hits
- `lite-config.yaml` (spec `005-lite-config`) exists and is loadable by the time `agent/tool_surface.py` is imported
