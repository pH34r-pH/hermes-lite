---
name: frontend-preview
description: "Start local preview via swa start or npm run dev, bound to localhost only."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, preview, swa, localhost, dev-server]
    related_skills: [frontend-smoke-check]
---

# frontend-preview

## Title
 frontend-preview — Local Frontend Preview

## Description
Start a local preview via `swa start` or `npm run dev`, enforcing `localhost` binding only for systemd egress filter compatibility. Detect the workspace framework via `FrameworkDetector` (Astro, Next.js, SvelteKit, static HTML) and choose the appropriate preview command. Surface the preview URL to the user.

## Trigger Conditions
- User invokes `/web preview`
- User asks to run or start the frontend locally

## Inputs
- Framework type (auto-detected)
- Preview command preference (auto-detected from `package.json` scripts)

## Outputs
- Preview URL (e.g., `http://localhost:3000`)
- Process status

## Notes
**Full implementation is pending.** This stub establishes the skill shape and loading contract for the web-frontend bundle.
