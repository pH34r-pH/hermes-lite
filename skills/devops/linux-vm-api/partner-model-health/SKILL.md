---
name: partner-model-health
description: "Call /v1/partner/chat/completions with test prompt and verify OpenAI chat completions schema."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [partner-model, ollama, health-check, api, vm]
    related_skills: [mcp-validate, az-vm-status]
---

# partner-model-health

## Title
 partner-model-health — Partner Small Model Health Check

## Description
Call `/v1/partner/chat/completions` with a test prompt and verify the response matches the OpenAI chat completions schema. On 502 error, diagnose whether the failure is in the reverse proxy, the Ollama instance, or the VM itself, and surface the most likely cause. Must return successfully within 10 seconds when the partner is healthy.

## Trigger Conditions
- User invokes `/vm partner health`
- User asks to check the partner model status

## Inputs
- Partner endpoint URL (`/v1/partner/chat/completions`)
- Test prompt (default: lightweight schema probe)

## Outputs
- Health status: healthy or unhealthy
- On 502: diagnosed most likely cause (reverse proxy, Ollama, VM)

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the linux-vm-api bundle.
