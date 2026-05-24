---
name: azure-ops
description: "Root bundle descriptor for Azure operations. Exposes /azure slash command with 11 skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [azure-ops, bundle, azure, devops, cloud]
    related_skills: [web-frontend, linux-vm-api]
    memory_profiles: [azure, infra]
---

# Azure-Ops Skill Bundle

The `azure-ops` bundle implements read-only Azure inspection, SWA management, VM operations, Bicep CRUD, and Key Vault secret resolution. It exposes the `/azure` slash command and provides 11 skills scoped to the Azure + SWA + VM topology.

## Skill Inventory

1. **az-login-status** — Return current Azure CLI login state and default subscription
2. **az-account-show** — Return active account details (name, tenant, subscription ID)
3. **az-resource-list** — Return filtered read-only list of resources in bound subscription/resource group
4. **az-swa-show** — Return current Azure Static Web App configuration (name, hostname, domains, routing)
5. **az-swa-config-update** — Edit SWA configuration (routes, auth providers, custom domains); gated by approval
6. **az-swa-deploy** — Produce deploy artifact and upload to SWA or trigger GitHub Actions workflow; gated by approval
7. **az-vm-status** — Return VM power state, private IP, and API health endpoint status
8. **az-vm-run-command** — Execute allowed diagnostics commands on VM via Azure Run Command API; gated by allowlist
9. **bicep-validate** — Validate Bicep modules against Azure schema
10. **bicep-deploy** — Deploy Bicep modules for SWA + VM topology; gated by approval
11. **keyvault-secret-show** — Resolve secrets read-only from Azure Key Vault; writes always require confirmation

## Approval Gates

- **swa-mutation**: Mandatory before `az-swa-config-update` mutates SWA settings
- **swa-deploy**: Mandatory before `az-swa-deploy` uploads or triggers deployment
- **vm-command**: `az-vm-run-command` is gated by per-VM `VmAllowlist`; off-list commands are refused and logged at WARNING
- **bicep-deploy**: Mandatory before `bicep-deploy` creates or updates resources

## Key Entities

- **AzureOpsKit**: The `skills/devops/azure-ops/` bundle
- **VmAllowlist**: Per-VM command allowlist gating `az-vm-run-command`
- **SwaConfig**: `staticwebapp.config.json` in the `web/` directory

## Memory Profile Bindings

- `azure` — Subscription, resource group, and SWA conventions
- `infra` — VM, systemd, and networking conventions

## Safety Rules

- Read-only skills never mutate Azure resources
- All mutation skills require explicit user confirmation regardless of workspace `approval_mode`
- No secrets (API keys, SSH keys, Tailscale auth keys) are ever logged
- `az-vm-run-command` refuses off-allowlist commands and logs at `WARNING`

## Notes

This is a skeleton bundle. Full skill logic implementation is pending per `specs/008-azure-ops-bundle/`.
