---
name: frontend-smoke-check
description: "Run Lighthouse-style checks against deployed SWA URL and report scores."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, lighthouse, smoke-test, accessibility, performance]
    related_skills: [frontend-preview]
---

# frontend-smoke-check

## Title
 frontend-smoke-check — Deployed Frontend Smoke Testing

## Description
Run Lighthouse-style checks against the deployed SWA URL and report performance, accessibility, and best-practice scores. If the URL is not yet deployed, return a clear "not reachable" result rather than hanging or producing a misleading zero-score. Must complete within 60 seconds.

## Trigger Conditions
- User invokes `/web smoke-check`
- User asks to test or check the deployed frontend

## Inputs
- Deployed SWA URL

## Outputs
- Performance, accessibility, and best-practice scores
- Reachability status

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the web-frontend bundle.
