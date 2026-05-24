# Tasks: Azure / Web Ops Skill Bundles

**Input**: Design documents from `/specs/008-azure-ops-bundle/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as specified in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Directory structures, module scaffolds, schema files, and upstream integration points

- [x] T001 Create `skills/devops/azure-ops/` directory tree: `az-login-status/`, `az-account-show/`, `az-resource-list/`, `az-swa-show/`, `az-swa-config-update/`, `az-swa-deploy/`, `az-vm-status/`, `az-vm-run-command/`, `bicep-validate/`, `bicep-deploy/`, `keyvault-secret-show/`, `lib/`
- [x] T002 Create `skills/software-development/web-frontend/` directory tree: `staticwebapp-config-validate/`, `staticwebapp-config-edit/`, `frontend-preview/`, `frontend-smoke-check/`, `lib/`, `schemas/`
- [x] T003 Create `skills/devops/linux-vm-api/` directory tree: `systemd-status/`, `systemd-restart/`, `reverse-proxy-edit/`, `reverse-proxy-validate/`, `apikey-rotate/`, `journalctl-read/`, `mcp-validate/`, `partner-model-health/`, `lib/`, `schemas/`
- [x] T004 [P] Create bundle manifests:
  - `skills/devops/azure-ops/manifest.yaml` — `/azure` slash command
  - `skills/software-development/web-frontend/manifest.yaml` — `/web` slash command
  - `skills/devops/linux-vm-api/manifest.yaml` — `/vm` slash command
- [ ] T005 Verify `agent/tool_surface.py` (spec 003) kit allowlist infrastructure exists; document three kit registration points
- [ ] T006 Verify `plugins/local_repo_workspace/` (spec 010) is available for commits to `azure-api` workspace
- [ ] T007 Verify `plugins/memory/` (spec 013) exposes `azure`, `web`, `infra`, and `api` memory profiles; document profile bindings
- [x] T008 [P] Add `lib/__init__.py` scaffolds for all three bundles with module docstrings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Python support modules and schemas that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Implement `AzCliWrapper` in `skills/devops/azure-ops/lib/az_cli_wrapper.py`
  - Subprocess runner for `az` commands with timeout (default 60 s, deploy 180 s)
  - Capture stdout/stderr, parse JSON output, surface Azure error codes
  - Environment scrubbing: clean PATH, no AZURE_* secrets in env
  - Handle `az login` required state with clear diagnostic message
- [x] T010 Implement `VmAllowlist` in `skills/devops/azure-ops/lib/vm_allowlist.py`
  - Load per-VM command allowlist from `infra` memory profile
  - Match command against allowlist patterns; refuse and log at `WARNING` on mismatch
  - Support glob patterns and exact-match entries
- [x] T011 Implement `BicepHelper` in `skills/devops/azure-ops/lib/bicep_helper.py`
  - Validate Bicep modules via `az bicep build` or `bicep build`
  - Report errors with file path and line number
  - Deploy via `az deployment group create` with what-if support
- [x] T012 Create `skills/software-development/web-frontend/schemas/staticwebapp.config.schema.json`
  - Cover `route`, `methods`, `rewrite`, `redirect`, `headers`, `navigationFallback`, `responseOverrides`, `mimeTypes`, `globalHeaders`
  - Report errors with JSON path and expected type
- [x] T013 Implement `FrameworkDetector` in `skills/software-development/web-frontend/lib/framework_detector.py`
  - Detect Astro (`astro.config.mjs`), Next.js (`next.config.js`), SvelteKit (`svelte.config.js`), or static HTML
  - Emit warning and ask user to confirm on framework mismatch
- [x] T014 Implement `SwaConfigValidator` in `skills/software-development/web-frontend/lib/swa_config_validator.py`
  - Validate `staticwebapp.config.json` against schema
  - Safe edit preserving schema validity (jsonschema + round-trip json parsing)
  - Detect missing rewrite/redirect target files in build output
- [x] T015 Implement `SystemdClient` in `skills/devops/linux-vm-api/lib/systemd_client.py`
  - Wrapper for `systemctl` commands via ssh or `az-vm-run-command`
  - Status query: `systemctl is-active`, `systemctl show`
  - Restart: `systemctl restart` (confirmation-gated at skill level)
  - Read last 50 lines of `journalctl` on failed start for diagnostics
- [x] T016 Implement `ProxyConfigEditor` in `skills/devops/linux-vm-api/lib/proxy_config_editor.py`
  - Safe editing for `caddy` (`Caddyfile`) or `nginx` (`nginx.conf` / `sites-available/`)
  - Parse `/v1/partner/*` route family and `/v1/*` API route
  - Validate syntax before applying (`caddy validate` or `nginx -t`)
- [x] T017 Implement `PartnerProvider` in `skills/devops/linux-vm-api/lib/partner_provider.py`
  - Register partner model (`/v1/partner/chat/completions`, `/v1/partner/embeddings`) as remote LM provider
  - Use existing OpenAI-compatible adapter
  - Place partner model in escalation chain after local Ollama, before paid providers
  - Test prompt health check with schema validation
- [x] T018 [P] Create root SKILL.md files for all three bundles documenting the domain scope and skill inventory

**Checkpoint**: Foundation ready — Azure CLI wrapper, VM allowlist, Bicep helper, SWA schema, framework detector, systemd client, proxy editor, and partner provider exist; user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Inspect Azure Resources and SWA Configuration (Priority: P1) 🎯 MVP

**Goal**: Safest operational surface — read-only Azure inspection without mutation risk

**Independent Test**: Run read-only skills against a sandbox subscription and verify no write operations are attempted

### Tests for User Story 1

- [ ] T019 [P] [US1] Unit test: `AzCliWrapper` parses `az account show` JSON correctly in `tests/unit/test_az_cli_wrapper.py`
- [ ] T020 [P] [US1] Unit test: `AzCliWrapper` returns diagnostic message when `az` is not authenticated in `tests/unit/test_az_cli_wrapper.py`
- [ ] T021 [P] [US1] Unit test: `az-resource-list` filters by resource group and returns ≤50 resources in under 10 s in `tests/unit/test_az_resource_list.py`
- [ ] T022 [P] [US1] Integration test: read-only skills against sandbox subscription produce zero write API calls in `tests/integration/test_azure_readonly.py`

### Implementation for User Story 1

- [x] T023 [US1] Write `skills/devops/azure-ops/az-login-status/SKILL.md`
  - Call `az account show` via `AzCliWrapper`
  - Return login state, subscription name, tenant ID, authenticated user
  - On not-authenticated: clear error suggesting `az login`
- [x] T024 [US1] Write `skills/devops/azure-ops/az-account-show/SKILL.md`
  - Return active account details: name, tenant, subscription ID
  - Handle unauthenticated gracefully
- [x] T025 [US1] Write `skills/devops/azure-ops/az-resource-list/SKILL.md`
  - Filter by bound subscription/resource group from `azure` memory profile
  - Return type, location, provisioning state for each resource
  - Cap at 50 resources; warn if more exist
- [x] T026 [US1] Write `skills/devops/azure-ops/az-swa-show/SKILL.md`
  - Return SWA name, default hostname, custom domains, current routing rules
  - Handle SWA not found gracefully
- [x] T027 [US1] Wire all four read-only skills into `skills/devops/azure-ops/SKILL.md`
- [ ] T028 [US1] Add `azure-ops` kit allowlist entry to `agent/tool_surface_allowlists.yaml` with read-only tools listed first

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Deploy the Static Web App Front-End (Priority: P1)

**Goal**: Boundary between "code exists" and "service is live" — deploy front-end to SWA

**Independent Test**: Run `az-swa-deploy` against a staging slot and verify the new build is active

### Tests for User Story 2

- [ ] T029 [P] [US2] Unit test: `az-swa-deploy` triggers GitHub Actions workflow via API when configured in `tests/unit/test_az_swa_deploy.py`
- [ ] T030 [P] [US2] Unit test: `az-swa-deploy` refuses upload without explicit user confirmation when `approval_mode` is `confirm` in `tests/unit/test_az_swa_deploy.py`
- [ ] T031 [P] [US2] Unit test: partial deploy (upload succeeds, activation fails) surfaces intermediate state in `tests/unit/test_az_swa_deploy.py`
- [ ] T032 [P] [US2] Integration test: deploy artifact under 50 MB completes upload and activation within 120 s in `tests/integration/test_swa_deploy.py`

### Implementation for User Story 2

- [x] T033 [US2] Write `skills/devops/azure-ops/az-swa-config-update/SKILL.md`
  - Edit SWA configuration: routes, auth providers, custom domains
  - Gate all mutations with explicit user confirmation
  - Use `AzCliWrapper` to call `az staticwebapp appsettings set` or equivalent
- [x] T034 [US2] Write `skills/devops/azure-ops/az-swa-deploy/SKILL.md`
  - Produce deploy artifact from `web/` build output
  - Upload via `swa deploy` CLI or trigger GitHub Actions workflow via API
  - Poll for completion status when using GitHub Actions
  - On failure: surface error logs and suggest next diagnostic step
  - On partial success: capture intermediate state, surface both aspects, suggest retry or rollback
  - Confirm mode: pause for explicit approval before any upload
- [x] T035 [US2] Wire `az-swa-config-update` and `az-swa-deploy` into `skills/devops/azure-ops/SKILL.md`
- [ ] T036 [US2] Integrate `LocalRepoWorkspace` for commits to `azure-api` repo when deploy is workflow-based

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Operate the Linux VM Back-End and Partner Model (Priority: P2)

**Goal**: Keep the VM-hosted proxy API and partner Ollama instance healthy

**Independent Test**: Run VM operational skills against the paired VM and verify systemd state changes and log retrieval

### Tests for User Story 3

- [ ] T037 [P] [US3] Unit test: `az-vm-run-command` refuses command not on per-VM allowlist and logs at WARNING in `tests/unit/test_vm_allowlist.py`
- [ ] T038 [P] [US3] Unit test: `systemd-status` reports states for both API proxy and partner Ollama units in `tests/unit/test_systemd_client.py`
- [ ] T039 [P] [US3] Unit test: `journalctl-read` returns exactly 100 lines without tailing in `tests/unit/test_systemd_client.py`
- [ ] T040 [P] [US3] Unit test: `partner-model-health` returns successful response schema match within 10 s in `tests/unit/test_partner_provider.py`
- [ ] T041 [P] [US3] Integration test: VM operational skills end-to-end against test VM in `tests/integration/test_vm_operations.py`

### Implementation for User Story 3

- [x] T042 [US3] Write `skills/devops/azure-ops/az-vm-status/SKILL.md`
  - Return VM power state, private IP, and API health endpoint badge
  - Use `AzCliWrapper` for VM state and `requests` for health endpoint
- [x] T043 [US3] Write `skills/devops/azure-ops/az-vm-run-command/SKILL.md`
  - Execute allowed commands via Azure Run Command API
  - Gate by `VmAllowlist`; refuse and log at `WARNING` if not allowed
  - Surface stdout/stderr to user
- [x] T044 [US3] Write `skills/devops/azure-ops/bicep-validate/SKILL.md`
  - Validate Bicep modules against Azure schema via `BicepHelper`
  - Report errors with file path and line
- [x] T045 [US3] Write `skills/devops/azure-ops/bicep-deploy/SKILL.md`
  - Deploy Bicep modules for SWA + VM topology
  - Gate with explicit user confirmation
- [x] T046 [US3] Write `skills/devops/azure-ops/keyvault-secret-show/SKILL.md`
  - Read-only secret resolution from Azure Key Vault
  - Never log secret values; redact in output and logs
  - Writes always require confirmation mode
- [x] T047 [US3] Write `skills/devops/linux-vm-api/systemd-status/SKILL.md`
  - Report state of API proxy systemd unit and partner Ollama systemd unit
  - Use `SystemdClient`
- [x] T048 [US3] Write `skills/devops/linux-vm-api/systemd-restart/SKILL.md`
  - Restart specified systemd unit on VM
  - Gate with user confirmation
  - On failure: read last 50 lines of `journalctl`, surface error, do not auto-restart
- [x] T049 [US3] Write `skills/devops/linux-vm-api/reverse-proxy-edit/SKILL.md`
  - Edit `caddy` or `nginx` configuration for API endpoint including `/v1/partner/*` route family
  - Use `ProxyConfigEditor`
- [x] T050 [US3] Write `skills/devops/linux-vm-api/reverse-proxy-validate/SKILL.md`
  - Validate proxy config syntax before applying changes
  - Call `caddy validate` or `nginx -t`
- [x] T051 [US3] Write `skills/devops/linux-vm-api/apikey-rotate/SKILL.md`
  - Rotate API keys via `keyvault-secret-show` and update systemd unit environment file
  - Never log new secrets
  - Gate with user confirmation
- [x] T052 [US3] Write `skills/devops/linux-vm-api/journalctl-read/SKILL.md`
  - Return bounded slice of logs (max 1000 lines) for specified unit
  - Prohibit interactive tailing
- [x] T053 [US3] Write `skills/devops/linux-vm-api/mcp-validate/SKILL.md`
  - Validate API's MCP surface against hermes-lite `mcp/` client skill
  - Report exact incompatibility if found
- [x] T054 [US3] Write `skills/devops/linux-vm-api/partner-model-health/SKILL.md`
  - Call `/v1/partner/chat/completions` with test prompt
  - Verify response matches OpenAI chat completions schema
  - On 502: diagnose reverse proxy, Ollama instance, or VM failure and surface most likely cause
- [x] T055 [US3] Wire all VM/api skills into `skills/devops/linux-vm-api/SKILL.md`
- [ ] T056 [US3] Add `linux-vm-api` kit allowlist entry to `agent/tool_surface_allowlists.yaml`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Validate Front-End Patterns and SWA Config Schema (Priority: P2)

**Goal**: Ensure the front-end is user-facing correct — valid config, framework-aware patterns, local preview, smoke checks

**Independent Test**: Introduce malformed `staticwebapp.config.json` and verify schema-validation rejects it; run Lighthouse check and verify scores are captured

### Tests for User Story 4

- [ ] T057 [P] [US4] Unit test: `staticwebapp-config-validate` rejects missing `route` field within 2 s in `tests/unit/test_swa_config_validator.py`
- [ ] T058 [P] [US4] Unit test: `staticwebapp-config-edit` preserves schema validity after route addition in `tests/unit/test_swa_config_validator.py`
- [ ] T059 [P] [US4] Unit test: `frontend-preview` binds to `localhost` only in `tests/unit/test_frontend_preview.py`
- [ ] T060 [P] [US4] Unit test: `frontend-smoke-check` returns performance, accessibility, and best-practice scores within 60 s in `tests/unit/test_frontend_smoke_check.py`
- [ ] T061 [P] [US4] Integration test: framework mismatch detection warns user in `tests/integration/test_web_frontend.py`

### Implementation for User Story 4

- [x] T062 [US4] Write `skills/software-development/web-frontend/staticwebapp-config-validate/SKILL.md`
  - Validate `staticwebapp.config.json` against schema
  - Emit error with JSON path and expected type
  - Detect missing rewrite/redirect target files
- [x] T063 [US4] Write `skills/software-development/web-frontend/staticwebapp-config-edit/SKILL.md`
  - Safely edit `staticwebapp.config.json`
  - Preserve schema validity via round-trip validation
  - Add routes, headers, or rewrites as requested
- [x] T064 [US4] Write `skills/software-development/web-frontend/frontend-preview/SKILL.md`
  - Start local preview via `swa start` or `npm run dev`
  - Enforce `localhost` binding only (systemd egress filter compatibility)
  - Surface preview URL to user
- [x] T065 [US4] Write `skills/software-development/web-frontend/frontend-smoke-check/SKILL.md`
  - Run Lighthouse-style checks against deployed SWA URL
  - Report performance, accessibility, and best-practice scores
  - Handle not-yet-deployed URL with clear "not reachable" result rather than hanging
- [x] T066 [US4] Wire all web-frontend skills into `skills/software-development/web-frontend/SKILL.md`
- [ ] T067 [US4] Add `web-frontend` kit allowlist entry to `agent/tool_surface_allowlists.yaml`
- [x] T068 [US4] Integrate `FrameworkDetector` into `frontend-preview` and `frontend-smoke-check` skills for context-aware behavior

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Partner Small Model Integration & Cross-Cutting Concerns

**Purpose**: Register partner model in agent escalation chain, bind memory profiles, enforce no-secret logging, and final verification

- [ ] T069 Integrate `PartnerProvider` into `agent/run_agent.py` or `agent/agent_init.py`
  - Register `/v1/partner/chat/completions` and `/v1/partner/embeddings` as remote LM provider
  - Use existing OpenAI-compatible adapter
  - Place partner model after local Ollama in escalation chain, before paid providers
  - Same Ollama adapter, JSON-schema tool-call validation, and per-kit failure budget as local Jetson Ollama
- [ ] T070 Bind `azure-ops` kit to `azure` and `infra` memory profiles on load (spec 013)
- [ ] T071 Bind `web-frontend` kit to `web` memory profile on load (spec 013)
- [ ] T072 Bind `linux-vm-api` kit to `infra` and `api` memory profiles on load (spec 013)
- [ ] T073 Verify `partner-model-health` successfully calls `/v1/partner/chat/completions` and schema-matches OpenAI response
- [ ] T074 Verify partner model appears in escalation chain and is reachable as configured provider
- [ ] T075 Verify no `azure-ops` or `linux-vm-api` skill logs secrets (API key, SSH key, Tailscale auth key) — log scan in integration tests
- [ ] T076 Verify `az-vm-run-command` refuses off-allowlist commands and logs at `WARNING`
- [ ] T077 Verify `frontend-preview` binds to `localhost` only (network scan or config inspection)
- [ ] T078 Verify `systemd-restart` requires user confirmation before executing
- [ ] T079 Verify `apikey-rotate` never logs new key values in agent log or gateway output
- [ ] T080 [P] Run retained unit-test suite and confirm zero regressions in skill loading, tool registry, or provider escalation
- [ ] T081 Update `agent/tool_surface_allowlists.yaml` with finalized tool names for all three kits after audit
- [ ] T082 Update `REDESIGN.md` §5.11, §10 references to reflect completed implementation
- [x] T083 Update `specs/008-azure-ops-bundle/` status to Complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Partner Integration (Phase 7)**: Depends on US3 completion for `partner-model-health`; can be drafted in parallel with US4
- **Polish (Final Phase)**: Depends on all desired user stories and partner integration being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Builds on US1 read-only infrastructure but can be tested standalone
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Needs VM and partner model available for integration testing
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — Needs SWA schema and framework detector; orthogonal to US1–US3

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Support library before skill markdown
- Read-only skills before mutate skills
- Core skill before integration into root SKILL.md
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel across all three bundles
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all four user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- US1 and US4 are orthogonal (Azure cloud vs. web frontend) and can proceed in parallel
- US3 VM skills and partner model integration can be drafted in parallel with US2 deploy skills

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (all three bundles)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (read-only Azure inspection)
4. **STOP and VALIDATE**: Test User Story 1 independently (`/azure status` returns login state and resources without any writes)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Partner model integration and polish → Final validation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Azure read-only) + User Story 2 (SWA deploy)
   - Developer B: User Story 3 (VM operations + partner model)
   - Developer C: User Story 4 (web frontend validation)
3. Once US3 partner model health is working:
   - Developer D: Partner provider registration in agent escalation chain
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- The three bundles MUST honor the per-kit tool-call-failure budget of 3 (spec 005)
- Memory profile bindings MUST be applied on kit load and removed on unload (spec 013)
- `azure-ops` and `linux-vm-api` mutate operations MUST require explicit user confirmation regardless of workspace `approval_mode`
- No secrets (API keys, SSH keys, Tailscale auth keys) may ever appear in agent logs — verified by automated log scanning
- `frontend-preview` MUST bind to `localhost` only, enforced by the systemd egress filter where applicable
- `journalctl-read` MUST be bounded and non-interactive; tailing is prohibited
