---
name: linux-vm-api
description: "Root bundle descriptor for Linux VM API operations. Exposes /vm slash command with 8 skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [linux-vm-api, bundle, vm, systemd, reverse-proxy, api, mcp, partner-model]
    related_skills: [azure-ops, web-frontend]
    memory_profiles: [infra, api]
---

# Linux-VM-API Skill Bundle

The `linux-vm-api` bundle manages systemd units for the proxy API and partner Ollama instance, edits reverse-proxy configuration, rotates API keys, reads bounded `journalctl` logs, validates MCP surfaces, and checks partner model health. It exposes the `/vm` slash command.

## Skill Inventory

1. **systemd-status** — Report state of API proxy and partner Ollama systemd units
2. **systemd-restart** — Restart a specified systemd unit on the VM; gated by confirmation
3. **reverse-proxy-edit** — Edit `caddy` or `nginx` configuration for `/v1/partner/*` and `/v1/*` routes; gated by approval
4. **reverse-proxy-validate** — Validate proxy config syntax via `caddy validate` or `nginx -t`
5. **apikey-rotate** — Rotate API keys via Key Vault and update systemd environment file; never logs secrets; always confirmation-mode
6. **journalctl-read** — Return bounded slice of logs (max 1000 lines) for specified unit; tailing prohibited
7. **mcp-validate** — Validate API MCP surface against hermes-lite `mcp/` client skill
8. **partner-model-health** — Call `/v1/partner/chat/completions` with test prompt and verify OpenAI chat completions schema

## Approval Gates

- **systemd-mutation**: Mandatory before `systemd-restart`
- **proxy-mutation**: Mandatory before `reverse-proxy-edit`
- **credential-rotation**: `apikey-rotate` always runs in `approval_mode: confirm` regardless of workspace default

## Key Entities

- **PartnerSmallModel**: Quantized 3B model (default `qwen3:3b-instruct`) running in Ollama on the VM, reverse-proxied through `/v1/partner/*`
- **ReverseProxyConfig**: `caddy` or `nginx` configuration routing `/v1/partner/*` to partner Ollama and `/v1/*` to proxy API

## Memory Profile Bindings

- `infra` — systemd hardening rules, reverse-proxy patterns, Tailscale mesh networking
- `api` — OpenAI-compatible API contract, route definitions, MCP exposure details

## Safety Rules

- `apikey-rotate` never logs new secret values in agent logs, gateway messages, or `state.db`
- `journalctl-read` is bounded and non-interactive; tailing is prohibited
- `systemd-restart` on failure reads last 50 lines of `journalctl`, surfaces error, does not auto-restart
- On partner model 502, diagnose reverse proxy vs Ollama vs VM failure and surface most likely cause

## Notes

This is a skeleton bundle. Full skill logic implementation is pending per `specs/008-azure-ops-bundle/`.
