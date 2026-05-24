---
name: reverse-proxy-validate
description: "Validate reverse-proxy config syntax before applying changes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [reverse-proxy, caddy, nginx, validation]
    related_skills: [reverse-proxy-edit]
---

# reverse-proxy-validate

## Title
 reverse-proxy-validate — Reverse Proxy Syntax Validation

## Description
Validate the reverse-proxy configuration syntax before applying changes. Calls `caddy validate` or `nginx -t` depending on the active proxy. Report exact syntax errors with file and line.

## Trigger Conditions
- User invokes `/vm proxy validate`
- User asks to check proxy config syntax

## Inputs
- Proxy config file path
- Proxy type: `caddy` or `nginx`

## Outputs
- Validation result: pass or error list with file and line

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
