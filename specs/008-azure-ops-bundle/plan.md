# Implementation Plan: Azure / Web Ops Skill Bundles

**Branch**: `008-azure-ops-bundle` | **Date**: 2026-05-24 | **Spec**: `specs/008-azure-ops-bundle/spec.md`

**Input**: Feature specification from `/specs/008-azure-ops-bundle/spec.md`

## Summary

Ship three coordinated skill bundles that together own the end-to-end Azure Static Web App + Linux VM API target:

1. **`skills/devops/azure-ops/`** — read-only Azure inspection (`az-login-status`, `az-account-show`, `az-resource-list`, `az-swa-show`), SWA configuration and deploy (`az-swa-config-update`, `az-swa-deploy`), VM operational surface (`az-vm-status`, `az-vm-run-command`), Bicep CRUD (`bicep-validate`, `bicep-deploy`), and Key Vault secret resolution (`keyvault-secret-show`).
2. **`skills/software-development/web-frontend/`** — framework-aware patterns for Astro/Next.js/SvelteKit/static HTML, `staticwebapp.config.json` validation and editing, local preview (`frontend-preview`), and Lighthouse-style smoke checks (`frontend-smoke-check`).
3. **`skills/devops/linux-vm-api/`** — systemd management (`systemd-status`, `systemd-restart`), reverse-proxy config editing (`reverse-proxy-edit`, `reverse-proxy-validate`), API key rotation (`apikey-rotate`), bounded log reading (`journalctl-read`), MCP surface validation (`mcp-validate`), and partner small model health checks (`partner-model-health`).

The partner small model running on the VM is exposed through `/v1/partner/chat/completions` and registered as a remote LM provider. All operational skills that mutate live Azure resources or VM state are gated by user confirmation regardless of workspace `approval_mode`.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: `azure-cli` (system dependency), `requests` (Key Vault, partner model health, GitHub API), `jsonschema` (staticwebapp.config.json validation), existing `agent/skill_commands.py`, existing `agent/tool_surface.py` (spec 003), existing `plugins/local_repo_workspace/` (spec 010), existing memory-profile subsystem (spec 013)

**Storage**: `~/.hermes-lite/cache/azure-ops/` (Azure API response cache), `~/.hermes-lite/cache/bicep/` (Bicep module cache), `skills/software-development/web-frontend/schemas/staticwebapp.config.schema.json` (SWA schema), `skills/devops/linux-vm-api/schemas/caddy.schema.json` or `nginx.schema.json` (proxy schema), workspace `web/staticwebapp.config.json`

**Testing**: pytest, plus integration tests requiring Azure sandbox subscription and paired Linux VM

**Target Platform**: Linux (Jetson Orin Nano) for agent; Azure cloud for target resources; Ubuntu 22.04 LTS VM for back-end

**Project Type**: Three coordinated skill bundles with Python support modules, JSON schemas, and provider integration

**Performance Goals**: `az-resource-list` returns results within 10 seconds for <50 resources; `az-swa-deploy` completes upload and activation within 120 seconds for build output <50 MB; `bicep-validate` catches schema errors within 5 seconds; `staticwebapp-config-validate` rejects malformed config within 2 seconds; `systemd-status` reports state within 5 seconds; `partner-model-health` returns within 10 seconds when healthy

**Constraints**: Read-only Azure inspection skills are the default operational surface; mutate operations require explicit user confirmation regardless of workspace mode; `az-vm-run-command` is gated by a per-VM allowlist; no secrets logged in agent logs; `frontend-preview` binds to `localhost` only; `journalctl-read` is bounded to max 1000 lines and interactive tailing is prohibited

**Scale/Scope**: Three skill bundles (~12–18 SKILL.md files total), Python support libraries for Azure CLI wrappers (~600–800 LOC), JSON schema files for SWA and proxy configs, partner model provider registration wiring in `agent/run_agent.py` or `agent/agent_init.py`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Security-First Development**: Azure mutate operations require explicit user confirmation regardless of workspace `approval_mode`. Key Vault secret reads are read-only; writes require confirmation. API key rotation never logs secrets.
- **Defense in Depth**: `az-vm-run-command` is gated by a per-VM allowlist mirroring `LocalRepoWorkspace` change-budget behavior. Reverse-proxy config validation runs before applying changes. Systemd restart requires confirmation.
- **Secure Defaults**: Read-only inspection skills (`az-login-status`, `az-resource-list`, `az-swa-show`) are the default surface. No write is attempted without confirmation. `frontend-preview` is localhost-only.
- **Dependency Management**: `azure-cli` is a system dependency installed outside the Python environment; agent uses subprocess calls with environment scrubbing. No heavy Azure SDK packages added.

**Result**: PASS — design aligns with all constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/008-azure-ops-bundle/
├── plan.md              # This file
├── spec.md              # Feature specification
└── tasks.md             # Concrete task list
```

### Source Code (repository root)

```text
skills/devops/azure-ops/
├── SKILL.md                    # Root bundle descriptor
├── az-login-status/SKILL.md    # Read-only Azure CLI login state
├── az-account-show/SKILL.md    # Read-only active account details
├── az-resource-list/SKILL.md   # Read-only filtered resource list
├── az-swa-show/SKILL.md        # Read-only SWA configuration
├── az-swa-config-update/SKILL.md  # SWA route/auth/domain mutation (gated)
├── az-swa-deploy/SKILL.md      # SWA deploy artifact upload (gated)
├── az-vm-status/SKILL.md       # Read-only VM power state + API health
├── az-vm-run-command/SKILL.md  # VM command execution (allowlist-gated)
├── bicep-validate/SKILL.md     # Bicep module schema validation
├── bicep-deploy/SKILL.md       # Bicep deployment (gated)
├── keyvault-secret-show/SKILL.md  # Key Vault read-only secret resolution
├── manifest.yaml               # Bundle manifest registering `/azure` slash command
└── lib/
    ├── __init__.py
    ├── az_cli_wrapper.py       # Subprocess wrapper for `az` with stdout/stderr capture, timeout, error parsing
    ├── vm_allowlist.py         # VmAllowlist — per-VM command allowlist loader from `infra` memory profile
    └── bicep_helper.py         # Bicep validate/deploy helpers

skills/software-development/web-frontend/
├── SKILL.md                            # Root bundle descriptor
├── staticwebapp-config-validate/SKILL.md  # Schema validation for staticwebapp.config.json
├── staticwebapp-config-edit/SKILL.md   # Safe config editing with schema preservation
├── frontend-preview/SKILL.md           # Local preview via swa start / npm run dev (localhost-only)
├── frontend-smoke-check/SKILL.md       # Lighthouse-style checks against deployed URL
├── manifest.yaml                       # Bundle manifest registering `/web` slash command
├── schemas/
│   └── staticwebapp.config.schema.json # Azure SWA schema
└── lib/
    ├── __init__.py
    ├── framework_detector.py           # Detect Astro/Next.js/SvelteKit/static HTML from workspace files
    └── swa_config_validator.py         # JSON schema validation and safe editing helpers

skills/devops/linux-vm-api/
├── SKILL.md                    # Root bundle descriptor
├── systemd-status/SKILL.md     # Systemd unit state report
├── systemd-restart/SKILL.md    # Systemd unit restart (confirmation-gated)
├── reverse-proxy-edit/SKILL.md # Caddy/nginx config editing
├── reverse-proxy-validate/SKILL.md  # Proxy config syntax validation
├── apikey-rotate/SKILL.md      # API key rotation via Key Vault + env file update (gated, no logging)
├── journalctl-read/SKILL.md    # Bounded log slice for specified unit
├── mcp-validate/SKILL.md       # MCP surface validation against hermes-lite mcp/ client
├── partner-model-health/SKILL.md  # Health check /v1/partner/chat/completions
├── manifest.yaml               # Bundle manifest registering `/vm` slash command
├── schemas/
│   ├── caddy.schema.json       # Caddy config schema (optional)
│   └── nginx.schema.json       # Nginx config schema (optional)
└── lib/
    ├── __init__.py
    ├── systemd_client.py       # Systemd wrapper via ssh/az-vm-run-command
    ├── proxy_config_editor.py  # Safe caddy/nginx config editing
    └── partner_provider.py     # Partner model registration as remote LM provider

~/.hermes-lite/skill-bundles/azure-ops.yaml   # Bundle alias (optional)
~/.hermes-lite/skill-bundles/web-frontend.yaml
~/.hermes-lite/skill-bundles/linux-vm-api.yaml

agent/
└── tool_surface.py             # UPDATE — register azure-ops, web-frontend, linux-vm-api kit allowlists

agent/
└── run_agent.py                # UPDATE — register partner model as remote LM provider in escalation chain
```

**Structure Decision**: Three separate skill bundles because each targets a distinct operational domain (Azure cloud, web frontend, VM back-end). Each bundle has its own manifest and slash command (`/azure`, `/web`, `/vm`). Python support libraries are scoped per bundle to minimize cross-bundle coupling. The partner model provider registration is the only cross-cutting agent-level change.

## Complexity Tracking

> The feature introduces three bundles rather than one. This is justified because:
> - The Azure cloud surface, web frontend surface, and VM back-end surface have different risk profiles, different gate requirements, and different memory profiles (`azure`, `web`, `infra`/`api`).
> - A single monolithic bundle would expose too many tools simultaneously to the 3B model, violating the tool-surface slimming goal (spec 003).
> - Separate bundles allow independent loading: a user inspecting Azure resources does not need the web-frontend or VM tools surfaced.
>
> | Violation | Why Needed | Simpler Alternative Rejected Because |
> |-----------|------------|-------------------------------------|
> | Three bundles instead of one | Different risk profiles, memory profiles, and tool surfaces; 3B model context limits | Single bundle would expose ~20 tools simultaneously, exceeding the slim tool surface constraint |
