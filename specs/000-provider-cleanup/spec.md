# Feature Specification: Non-Allowlisted LM Provider Cleanup

**Feature Branch**: `000-provider-cleanup`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Remove non-allowlisted LM providers and media-generation providers from the agent surface to shrink the dependency tree, reduce prompt noise, and eliminate dead code paths on the cyberdeck."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Non-Allowlisted Provider Modules (Priority: P1)

Hermes-lite must delete all provider adapter modules, transport layers, and schema files that correspond to non-allowlisted LM providers, so the codebase contains only Ollama (new adapter), OpenAI, GitHub Copilot, and Claude (Anthropic).

**Why this priority**: This is the foundational cleanup step. Every other provider refactor depends on these files being removed first so import chains do not resurrect deleted surfaces.

**Independent Test**: Can be fully tested by running `python -c "import agent"` after deletion and confirming no ImportError from missing provider modules.

**Acceptance Scenarios**:

1. **Given** the agent tree contains `agent/azure_identity_adapter.py`, **When** the cleanup is applied, **Then** the file is deleted and no other module imports it
2. **Given** the agent tree contains `agent/bedrock_adapter.py`, **When** the cleanup is applied, **Then** the file is deleted and no other module imports it
3. **Given** the agent tree contains `agent/gemini_native_adapter.py`, `agent/gemini_cloudcode_adapter.py`, `agent/gemini_schema.py`, `agent/google_code_assist.py`, and `agent/google_oauth.py`, **When** the cleanup is applied, **Then** all five files are deleted and no other module imports them
4. **Given** the agent tree contains `agent/codex_runtime.py` and `agent/codex_responses_adapter.py`, **When** the cleanup is applied, **Then** both files are deleted and no other module imports them
5. **Given** the agent tree contains `agent/moonshot_schema.py`, **When** the cleanup is applied, **Then** the file is deleted and no other module imports it
6. **Given** the agent tree contains `agent/models_dev.py` and `agent/portal_tags.py`, **When** the cleanup is applied, **Then** both files are deleted and no other module imports them
7. **Given** the agent tree contains `agent/auxiliary_client.py`, **When** the cleanup is applied, **Then** the file is deleted and replaced with a single-provider helper pattern
8. **Given** `agent/credential_sources.py` contains xAI / Grok OAuth paths, **When** the cleanup is applied, **Then** those code paths are removed

---

### User Story 2 - Remove Image and Video Generation Providers (Priority: P2)

Hermes-lite must delete all image-generation and video-generation provider modules, registries, and routing code because the cyberdeck fork does not support media generation.

**Why this priority**: Media generation is out of scope for a text-first, offline-capable cyberdeck. Removing these modules eliminates large optional dependencies and reduces the tool-discovery surface exposed to small models.

**Independent Test**: Can be fully tested by verifying `plugins/image_gen/`, `plugins/video_gen/`, and the matching `agent/image_gen_*.py` and `agent/video_gen_*.py` files no longer exist and their registries no longer appear in `model_tools.py` or `toolsets.py`.

**Acceptance Scenarios**:

1. **Given** the repo contains `agent/image_gen_provider.py`, `agent/image_gen_registry.py`, and `agent/image_routing.py`, **When** the cleanup is applied, **Then** all three files are deleted
2. **Given** the repo contains `agent/video_gen_provider.py` and `agent/video_gen_registry.py`, **When** the cleanup is applied, **Then** both files are deleted
3. **Given** the repo contains `plugins/image_gen/` and `plugins/video_gen/`, **When** the cleanup is applied, **Then** both directories are deleted
4. **Given** any skill or tool imports an image-gen or video-gen registry, **When** the cleanup is applied, **Then** that import is removed and the skill still loads without error

---

### User Story 3 - Update Provider Routing and Credential Pool (Priority: P3)

Hermes-lite must update the provider routing tables, credential pool, and any factory methods so that only the four allowlisted providers (Ollama, OpenAI, Copilot, Claude) are resolvable at runtime.

**Why this priority**: Deleting files is not enough if dynamic provider resolution or the credential pool still references them. This story ensures the runtime fails closed when a stray config references a removed provider.

**Independent Test**: Can be fully tested by starting the agent with a legacy config that references a removed provider and observing a clear `ConfigurationError` at startup.

**Acceptance Scenarios**:

1. **Given** the credential pool enumerates providers, **When** the cleanup is applied, **Then** the enumeration contains only `ollama`, `openai`, `copilot`, and `claude`
2. **Given** a user config references `bedrock` or `gemini` as a provider, **When** the agent loads the config, **Then** it raises a clear error naming the disallowed provider
3. **Given** the transport layer factory maps provider names to adapter classes, **When** the cleanup is applied, **Then** the factory only maps the four allowlisted names
4. **Given** the agent runs a `hermes-lite doctor` check, **When** it inspects provider health, **Then** it only probes Ollama, OpenAI, Copilot, and Claude endpoints

---

### User Story 4 - Retain and Verify Allowlisted Provider Modules (Priority: P4)

Hermes-lite must keep the four allowlisted provider modules intact and verify they still pass existing tests after the cleanup.

**Why this priority**: This is a regression-prevention story. Deleting files risks breaking import chains that the retained modules share (e.g., common transport base classes, retry utilities, or stream diagnostics).

**Independent Test**: Can be fully tested by running the provider-specific unit tests for OpenAI, Copilot, and Claude adapters, and by smoke-testing Ollama connectivity after the new adapter lands.

**Acceptance Scenarios**:

1. **Given** `agent/chat_completion_helpers.py` is an OpenAI-compatible helper, **When** the cleanup is applied, **Then** the file is retained and its tests still pass
2. **Given** `agent/copilot_acp_client.py`, `acp_adapter/`, and `acp_registry/` are Copilot modules, **When** the cleanup is applied, **Then** all are retained and their tests still pass
3. **Given** `agent/anthropic_adapter.py` is the Claude module, **When** the cleanup is applied, **Then** the file is retained and its tests still pass
4. **Given** `agent/lmstudio_reasoning.py` exists, **When** the cleanup is applied, **Then** it is retained until `agent/ollama_adapter.py` (spec 002) replaces it

---

### Edge Cases

- What happens when a third-party plugin or skill imports a removed provider module by dynamic name? The cleanup must include a ``plugins/`` audit to strip such imports.
- What happens when ``agent/credential_sources.py`` still has xAI-specific OAuth refresh logic buried inside a shared credential refresh loop? The cleanup must excise those branches without breaking the shared loop for OpenAI and Claude.
- How does the system handle a ``state.db`` from upstream Hermes that contains session records referencing removed providers? The cleanup must be code-only; historical session data is left intact and simply renders a "provider unavailable" note if recalled.
- What happens when ``agent/tool_surface.py`` (new in spec 002) validates tool schemas and finds a tool that internally imports a removed provider? The tool must be refused at load time with a descriptive error.
- What happens when a skill bundle references ``models_dev.py`` for model metadata? The skill must be updated to source metadata from a slimmed ``agent/model_metadata.py`` or from the Ollama adapter's model probing endpoint.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST delete `agent/azure_identity_adapter.py` and all references to Azure Foundry / Entra ID provider logic
- **FR-002**: System MUST delete `agent/bedrock_adapter.py` and all references to AWS Bedrock provider logic
- **FR-003**: System MUST delete `agent/gemini_native_adapter.py`, `agent/gemini_cloudcode_adapter.py`, `agent/gemini_schema.py`, `agent/google_code_assist.py`, and `agent/google_oauth.py` and all references to Gemini Native / CloudCode provider logic
- **FR-004**: System MUST delete `agent/codex_runtime.py` and `agent/codex_responses_adapter.py` and all references to Codex runtime provider logic
- **FR-005**: System MUST delete `agent/moonshot_schema.py` and all references to Moonshot / Kimi provider logic
- **FR-006**: System MUST delete `agent/models_dev.py` and `agent/portal_tags.py` and all references to MiniMax, HuggingFace, NovitaAI, NVIDIA NIM, MiMo, OpenRouter, z.ai/GLM, and Nous Portal model picker logic
- **FR-007**: System MUST delete `agent/auxiliary_client.py` and replace any dependent caller with a single-provider helper pattern
- **FR-008**: System MUST remove xAI / Grok OAuth branches from `agent/credential_sources.py`
- **FR-009**: System MUST delete `agent/image_gen_provider.py`, `agent/image_gen_registry.py`, `agent/image_routing.py`, `agent/video_gen_provider.py`, `agent/video_gen_registry.py`, and the directories `plugins/image_gen/` and `plugins/video_gen/`
- **FR-010**: System MUST update provider enumeration, credential pool, transport factory, and ``hermes-lite doctor`` to only recognize Ollama, OpenAI, Copilot, and Claude
- **FR-011**: System MUST raise a clear ``ConfigurationError`` at startup when any config references a removed provider
- **FR-012**: System MUST retain `agent/chat_completion_helpers.py`, `agent/copilot_acp_client.py`, `acp_adapter/`, `acp_registry/`, `agent/anthropic_adapter.py`, and `agent/lmstudio_reasoning.py` until it is replaced by `agent/ollama_adapter.py`

### Key Entities

- **RemovedProviderSet**: The canonical list of disallowed provider names (azure_foundry, bedrock, gemini, codex, xai, moonshot, minimax, huggingface, novitaai, nvidia_nim, mimo, openrouter, zai_glm, nous_portal, auxiliary)
- **ProviderRegistry**: The runtime mapping of provider names to adapter classes; post-cleanup it contains exactly four entries
- **CredentialPool**: The runtime pool of API credentials; post-cleanup it only holds credentials for the four allowlisted providers

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `find agent/ -name "*azure_identity*" -o -name "*bedrock*" -o -name "*gemini*" -o -name "*codex*" -o -name "*moonshot*" -o -name "*models_dev*" -o -name "*portal_tags*" -o -name "*auxiliary_client*"` returns zero files after the cleanup
- **SC-002**: `find plugins/ -type d \( -name "image_gen" -o -name "video_gen" \)` returns zero directories after the cleanup
- **SC-003**: The agent startup smoke test (`python -c "from agent import *; load_providers()"`) completes without ImportError in under 5 seconds
- **SC-004**: A config file referencing a removed provider causes the agent to exit with a clear error message within 2 seconds of config load
- **SC-005**: Existing unit tests for OpenAI, Copilot, and Claude adapters still pass after the cleanup (zero regression)
- **SC-006**: The `agent/` directory contains at most 55 Python files after cleanup (down from 100+), establishing a measurable shrink target

## Assumptions

- The four allowlisted provider modules (OpenAI, Copilot, Claude, and the future Ollama adapter) do not dynamically import any of the removed modules at runtime
- Upstream Hermes' common transport base classes (`agent/transports/base.py`, `agent/transports/chat_completions.py`, `agent/transports/anthropic.py`) are retained and are sufficient for the allowlisted providers
- The `agent/model_metadata.py` module can absorb any model-metadata lookup still needed by skills that previously relied on `models_dev.py`
- No third-party plugins outside the repo need to keep referencing removed providers; any such plugins will be patched or dropped in parallel
- The cleanup is a one-way code deletion; restoring a removed provider later would require reverting Git commits, not a runtime toggle
- `agent/stream_diag.py` and `agent/retry_utils.py` remain shared infrastructure and are not affected by provider-specific deletions
