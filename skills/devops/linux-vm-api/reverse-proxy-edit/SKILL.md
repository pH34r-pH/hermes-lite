---
name: reverse-proxy-edit
description: "Edit caddy or nginx configuration for API endpoints including /v1/partner/* route family."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [reverse-proxy, caddy, nginx, vm, mutation, api]
    related_skills: [reverse-proxy-validate]
---

# reverse-proxy-edit

## Title
 reverse-proxy-edit — Reverse Proxy Configuration Editing

## Description
Edit `caddy` (`Caddyfile`) or `nginx` (`nginx.conf` / `sites-available/`) configuration for the API endpoint, including the `/v1/partner/*` route family. Uses `ProxyConfigEditor` for safe editing. Gated by explicit user confirmation before applying changes.

## Trigger Conditions
- User invokes `/vm proxy edit`
- User asks to modify reverse proxy routes or upstreams

## Inputs
- Desired route or upstream changes
- Proxy type: `caddy` or `nginx`

## Outputs
- Updated proxy config file (on approval)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
