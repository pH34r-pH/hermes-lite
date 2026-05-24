# Feature Specification: Azure / Web Ops Skill Bundles

**Feature Branch**: `008-azure-ops-bundle`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Three bundles: skills/devops/azure-ops/ (Azure CLI, Bicep, SWA deploy), skills/software-development/web-frontend/ (framework patterns, staticwebapp.config.json), skills/devops/linux-vm-api/ (systemd, reverse proxy, partner small model). Read REDESIGN.md §5.11, §10."

## Current State

Upstream Hermes Agent ships generic `skills/devops/` and `skills/software-development/` skills for shell execution, file editing, and basic cloud provider interactions. However, there is **no Azure-focused operational bundle**, **no SWA-targeted frontend skill bundle**, and **no Linux VM API operations bundle**. The upstream agent lacks:
- Structured Azure CLI read-only inspection tools (`az-login-status`, `az-resource-list`, etc.)
- Azure Static Web App configuration management (`az-swa-show`, `az-swa-config-update`)
- Bicep validation and deployment helpers scoped to the SWA + VM topology
- Framework-aware frontend patterns for Astro/Next/SvelteKit targeting SWA
- `staticwebapp.config.json` schema validation and editing
- Systemd unit management for the API back-end and partner Ollama instance
- Reverse-proxy configuration editing (`caddy`/`nginx`) for the `/v1/partner/*` route family
- Integration between the deployed partner small model and the agent's provider escalation chain

The upstream agent can run `az` commands via generic shell tools, but it has no kit-shaped tool surface that scopes tools to the Azure + SWA + VM topology, respects per-VM allowlists, or validates `staticwebapp.config.json` against the SWA schema.

## Target State

Hermes-lite ships three coordinated skill bundles that together own the end-to-end Azure Static Web App + Linux VM API target:

1. **`skills/devops/azure-ops/`** — read-only Azure inspection, SWA configuration and deploy, VM operational surface, Bicep CRUD, and Key Vault secret resolution.
2. **`skills/software-development/web-frontend/`** — framework-aware patterns for the chosen SWA stack, `staticwebapp.config.json` validation, local preview, and Lighthouse-style smoke checks.
3. **`skills/devops/linux-vm-api/`** — systemd management for the proxy API and partner Ollama, reverse-proxy config editing, API key rotation, `journalctl` diagnostics, and MCP surface validation.

These bundles, combined with `LocalRepoWorkspace` (§5.9) and the spec-kit (§5.10), let hermes-lite own both halves of the SWA + Linux VM API target. The **partner small model** running on the VM is exposed through `/v1/partner/chat/completions` and registered as a remote LM provider, giving the agent a rate-limit-free experimentation target.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect Azure Resources and SWA Configuration (Priority: P1)

A user asks hermes-lite to check the health of their Azure deployment. `az-login-status`, `az-account-show`, and `az-resource-list` return read-only subscription and resource group metadata. `az-swa-show` returns the current SWA configuration including routes, auth providers, and custom domains.

**Why this priority**: Read-only inspection is the safest operational surface. It validates that the agent can reach Azure without risking mutation, and it gives the user situational awareness before any changes are proposed.

**Independent Test**: Can be fully tested by running the read-only skills against a sandbox subscription and verifying that no write operations are attempted.

**Acceptance Scenarios**:

1. **Given** the user types `/azure status`, **When** `az-login-status` and `az-account-show` run, **Then** they return the current subscription name, tenant ID, and authenticated user
2. **Given** the user asks for resources, **When** `az-resource-list` runs, **Then** it returns a filtered list of resources in the bound resource group with type, location, and provisioning state
3. **Given** the user asks for SWA config, **When** `az-swa-show` runs, **Then** it returns the SWA name, default hostname, custom domains, and current routing rules
4. **Given** the user is not logged in to Azure CLI, **When** any read-only skill runs, **Then** it returns a clear error suggesting `az login` and does not crash

---

### User Story 2 - Deploy the Static Web App Front-End (Priority: P1)

After the spec-kit implements front-end changes in the `azure-api` repo, the user asks hermes-lite to deploy. `az-swa-deploy` produces a deploy artifact (build output) and uploads it via `swa deploy` or references the GitHub Actions pipeline.

**Why this priority**: Deploy is the boundary between "code exists" and "service is live". For the SWA target, this is the primary user-facing deploy operation.

**Independent Test**: Can be fully tested by running `az-swa-deploy` against a staging slot and verifying that the new build is active.

**Acceptance Scenarios**:

1. **Given** the `web/` directory has a successful build output, **When** `az-swa-deploy` runs, **Then** it uploads the build artifact to the SWA and returns the deployment URL
2. **Given** the workspace uses GitHub Actions for deploy, **When** `az-swa-deploy` runs, **Then** it triggers the workflow via the GitHub API and polls for completion status
3. **Given** the deploy fails (build error, upload timeout), **When** `az-swa-deploy` runs, **Then** it surfaces the error logs and suggests the next diagnostic step
4. **Given** the user has not confirmed deploy (approval mode is `confirm` or `pr-only`), **When** `az-swa-deploy` runs, **Then** it pauses for explicit approval before any upload occurs

---

### User Story 3 - Operate the Linux VM Back-End and Partner Model (Priority: P2)

A user asks hermes-lite to check the VM health, restart the API proxy, or validate the partner small model endpoint. `az-vm-status` returns VM state. `az-vm-run-command` executes allowed diagnostics. `linux-vm-api` skills manage systemd units, read `journalctl`, and validate the MCP surface.

**Why this priority**: The Linux VM hosts both the proxy API and the partner Ollama instance. Keeping these services healthy is essential for the self-enhancement loop.

**Independent Test**: Can be fully tested by running VM operational skills against the paired VM and verifying systemd state changes and log retrieval.

**Acceptance Scenarios**:

1. **Given** the user asks for VM status, **When** `az-vm-status` runs, **Then** it returns the VM power state, private IP, and a badge indicating whether the API health endpoint is responding
2. **Given** the user asks to restart the API service, **When** `az-vm-run-command` executes `systemctl restart api-proxy`, **Then** it succeeds only if the command is on the per-VM allowlist
3. **Given** the user asks for recent logs, **When** the `journalctl` skill runs, **Then** it returns the last 100 lines for the specified unit without opening an interactive tail
4. **Given** the user asks to validate the partner model, **When** the MCP validation skill runs, **Then** it calls `/v1/partner/chat/completions` with a test prompt and confirms the response schema matches OpenAI chat completions

---

### User Story 4 - Validate Front-End Patterns and SWA Config Schema (Priority: P2)

A user asks hermes-lite to add a new route to the SWA or to validate the `staticwebapp.config.json`. The web-frontend bundle provides schema validation, framework-aware editing, local preview via `swa start`, and Lighthouse-style smoke checks against the deployed URL.

**Why this priority**: The front-end is the user-facing surface of the `azure-api` repo. Invalid `staticwebapp.config.json` can break routing or expose unintended content. Schema validation and smoke checks catch these errors before they reach production.

**Independent Test**: Can be fully tested by introducing a malformed `staticwebapp.config.json` and verifying that the schema-validation skill rejects it, and by running a Lighthouse check and verifying the score is captured.

**Acceptance Scenarios**:

1. **Given** a malformed `staticwebapp.config.json` (e.g., missing required `route` field), **When** schema validation runs, **Then** it emits an error with the JSON path and expected type
2. **Given** a valid config, **When** the user adds a new route via the web-frontend skill, **Then** the updated config passes schema validation and the route is reflected in the file
3. **Given** the user runs local preview, **When** `swa start` or `npm run dev` is invoked, **Then** it binds to `localhost` only, enforced by the systemd egress filter
4. **Given** the SWA is deployed, **When** the Lighthouse smoke check runs, **Then** it reports performance, accessibility, and best-practice scores for the deployed URL

---

### Edge Cases

- What happens when Azure CLI is not installed or not authenticated? The `azure-ops` skills must return a clear diagnostic message and suggest `az login` rather than attempting shell commands that will fail opaquely.
- How does the system handle a `swa deploy` that partially succeeds (upload completes but activation fails)? The skill must capture the intermediate state, surface both success and failure aspects, and suggest retry or rollback.
- What happens when `az-vm-run-command` receives a command not on the per-VM allowlist? The skill must refuse execution and log the refusal at `WARNING` level, mirroring the `LocalRepoWorkspace` change-budget behavior.
- How does the `linux-vm-api` bundle handle a systemd unit that fails to start? It must read the last 50 lines of `journalctl`, surface the error, and never attempt to auto-restart without user confirmation.
- What happens when the partner small model endpoint (`/v1/partner/chat/completions`) returns a 502? The `linux-vm-api` bundle must diagnose whether the failure is in the reverse proxy, the Ollama instance, or the VM itself, and surface the most likely cause.
- What happens when `staticwebapp.config.json` references a file that does not exist in the build output? Schema validation must catch file-not-found errors for `rewrite` or `redirect` targets.
- How does the system handle a framework mismatch (workspace claims Astro but the files look like Next.js)? The web-frontend skill must detect the mismatch, emit a warning, and ask the user to confirm the intended framework before applying patterns.
- What happens when the Lighthouse smoke check runs against a URL that is not yet deployed? The skill must return a clear "not reachable" result rather than hanging or producing a misleading zero-score.

## Requirements *(mandatory)*

### Functional Requirements

#### Azure-Ops Bundle (`skills/devops/azure-ops/`)

- **FR-001**: `az-login-status` MUST return the current Azure CLI login state and default subscription
- **FR-002**: `az-account-show` MUST return the active account details (name, tenant, subscription ID)
- **FR-003**: `az-resource-list` MUST return a filtered, read-only list of resources in the bound subscription/resource group
- **FR-004**: `az-swa-show` MUST return the current Azure Static Web App configuration: name, hostname, custom domains, and routing rules
- **FR-005**: `az-swa-config-update` MUST edit SWA configuration (routes, auth providers, custom domains) through the Azure API
- **FR-006**: `az-swa-deploy` MUST produce a deploy artifact and upload it via `swa deploy` or trigger the configured GitHub Actions workflow
- **FR-007**: `az-vm-status` MUST return the VM power state, private IP, and API health endpoint status
- **FR-008**: `az-vm-run-command` MUST execute allowed commands on the VM through the Azure Run Command API, gated by a per-VM allowlist
- **FR-009**: `bicep-validate` MUST validate Bicep modules against the Azure schema and report errors
- **FR-010**: `bicep-deploy` MUST deploy Bicep modules for the paired SWA + VM topology
- **FR-011**: `keyvault-secret-show` MUST resolve secrets read-only from Azure Key Vault; writes MUST always require confirmation mode

#### Web-Frontend Bundle (`skills/software-development/web-frontend/`)

- **FR-012**: The bundle MUST support framework-aware patterns for Astro, Next.js, SvelteKit, or static HTML, selected per workspace
- **FR-013**: `staticwebapp-config-validate` MUST validate `staticwebapp.config.json` against the SWA schema and report errors with JSON paths
- **FR-014**: `staticwebapp-config-edit` MUST safely edit `staticwebapp.config.json` while preserving schema validity
- **FR-015**: `frontend-preview` MUST start a local preview via `swa start` or `npm run dev`, gated to `localhost` only
- **FR-016**: `frontend-smoke-check` MUST run Lighthouse-style checks against the deployed SWA URL and report performance, accessibility, and best-practice scores
- **FR-017**: The bundle MUST bind to the `web` memory profile so frontend conventions are isolated from other workflows

#### Linux-VM-API Bundle (`skills/devops/linux-vm-api/`)

- **FR-018**: `systemd-status` MUST report the state of the API proxy systemd unit and the partner Ollama systemd unit
- **FR-019**: `systemd-restart` MUST restart a specified systemd unit on the VM, gated by user confirmation
- **FR-020**: `reverse-proxy-edit` MUST edit `caddy` or `nginx` configuration for the API endpoint, including the `/v1/partner/*` route family
- **FR-021**: `reverse-proxy-validate` MUST validate the reverse-proxy config syntax before applying changes
- **FR-022**: `apikey-rotate` MUST rotate API keys via `keyvault-secret-show` and update the systemd unit's environment file; it MUST never log the new secrets
- **FR-023**: `journalctl-read` MUST return a bounded slice of logs (max 1000 lines) for the specified unit; interactive tailing is prohibited
- **FR-024**: `mcp-validate` MUST validate the API's MCP surface against the hermes-lite `mcp/` client skill
- **FR-025**: `partner-model-health` MUST call `/v1/partner/chat/completions` with a test prompt and verify the response matches the OpenAI chat completions schema
- **FR-026**: The bundle MUST bind to the `infra` and `api` memory profiles

#### Partner Small Model Integration

- **FR-027**: The partner model endpoint (`/v1/partner/chat/completions` and `/v1/partner/embeddings`) MUST be registered in hermes-lite as a remote LM provider through the existing OpenAI-compatible adapter
- **FR-028**: The partner model MUST be the default target for new-API skill development; paid providers MUST remain on the escalation chain (§12.1)
- **FR-029**: The partner model MUST use the same Ollama adapter, JSON-schema tool-call validation, and per-kit failure budget as the local Ollama on the Jetson

### Key Entities

- **AzureOpsKit**: The `skills/devops/azure-ops/` bundle exposing read-only inspection, SWA management, VM operations, Bicep CRUD, and Key Vault access.
- **WebFrontendKit**: The `skills/software-development/web-frontend/` bundle exposing framework patterns, SWA config validation/editing, local preview, and smoke checks.
- **LinuxVmApiKit**: The `skills/devops/linux-vm-api/` bundle exposing systemd management, reverse-proxy editing, API key rotation, log reading, and MCP validation.
- **PartnerSmallModel**: A quantized 3B model (default candidate `qwen3:3b-instruct`) running in a separate Ollama instance on the `azure-api` VM, reverse-proxied through `/v1/partner/*`.
- **VmAllowlist**: A per-VM command allowlist that gates `az-vm-run-command` execution, mirroring the `LocalRepoWorkspace` change-budget pattern.
- **SwaConfig**: The `staticwebapp.config.json` file in the `web/` directory, validated against the Azure SWA schema.
- **ReverseProxyConfig**: The `caddy` or `nginx` configuration on the Linux VM that routes `/v1/partner/*` to the partner Ollama instance and `/v1/*` to the proxy API.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `az-resource-list` returns a resource list within 10 seconds for a subscription with fewer than 50 resources
- **SC-002**: `az-swa-deploy` completes upload and activation within 120 seconds for a build output under 50 MB
- **SC-003**: `bicep-validate` catches at least one schema error in a deliberately malformed Bicep file during integration testing
- **SC-004**: `staticwebapp-config-validate` rejects a malformed config within 2 seconds and reports the exact JSON path of the error
- **SC-005**: `frontend-smoke-check` returns Lighthouse scores for performance, accessibility, and best practices within 60 seconds
- **SC-006**: `systemd-status` reports the state of both the API proxy and partner Ollama units within 5 seconds
- **SC-007**: `partner-model-health` returns a successful response from `/v1/partner/chat/completions` within 10 seconds when the partner is healthy
- **SC-008**: `mcp-validate` confirms the API's MCP surface is compatible with the hermes-lite `mcp/` client skill, or reports the exact incompatibility
- **SC-009**: The partner model is reachable as a configured provider in hermes-lite and appears in the escalation chain after local Ollama
- **SC-010**: No `azure-ops` or `linux-vm-api` skill ever logs a secret (API key, SSH key, Tailscale auth key) — verified by log scanning in integration tests

## Assumptions

- The `azure-api` repo contains `infra/`, `web/`, and `api/` sub-trees, and is registered in `~/.hermes-lite/workspaces.yaml`
- Azure CLI (`az`) is installed and authenticated on the cyberdeck; the bound subscription and resource group are configured in the `azure` memory profile
- The target Azure Static Web App and Linux VM already exist; bootstrap creation is out of scope for these bundles and handled by Bicep deployment in the `infra/` directory
- The Linux VM runs Ubuntu 22.04 LTS (or later) with `systemd`, and `caddy` or `nginx` is pre-installed
- The partner Ollama instance is installed and configured to bind to a private interface on the VM
- The `web` memory profile contains the chosen framework (Astro, Next.js, SvelteKit, or static HTML) and SWA conventions
- The `infra` memory profile contains systemd hardening rules, reverse-proxy patterns, and Tailscale mesh networking conventions
- The `api` memory profile contains the OpenAI-compatible API contract, route definitions, and MCP exposure details
- LocalRepoWorkspace (§5.9) is available for commits to `azure-api`; operational skills that mutate live Azure resources or VM state are gated by user confirmation regardless of workspace `approval_mode`
- The partner model VM is sized small (e.g., Standard_D2as_v5); GPU is not required for the partner 3B model
- TLS termination and public DNS are handled outside these bundles; the bundles operate on the assumption that HTTPS is already configured for the SWA and VM endpoints
