# Feature Specification: Open WebUI Gateway

**Feature Branch**: `011-openwebui-gateway`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "New gateway/platforms/openwebui/ package. Registers as Open WebUI pipeline. Maps conversation IDs to hermes session IDs. User allowlist. Streams markdown, code blocks, citations. Read REDESIGN.md §5.3."

## Current State

Upstream Hermes Agent ships a `gateway/platforms/` directory containing 40+ platform adapters (Telegram, Discord, Slack, WhatsApp, Signal, Email, Yuanbao, Weixin, Feishu, DingTalk, WeCom, QQ, BlueBubbles, Matrix, Mattermost, HomeAssistant, SMS, Webhook, API server, etc.). Each adapter inherits from `gateway/platforms/base.py` and implements platform-specific intake, routing, and response streaming. There is **no Open WebUI platform adapter**. While upstream Hermes had a bundled web dashboard (`web/`, `website/`, `plugins/web/`), that dashboard is a full standalone web UI, not an Open WebUI pipeline integration. The upstream agent has no concept of mapping Open WebUI conversation IDs to hermes session IDs, no Open WebUI user allowlist enforcement, and no pipeline-shaped response streaming that targets Open WebUI's markdown/code-block/citation rendering conventions.

The upstream `gateway/session.py` and `gateway/session_context.py` manage session creation and persistence in `state.db`, but there is no integration point for external conversation-ID mapping. The upstream `agent/display.py` and `agent/markdown_tables.py` format responses for terminal and chat platforms, but they do not emit pipeline-shaped streaming deltas optimized for a browser UI.

## Target State

Hermes-lite ships a `gateway/platforms/openwebui/` package that registers as an Open WebUI pipeline named "Hermes-Lite". The pipeline adapter:

- Accepts Open WebUI conversation payloads and maps each Open WebUI conversation ID to a hermes session ID in `state.db`, so the same session history is visible across TUI, Discord, and Open WebUI.
- Enforces an allowlist of Open WebUI users (`lite-config.yaml` or a dedicated file); non-allowlisted users receive a polite refusal.
- Streams responses with markdown tables, fenced code blocks, and citation references (especially arXiv IDs) formatted for Open WebUI's rendering pipeline.
- Converges on the same agent loop (`run_agent.py`) and the same `state.db` as Discord and TUI, so a directive issued in Open WebUI can be inspected in the TUI and vice versa.
- Supports the same slash commands and kit loading as other gateways, including `/arxiv`, `/spec`, and `/sec`.

The adapter is the **experimentation endpoint** that runs alongside Discord (the stable remote source), not a replacement for it.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register as an Open WebUI Pipeline and Map Conversations (Priority: P1)

An admin configures Open WebUI to use the Hermes-Lite pipeline. A user opens the Open WebUI chat interface, sends a message, and the adapter maps the Open WebUI conversation ID to a hermes session ID in `state.db`. Subsequent messages in the same conversation reuse the session.

**Why this priority**: Conversation-to-session mapping is what makes Open WebUI a first-class gateway. Without it, every message would start a new orphan session and lose context.

**Independent Test**: Can be fully tested by sending two messages in the same Open WebUI conversation and verifying in `state.db` that both are attached to the same hermes session ID.

**Acceptance Scenarios**:

1. **Given** the admin adds "Hermes-Lite" to Open WebUI's pipeline settings, **When** a user sends a message, **Then** the pipeline adapter receives the payload and routes it into the hermes agent loop
2. **Given** a conversation with Open WebUI conversation ID `conv-123`, **When** the first message is processed, **Then** a new hermes session is created and the mapping `conv-123 → <session-id>` is stored in `state.db`
3. **Given** the same conversation sends a second message, **When** the adapter processes it, **Then** it reuses the mapped session ID and appends to the existing conversation history
4. **Given** the user opens a new browser tab with a different conversation ID, **When** a message is sent, **Then** a new hermes session is created and mapped independently

---

### User Story 2 - Enforce User Allowlist (Priority: P1)

The hermes-lite admin configures an allowlist of Open WebUI users. An allowlisted user can chat normally. A non-allowlisted user receives a polite refusal message and cannot trigger agent tool calls.

**Why this priority**: The Open WebUI pipeline is exposed to any browser with access to the host. An allowlist prevents unauthorized users from consuming agent quota or triggering workspace mutations.

**Independent Test**: Can be fully tested by configuring an allowlist with one user, sending messages from both allowed and disallowed users, and verifying the responses.

**Acceptance Scenarios**:

1. **Given** user `alice` is in the allowlist, **When** she sends a message, **Then** the agent processes it normally and returns a response
2. **Given** user `bob` is not in the allowlist, **When** he sends a message, **Then** he receives a polite refusal: "This agent is restricted. Contact the admin to request access."
3. **Given** the allowlist is empty (default opt-out), **When** any user sends a message, **Then** all users are refused until the admin adds at least one entry
4. **Given** a non-allowlisted user attempts to trigger a `/spec` command, **When** the message is received, **Then** it is rejected at the gateway layer before reaching the agent loop

---

### User Story 3 - Stream Markdown, Code Blocks, and Citations (Priority: P2)

A user asks hermes-lite to explain a concept or summarize a paper. The adapter streams the response back to Open WebUI with properly formatted markdown, fenced code blocks with language tags, and citation references (e.g., `arXiv:2501.12345`).

**Why this priority**: Open WebUI renders markdown, code blocks, and citations with special styling. Proper formatting makes the agent output readable and professional in the browser.

**Independent Test**: Can be fully tested by asking for a code example and an arXiv citation, then verifying the rendered HTML in Open WebUI.

**Acceptance Scenarios**:

1. **Given** the agent produces a response containing a Python code snippet, **When** it streams through the Open WebUI adapter, **Then** the code is wrapped in triple-backtick fences with language tag `python`
2. **Given** the agent references `arXiv:2501.12345`, **When** the response streams, **Then** the citation is formatted as a markdown link pointing to the local knowledge repo or the arXiv URL
3. **Given** the agent produces a comparison table, **When** the response streams, **Then** the table uses markdown pipe syntax and renders correctly in Open WebUI
4. **Given** the response contains reasoning steps, **When** the adapter processes it, **Then** reasoning content is either collapsed into a `<details>` block or stripped, per user config, and never mixed with the final answer

---

### User Story 4 - Cross-Gateway Session Visibility (Priority: P2)

A user starts a conversation in Open WebUI, then switches to the TUI and asks to see the same session history. Because both gateways use the same `state.db`, the TUI lists the session and the user can continue the conversation.

**Why this priority**: Cross-gateway visibility is a core value of hermes-lite. The user must not lose context when switching surfaces.

**Independent Test**: Can be fully tested by creating a session in Open WebUI, opening the TUI, and verifying the session appears in the TUI session list with the same messages.

**Acceptance Scenarios**:

1. **Given** a session was created via Open WebUI, **When** the TUI session list is queried, **Then** the session appears with metadata indicating it originated from `openwebui`
2. **Given** the user continues the session in the TUI, **When** a new message is sent, **Then** the response is stored in `state.db` and will appear if the user returns to Open WebUI
3. **Given** the user asks for session search in Open WebUI, **When** FTS5 recall runs, **Then** it searches across sessions from all gateways (TUI, Discord, Open WebUI)
4. **Given** the curator runs a background review pass, **When** it processes the session, **Then** it sees the full conversation regardless of which gateway messages originated from

---

### Edge Cases

- What happens when Open WebUI sends a conversation ID that is already mapped but the session was deleted? The adapter must detect the stale mapping, create a new session, and overwrite the mapping in `state.db`.
- How does the adapter handle a very long response that exceeds Open WebUI's message length limit? It must chunk the response into multiple messages or truncate gracefully with a "continued..." indicator.
- What happens when the Open WebUI pipeline receives a tool-call result containing a file path? The adapter must redact absolute paths (via `agent/redact.py`) before streaming the result to the browser.
- How does the adapter handle a streaming error mid-response? It must send a partial message to the user indicating the error, close the stream cleanly, and log the failure to `logs/agent.jsonl`.
- What happens when the user sends a message while the agent is still processing the previous one? The adapter must queue the message or return a "busy" indicator, never interleaving two agent loops for the same session.
- How does the adapter handle a message containing markdown that could break Open WebUI's rendering? It must sanitize or escape raw HTML, unclosed backticks, and malformed table syntax before streaming.
- What happens when the Open WebUI instance is served over HTTP (not HTTPS)? The adapter must issue a warning in the admin logs but still function; it does not enforce TLS at the pipeline layer.
- How does the adapter handle a user whose allowlist status changes mid-conversation? The check is performed on every message intake; if a user is removed from the allowlist, subsequent messages are refused.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The adapter MUST register as an Open WebUI pipeline named "Hermes-Lite" under `gateway/platforms/openwebui/`
- **FR-002**: The adapter MUST accept Open WebUI conversation payloads and route them into the hermes agent loop via the same `AIAgent.chat()` / `run_conversation()` interface used by Discord and TUI
- **FR-003**: The adapter MUST map each Open WebUI conversation ID to a hermes session ID and persist the mapping in `state.db`
- **FR-004**: The adapter MUST reuse an existing session when a known conversation ID is received
- **FR-005**: The adapter MUST enforce a user allowlist; non-allowlisted users MUST receive a polite refusal and MUST NOT reach the agent loop
- **FR-006**: The allowlist MUST be configurable in `lite-config.yaml` or a dedicated allowlist file
- **FR-007**: The adapter MUST stream responses to Open WebUI as markdown with proper fenced code blocks (triple backticks + language tag)
- **FR-008**: The adapter MUST format citation references (especially arXiv IDs) as markdown links
- **FR-009**: The adapter MUST format markdown tables using pipe syntax compatible with Open WebUI rendering
- **FR-010**: Reasoning content MUST be either collapsed into a `<details>` block or stripped, per user config, and never mixed with the final answer
- **FR-011**: The adapter MUST redact absolute file paths and secrets (via `agent/redact.py`) before streaming tool results to the browser
- **FR-012**: The adapter MUST handle concurrent messages per session by queuing or returning a busy indicator; it MUST NOT interleave agent loops
- **FR-013**: The adapter MUST sanitize raw HTML, unclosed backticks, and malformed table syntax before streaming to Open WebUI
- **FR-014**: The adapter MUST log all intake, mapping, and streaming events to `logs/agent.jsonl`
- **FR-015**: The adapter MUST support the same slash commands (`/arxiv`, `/spec`, `/sec`, etc.) as Discord and TUI
- **FR-016**: The adapter MUST converge on the same `state.db`, memory profiles, and kits as all other gateways

### Key Entities

- **OpenWebUIAdapter**: The pipeline adapter class under `gateway/platforms/openwebui/` implementing intake, session mapping, allowlist checks, and response streaming.
- **ConversationMapping**: The persistent mapping between an Open WebUI conversation ID and a hermes session ID stored in `state.db`.
- **UserAllowlist**: The configurable list of allowed Open WebUI users who may interact with the agent.
- **PipelineStream**: The streaming response formatter that converts agent output into Open WebUI-compatible markdown chunks.
- **OpenWebUISessionContext**: The session context object passed to the agent loop, including the Open WebUI user, conversation ID, and gateway origin.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The adapter registers successfully as an Open WebUI pipeline and appears in the pipeline list
- **SC-002**: Conversation ID mapping is created on first message and reused on subsequent messages within 500 ms
- **SC-003**: A non-allowlisted user is refused within 200 ms without reaching the agent loop
- **SC-004**: A code block in the agent response is streamed with correct triple-backtick fences and language tag in 100% of test cases
- **SC-005**: An arXiv citation is formatted as a markdown link in 100% of test cases
- **SC-006**: A session created in Open WebUI appears in the TUI session list within 2 seconds of `state.db` write
- **SC-007**: The adapter handles a 10,000-token response without truncation or rendering errors
- **SC-008**: Concurrent messages to the same session are queued rather than interleaved, verified by sending two rapid messages
- **SC-009**: Raw HTML and unclosed backticks are sanitized before reaching Open WebUI, verified by malicious input tests
- **SC-010**: The adapter completes a full chat-turn (intake → agent loop → stream) in under 5 seconds for a simple greeting on the Jetson 25 W mode

## Assumptions

- Open WebUI is installed and accessible on the target host (VM or local); the pipeline integration uses Open WebUI's standard pipeline/function hook interface
- The Open WebUI instance may be served over HTTP or HTTPS; TLS enforcement is outside the adapter's scope
- `state.db` is the canonical session store and is writable by the hermes-lite process
- The user allowlist is maintained by the admin; an empty allowlist defaults to deny-all
- The adapter uses the same `AIAgent` instance and tool surface as Discord and TUI; kit loading and memory profiles are gateway-agnostic
- Open WebUI's rendering pipeline supports standard markdown (CommonMark or GitHub-flavored); exotic extensions are not required
- The adapter does not implement voice, image, or video streaming; text and markdown are the supported content types
- Agent responses may be long; the adapter chunks or streams them according to Open WebUI's expected payload shape
- The same `agent/redact.py` layer used by Discord and TUI is applied to Open WebUI output
- If Open WebUI is unreachable, the adapter fails gracefully and logs the error without crashing the hermes-lite process
