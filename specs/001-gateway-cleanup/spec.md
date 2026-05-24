# Feature Specification: Non-Allowlisted Gateway and Web Dashboard Cleanup

**Feature Branch**: `001-gateway-cleanup`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Remove non-allowlisted chat platforms and the bundled web dashboard, retaining only TUI, Discord, and Open WebUI. Introduce a new Open WebUI gateway that converges all three surfaces on the same agent loop and state.db."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Non-Allowlisted Chat Platforms (Priority: P1)

Hermes-lite must delete all gateway platform modules, adapters, and identity helpers that correspond to non-allowlisted chat surfaces, leaving only Discord, TUI, and the future Open WebUI gateway.

**Why this priority**: This is the foundational gateway cleanup. Every platform module carries dependencies (HTTP clients, crypto, sticker caches, rate-limit shims) that bloat the Jetson image and increase the cognitive surface for a 3B model.

**Independent Test**: Can be fully tested by running `python -c "from gateway.platforms import *; load_platforms()"` after deletion and confirming only Discord, TUI, and Open WebUI adapters load.

**Acceptance Scenarios**:

1. **Given** `gateway/platforms/telegram.py` and `gateway/platforms/telegram_network.py` exist, **When** the cleanup is applied, **Then** both files are deleted and no other module imports them
2. **Given** `gateway/platforms/slack.py` exists, **When** the cleanup is applied, **Then** the file is deleted and no other module imports it
3. **Given** `gateway/platforms/whatsapp.py` exists, **When** the cleanup is applied, **Then** the file is deleted and no other module imports it
4. **Given** `gateway/platforms/signal.py` and `gateway/platforms/signal_rate_limit.py` exist, **When** the cleanup is applied, **Then** both files are deleted and no other module imports them
5. **Given** `gateway/platforms/email.py` exists, **When** the cleanup is applied, **Then** the file is deleted and no other module imports it
6. **Given** `gateway/platforms/yuanbao.py`, `gateway/platforms/yuanbao_proto.py`, `gateway/platforms/yuanbao_sticker.py`, and `gateway/platforms/yuanbao_media.py` exist, **When** the cleanup is applied, **Then** all four files are deleted and no other module imports them
7. **Given** `gateway/platforms/weixin.py` exists, **When** the cleanup is applied, **Then** the file is deleted and no other module imports it
8. **Given** `gateway/platforms/wecom.py`, `gateway/platforms/wecom_callback.py`, and `gateway/platforms/wecom_crypto.py` exist, **When** the cleanup is applied, **Then** all three files are deleted
9. **Given** `gateway/platforms/feishu.py`, `gateway/platforms/feishu_comment.py`, and `gateway/platforms/feishu_comment_rules.py` exist, **When** the cleanup is applied, **Then** all three files are deleted
10. **Given** `gateway/platforms/dingtalk.py`, `gateway/platforms/qqbot/`, `gateway/platforms/matrix.py`, `gateway/platforms/mattermost.py`, `gateway/platforms/homeassistant.py`, `gateway/platforms/bluebubbles.py`, `gateway/platforms/sms.py`, `gateway/platforms/msgraph_webhook.py`, and `gateway/platforms/webhook.py` exist, **When** the cleanup is applied, **Then** all are deleted

---

### User Story 2 - Remove Bundled Web Dashboard and Related Plugins (Priority: P2)

Hermes-lite must delete the bundled web dashboard (`website/`, `web/`, `plugins/web/`, `example-dashboard/`) and related media or achievement plugins because the fork relies on Open WebUI as its browser surface and does not ship a standalone web UI.

**Why this priority**: The bundled dashboard is a large Docusaurus/React dependency tree that is irrelevant to the cyberdeck. Removing it frees disk space and eliminates a maintenance surface.

**Independent Test**: Can be fully tested by verifying `website/`, `web/`, `plugins/web/`, `plugins/image_gen/`, `plugins/video_gen/`, `plugins/spotify/`, `plugins/google_meet/`, `plugins/teams_pipeline/`, and `plugins/hermes-achievements/` no longer exist.

**Acceptance Scenarios**:

1. **Given** the repo contains `website/`, **When** the cleanup is applied, **Then** the directory is deleted
2. **Given** the repo contains `web/`, **When** the cleanup is applied, **Then** the directory is deleted
3. **Given** the repo contains `plugins/web/`, **When** the cleanup is applied, **Then** the directory is deleted (or reduced to web-search-provider components only per REDESIGN.md §4.3)
4. **Given** the repo contains `plugins/spotify/`, `plugins/google_meet/`, `plugins/teams_pipeline/`, and `plugins/hermes-achievements/`, **When** the cleanup is applied, **Then** all four directories are deleted
5. **Given** any gateway session initializer references a web-dashboard URL, **When** the cleanup is applied, **Then** that reference is removed

---

### User Story 3 - Introduce Open WebUI Gateway (Priority: P3)

Hermes-lite must create a new `gateway/platforms/openwebui/` package that registers as an Open WebUI pipeline, maps Open WebUI conversation IDs to Hermes session IDs, enforces a user allowlist, and streams responses.

**Why this priority**: Open WebUI is the third allowlisted surface alongside TUI and Discord. It provides a browser-based experimentation endpoint backed by the Azure Static Web App without requiring a custom dashboard.

**Independent Test**: Can be fully tested by running an Open WebUI instance, installing the Hermes-Lite pipeline, sending a message, and verifying the response appears in the Hermes session history.

**Acceptance Scenarios**:

1. **Given** `gateway/platforms/openwebui/` is created, **When** the gateway loads, **Then** it registers under the name "Hermes-Lite" in Open WebUI's pipeline list
2. **Given** an Open WebUI user sends a message, **When** the pipeline receives it, **Then** the gateway creates or reuses a Hermes session in `state.db` and maps the Open WebUI conversation ID to the Hermes session ID
3. **Given** the Open WebUI gateway has an allowlist configured, **When** a disallowed user sends a message, **Then** the gateway rejects the request with an HTTP 403 and logs the attempt
4. **Given** the agent produces a response containing markdown tables, code blocks, and arXiv citations, **When** the gateway streams it back, **Then** the Open WebUI client renders them correctly
5. **Given** a session started in Open WebUI, **When** the same session ID is inspected in the TUI or Discord, **Then** the conversation history is identical because all surfaces converge on the same `state.db`

---

### User Story 4 - Converge All Surfaces on Shared Agent Loop and State (Priority: P4)

Hermes-lite must ensure that TUI, Discord, and Open WebUI all feed into the same agent conversation loop, skill surface, and `state.db` so a user can switch surfaces mid-session without data loss.

**Why this priority**: This is the user-experience guarantee of the three-surface design. Divergence defeats the purpose of keeping multiple gateways.

**Independent Test**: Can be fully tested by starting a session in Discord, sending a directive, then opening the TUI for the same session ID and verifying the history and agent state are consistent.

**Acceptance Scenarios**:

1. **Given** a user sends a directive via Discord, **When** the agent processes it and stores the result in `state.db`, **Then** the TUI lists the same session and the same turn count
2. **Given** a user sends a directive via Open WebUI, **When** the agent processes it and stores the result in `state.db`, **Then** the Discord bot can quote the same session ID on request
3. **Given** the curator or background reviewer enqueues a job, **When** the job is stored in `~/.hermes-lite/queue/curator.jsonl`, **Then** any surface can surface the approval prompt when the batch threshold is reached
4. **Given** the active skill kit changes (e.g. from arXiv to spec-kit), **When** the tool surface is rebuilt, **Then** all three gateways see the same rebuilt tool schema

---

### Edge Cases

- What happens when a `gateway/platforms/__init__.py` dynamic loader iterates over all `.py` files in the directory? The loader must be updated to skip deleted platforms or to use an explicit allowlist rather than filesystem discovery.
- What happens when a user's upstream `config.yaml` still references `telegram` or `slack` as an enabled gateway? The config loader must raise a clear error naming the disallowed platform.
- How does the system handle an Open WebUI pipeline that sends a conversation ID containing characters unsafe for SQLite primary keys? The mapping layer must sanitize or hash the external ID before using it as a lookup key.
- What happens when two surfaces (e.g. Discord and Open WebUI) send messages to the same Hermes session simultaneously? The agent loop must serialize turns per session; concurrent requests must queue or return a 409 busy response.
- What happens when the Open WebUI gateway receives a message larger than the Ollama context window? The gateway must rely on the existing context compressor (`agent/context_compressor.py`) rather than implementing its own truncation logic.
- What happens when `gateway/platforms/discord.py` imports platform helpers from a deleted module? Any shared helpers in `gateway/platforms/helpers.py` that were only used by deleted platforms must be audited and excised if unused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST delete `gateway/platforms/telegram.py`, `gateway/platforms/telegram_network.py`, and all Telegram-specific identity, sticker, and topic-preservation logic
- **FR-002**: System MUST delete `gateway/platforms/slack.py` and all Slack-specific adapter logic
- **FR-003**: System MUST delete `gateway/platforms/whatsapp.py` and all WhatsApp-specific identity and adapter logic
- **FR-004**: System MUST delete `gateway/platforms/signal.py`, `gateway/platforms/signal_rate_limit.py`, and all Signal-specific adapter logic
- **FR-005**: System MUST delete `gateway/platforms/email.py` and all email-specific adapter logic
- **FR-006**: System MUST delete `gateway/platforms/yuanbao.py`, `gateway/platforms/yuanbao_proto.py`, `gateway/platforms/yuanbao_sticker.py`, and `gateway/platforms/yuanbao_media.py`
- **FR-007**: System MUST delete `gateway/platforms/weixin.py` and all Weixin-specific adapter logic
- **FR-008**: System MUST delete `gateway/platforms/wecom.py`, `gateway/platforms/wecom_callback.py`, and `gateway/platforms/wecom_crypto.py`
- **FR-009**: System MUST delete `gateway/platforms/feishu.py`, `gateway/platforms/feishu_comment.py`, and `gateway/platforms/feishu_comment_rules.py`
- **FR-010**: System MUST delete `gateway/platforms/dingtalk.py`, `gateway/platforms/qqbot/`, `gateway/platforms/matrix.py`, `gateway/platforms/mattermost.py`, `gateway/platforms/homeassistant.py`, `gateway/platforms/bluebubbles.py`, `gateway/platforms/sms.py`, `gateway/platforms/msgraph_webhook.py`, and `gateway/platforms/webhook.py`
- **FR-011**: System MUST delete `website/`, `web/`, `plugins/web/` (or reduce it to web-search-provider components only), `plugins/spotify/`, `plugins/google_meet/`, `plugins/teams_pipeline/`, and `plugins/hermes-achievements/`
- **FR-012**: System MUST retain `gateway/platforms/discord.py`, `tui_gateway/`, and `ui-tui/`
- **FR-013**: System MUST create `gateway/platforms/openwebui/` containing at minimum: pipeline registration, session ID mapping, user allowlist enforcement, and streaming response logic
- **FR-014**: System MUST map Open WebUI conversation IDs to Hermes session IDs bidirectionally and store the mapping in `state.db`
- **FR-015**: System MUST reject Open WebUI requests from users not on the allowlist with HTTP 403
- **FR-016**: System MUST update `gateway/platforms/__init__.py` or the platform loader to only enumerate the three allowlisted surfaces
- **FR-017**: System MUST raise a clear ``ConfigurationError`` at startup when any config references a removed platform
- **FR-018**: System MUST ensure Discord, TUI, and Open WebUI all use the same `agent/conversation_loop.py`, `agent/tool_surface.py`, and `state.db` instance

### Key Entities

- **GatewayPlatformSet**: The canonical list of allowed gateway surfaces — `discord`, `tui`, `openwebui`
- **OpenWebuiGateway**: The new gateway adapter that implements the Open WebUI pipeline protocol
- **SessionIdMapping**: The table or key-value store that maps external Open WebUI conversation IDs to internal Hermes session IDs
- **PlatformLoader**: The runtime mechanism that discovers and registers gateway platforms; post-cleanup it uses an explicit allowlist

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `find gateway/platforms/ -maxdepth 1 -name "*.py" | wc -l` returns at most 5 files (`__init__.py`, `base.py`, `discord.py`, `helpers.py`, and the Open WebUI entry) after the cleanup
- **SC-002**: `ls website/ web/ plugins/web/ plugins/spotify/ plugins/google_meet/ plugins/teams_pipeline/ plugins/hermes-achievements/ 2>&1 | grep "No such file" | wc -l` returns 7 after the cleanup
- **SC-003**: The agent startup smoke test (`python -c "from gateway.platforms import load_platforms; p=load_platforms(); assert set(p) == {'discord','tui','openwebui'}"`) completes successfully
- **SC-004**: A config file referencing a removed platform causes the agent to exit with a clear error message within 2 seconds of config load
- **SC-005**: The Open WebUI gateway responds to a test message with a valid pipeline payload in under 5 seconds when Ollama is available
- **SC-006**: A session created in Discord is visible in the TUI with identical turn count and message content within 1 second of state commit

## Assumptions

- The TUI gateway (`tui_gateway/`) and its Ink/React frontend (`ui-tui/`) do not depend on any deleted platform modules
- Discord gateway (`gateway/platforms/discord.py`) does not dynamically import deleted platforms at runtime
- Open WebUI is already deployed and accessible on the target VM or network; the gateway only needs to implement the pipeline protocol, not deploy Open WebUI itself
- The shared `gateway/session.py`, `gateway/session_context.py`, and `hermes_state.py` are platform-agnostic and remain intact
- The `gateway/platforms/base.py` abstraction is sufficient for Open WebUI to implement without introducing a new base class
- Any cross-platform helpers in `gateway/platforms/helpers.py` are either retained because Discord uses them, or deleted if they were only used by removed platforms
- The `state.db` schema does not require migration; new tables for Open WebUI mapping are additive
