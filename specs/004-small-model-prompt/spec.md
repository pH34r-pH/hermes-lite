# Feature Specification: Small-Model System Prompt Profile

**Feature Branch**: `004-small-model-prompt`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New system-prompt profile for small models: remove verbose tool preamble, remove irrelevant platform guidance, limit active toolset to one kit at a time, shorten to <300 tokens, rely on byte-stable prefix caching. Read REDESIGN.md §5.5 and existing agent/system_prompt.py."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Verbose Tool-Use Preamble (Priority: P1)

Hermes-lite must provide a new system-prompt profile (keyed as `"small"` in `agent/system_prompt.py`) that strips the lengthy tool-use enforcement guidance, model-family operational directives, and computer-use blocks that upstream ships for large cloud models. The remaining guidance must fit in a single concise paragraph.

**Why this priority**: The upstream `TOOL_USE_ENFORCEMENT_GUIDANCE` plus `OPENAI_MODEL_EXECUTION_GUIDANCE` alone exceed 200 tokens. On a 3B model with a 32k context window, every token in the system prompt displaces user content or retrieval context.

**Independent Test**: Can be fully tested by constructing an `AIAgent` with `prompt_profile="small"` and asserting that the stable tier token count is under 300 tokens.

**Acceptance Scenarios**:

1. **Given** the agent is configured with `prompt_profile="small"`, **When** `build_system_prompt_parts()` is called, **Then** the `stable` tier does not contain the full `TOOL_USE_ENFORCEMENT_GUIDANCE` block
2. **Given** the agent is configured with `prompt_profile="small"`, **When** the prompt is tokenized, **Then** the stable tier is strictly fewer than 300 tokens
3. **Given** the agent is configured with `prompt_profile="small"`, **When** `build_system_prompt_parts()` is called, **Then** a single concise tool-use sentence (e.g. "Use available tools to act; do not describe intentions without acting.") replaces the multi-paragraph upstream guidance
4. **Given** the default upstream profile is used, **When** the prompt is built, **Then** the full verbose guidance is retained so upstream behavior is unchanged for non-lite deployments

---

### User Story 2 - Remove Irrelevant Platform Guidance (Priority: P2)

Hermes-lite must omit `PLATFORM_HINTS` entries for platforms that have been removed from the fork (Telegram, Slack, WhatsApp, Signal, Yuanbao, Feishu, etc.) and must inject only the platform hint relevant to the current gateway (Discord, TUI, or Open WebUI).

**Why this priority**: The upstream `PLATFORM_HINTS` dict contains guidance for 15+ messaging platforms. A small model running on the cyberdeck will only ever surface Discord, TUI, or Open WebUI. Including deleted platforms bloats the prompt and can confuse the model.

**Independent Test**: Can be fully tested by setting `agent.platform="discord"`, building the small profile, and grepping the stable tier for deleted platform names; none must appear.

**Acceptance Scenarios**:

1. **Given** `agent.platform="discord"`, **When** the small profile is built, **Then** the stable tier contains only the Discord platform hint and no other platform hints
2. **Given** `agent.platform="openwebui"`, **When** the small profile is built, **Then** an Open WebUI-specific platform hint is present and all other platform hints are absent
3. **Given** `agent.platform="cli"` (TUI), **When** the small profile is built, **Then** the CLI hint is present and references to `MEDIA:/path` interception are concise
4. **Given** a deleted platform name such as `"telegram"` or `"slack"`, **When** the small profile is built, **Then** neither the name nor any of its guidance text appears anywhere in the system prompt

---

### User Story 3 - Limit Active Toolset to One Kit at a Time (Priority: P3)

Hermes-lite must modify the skills-prompt and tool-aware guidance blocks so they reference only the tools belonging to the active kit. The skills index preamble must be shortened or omitted when the profile is `"small"`, and per-tool guidance (e.g. `MEMORY_GUIDANCE`, `KANBAN_GUIDANCE`) must be included only if the corresponding tool is in the active kit.

**Why this priority**: The upstream skills prompt includes a mandatory enumeration of all available skills and heavy guidance for memory, kanban, session search, etc. A small model operating in the arxiv kit does not need kanban worker lifecycle rules in its system prompt.

**Independent Test**: Can be fully tested by activating the `arxiv` kit with the small profile and asserting that `kanban_show`, `memory`, and `session_search` guidance blocks are absent from the stable tier.

**Acceptance Scenarios**:

1. **Given** `active_kit="arxiv"` and `prompt_profile="small"`, **When** the system prompt is assembled, **Then** the stable tier does not contain `KANBAN_GUIDANCE` because the kanban tools are not in the arxiv kit allowlist
2. **Given** `active_kit="spec-kit"` and `prompt_profile="small"`, **When** the system prompt is assembled, **Then** only the skills relevant to spec authoring appear in the skills index (or the skills index is omitted entirely)
3. **Given** the small profile is active, **When** the `computer_use` tool is not in the active kit, **Then** `COMPUTER_USE_GUIDANCE` is absent from the stable tier
4. **Given** the small profile is active and the active kit includes `memory`, **When** the system prompt is assembled, **Then** a condensed single-sentence memory guidance replaces the full multi-paragraph `MEMORY_GUIDANCE`

---

### User Story 4 - Rely on Byte-Stable Prefix Caching (Priority: P4)

Hermes-lite must ensure that the small-profile system prompt is byte-identical across turns when the active kit, platform, and model do not change. The timestamp line must remain date-only (already upstream behavior), and any kit-specific text must be rendered deterministically so that Ollama / llama.cpp prefix caches remain warm.

**Why this priority**: Prefix-cache hits are the single largest latency win for on-device small models. A single changed byte invalidates the entire KV cache for the system prompt.

**Independent Test**: Can be fully tested by calling `build_system_prompt()` twice in a row with identical agent state and asserting byte equality of the full string.

**Acceptance Scenarios**:

1. **Given** identical agent state (same kit, platform, model, no new memory), **When** `build_system_prompt()` is called on turn N and turn N+1, **Then** the resulting strings are byte-for-byte identical
2. **Given** a context compression event occurs, **When** the prompt is rebuilt, **Then** only the volatile tier changes; the stable tier remains byte-identical and cacheable
3. **Given** the active kit changes from `arxiv` to `dev`, **When** the prompt is rebuilt, **Then** the stable tier changes (expected cache miss) and the new stable tier is itself byte-identical on subsequent turns
4. **Given** the small profile is active, **When** the agent initializes, **Then** the system prompt is cached on `agent._cached_system_prompt` and is not rebuilt unless invalidated by a kit switch or compression event

---

### Edge Cases

- What happens when `agent.platform` is set to a deleted platform string leaked from an old config? The small profile must emit no platform hint rather than crashing or falling back to a verbose default.
- How does the system handle a kit that has zero allowlisted tools? The small profile must still produce a valid system prompt with concise identity and no tool guidance.
- What happens when the user provides a custom `system_message` that is itself longer than 300 tokens? The custom message goes into the `context` tier, which is outside the small-profile's 300-token commitment for the `stable` tier only.
- What happens when SOUL.md is present and is longer than 300 tokens on its own? The small profile may truncate SOUL.md to a head/tail summary or fall back to `DEFAULT_AGENT_IDENTITY` if the full SOUL.md exceeds the budget.
- How does the small profile interact with the `alibaba` model identity workaround? It must still inject the short model-identity sentence when `provider == "alibaba"`, because the workaround is required for correct behavior.
- What happens when the agent is spawned as a kanban worker (HERMES_KANBAN_TASK env set) but the small profile is active? The kanban guidance must still appear because the worker cannot function without it; however it should be the only expanded guidance block in an otherwise concise prompt.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add a new `prompt_profile` parameter to `AIAgent` (default `"default"`, accept `"small"`) that is stored on the agent instance
- **FR-002**: System MUST implement a `build_small_system_prompt_parts(agent, system_message)` function in `agent/system_prompt.py` that returns the same three-tier dict (`stable`, `context`, `volatile`) with a drastically shortened stable tier
- **FR-003**: The small-profile stable tier MUST be fewer than 300 tokens when tokenized with tiktoken `cl100k_base` (the encoding used by most small models)
- **FR-004**: The small-profile stable tier MUST omit `TOOL_USE_ENFORCEMENT_GUIDANCE`, `OPENAI_MODEL_EXECUTION_GUIDANCE`, `GOOGLE_MODEL_OPERATIONAL_GUIDANCE`, and `COMPUTER_USE_GUIDANCE` in full
- **FR-005**: The small-profile stable tier MUST include at most one platform hint — the hint matching `agent.platform` if it is in the allowlisted set (`discord`, `tui`/`cli`, `openwebui`); otherwise omit platform hints entirely
- **FR-006**: The small-profile stable tier MUST omit `PLATFORM_HINTS` entries for all deleted platforms (Telegram, Slack, WhatsApp, Signal, Email, Yuanbao, Weixin, WeCom, Feishu, DingTalk, QQBot, Matrix, Mattermost, HomeAssistant, BlueBubbles, SMS, Webhook)
- **FR-007**: The small-profile stable tier MUST conditionally include per-tool guidance blocks (`MEMORY_GUIDANCE`, `SESSION_SEARCH_GUIDANCE`, `SKILLS_GUIDANCE`, `KANBAN_GUIDANCE`) only when the corresponding tool is present in the active kit's allowlist; when included, a condensed one-sentence variant must be used
- **FR-008**: The small-profile stable tier MUST shorten or omit the skills index block (`build_skills_system_prompt`) unless the active kit explicitly requires skill awareness
- **FR-009**: System MUST fall back to `DEFAULT_AGENT_IDENTITY` when SOUL.md would cause the stable tier to exceed the 300-token budget
- **FR-010**: System MUST continue to inject the Alibaba model-identity workaround and environment hints in the small profile, because both are required for correct operation
- **FR-011**: System MUST keep the upstream `build_system_prompt_parts()` function intact (renamed or branched) so that non-lite profiles continue to work unchanged

### Key Entities

- **SmallProfileStableTier**: The shortened system-prompt content for small models. Lives in `agent/system_prompt.py` as a conditional branch.
- **PromptProfile**: A string enum (`"default"`, `"small"`) stored on `AIAgent` that selects which assembly function to call.
- **PlatformHintAllowlist**: The set of platforms whose hints may appear in the small profile: `discord`, `cli`/`tui`, `openwebui`.
- **TokenBudget**: The 300-token upper bound enforced on the small-profile stable tier. Measured with tiktoken for consistency.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The small-profile stable tier token count is under 300 tokens for all supported kits (arxiv, spec-kit, dev, web-ops, azure-ops, security), verified by a parameterized pytest loop
- **SC-002**: A grep for deleted platform names across the small-profile stable tier returns zero matches for every deleted platform
- **SC-003**: Two successive calls to `build_system_prompt()` with identical state produce byte-identical strings, verified by `assert prompt_1 == prompt_2`
- **SC-004**: Switching from `"default"` to `"small"` profile reduces the stable tier token count by at least 60%, measured by `(tokens_default - tokens_small) / tokens_default >= 0.6`
- **SC-005**: Agent startup smoke test (`python -c "from agent.system_prompt import build_system_prompt_parts; ..."`) passes for both `"default"` and `"small"` profiles without import errors
- **SC-006**: The kanban worker path (`HERMES_KANBAN_TASK` set) with `"small"` profile still includes a condensed kanban guidance block, verified by substring search in the stable tier

## Assumptions

- The upstream `agent/system_prompt.py` three-tier architecture (`stable`, `context`, `volatile`) is preserved; only the contents of the stable tier change
- tiktoken is available in the hermes-lite environment to measure token budgets accurately
- The `active_kit` is known at agent initialization time and does not change without an explicit invalidate/rebuild cycle
- Platform hints for Discord, TUI, and Open WebUI are retained in `agent/prompt_builder.py` or added to `agent/system_prompt.py`; they are not deleted by `001-gateway-cleanup`
- SOUL.md is optional; when present it may be large, so the small profile must be willing to ignore it to meet the 300-token budget
- The skills index (`build_skills_system_prompt`) is considered optional for small-model operation because the user can explicitly load a skill via slash command when needed
