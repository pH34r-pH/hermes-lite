# Feature Specification: Ollama Adapter

**Feature Branch**: `002-ollama-adapter`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Create a tight Ollama adapter `agent/ollama_adapter.py` that speaks `/api/chat` and `/api/generate` directly, supports function-calling via JSON-schema prompts pre-validated against the active toolset, exposes a token-budget estimator using tiktoken heuristics for small models, and streams reasoning plus tool-call deltas through the existing `agent/stream_diag.py` plumbing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Direct Ollama Chat and Generate Endpoints (Priority: P1)

Hermes-lite must implement an adapter that sends requests directly to Ollama's `/api/chat` and `/api/generate` endpoints, replacing the upstream LM Studio reasoning module as the default local provider.

**Why this priority**: The Ollama adapter is the primary inference backend for the cyberdeck. Without it, the device cannot run the default `ministral-3:3b` model offline, breaking the offline-first premise.

**Independent Test**: Can be fully tested by starting Ollama locally with `ministral-3:3b` loaded, initializing the adapter, sending a simple chat message, and receiving a non-empty response within 10 seconds.

**Acceptance Scenarios**:

1. **Given** Ollama is running at `http://127.0.0.1:11434` with `ministral-3:3b` available, **When** the adapter receives a chat request with a system prompt and user message, **Then** it posts to `/api/chat` and returns the assistant's text response
2. **Given** Ollama is running, **When** the adapter receives a generate request with a raw prompt string, **Then** it posts to `/api/generate` and returns the generated text
3. **Given** the adapter is configured with `base_url` pointing to a remote Ollama instance (e.g. the partner VM), **When** a chat request is issued, **Then** the adapter targets the remote `/api/chat` endpoint correctly
4. **Given** the model is unavailable in Ollama, **When** the adapter attempts a request, **Then** it surfaces a clear error describing the missing model and suggests `ollama pull`

---

### User Story 2 - Function-Calling via JSON-Schema Prompts (Priority: P2)

The Ollama adapter must support tool use by injecting JSON-schema descriptions of the active toolset into the prompt, pre-validating those schemas, and parsing the model's structured tool-call output back into Hermes' standard tool-call message format.

**Why this priority**: Small models like Ministral-3 3B require explicit JSON-schema guidance to emit valid tool calls. The adapter must bridge Ollama's native format with Hermes' tool-execution loop.

**Independent Test**: Can be fully tested by loading a single-kit tool surface (e.g. arXiv kit), sending a user message that should trigger a tool call, and verifying the adapter returns a valid `tool_calls` list that `agent/tool_executor.py` can dispatch.

**Acceptance Scenarios**:

1. **Given** the active kit exposes three tools with JSON schemas, **When** the adapter builds the prompt, **Then** it injects the schemas into the system or user prompt in a stable, cache-friendly format
2. **Given** a tool schema is invalid (e.g. missing required fields), **When** the adapter pre-validates the active toolset, **Then** it rejects the invalid schema at prompt-build time with a descriptive error
3. **Given** the model responds with a JSON object matching a tool schema, **When** the adapter parses the response, **Then** it converts the JSON into an OpenAI-compatible `tool_calls` entry with `name` and `arguments` fields
4. **Given** the model responds with text that is not a valid tool call, **When** the adapter parses the response, **Then** it returns a plain assistant message without tool calls and the conversation loop continues normally
5. **Given** the model emits a partial or malformed JSON tool call, **When** the adapter parses the response, **Then** it surfaces a parse error as a tool-result failure so the loop can retry or escalate

---

### User Story 3 - Token-Budget Estimator for Small Models (Priority: P3)

The Ollama adapter must expose a token-budget estimator that computes the approximate token count of the outgoing prompt using `tiktoken` heuristics, compares it against the model's declared context limit, and reports remaining headroom to the iteration budget tracker.

**Why this priority**: A 3B model on an 8 GB device has no margin for context overflow. The estimator prevents requests that would silently truncate mid-prompt, which is catastrophic for tool-call fidelity.

**Independent Test**: Can be fully tested by constructing a prompt of known token length, calling the estimator, and verifying the reported count is within 10 percent of `tiktoken`'s count for the same text.

**Acceptance Scenarios**:

1. **Given** a prompt containing 500 tokens of text, **When** the estimator runs, **Then** it returns a count between 450 and 550 tokens
2. **Given** the model's context window is 32k tokens and the prompt is 30k tokens, **When** the estimator runs, **Then** it reports only 2k tokens of remaining headroom and emits a warning
3. **Given** the prompt includes JSON-schema tool descriptions, **When** the estimator runs, **Then** it counts the schema text as part of the prompt budget
4. **Given** the estimated token count exceeds a configurable threshold (default 80 percent of context window), **When** the adapter sends the request, **Then** it triggers `agent/context_compressor.py` before posting to Ollama
5. **Given** `tiktoken` is not installed, **When** the estimator runs, **Then** it falls back to a character-based heuristic and logs a one-time warning

---

### User Story 4 - Streaming Through Stream Diagnostics (Priority: P4)

The Ollama adapter must stream reasoning content and tool-call deltas through Hermes' existing `agent/stream_diag.py` plumbing so that the TUI spinner, Discord typing indicator, and Open WebUI progress bar all receive real-time token events.

**Why this priority**: Streaming is the user-experience standard for chat interfaces. Reusing `stream_diag.py` ensures consistent behavior across all three surfaces without duplicating streaming logic in the adapter.

**Independent Test**: Can be fully tested by initiating a chat request, observing that tokens arrive incrementally in the TUI or Discord, and verifying the final assembled message matches the non-streaming response.

**Acceptance Scenarios**:

1. **Given** a chat request with streaming enabled, **When** Ollama returns tokens one at a time, **Then** the adapter yields each token through `stream_diag.py` within 50 milliseconds of receipt
2. **Given** the model emits a reasoning preamble (e.g. `<think>`...`</think>`), **When** the adapter streams the response, **Then** reasoning tokens are routed through the reasoning channel and final answer tokens through the answer channel
3. **Given** the model emits a tool-call delta mid-stream, **When** the adapter processes the stream, **Then** it buffers the delta until the JSON object is complete, then yields a structured tool-call event
4. **Given** the stream is interrupted by a network error, **When** the adapter detects the disconnect, **Then** it yields a terminal error event through `stream_diag.py` and the conversation loop handles it via `agent/retry_utils.py`
5. **Given** streaming is disabled (e.g. by user config), **When** the adapter sends the request, **Then** it waits for the full response and returns it as a single message without invoking the streaming path

---

### Edge Cases

- What happens when Ollama returns an NDJSON stream line that is not valid JSON? The adapter must skip the line, log a debug warning, and continue streaming rather than crashing the entire session.
- What happens when the model generates a tool call for a tool name that does not exist in the active toolset? The adapter must validate the tool name against the allowlist before yielding the tool-call event; invalid names are treated as parse failures.
- What happens when the prompt exceeds Ollama's context window and Ollama silently truncates? The adapter must rely on the token-budget estimator to pre-empt truncation; if truncation still occurs, the model's response often degenerates into repetitions, which the adapter should detect and surface as a budget-exceeded error.
- What happens when `ollama serve` is bound to a UNIX socket instead of TCP? The adapter must accept a `base_url` like `http+unix:///path/to/socket` and route requests accordingly, or document TCP as the required transport.
- What happens when the Jetson switches power modes (e.g. from 25 W to 7 W idle) mid-request? The adapter is stateless per request; any timeout increase due to lower clocks is handled by Ollama's own queue, not the adapter.
- What happens when the partner small model on the remote VM uses the same adapter code but a different model tag? The adapter must be model-agnostic; the model tag is passed as a parameter, and the adapter probes `/api/tags` to verify availability.
- What happens when Ollama's `/api/chat` response includes an empty `message.content` but a populated `message.tool_calls` field? The adapter must correctly prioritize tool calls over empty content and not emit a spurious blank assistant message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create `agent/ollama_adapter.py` as the canonical Ollama provider adapter
- **FR-002**: The adapter MUST support Ollama's `/api/chat` endpoint for conversational requests
- **FR-003**: The adapter MUST support Ollama's `/api/generate` endpoint for raw prompt requests
- **FR-004**: The adapter MUST accept a configurable `base_url` (default `http://127.0.0.1:11434`) to support both local Jetson Ollama and remote partner VM Ollama
- **FR-005**: The adapter MUST accept a configurable `model` parameter and verify model availability via Ollama's `/api/tags` endpoint before the first request
- **FR-006**: The adapter MUST inject JSON-schema descriptions of the active toolset into prompts for function-calling support
- **FR-007**: The adapter MUST pre-validate every injected tool schema against the active toolset; invalid schemas must raise at prompt-build time
- **FR-008**: The adapter MUST parse the model's structured output back into OpenAI-compatible `tool_calls` messages with `name` and `arguments` fields
- **FR-009**: The adapter MUST expose `estimate_token_budget(prompt: str, tools: list) -> dict` using `tiktoken` heuristics when available, falling back to character-based heuristics otherwise
- **FR-010**: The estimator MUST compare the prompt token count against the model's declared context limit and report remaining headroom
- **FR-011**: The adapter MUST trigger `agent/context_compressor.py` when the estimated token count exceeds 80 percent of the context window
- **FR-012**: The adapter MUST stream response tokens through `agent/stream_diag.py` when streaming is enabled
- **FR-013**: The adapter MUST separate reasoning tokens from answer tokens during streaming when the model emits reasoning delimiters
- **FR-014**: The adapter MUST yield structured tool-call events only after the complete JSON object has been buffered and validated
- **FR-015**: The adapter MUST handle network errors, empty responses, and malformed NDJSON lines gracefully without crashing the conversation loop
- **FR-016**: The adapter MUST be model-agnostic; swapping from `ministral-3:3b` to another Ollama model is a config change, not a code change
- **FR-017**: System MUST delete `agent/lmstudio_reasoning.py` after `agent/ollama_adapter.py` is integrated and all callers are migrated

### Key Entities

- **OllamaAdapter**: The provider adapter class that encapsulates `/api/chat`, `/api/generate`, streaming, token estimation, and tool-call parsing
- **OllamaRequest**: The normalized request payload sent to Ollama containing messages, model tag, stream flag, and options
- **OllamaResponse**: The normalized response payload containing assistant text, reasoning text, and optional tool calls
- **TokenBudget**: The estimator output containing `prompt_tokens`, `max_tokens`, `remaining_tokens`, and a `warning` flag
- **ToolSchemaInjector**: The logic that serializes the active kit's tool schemas into a prompt section

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The adapter successfully completes a non-streaming chat request to local Ollama with `ministral-3:3b` and returns a response of at least 10 tokens in under 10 seconds
- **SC-002**: The adapter successfully completes a streaming chat request and yields the first token within 2 seconds of the HTTP request being sent
- **SC-003**: A tool-call prompt containing three JSON schemas is pre-validated and the adapter returns a valid `tool_calls` entry when the model emits matching JSON, with parsing accuracy at or above 95 percent in a 20-request test suite
- **SC-004**: The token-budget estimator's output is within 10 percent of `tiktoken` for English text prompts between 100 and 10 000 tokens
- **SC-005**: When the estimated prompt size exceeds 80 percent of context window, the adapter invokes `agent/context_compressor.py` before posting and the resulting prompt fits within the window
- **SC-006**: A streaming session interrupted by a simulated network dropout yields a terminal error event through `stream_diag.py` within 1 second of disconnect
- **SC-007**: After `agent/ollama_adapter.py` is integrated, `agent/lmstudio_reasoning.py` is deleted and the agent's unit-test suite still passes with zero provider-related regressions

## Assumptions

- Ollama is already installed on the Jetson and accessible at `http://127.0.0.1:11434`; the adapter does not manage Ollama installation or model pulling
- The Ollama API is stable at the `/api/chat` and `/api/generate` paths as documented in the Ollama REST API reference
- `agent/stream_diag.py` is retained verbatim and its streaming callback interface is sufficient for NDJSON token events
- `tiktoken` is optionally available in the virtual environment; its absence is handled gracefully
- The model supports tool use via JSON-schema prompting in the prompt text; the adapter does not rely on Ollama-native tool-calling extensions that may not be available for all models
- The adapter runs in the same process as the agent loop; multi-process or RPC adapter patterns are out of scope
- `agent/retry_utils.py` handles transient HTTP errors (connection refused, timeout) so the adapter does not need its own retry layer
- The context window size is obtained from a config knob (default 32768 for Ministral-3 3B) rather than dynamically probing the model, because Ollama's model info endpoint does not always expose context length reliably
