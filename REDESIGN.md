# Hermes-Lite — Cyberdeck Fork Proposal for the Research → Implement → Self-Enhance Loop

This is a self-contained design document for **hermes-lite**, a
focused, opinionated fork of
[Hermes Agent](https://github.com/NousResearch/hermes-agent) intended
to turn a portable NVIDIA Jetson Orin Nano 8 GB into a developer
"cyberdeck" — an offline-capable, persistent AI working environment
that researches, designs, implements, and deploys its own services
and then uses those services to enhance the next iteration. The
document describes the entire design without external references;
everything required to evaluate, scope, and build hermes-lite is
contained here.

Hermes-lite is intended to:

- run on a portable **"cyberdeck" Jetson Orin Nano 8 GB** that a
  single developer can use **offline, without paid services**,
  unifying paid OpenAI / Copilot / Claude access behind a personally
  owned API when connectivity is available;
- drive small local models (target reference model: **Ministral-3
  3B**, with documented alternatives in §12) intentionally, so the
  same agent stack can later scale **horizontally across a swarm of
  low-cost devices** communicating over a Tailscale mesh VPN — each
  tuned as a narrow expert;
- support **only** four LM providers: **Ollama, OpenAI, GitHub
  Copilot, Claude (Anthropic)**, with the latter three reached
  through the developer-owned API once it is deployed;
- expose **three** surfaces: a local **TUI**, **Discord**, and
  **Open WebUI**. Discord is treated as the **stable, reliable
  remote prompt source**; the Azure Static Web App (built and
  deployed by hermes-lite itself) backs **Open WebUI as an
  experimentation endpoint** alongside Discord, never as a
  replacement. The TUI is the guaranteed local surface;
- be organized around the full **research → spec → implement →
  deploy → self-enhance loop**: perform **arXiv research** as the
  proof-of-concept inbound flow, convert findings into spec proposals
  using a **spec-kit-style spec → plan → tasks → implement** pattern,
  push to `main`, let CICD deploy, and then **use the
  freshly-deployed API to enhance the next iteration of the agent
  itself**;
- service one concrete production target: a **monorepo** that holds
  infrastructure-as-code, the Azure Static Web App front-end, and the
  Linux VM back-end API — all deployed by a single CICD pipeline so
  hermes-lite never directly touches Azure for routine deploys;
- retain **all** Hermes skills relevant to web development, Azure
  resources, networking, git, MCP, security and red-teaming, and
  general dev workflow — only the surfaces we will never use
  (image/video/voice/non-allowlisted chat platforms / non-allowlisted
  LM providers) are dropped;
- keep Hermes' memory, persistence, and learning loop intact, with
  one operational change: **curator and background-review passes are
  enqueued and run in batches under user direction**, never
  autonomously (§12.2);
- safely accept directives that **modify, commit, and push to local
  git repositories** on the same device.

## 1. Design Premises

1. **Small models magnify environment quality.** A 3B model has very
   little room to recover from a noisy environment, sprawling tool
   surface, or ambiguous prompts. Every reduction in surface area
   translates into measurable capability gains.
2. **Small models are also a swarm strategy.** Targeting a 3B model on
   a Jetson Orin Nano now means the same agent stack can later run on
   $200–$500 edge devices in parallel, each tuned to a narrow domain,
   communicating over a Tailscale mesh VPN. The constraints we accept
   here pay forward when we fan out.
3. **Offline-first cyberdeck.** The Jetson is a portable developer
   workstation. Hermes-lite must be **fully functional with no
   internet**: Ollama for the model, on-disk skills, `state.db` for
   recall, the TUI for input. Network providers and gateways are
   strict upgrades when connectivity is available, never
   prerequisites.
4. **One workload at a time, but a complete one.** The device is not a
   chat product. It runs **one cohesive workflow at a time** —
   research a topic, write a spec, plan and break down tasks, then
   implement, push to `main`, and let CICD deploy. The arXiv kit, the
   spec-kit, the dev kit, the azure-ops kit, the web-ops kit, and the
   security kit are loaded one at a time via `agent/tool_surface.py`,
   and the kit hand-off is itself a first-class state transition.
5. **Subtract surfaces, keep skills.** The fork drops *platforms* we
   will never use (image gen, video gen, voice, non-allowlisted chat
   surfaces, non-allowlisted LM providers). It does **not** drop
   dev-workflow or security skills. Hermes'
   `software-development/`, `devops/`, `github/`, `mcp/`,
   `data-science/`, `domain/`, and security/red-team skill trees stay
   in the tree, because they are the engine of the research → spec →
   implement → deploy → self-enhance loop.
6. **CICD owns deploy; hermes-lite owns three repos.** Hermes-lite
   owns three first-class git repos on the cyberdeck, registered as
   peers in `~/.hermes-lite/workspaces.yaml`:
   - **`blue-swallow-society`** — the infra-as-code + Azure Static Web App
     front-end + Linux VM back-end API. A single CICD pipeline
     declared inside this repo is the only routine path that
     touches live Azure resources.
   - **`hermes-lite`** — the fork itself. The agent treats its own
     source tree as just another registered workspace, so
     self-improvement (new skills, refined prompts, harness
     fixes) lands as a normal spec → plan → tasks → PR cycle.
   - **`knowledge`** — a shared research store (papers, notes,
     extracts, seeds) that is pulled locally on the Jetson,
     evolves independently of either code repo, and is intended
     to be shared with other developers and other cyberdecks.
   The agent's Azure write surface (§5.11) exists for bootstrap
   and incident response, not for everyday deploys.
7. **The agent enhances itself through its own API — and through
   its own source.** Once the personally-owned API on the Linux VM
   is live, hermes-lite is allowed to call it as a remote LM
   provider via the existing OpenAI-compatible adapter, **including
   a self-hosted partner small model deployed on the same VM**
   (§5.11). The partner model gives the agent a rate-limit-free
   experimentation target so API-based skill development does not
   block on paid quotas. New API features and harness improvements
   hermes-lite ships unlock new capabilities for hermes-lite the
   next time it runs the loop. This is the headline value
   proposition.
8. **Red-team yourself.** Because the agent commits, pushes, deploys,
   and then calls its own deployed services, security and red-team
   skills are first-class — not optional add-ons. The fork retains
   pentest, threat-modeling, and secure-coding skills so the agent
   can probe its own surface before exposing it to the public
   internet.
9. **Persistence stays.** The reason to fork hermes (instead of
   writing from scratch) is the conversational persistence, FTS5
   recall, curator, background review, skills, and trajectory
   capture. We keep those.
10. **Linux first, single-user, single-tenant.** Windows-only paths,
    POSIX-PTY-only paths, and macOS-specific skills can be removed.
11. **No new providers, no new chat gateways.** The fork explicitly
    closes off third-party LM/transport additions to keep the
    dependency tree small. New *skill bundles* (spec-kit, azure-ops,
    web-ops, security) are fair game; new providers and chat
    platforms are not. Discord stays as the **stable remote prompt
    source**; the Static Web App (Open WebUI-backed) is an
    **experimentation endpoint** that runs alongside Discord, not a
    replacement. We deliberately keep two remote gateways so we
    never lock ourselves to one transport.

## 2. Target Hardware and Models

Reference device: **NVIDIA Jetson Orin Nano 8 GB**.

| Concern | Target |
| ------- | ------ |
| Device | Jetson Orin Nano 8 GB (`aarch64`, integrated 1024-core Ampere GPU, 40 TOPS sparse / 20 TOPS dense INT8) |
| OS | NVIDIA JetPack 6.x (Ubuntu 22.04, glibc, `aarch64`) |
| Default power mode | **25 W (`nvpmodel -m 1`)** — sustained-thermal-stable in observation; the watchdog defaults to this mode for any session lasting more than 20 minutes |
| Burst power mode | `nvpmodel -m 0` (MAXN, 15 W TDP nominal but unrestricted clocks): used for short bursts of ≤10–20 minutes, e.g. an `arxiv-skim` over a 20-page paper or a `spec-implement` pass over a large diff. The watchdog returns to 25 W once the burst-skill releases its iteration budget |
| Idle power mode | 7 W (`nvpmodel -m 2`) when the agent has no active session for more than 5 minutes |
| RAM | 8 GB unified (CPU + GPU share); design budget ~6 GB resident across agent + model + gateways |
| Disk | **512 GB microSD** card; budget split documented in §7.4 |
| Local model runtime | Ollama (`http://127.0.0.1:11434`) with CUDA acceleration via JetPack |
| Primary local model | `ministral-3:3b` (Q4_K_M, ~2.3 GB on disk, ~2.7 GB resident) |
| Documented alternatives | See §12.1; the adapter is model-agnostic so swapping is a config change, not a code change |
| Remote escalation | OpenAI, GitHub Copilot, Claude (Anthropic API) — reached through the developer-owned API once it is deployed |
| Thermals | Active cooling required for any sustained 25 W or MAXN; thermal watchdog reports back via `hermes-lite doctor` and forces a drop to 7 W on a thermal alarm |

A Jetson Orin Nano lifts the budget slightly versus a generic 8 GB
Linux VM because the GPU shares the unified 8 GB pool with the CPU.
We size the agent process tightly so that Ollama + Ministral-3 3B can
coexist with the agent, gateways, and a TUI without swapping.

## 3. Provider and Gateway Allow-List

### 3.1 LM Providers Retained

| Provider | Hermes module(s) retained | Notes |
| -------- | ------------------------- | ----- |
| Ollama (local) | `agent/lmstudio_reasoning.py` replaced with a tighter `agent/ollama_adapter.py` (new); reuse credential pool patterns | Default provider for 3B model on the cyberdeck |
| **Ollama (partner, on `blue-swallow-society` VM)** | Same adapter, different base URL | Self-hosted partner small model exposed through the developer-owned API (§5.11); rate-limit-free experimentation target for API-driven skill development |
| OpenAI | `agent/chat_completion_helpers.py`, OpenAI-compatible adapters | Used as escalation for hard prompts |
| GitHub Copilot | `agent/copilot_acp_client.py`, `acp_adapter/`, `acp_registry/` | Used when running adjacent to a Copilot-paired editor |
| Claude (Anthropic) | `agent/anthropic_adapter.py` | Used for long-context summarization and code-heavy tasks |

### 3.2 LM Providers Removed

Drop the modules and any plugin code that imports them:

- Azure Foundry / Entra ID adapter
  (`agent/azure_identity_adapter.py`).
- AWS Bedrock (`agent/bedrock_adapter.py`).
- Gemini Native + CloudCode + schema
  (`agent/gemini_native_adapter.py`,
  `agent/gemini_cloudcode_adapter.py`, `agent/gemini_schema.py`,
  `agent/google_code_assist.py`, `agent/google_oauth.py`).
- Codex runtime and responses adapter
  (`agent/codex_runtime.py`, `agent/codex_responses_adapter.py`).
- xAI / Grok OAuth and routing
  (`agent/credential_sources.py` xAI paths,
  `fix(xai-oauth): ...` logic).
- Moonshot/Kimi schema (`agent/moonshot_schema.py`).
- MiniMax, Hugging Face, NovitaAI, NVIDIA NIM, MiMo, OpenRouter,
  z.ai/GLM, Nous Portal model picker (`agent/models_dev.py`,
  `agent/portal_tags.py`).
- Auxiliary client (`agent/auxiliary_client.py`) is replaced with a
  single-provider helper.

### 3.3 Gateway / Surface Platforms Retained

| Surface | Source | Notes |
| ------- | ------ | ----- |
| TUI | `tui_gateway/`, `ui-tui/` | Retained for local SSH and headed sessions on the Jetson |
| Discord | `gateway/platforms/discord/` (from `gateway/platforms/`) | Single bot, single guild, allowlisted channel IDs |
| Open WebUI | New `gateway/platforms/openwebui/` (custom) | Backed by Open WebUI's pipelines/functions, gives a browser UI without standing up a full hermes web dashboard |

All three surfaces converge on the same agent loop and the same
`state.db`, so a directive issued in Discord can be inspected in the
TUI, and the Open WebUI session lists the same history.

### 3.4 Gateway Platforms Removed

- Telegram, Slack, WhatsApp, Signal, Email, Yuanbao, Weixin, plus all
  their adapter, identity, sticker, and ID-pinning code.
- The bundled web dashboard (`web/`, `website/`, `plugins/web/`,
  `example-dashboard/`).

### 3.5 Components Always Removed

- Voice / TTS dependencies (`.[termux]` extras, ElevenLabs assets,
  TTS workspace audio).
- Image generation (`plugins/image_gen/`, `agent/image_gen_provider.py`,
  `agent/image_gen_registry.py`, `agent/image_routing.py`).
- Video generation (`plugins/video_gen/`,
  `agent/video_gen_provider.py`, `agent/video_gen_registry.py`).
- Spotify, Google Meet, Microsoft Teams pipeline, achievements
  (`plugins/spotify/`, `plugins/google_meet/`,
  `plugins/teams_pipeline/`, `plugins/hermes-achievements/`).
- All Microsoft Foundry / Atropos / Tinker / Apple-specific skills.
- Sticker cache, WhatsApp identity, Telegram topic preservation,
  case-sensitive Telegram chat-ID handling.
- Homebrew packaging, Termux extras, Nix flake, MinGit bootstrap,
  Windows UTF-8 stdio shim. Keep only the `pyproject.toml` and a
  Linux-only Dockerfile/systemd unit.

## 4. Components Retained Verbatim (or near-verbatim)

These keep their Hermes shape because they are the reason to fork.

### 4.1 Agent Core

- `agent/conversation_loop.py`
- `agent/prompt_builder.py`, `agent/system_prompt.py`,
  `agent/prompt_caching.py`
- `agent/tool_executor.py`, `agent/tool_guardrails.py`,
  `agent/tool_dispatch_helpers.py`, `agent/tool_result_classification.py`
- `agent/iteration_budget.py`
- `agent/error_classifier.py`, `agent/retry_utils.py`
- `agent/redact.py`, `agent/think_scrubber.py`,
  `agent/message_sanitization.py`
- `agent/curator.py`, `agent/curator_backup.py`,
  `agent/background_review.py`
- `agent/skill_bundles.py`, `agent/skill_commands.py`,
  `agent/skill_preprocessing.py`, `agent/skill_utils.py`
- `agent/context_engine.py`, `agent/context_compressor.py`,
  `agent/conversation_compression.py`, `agent/context_references.py`,
  `agent/manual_compression_feedback.py`
- `agent/memory_manager.py`, `agent/memory_provider.py`,
  `plugins/memory/`
- `agent/insights.py`, `agent/account_usage.py`,
  `agent/usage_pricing.py`, `agent/rate_limit_tracker.py`,
  `agent/nous_rate_guard.py`
- `agent/markdown_tables.py`, `agent/display.py`,
  `agent/title_generator.py`
- `agent/trajectory.py`, `trajectory_compressor.py`,
  `mini_swe_runner.py`

### 4.2 Persistence and Recall

- `hermes_state.py` with `state.db` as the canonical store.
- Per-session JSON snapshot writer (already opt-in upstream).
- FTS5 session search and LLM-summarized cross-session recall.
- Honcho dialectic user modeling (memory provider implementation).
- `gateway/session.py`, `gateway/session_context.py`,
  `gateway/mirror.py`, `gateway/memory_monitor.py`,
  `gateway/shutdown_forensics.py`.

### 4.3 Skills and Plugins (Retained Subset)

The retained skill surface is intentionally broad. The fork removes
platforms (voice, image, video, non-allowlisted chat surfaces) but
**keeps every Hermes skill family that supports the research → spec
→ implement loop** against the SWA + Linux VM API target.

#### Skill domains retained (from upstream `skills/`)

| Domain                  | Why we keep it                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `research/`             | arXiv discovery, literature review, citation handling — the inbound side of the loop.                                     |
| `data-science/`         | Statistical analysis, dataset shaping, plotting — used to evaluate research claims and benchmark our own API.             |
| `software-development/` | Source-code edit, refactor, lint, test patterns — including the **web frontend** skills (HTML/CSS/JS/TS, framework idioms) the SWA needs. |
| `devops/`               | Container builds, systemd, log scraping, deployment helpers, CI patterns — covers both the Linux VM API and the SWA pipeline. |
| `github/`               | PR / issue / release / workflow management — drives the implement half of the loop end-to-end and owns the CICD pipeline definitions. |
| `mcp/`                  | Talking to MCP servers — including the OpenAI and Copilot endpoints that the back-end API exposes.                        |
| `domain/`               | User-defined long-lived domain memories — where the cyberdeck + API + swarm system knowledge lives.                       |
| `note-taking/`          | Research notes, spec drafts, retrospectives.                                                                              |
| `productivity/`         | TODO management, calendar-like reminders for review windows.                                                              |
| `index-cache/`          | Fast file/symbol lookup over the registered monorepo — keeps the dev kit responsive on a 3B model.                        |
| `autonomous-ai-agents/` | Sub-agent orchestration patterns we will reuse in the spec → plan → tasks → implement flow and across the Tailscale swarm. |
| `dogfood/`              | Self-improvement tasks the curator can replay against hermes-lite itself.                                                 |
| `security/` (and any `red-team/` / `pentest/` subtrees) | Threat modeling, secure coding review, dependency auditing, secrets scanning, and **active pentest** patterns against the agent's own deployed API and SWA. This domain is **non-negotiable** because the agent ships code that it then calls. |

#### Skill families added by hermes-lite

- `skills/research/arxiv/` — the arXiv research bundle (§5.4).
- `skills/development/spec-kit/` — spec → plan → tasks → implement
  bundle (§5.10).
- `skills/devops/azure-ops/` — Azure CLI, Bicep, Static Web App and
  Linux VM API deploys (§5.11).
- `skills/software-development/web-frontend/` — opinionated frontend
  patterns for the SWA target (routing, layout, deploy config).
- `skills/devops/linux-vm-api/` — operate the Linux VM back-end:
  systemd unit, reverse proxy, TLS, log rotation, API key rotation.
- `skills/devops/networking/` — DNS, firewall, egress allowlist, port
  forwarding, certificate management, and **Tailscale mesh** setup so
  the cyberdeck can join a swarm later — the connective tissue
  between the SWA, the VM, the OpenAI/Copilot API providers, and
  other devices in the mesh.
- `skills/security/red-team/` — self-pentest skills for the deployed
  SWA + VM API: web-app fuzzing harness, auth bypass checks, CORS
  and CSP review, rate-limit probing, dependency CVE scanning, and
  basic infra recon against our own surface (§5.12).

#### Plugins retained

- `plugins/browser/` — used by arXiv fetch and by web-frontend smoke
  checks against the deployed SWA.
- `plugins/context_engine/` — context shaping and compression.
- `plugins/kanban/` — task board + worktree orchestration; the
  spec-kit bundle and `LocalRepoWorkspace` both delegate to it for
  parallel work.
- `plugins/memory/` — per-profile memory namespaces (§5.7).
- `plugins/observability/langfuse/` (optional) — trace inspection for
  hard prompts.
- `plugins/web/` reduced to the **web search provider** components
  only (xAI removed, retain open providers compatible with our
  allowlist) — used by both research and dev kits for lookups.
- `plugins/github/` (if present upstream as a standalone plugin) —
  PR / issue / workflow helpers used by spec-kit's implement step.
- `plugins/mcp/` (or equivalent MCP client surface) — calling MCP
  servers, including the one the back-end API exposes for OpenAI and
  Copilot.

#### Plugin platform features kept intact

- `ctx.llm`, `apply_yaml_config_fn`, dynamic `sys.modules`
  registration. New plugins under §5.9, §5.10, §5.11 all use these
  hooks rather than forking the core loop.

### 4.4 Scheduling and Long-Running

- `cron/` retained, with Linux-only paths (drop Windows subprocess
  console hiding code).
- Per-session JSON snapshot writer.
- Subagent / `mini_swe_runner.py` retained.

## 5. New Components Introduced by the Fork

### 5.1 `hermes-lite` Profile

A new top-level YAML profile, e.g. `lite-config.yaml`, that:

- pins the default model to `ollama:ministral-3:3b`;
- pins escalation order: `ollama` → `copilot` → `openai` → `claude`;
- declares `enabled_gateways: [discord, openwebui, tui]` — Discord
  is the stable remote source; Open WebUI (SWA-backed) is the
  experimentation endpoint; the TUI is always-on locally;
- caps iteration budget to 25 (vs. 50+ default) and sets a per-kit
  tool-call-failure budget of 3 before forced escalation (§12.1);
- enables byte-stable prompt prefix caching by default;
- enables per-session JSON snapshots by default;
- runs the curator and background reviewer in **deferred-queue
  mode** (§12.2): each loop tick enqueues curator/reviewer jobs
  into `~/.hermes-lite/queue/curator.jsonl` instead of executing
  them inline. A configurable threshold (default: 25 enqueued jobs
  or 4 hours of accumulated work) triggers the agent to ask the
  user, in the originating gateway, to authorize a batched curator
  pass;
- disables image, video, voice, and all dropped providers at config
  load (fail-closed) so a stray skill cannot re-enable them.

### 5.2 `agent/ollama_adapter.py` (New)

A tight Ollama adapter that:

- speaks the `/api/chat` and `/api/generate` endpoints directly;
- supports function-calling via JSON-schema prompts that are
  pre-validated against the active toolset;
- exposes a token-budget estimator that uses `tiktoken` heuristics
  for small models;
- streams reasoning + tool-call deltas through Hermes' existing
  `agent/stream_diag.py` plumbing.

### 5.3 Open WebUI Gateway

A `gateway/platforms/openwebui/` package that:

- registers as an Open WebUI pipeline ("Hermes-Lite") so any browser
  with access to the VM can chat with the agent;
- maps Open WebUI conversation IDs to hermes session IDs in
  `state.db`;
- enforces an allowlist of Open WebUI users;
- streams responses with markdown tables, code blocks, and citation
  references (especially arXiv IDs).

### 5.4 arXiv Research Skill Bundle

A new skill bundle under `skills/research/arxiv/` and a manifest
entry that exposes `/arxiv` as a single slash command. The bundle
loads, in order:

1. `arxiv-discover` — query arXiv (and optionally OpenAlex /
   Semantic Scholar) for candidate papers. The arXiv API client
   enforces a **strict 1 request per 3 seconds** rate limit with
   jittered backoff, a 1000-results-per-day soft cap, and a
   `User-Agent` that identifies the cyberdeck plus a contact
   address. Hits are cached aggressively; a repeat query within
   24 hours never re-hits the wire.
2. `arxiv-fetch` — fetch PDFs / HTML, persist under
   `~/repos/knowledge/papers/<arxiv-id>/` (note: under the
   **knowledge repo** — see §5.13 — not `~/.hermes-lite/`),
   extract metadata.
3. `arxiv-skim` — produce a stable section-by-section skim with
   page-aware citations.
4. `arxiv-extract` — pull claims, methods, datasets, and results
   into structured JSON (`extract.json` next to the paper).
5. `arxiv-compare` — generate a comparison table across the active
   reading list, with cross-references stored in memory.
6. `arxiv-write` — produce a research note with citations resolved
   against the local paper store. The note is written into the
   **knowledge repo** (`~/repos/knowledge/notes/<topic>.md`) so it
   can be
   shared, reviewed by others, and version-controlled
   independently of the `blue-swallow-society` and `hermes-lite` codebases.

The bundle is designed so each constituent skill fits into a 3B
context window on its own, and the orchestration is sequential
rather than tool-call-heavy. The knowledge repo is registered as a
workspace alongside `blue-swallow-society` and `hermes-lite`, so `arxiv-write`
commits notes
through the same `workspace.*` write path and the same audit log.

### 5.5 Small-Model System Prompt Profile

A new system-prompt profile keyed in
`agent/system_prompt.py` for "small models" that:

- removes verbose tool-use preamble;
- removes irrelevant platform-specific guidance (Telegram, etc.);
- limits the active toolset to one **kit** at a time (e.g. arXiv kit,
  dev kit, kanban kit, but never all three);
- shortens role/style language to <300 tokens of system prompt;
- relies on byte-stable prefix caching so the same kit reuses the
  cache between turns.

### 5.6 Tool-Surface Slimmer

A new `agent/tool_surface.py` module that:

- exposes only the tools required by the **active kit** to the model;
- validates tool schemas against a hand-curated allow-list per kit;
- emits a static (cache-friendly) tool schema digest, so prompt cache
  keys remain stable across turns;
- refuses to load any tool that imports a removed provider.

### 5.7 Memory Profiles per Workflow

Reuse `plugins/memory/` profile isolation to give each workflow its
own memory namespace. Each kit binds to one or two profiles so the
active context stays small and stable:

| Profile     | Kit(s) bound                | What lives here                                                                                                                          |
| ----------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `research`  | arxiv                       | Reading list, paper extracts, comparison tables, written notes, open questions. Backed by the `knowledge` repo (§5.13).                  |
| `spec`      | spec-kit                    | Spec proposals (`spec.md`), plans (`plan.md`), task lists (`tasks.md`), constitution, review notes, approvals.                           |
| `dev`       | spec-kit, web-ops, security | Repo conventions, build commands, code-review patterns, lint/test invocations, branch hygiene rules.                                     |
| `web`       | web-ops                     | Frontend conventions for the SWA target (routing, components, styles, deploy config, SWA `staticwebapp.config.json`).                    |
| `azure`     | azure-ops                   | Azure CLI patterns, Bicep modules for SWA + VM, RBAC, key vault references, deploy slots, networking rules.                              |
| `infra`     | azure-ops, dev, security    | Linux VM host knowledge — systemd, reverse proxy (`caddy`/`nginx`), TLS, DNS, firewall, egress allowlist, log rotation, Tailscale mesh. |
| `api`       | dev, web-ops, security      | The OpenAI/Copilot back-end API contract — routes, auth, rate limits, MCP exposure, observability.                                       |
| `security`  | security (write); others read-only | Threat models, findings reports, baselines, scope allowlist, credential rotation history. Only the `/sec` kit may write here.    |

Profile selection is part of the active kit, so loading the arXiv kit
also points memory at `research`; loading the spec-kit points memory
at `spec + dev`; loading azure-ops points memory at `azure + infra`;
loading the security kit points memory at `security` (write) plus
`web + api + infra` (read).

### 5.8 `hermes-lite doctor`

A reduced doctor command that checks only:

- Ollama reachability and model presence;
- OpenAI / Copilot / Claude credentials if configured;
- Discord and Open WebUI bindings;
- TUI client availability;
- `state.db` schema version;
- skills index integrity;
- free disk space in `~/.hermes-lite/`;
- thermal state and `nvpmodel` power mode on Jetson;
- registered local repo workspaces (see §5.9) and their git
  authentication state.

### 5.9 LocalRepoWorkspace Plugin

A new plugin under `plugins/local_repo_workspace/` that mediates every
filesystem and git operation performed against repos cloned on the
device. It is the only sanctioned path for hermes-lite to mutate code
outside `~/.hermes-lite/`.

Responsibilities:

- Maintain a **workspace registry** at
  `~/.hermes-lite/workspaces.yaml` enumerating every repo hermes is
  allowed to touch, each with: id, friendly name, absolute path,
  default branch, allowed branch prefixes, push remote, commit author
  identity, allowed file globs, and required reviewers.
- Provide typed tools (`workspace.list`, `workspace.locate`,
  `workspace.status`, `workspace.diff`, `workspace.apply_patch`,
  `workspace.commit`, `workspace.push`, `workspace.open_pr`) that the
  agent loop can call. Each tool is schema-validated and respects the
  registry constraints.
- Resolve the **active workspace** for a directive by matching the
  directive's natural-language target ("the website repo",
  "my-blog", a URL) against the registry, then asking the user for
  confirmation when there is ambiguity.
- Enforce **branch hygiene** identical to micromanager: never mutate
  `main`/`master` directly; create or reuse a topic branch matching
  the allowed prefix (e.g. `hermes/`, `bot/`).
- Enforce a **change budget**: maximum N files and M lines per
  directive without escalation; exceeding the budget requires a
  second confirmation envelope (see security model in §9).
- Emit a structured **change journal** under
  `~/.hermes-lite/journal/<session-id>/<step>.json` containing the
  unified diff, commit metadata, and any pre/post test output, so the
  curator and background reviewer can audit changes.
- Run a **pre-commit gate**: configured per workspace (e.g.
  `pre-commit run --all-files`, `npm run lint`, `cargo check`,
  `pytest -q`). A failed gate blocks the commit and surfaces the
  failure back to the gateway.
- Use git through `subprocess` with environment scrubbing (no
  inherited `GIT_*` overrides), an SSH agent socket pinned per
  workspace, and `git config` overrides set only on the working copy.

This plugin is the missing link between Discord/Open WebUI/TUI
directives and real on-disk changes.

### 5.10 Spec-Kit Skill Bundle

A new bundle under `skills/development/spec-kit/` that implements
the **spec-driven development** pattern described at
[speckit.org](https://speckit.org) and codified by the upstream
`specify` CLI (https://github.com/github/spec-kit). Hermes-lite
does not depend on the `specify` CLI at runtime — it ships its own
native skills that produce the same artifact shapes (`spec.md`,
`plan.md`, `tasks.md`, `analyze.md`, `checklist.md`, `tests.md`,
constitution) so a standalone Jetson can run the full loop offline
against any registered workspace. Where the spec-kit pattern is
ambiguous, the upstream `specify` CLI's behavior is the reference
implementation.

The bundle exposes a `/spec` slash command and the following
sequential skills (each sized for a 3B model context, each mirroring
the corresponding `specify` CLI command):

1. `spec-constitution` — create or update the workspace's
   `specs/constitution.md` (governing principles, tone, and
   non-negotiables for the spec process). Mirrors
   `specify constitution`.
2. `spec-specify` — turn a research outcome or a free-form ask
   into `specs/<feature>/spec.md`. Pulls citations from the
   `research` memory profile when the input is a research note
   (§5.13). Mirrors `specify specify`.
3. `spec-clarify` — generate up to five targeted clarification
   questions; await the user's answers in the originating gateway;
   write the answers back into `spec.md`. Mirrors
   `specify clarify`.
4. `spec-plan` — produce `plan.md` with architecture, contracts,
   and risks. Reads the `dev`, `web`, `azure`, `infra`, and `api`
   memory profiles as needed. Mirrors `specify plan`.
5. `spec-tasks` — produce a dependency-ordered `tasks.md` keyed
   off `plan.md`. Each task is small enough for one
   `workspace.*` tool chain. Mirrors `specify tasks`.
6. `spec-test` — optional TDD step: emit `tests.md` describing
   the executable requirements derived from `spec.md` and
   `plan.md` before any implementation runs. Mirrors
   `specify test`.
7. `spec-analyze` — non-destructive cross-artifact consistency
   analysis across `spec.md`, `plan.md`, and `tasks.md`. Mirrors
   `specify analyze`.
8. `spec-checklist` — generate a verification checklist for the
   active feature. Mirrors `specify checklist`.
9. `spec-implement` — execute the tasks one-by-one through the
   `LocalRepoWorkspace` tool set; each task closes with a commit
   and the pre-commit gate. Mirrors `specify implement`.
10. `spec-review` — invoke the background reviewer over the diff
    set and surface findings before opening the PR. (No direct
    `specify` CLI equivalent; native to hermes-lite.)

**Hand-off contract.**

- `arxiv-write` (the last arXiv skill) writes a note and, on user
  confirmation, emits a structured `spec-seed.json` containing the
  proposed feature title, summary, problem statement, candidate
  approach, citations, and acceptance criteria draft.
- `spec-specify` reads `spec-seed.json` and produces `spec.md`.
- `spec-implement` reads `tasks.md` and dispatches each task
  through `workspace.apply_patch` / `workspace.commit` /
  `workspace.push` / `workspace.open_pr` (§5.9).

**Approval gates.**

- The transition from `arxiv-write` to `spec-specify` is
  user-confirmed in the originating gateway (Discord / Open WebUI
  / TUI). Hermes never auto-promotes research output into a spec.
- The transition from `spec-tasks` to `spec-implement` is the
  second mandatory approval point. After this point the active
  workspace's `approval_mode` (§9.5) governs each individual write.
- `spec-implement` honors the per-workspace change budget; tasks
  that exceed the budget pause for re-approval the same way as a
  bare `LocalRepoWorkspace` write.

### 5.11 Azure / Web Ops Kits

Two small bundles that wrap the existing Azure and web-frontend
skills into kit-shaped tool surfaces.

**`skills/devops/azure-ops/`** — the operational half:

- `az-login-status`, `az-account-show`, `az-resource-list` —
  read-only inspection of the bound subscription.
- `az-swa-show`, `az-swa-config-update` — Azure Static Web App
  configuration: routes, auth providers, custom domains.
- `az-swa-deploy` — produce a deploy artifact (build output
  uploaded via `swa deploy` or via GitHub Actions reference).
- `az-vm-status`, `az-vm-run-command` — Linux VM operational
  surface; `run-command` is gated by a per-VM allowlist that
  mirrors the LocalRepoWorkspace pattern.
- `bicep-validate`, `bicep-deploy` — Bicep module CRUD for the
  paired SWA + VM topology.
- `keyvault-secret-show` — read-only secret resolution; writes are
  always confirmation-mode.

**`skills/software-development/web-frontend/`** — the build half:

- Framework-aware patterns for the chosen SWA stack (Astro, Next,
  SvelteKit, or static HTML — picked per workspace).
- `staticwebapp.config.json` editing with schema validation.
- Local preview via `swa start` or `npm run dev`, gated to
  `localhost` only by the systemd egress filter.
- Lighthouse-style smoke checks against the deployed SWA URL
  (uses `plugins/browser/`).

**`skills/devops/linux-vm-api/`** — the back-end half (covers both
the OpenAI/Copilot/Claude proxy *and* a self-hosted partner small
model running alongside it on the same VM):

- Manage the systemd unit for the OpenAI/Copilot/Claude proxy API.
- Manage the systemd unit for `ollama serve` running the **partner
  small model** (a separate Ollama instance bound to a private
  interface and reverse-proxied through the API as a first-class
  provider; see “Partner Small Model” below).
- Rotate API keys via the `keyvault-secret-show` skill.
- Edit reverse-proxy config (`caddy`/`nginx`) for the API endpoint,
  including the `/v1/partner/*` route family that fronts the
  partner Ollama.
- Read `journalctl` slices for diagnostics; never tail interactively.
- MCP exposure: validate the API's MCP surface against the
  hermes-lite `mcp/` client skill so the agent's own API consumers
  remain compatible.

**Partner Small Model (deployed on the `blue-swallow-society` VM).** A central
element of the self-enhancement loop: the same VM that hosts the
proxy API also hosts a small Ollama instance running a partner
model (default candidate `qwen3:3b-instruct`, with the same
alternatives matrix as §12.1). The partner model is exposed
through the developer-owned API at `/v1/partner/chat/completions`
and `/v1/partner/embeddings`, and it is registered in hermes-lite
as a remote LM provider through the existing OpenAI-compatible
adapter pointed at that endpoint.

The partner model exists for three concrete reasons:

1. **Rate-limit-free experimentation.** API-driven skill changes
   (new endpoints, new auth flows, new routing rules) can be
   exercised against the partner model without burning paid
   OpenAI / Copilot / Claude quota. The escalation chain still
   ends in the paid providers, but day-to-day iteration uses the
   partner.
2. **Network-loop validation.** Calling the partner exercises the
   full network path (cyberdeck → Tailscale or public TLS → VM
   reverse proxy → API → partner Ollama) on every loop, so
   regressions in TLS, auth, or rate-limit middleware surface
   immediately rather than the next time a paid call goes out.
3. **Cyberdeck-mirrors-cloud parity.** The partner model on the VM
   uses the same Ollama adapter, the same JSON-schema tool-call
   validation, and the same per-kit failure budget as the local
   Ollama on the Jetson. A skill that works against local Ollama
   on the cyberdeck is expected to work against partner Ollama on
   the VM and vice versa; divergence is a bug.

The partner model's VM is sized small (a single Standard_D2as_v5
or similar burstable shape with one CPU-only quantized 3B model is
adequate for development); the GPU is **not** a requirement at
this stage. Routine model swaps on the partner are themselves a
spec → plan → tasks → PR cycle against `blue-swallow-society`'s `infra/`
modules.

These three bundles, combined with `LocalRepoWorkspace` (§5.9) and
the spec-kit (§5.10), are what lets hermes-lite own both halves of
the SWA + Linux VM API target end-to-end — and the partner small
model is what makes the self-enhancement loop continuous instead
of quota-gated.

### 5.12 Security & Red-Team Ops Kit

A new bundle under `skills/security/red-team/` plus a small
complementary `skills/security/blue-team/` subtree. The agent ships
code it then calls itself; without an internal pentest discipline,
the loop will eventually compromise its own host.

The kit exposes a `/sec` slash command and the following sequential
skills (each sized for a 3B model context, all targeting **only the
agent's own deployed surface**):

1. `sec-threat-model` — produce or refresh a STRIDE-style threat
   model for the SWA + VM API + Bicep stack, persisted under the
   monorepo (`security/threat-model.md`) and bound to the
   `security` memory profile.
2. `sec-static-scan` — run `ripgrep`-based secret scanning,
   dependency CVE scanning (`pip-audit`, `npm audit`, `cargo audit`,
   `gh advisory` lookups), and a Bicep linter pass over the monorepo.
3. `sec-config-review` — review `staticwebapp.config.json`, CORS
   rules, CSP headers, reverse-proxy config, systemd hardening,
   Tailscale ACLs, and Key Vault access policies against a stored
   baseline.
4. `sec-auth-probe` — active checks against the deployed API:
   missing-auth requests, expired-token replay, role escalation
   attempts, and CORS pre-flight abuse. Results are captured as
   structured findings.
5. `sec-web-probe` — active checks against the deployed SWA:
   directory listing, broken-link sweep, mixed-content detection,
   open-redirect attempts, and cookie-attribute review. Runs through
   `plugins/browser/` so the same surface used for smoke checks
   handles the probes.
6. `sec-rate-limit-probe` — controlled rate-limit and burst testing
   against allowlisted endpoints, with explicit budgets so the probe
   never DOSes the live service.
7. `sec-fuzz` — schema-driven fuzzing of the API request bodies,
   constrained to a fixed iteration budget and a recorded corpus.
8. `sec-findings-write` — write a findings report under
   `security/findings/<date>-<topic>.md` in the monorepo, with
   reproduction steps, severity, and a recommended fix; emits a
   structured `spec-seed.json` so the spec-kit can take the finding
   into the implement loop (§5.10).
9. `sec-rotate-credentials` — rotate API keys, SSH keys, and
   Tailscale auth keys; updates Key Vault and the systemd unit's
   environment file; never logs the new secrets.

**Approval and blast-radius rules.**

- Every active probe (steps 4–7) requires the workspace
  `approval_mode` to be at least `confirm` and runs **only against
  the registered, owned hostnames** declared in
  `~/.hermes-lite/security-scope.yaml`. The egress filter (§7.3)
  blocks the probes from reaching any other host.
- Probes are **rate-limited at the agent layer** in addition to
  whatever the target enforces, so a misconfigured probe cannot
  flood the API.
- `sec-rotate-credentials` is `approval_mode: confirm` everywhere,
  even if the workspace default is `auto`.
- Findings never get auto-fixed; they always feed the spec-kit so
  the fix lands as a tracked spec + plan + tasks + PR (§10).
- The `security` memory profile is **read-only to all other kits**;
  only the security kit may write to it. This prevents a research
  prompt from contaminating the threat model.

**Why this is non-negotiable.** Hermes-lite writes code, opens PRs,
lets CICD deploy, and then calls the resulting API as a remote LM
provider. Without a self-pentest discipline, the agent could (a)
introduce a vulnerability and then exfiltrate state through the
vulnerability it just introduced, and (b) leak personally-owned
API keys to the public internet through a misconfigured SWA route.
The `/sec` kit closes that gap.

### 5.13 Knowledge Corpora and the Knowledge Repo

Hermes-lite separates **codebase artifacts** from **shared
research artifacts** so the knowledge record can evolve
independently of any product repo and can be pulled, shared, and
rebased by other developers and other cyberdecks across the
Tailscale swarm:

- **Knowledge repo** (`~/repos/knowledge`): a dedicated Git repo,
  registered in `~/.hermes-lite/workspaces.yaml` as one of the
  three first-class repos owned by hermes-lite (alongside
  `blue-swallow-society` and the `hermes-lite` source fork; see §1 premise
  6), `approval_mode: pr-only` for shared collaboration (or `auto`
  for trusted single-user use), organized as:
  - `papers/<arxiv-id>/` — cached PDFs, HTML, and extracted
    metadata. Files are content-addressed; the same `<arxiv-id>`
    is never re-downloaded.
  - `notes/<topic>.md` — long-form notes produced by
    `arxiv-write`.
  - `extracts/<arxiv-id>.json` — structured extracts.
  - `seeds/<feature>.json` — `spec-seed.json` envelopes queued
    for the spec-kit. The spec-kit consumes seeds from this
    directory and links back to the originating notes.
  - `index/` — FTS5 sidecar index over notes and extracts for
    quick recall, regenerated by a cron-driven skill.
  The knowledge repo is intended to be shared with collaborators
  (other developers, other cyberdecks across the Tailscale swarm)
  and rebased onto its own `main` independently of `blue-swallow-society`
  and `hermes-lite`. It is the persistent, portable research
  product of the cyberdeck.
- **Wikipedia corpus** (`~/.hermes-lite/corpora/wikipedia/`): a
  text-only mirror of English Wikipedia (current dump, ~110 GB on
  disk after extraction; or a smaller 25 GB "vital articles" subset
  if storage budget is tight). The corpus is exposed via a
  read-only skill `corpus-wiki-lookup` that wraps a local FTS5
  index over the dump. It is the **ground-truth fallback** for
  factual lookups when no arXiv paper is on hand and the cyberdeck
  is offline. Hermes-lite never writes to the corpus; refresh is a
  manual `pull-wikipedia.sh` invocation captured in `cron/`.
- **Skill index sidecars** (`~/.hermes-lite/index/`): the upstream
  Hermes FTS5 indexes over `state.db` plus a new index over the
  knowledge repo (`~/repos/knowledge/index/`), accessed through a
  single `corpus-recall` skill so the model sees one consistent
  retrieval surface across personal recall, knowledge-repo notes,
  and Wikipedia ground truth.

Disk allocation on the 512 GB microSD card is captured in §7.4.

### 5.14 Diagnostic Logging and Self-Improvement Signals

Diagnostic logging is **first-class infrastructure**, not an
afterthought. The self-enhancement loop (§10) is only as good as
the signal it can mine from prior runs: which kit was active,
which tool calls succeeded, which failed and why, where the model
escalated, how the curator and reviewer judged a session, and how
the deployed API behaved when the agent called it back. Hermes-lite
retains every upstream logging surface that already exists and adds
a small, opinionated diagnostics layer on top.

**Retained from upstream Hermes.**

- `state.db` SQLite store \u2014 the canonical session, tool-call, and
  recall record. Already FTS5-indexed; the new diagnostics layer
  rides on it rather than creating a parallel database.
- Trajectory capture under `~/.hermes-lite/trajectories/` \u2014 every
  session is serialized turn-by-turn for later replay, distillation,
  and curator review.
- Per-session JSON snapshots \u2014 a session-level mirror of the same
  data, easier to diff and ship to collaborators.
- Curator and background-reviewer outputs \u2014 already structured;
  now queue-backed (\u00a712.2) so each reviewer pass leaves an audit
  trail in `~/.hermes-lite/queue/`.
- `journalctl` records for the hermes-lite systemd unit \u2014 OS-level
  process events, restart counts, OOM notices.\n- Insights / usage / rate-limit / pricing modules in `agent/` \u2014\n  retained verbatim and reused by the partner-model adapter so the\n  cyberdeck and the VM partner share one cost-and-quota view.\n\n**Added by hermes-lite.**\n\n- **`agent/diagnostics.py`** \u2014 a single structured logger that\n  emits newline-delimited JSON to `~/.hermes-lite/logs/`. Every\n  log line carries: `ts`, `session_id`, `kit`, `skill`, `provider`,\n  `model`, `workspace`, `gateway`, `event`, `latency_ms`, plus\n  event-specific payload. Stable schema so downstream analysis is\n  cheap.\n- **Log streams**, each in its own newline-delimited JSON file with\n  daily rotation and a 90-day retention window:\n  - `logs/agent.jsonl` \u2014 loop ticks, kit loads and unloads, memory\n    profile switches, iteration counts.\n  - `logs/tools.jsonl` \u2014 every tool call with schema validation\n    result, latency, and outcome (success / parse-fail / semantic-\n    fail / refusal / timeout).\n  - `logs/providers.jsonl` \u2014 every LM call: provider, model,\n    request size, response size, latency, cost (when known),\n    cache-hit indicator, and which provider in the escalation\n    chain answered.\n  - `logs/workspace.jsonl` \u2014 every `workspace.*` call: target\n    repo, files touched, byte delta, change-budget remaining,\n    pre-commit gate result, commit SHA.\n  - `logs/security.jsonl` \u2014 every `/sec` probe and finding; this\n    stream is `mode 0600` and rotates separately so it can be\n    archived without leaking into shared diagnostic dumps.\n  - `logs/thermal.jsonl` \u2014 5-second `tegrastats` samples: CPU\n    temp, GPU temp, current `nvpmodel` mode, throttling flags.\n  - `logs/api.jsonl` \u2014 calls hermes-lite makes to its own\n    deployed `blue-swallow-society` endpoint (including the partner small\n    model): request id, route, status, latency, partner-vs-paid\n    routing decision, and self-pentest probe results.\n- **`hermes-lite diagnostics` CLI** with three subcommands:\n  - `tail <stream>` \u2014 live-follow a stream with structured\n    filtering (`--kit`, `--provider`, `--workspace`).\n  - `summarize --since <duration>` \u2014 generate a Markdown digest\n    of the last *N* hours grouped by kit, provider, and outcome\n    class; suitable for pasting into a self-improvement spec seed.\n  - `export --to ~/repos/knowledge/diagnostics/<date>.jsonl.gz` \u2014\n  redacted export for sharing with the swarm or a collaborator.\n    Redaction strips prompts, full tool arguments, and any field\n    matching the security-kit redaction rules.\n\n**Self-improvement signals derived from logs.** The curator and\nthe spec-kit treat the diagnostic streams as a primary source:\n\n1. **Tool-call failure clustering.** The curator scans\n   `logs/tools.jsonl` for repeated `parse-fail` or `semantic-fail`\n   events on the same skill, then proposes prompt or schema\n   tightenings as `spec-seed.json` envelopes against the\n   `hermes-lite` repo.\n2. **Escalation patterns.** `logs/providers.jsonl` reveals which\n   skills routinely escalate from the local 3B model to the\n   partner model or to paid providers; the curator suggests model\n   swaps, better few-shot examples, or skill restructuring.\n3. **Latency hotspots.** Per-kit latency percentiles produced by\n   `summarize` feed plan-level decisions about which skills are\n   worth caching, batching, or running on the partner model.\n4. **Workspace blast-radius monitoring.** `logs/workspace.jsonl`\n   makes oversized commits visible at a glance; the security kit\n   uses it as an additional input to the pre-PR review.\n5. **Thermal-driven plan adjustments.** Sustained throttling in\n   `logs/thermal.jsonl` is surfaced by the watchdog (\u00a712.8) as a\n   curator prompt to reconsider chunk sizes or model choice.\n6. **API drift detection.** `logs/api.jsonl` records the\n   contract-versus-actual shape of every self-call; mismatches\n   feed `sec-config-review` and trigger a re-run of `sec-auth-probe`\n   before the next loop iteration is allowed to use the endpoint.\n\n**Retention and privacy.**\n\n- Default retention: 90 days for `agent`, `tools`, `providers`,\n  `workspace`, `thermal`, `api`; 365 days for `security`.\n- All streams support `redact` rules in `lite-config.yaml`; the\n  default rules cover OpenAI/Anthropic API keys, JWTs, GitHub\n  PATs, Tailscale auth keys, and any value bound to the `security`\n  memory profile.\n- Exports to the knowledge repo or to other cyberdecks go through\n  the redaction pipeline before they leave the device.\n\n**Operational knobs.** `lite-config.yaml` keys:\n`diagnostics.enabled` (default `true`),\n`diagnostics.streams.*.retention_days`,\n`diagnostics.streams.*.redact_rules`,\n`diagnostics.export.knowledge_repo_path`,\n`diagnostics.cli.default_summary_window`.

## 6. Removed Surface — Quick Reference

| Removed | Why |
| ------- | --- |
| Telegram / Slack / WhatsApp / Signal / Email / Yuanbao / Weixin gateways | Out of scope; reduce auth and dep surface |
| Bundled web dashboard and web UI plugins | Open WebUI covers browser usage |
| Voice/TTS, image gen, video gen | Heavy deps, irrelevant for research/dev |
| All non-allowlisted LM providers | Reduce dep surface and security review |
| Apple, Gaming, GIFs, Social-media, Smart-home, Creative skills | Not research/dev |
| Spotify, Google Meet, Achievements, Teams pipeline plugins | Not research/dev |
| Atropos RL, Tinker integration | Removed upstream already |
| Windows-only code paths (MinGit, UTF-8 stdio shim, Camofox) | Linux/Jetson-only |
| `--yolo` flag default | Stays opt-in; default is "approve sensitive tool calls" |

Note: the **TUI is retained** for local sessions on the Jetson (HDMI
or SSH), so `tui_gateway/` and `ui-tui/` stay in the tree.

This removes a large fraction of `pyproject.toml` extras and lets the
installed wheel ship a much smaller dependency tree.

## 7. Packaging and Deploy

### 7.1 Repo Layout

Keep the upstream tree (so we can rebase from `main` cleanly), and add:

```
hermes-lite/
  README.md
  lite-config.yaml
  Dockerfile.lite
  systemd/hermes-lite.service
  scripts/
    install.sh                  # Linux-only installer
    bootstrap-ollama.sh
    pull-ministral-3.sh
  agent/
    ollama_adapter.py
    tool_surface.py
  gateway/platforms/openwebui/
  skills/research/arxiv/
  tests/lite/
```

`scripts/install.sh` does the equivalent of upstream's `setup-hermes.sh`
but only installs the lite extras, skipping every removed provider and
gateway.

### 7.2 Container

A `Dockerfile.lite` based on `python:3.11-slim` that installs:

- the lite extras of the pinned wheel;
- `ripgrep` (required for skill index, `@folder` references);
- `ffmpeg` only if voice is enabled (default off);
- nothing else.

Image target: **<350 MB** uncompressed. The Ollama daemon runs on the
host or in a sibling container.

### 7.3 systemd Service

A `hermes-lite.service` unit runs `hermes gateway` with the
`lite-config.yaml` profile. The unit:

- pins memory with `MemoryHigh=4G`, `MemoryMax=5.5G` (sized for the
  Jetson Orin Nano 8 GB unified pool minus Ollama's working set);
- isolates filesystem with `ProtectHome=tmpfs` plus
  `ReadWritePaths=~/.hermes-lite ~/repos`, so only registered repo
  workspaces under `~/repos/` and the agent's own state directory are
  writable;
- denies network egress except for Ollama, OpenAI, Copilot, Claude,
  arXiv, OpenAlex, Discord, the Open WebUI host, GitHub (HTTPS + SSH
  for git push), and any additional git remotes declared in
  `workspaces.yaml`;
- restarts on failure with a 30s backoff;
- logs to journald.

### 7.4 Resource Budget (Jetson Orin Nano 8 GB)

Unified memory means CPU and GPU draw from the same 8 GB pool. The
model runs through Ollama with CUDA, so its working set lives in the
shared region. The budget is sized slightly higher than a generic
8 GB VM because we now keep the TUI active and we expect the GPU to
stage prompt + KV-cache buffers in unified memory.

| Component | Budget |
| --------- | ------ |
| Hermes-lite Python process | ~750 MB resident |
| TUI client (local SSH or HDMI session) | ~150 MB when attached, ~0 idle |
| Ollama daemon (idle) | ~180 MB |
| Ollama model + KV cache (Ministral-3 3B Q4, ctx ≤8k) | ~3.0 GB while active |
| state.db + FTS5 + trajectory + paper cache | <1.5 GB resident working set |
| Discord + Open WebUI clients | <150 MB combined |
| JetPack OS, journald, networking | ~1.0 GB |
| Headroom for spikes (skim/extract bursts) | ~0.5 GB |
| **Total target** | **≤7.2 GB on the 8 GB Jetson, no swap** |

Swap is configured but treated as a safety net, not a working
surface. If the watchdog observes swap-in > 50 MB sustained, it
downgrades model size or unloads non-active kits.

#### Disk budget (512 GB microSD)

| Slice | Budget |
| ----- | ------ |
| JetPack OS, Docker, system | ~40 GB |
| Ollama model store (3–5 quantized models, ~3 GB each) | ~20 GB |
| `~/.hermes-lite/` (state.db, FTS5 indexes, trajectories, queue, sessions, diagnostic logs) | ~30 GB |
| Wikipedia corpus (full English text dump, FTS5 sidecar) | ~120 GB |
| Knowledge repo (`~/repos/knowledge`: cached papers, notes, extracts, seeds) | ~60 GB |
| `blue-swallow-society` repo (`~/repos/blue-swallow-society`: infra/web/api/specs/security) | ~10 GB |
| `hermes-lite` repo (`~/repos/hermes-lite`: the fork itself) | ~5 GB |
| Logs, journald, system caches | ~10 GB |
| Headroom (snapshots, scratch, model swaps) | ~215 GB |
| **Total target** | **≤512 GB on the microSD card** |

The Wikipedia and knowledge-repo slices are the dominant non-system
consumers and are sized so a developer can do offline research for
months between syncs.

## 8. arXiv Research Agent — Concrete Flow

Once the fork lands, the canonical arXiv research session looks like:

1. User joins the Discord allowlisted channel (or opens Open WebUI).
2. User issues `/arxiv "small language model alignment 2026"`.
3. The orchestrator loads the **arXiv kit** (sole active kit) and
   the `research` memory profile.
4. `arxiv-discover` queries arXiv + OpenAlex, dedupes against the
   local store, and posts a candidate list.
5. The user picks a subset.
6. `arxiv-fetch` downloads PDFs to `~/.hermes-lite/papers/<id>/`.
7. `arxiv-skim` runs the 3B model section-by-section over a long
   paper, never loading the full paper into context.
8. `arxiv-extract` writes `extract.json` per paper.
9. `arxiv-compare` cross-references extracts and posts a comparison
   table to the same channel.
10. `arxiv-write` drafts a note in `~/.hermes-lite/notes/` with
    citations resolved to local PDFs, and — if the user replies
    with `/spec` or "propose a spec from this" — emits a
    `spec-seed.json` envelope describing a candidate feature, its
    citations, and a draft acceptance-criteria list.
11. The curator proposes (does not commit) skill improvements based on
    what the agent struggled with.
12. The background reviewer critiques the draft and posts findings.
13. Trajectory capture writes the session to
    `~/.hermes-lite/trajectories/<session-id>.jsonl` for future model
    distillation experiments.
14. **Hand-off.** If `spec-seed.json` was emitted, the orchestrator
    unloads the arXiv kit and loads the **spec-kit** (§5.10) against
    the registered workspace the user names. The arXiv kit is done;
    the loop continues in §10.

Every step is sized for a 3B model: each skill is a single,
narrowly-scoped operation with a fixed toolset, and the orchestrator
keeps only the active skill's prompt in context.

## 9. Local Repo Modification from Gateway Directives

This section answers the user's concrete question:

> Suppose I send a Discord message asking hermes to update the
> homepage of a website whose repo is checked out on the same box.
> Can hermes-lite identify the repo, make changes, commit, push, and
> report back in Discord?

Yes. Below is the design that makes it safe and predictable.

### 9.1 Why Hermes Already Gets You Most of the Way

Hermes' built-in tool surface includes file read/write and shell
execution. The agent loop, tool guardrails
(`agent/tool_guardrails.py`), file safety helpers
(`agent/file_safety.py`), and command-allowlist machinery from
OpenClaw migration are all already in the tree. The fork's job is
not to invent file-mutation; it is to **scope** file-mutation to a
registry of approved local repos and to enforce a sane approval
workflow before commits are pushed.

The `plugins/kanban/` plugin already demonstrates worker tools and
worktree-based branch routing. The `software-development/` and
`devops/` skills already include code-edit, lint, and test patterns.
The new `LocalRepoWorkspace` plugin (§5.9) wires those primitives
to the gateway-directed flow.

### 9.2 End-to-End Discord Flow

Assume the website repo is checked out at `~/repos/my-blog`, the
default branch is `main`, and the workspace is registered as
`my-blog` in `~/.hermes-lite/workspaces.yaml`.

1. **Discord message.** The user posts in an allowlisted channel:
   "Update the homepage hero copy on my-blog to say `Now writing
   about Jetson agents`. Open a PR."
2. **Gateway intake.** The Discord gateway routes the message into
   the agent loop, attaching the channel/user as the session origin.
3. **Kit selection.** The orchestrator detects intent
   ("update ... repo ... open a PR") and loads the **dev kit** plus
   the **`my-blog` workspace**. The arXiv kit is unloaded if active.
4. **Workspace resolution.** `workspace.locate("my-blog")` returns
   the absolute path and metadata from the registry. If the name is
   ambiguous, hermes replies in Discord with candidates and waits
   for a pick.
5. **Branch hygiene.** `workspace.status` confirms a clean tree;
   `workspace.checkout` creates `hermes/update-hero-copy` off `main`
   (the allowed prefix is set in the registry).
6. **Targeted read.** The agent reads only the file paths declared
   in the workspace's allowed globs (e.g. `src/pages/index.*`,
   `content/home/*.md`), keeping the model's context small.
7. **Edit.** The agent proposes a patch via `workspace.apply_patch`.
   Patches are unified diffs; the tool validates the patch applies
   cleanly and runs the workspace's pre-commit gate
   (`npm run lint && npm test` for a static-site repo, configurable).
8. **Approval.** Because "open a PR" was an explicit directive, the
   change passes the change-budget check (e.g. ≤2 files, ≤30 lines).
   If the budget is exceeded, hermes replies in Discord with the
   diff and waits for an explicit "approved" reply.
9. **Commit.** `workspace.commit` writes a commit with a
   schema-validated message:

   ```text
   feat(home): update hero copy

   Source: discord/<channel-id>/<message-id>
   Session: <hermes-session-id>
   Author-Identity: <configured commit author>
   ```
10. **Push.** `workspace.push` pushes the topic branch to the remote
    using the SSH agent socket configured for the workspace. The
    network egress filter only allows the registered remote.
11. **PR.** `workspace.open_pr` opens the PR using the GitHub CLI
    (or REST) with a body that links back to the originating Discord
    message and includes the diff summary.
12. **Reply.** The Discord gateway streams a final message back into
    the channel:

    ```text
    ✅ Branch hermes/update-hero-copy pushed to origin.
    PR #123: https://github.com/<owner>/my-blog/pull/123
    Files changed: src/pages/index.astro (+1 / -1)
    Lint: pass  Test: pass
    ```
13. **Journal & memory.** The change journal under
    `~/.hermes-lite/journal/<session-id>/` and the `dev` memory
    profile both record the change so future sessions know the repo
    has an open PR.

### 9.3 How Hermes Identifies the Right Repo

Identification is registry-first, never path-guessing:

- **Primary**: lookup by friendly name in `workspaces.yaml`.
- **Secondary**: fuzzy match against `friendly_name`, `git remote
  url`, and the basename of `path`. A confidence below the cutoff
  forces a clarification reply in Discord.
- **Tertiary**: if the directive mentions a directory under
  `~/repos/`, hermes checks if it appears in the registry. If not,
  hermes refuses and instead replies with the steps to register the
  workspace (it never silently writes to an unregistered repo).

The registry is editable from the TUI via
`hermes-lite workspace add` (a thin wrapper around the plugin) and
requires the user to set the allowed branch prefix, allowed file
globs, change budget, and pre-commit gate up front.

### 9.4 Security Model

| Concern | Mitigation |
| ------- | ---------- |
| Untrusted Discord users | Per-user allowlist in `lite-config.yaml`; non-allowlisted users can converse but cannot trigger `workspace.*` tools |
| Path traversal | All tool inputs are normalized and resolved against the workspace root; symlink escapes are rejected |
| Branch sabotage | Default and protected branches are read-only via tool contract; the registry's `allowed_branch_prefixes` is enforced before any write |
| Force-push and history rewrite | Disabled; `workspace.push` does not pass `--force` and never invokes `git reset --hard origin/<branch>` |
| Credential exfiltration | Git executes with a scrubbed environment; SSH agent socket is bound per workspace; secrets never enter the model context (redaction layer + `agent/redact.py`) |
| Excess change | Per-directive change budget (files/lines) with explicit second-confirmation envelope for overage |
| Bypass via shell | The bare `runInTerminal` tool is gated by `agent/tool_guardrails.py`; in the dev kit, it is restricted to a per-workspace allowlist of binaries (`git`, `node`, `npm`, `pnpm`, `pytest`, `pre-commit`, `cargo`, `make`, ...) |
| Pushing to wrong remote | Egress filter (§7.3) only allows registered remotes; the push tool also verifies `git remote get-url` matches the registry |
| Audit | Every mutation produces an entry in the change journal and in `state.db`; the curator and background reviewer can replay |

The net effect is that hermes-lite has **opt-in, registry-bounded
write access** to a fixed set of repos, with all other paths read-only
or inaccessible.

### 9.5 Approval Modes

The registry's `approval_mode` per workspace controls how much
autonomy the agent has:

- `auto`: small changes (within budget) commit and push without
  asking. Used for `README` typos, lint fixes, etc.
- `confirm`: every change waits for an explicit "approved" reply on
  the originating gateway (Discord, TUI, Open WebUI).
- `pr-only`: hermes may commit and push to topic branches but never
  merges to `main`; a PR is always opened.
- `read-only`: hermes may read the repo for context but cannot write
  to it.

The default for new workspaces is `pr-only`. `auto` requires explicit
opt-in plus a tighter change budget.

### 9.6 Concurrency and Worktrees

For parallel work, hermes-lite reuses the kanban plugin's worktree
behavior. Each long-running directive (`/repo work-on <task>`) gets
its own worktree under `~/.hermes-lite/worktrees/<workspace>/<id>/`
rather than mutating the live checkout. Worktree creation, branch
routing, and cleanup are owned by the kanban plugin; the
`LocalRepoWorkspace` plugin just delegates to it when the directive
requests an isolated change set.

### 9.7 Failure Handling

- **Patch fails to apply.** Hermes reports the rejected hunks back
  to Discord and does not commit. It may attempt a model-driven
  retry with a tighter prompt, capped by the iteration budget.
- **Pre-commit gate fails.** Hermes reports the failing tool output
  (truncated) and waits for either a fix-it directive or a
  cancellation.
- **Push rejected.** Hermes pulls with rebase, attempts to replay
  the commit, and reports the result. If the rebase has conflicts,
  hermes stops and asks for direction.
- **Network egress denied.** Hermes detects the systemd egress
  rejection, surfaces a clear error, and pauses.
- **Model hallucinates a path.** The `LocalRepoWorkspace` tool
  rejects writes to unknown paths before the model can chain
  follow-up operations.

### 9.8 What This Adds to the Phased Plan

The `LocalRepoWorkspace` plugin slots into Phase 2 (Additions)
alongside the gateway work. The minimum tool set ships there; the
approval-mode polish and worktree integration extend into Phase 4
(Hardening). No new phase is required.

## 10. Research → Spec → Implement → Deploy → Self-Enhance Loop

arXiv research (§8) is the inbound proof-of-concept; local-repo
modification (§9) is the outbound mechanism; the spec-kit bundle
(§5.10) is the bridge; CICD is the deploy boundary for `blue-swallow-society`;
the **partner small model on the Azure VM** (§5.11) is the
rate-limit-free experimentation target; and the freshly-deployed
endpoints are what make the loop reflexive. End-to-end, hermes-lite
drives the following flow across **three registered repos**—
with the **Azure Static Web App front-end + Linux VM API back-end**
target as the worked example for the `blue-swallow-society` repo.

### 10.1 Target Topology — Three Repos and a Partner Model

Hermes-lite owns three first-class git repos on the cyberdeck,
each registered in `~/.hermes-lite/workspaces.yaml` and each
governed by its own approval mode, branch prefix, and change
budget. CICD scope is intentionally narrow: only `blue-swallow-society` has
a deploy pipeline, because only `blue-swallow-society` ships running cloud
resources.

**Repo 1 — `blue-swallow-society`** (`~/repos/blue-swallow-society`, workspace name
`blue-swallow-society`, `approval_mode: pr-only`, branch prefix `hermes/`):

- `infra/` — Bicep modules describing the Azure Static Web App,
  the Linux VM, the reverse proxy / TLS, DNS records, Key Vault
  references, the **partner-model VM (Ollama running a 3B
  partner)**, and (eventually) the Tailscale ACL.
- `web/` — the Azure Static Web App source: documents the system,
  hosts the developer UI, and backs the **Open WebUI alternate
  gateway** that runs alongside Discord.
- `api/` — the Linux VM back-end API source: an OpenAI-compatible
  service that **proxies OpenAI, GitHub Copilot, and Claude**, and
  that fronts the partner Ollama under `/v1/partner/*`, behind
  one personally-owned endpoint with auth, rate limits, and an
  MCP surface.
- `specs/` — spec-kit output for changes targeting this repo
  (`specs/<feature>/spec.md`, `plan.md`, `tasks.md`, `analyze.md`,
  `checklist.md`, optional `tests.md`).
- `security/` — threat models, baselines, findings, and the
  `security-scope.yaml` declaring the hostnames the security kit
  may probe.
- `.github/workflows/` (or `azure-pipelines.yml`) — the **single
  CICD pipeline** that deploys infra, web, api, and the partner
  model VM in one coordinated release on merges to `main`.

**Repo 2 — `hermes-lite`** (`~/repos/hermes-lite`, workspace name
`hermes-lite`, `approval_mode: pr-only`, branch prefix `hermes/`):

- The fork itself — `agent/`, `gateway/`, `plugins/`, `skills/`,
  `lite-config.yaml`, `lite-removed.manifest.yaml`, `tests/lite/`,
  the systemd unit, the diagnostics layer (§5.14).
- `specs/` — spec-kit output for changes that target the agent
  harness itself (new kits, refined prompts, schema tightenings,
  curator improvements). Self-improvement spec seeds emitted by
  the diagnostics layer land here, not in `blue-swallow-society`.
- **No CICD deploy** — changes to `hermes-lite` are validated by
  `tests/lite/`, the security kit, and an integration smoke against
  the Open WebUI pinned version (§12.3). A merged PR triggers a
  local `scripts/install.sh` re-run on the cyberdeck (and on each
  swarm node) as a rolling pull, never an Azure deploy.

**Repo 3 — `knowledge`** (`~/repos/knowledge`, workspace name
`knowledge`, `approval_mode: pr-only` shared / `auto` local-only,
branch prefix `hermes/`):

- The shared research store: `papers/`, `notes/`, `extracts/`,
  `seeds/`, `index/` (§5.13). Pulled locally on the Jetson and
  treated as a workspace alongside the two code repos.
- **No CICD** — the only "deploy" is `git push` to the shared
  remote so collaborators and other cyberdecks in the Tailscale
  swarm can pull. Redacted diagnostic exports (§5.14) optionally
  land under `knowledge/diagnostics/` for swarm-wide telemetry
  sharing.

**Cross-repo references.** A `seeds/<feature>.json` envelope in
`knowledge` names the **target repo** (`blue-swallow-society` or
`hermes-lite`) so `spec-specify` writes the resulting `spec.md`
into the correct workspace. Citations in `blue-swallow-society/specs/` and
`hermes-lite/specs/` link back into `knowledge/notes/` and
`knowledge/papers/`, keeping research provenance auditable across
the three repos.

**Deploy boundary.** CICD is the only routine path that touches
Azure, and it is scoped to `blue-swallow-society` alone. The agent's
azure-ops kit (§5.11) exists for bootstrap, drift inspection, and
incident response, not for everyday deploys.

**Self-call.** Once the API and partner model are live on
`blue-swallow-society`, the OpenAI-compatible adapter retained in §3.1 is
configured (by the `infra` memory profile) to reach both: paid
providers through `/v1/chat/completions` and the partner small
model through `/v1/partner/chat/completions`. The partner is the
default target for new-API skill development; paid providers stay
on the escalation chain (§12.1). New API features and harness
improvements become new model behaviors the next time hermes-lite
runs the loop.

### 10.2 Canonical Loop

1. **Discord (or Open WebUI / TUI) prompt.** The user posts a
   directive in an allowlisted channel — either an `blue-swallow-society`
   feature ("add a `POST /v1/cache` endpoint") or a `hermes-lite`
   harness improvement ("tighten the `arxiv-extract` JSON schema
   so the 3B model stops emitting trailing commas"). The
   originating gateway and target repo are recorded for the
   rest of the loop.
2. **Research.** The orchestrator loads the arXiv kit (§8) and
   the `research` memory profile. The kit produces notes,
   extracts, and a comparison table **into the `knowledge`
   repo**; on user confirmation, `arxiv-write` emits a
   `spec-seed.json` envelope under `knowledge/seeds/` naming the
   target repo.
3. **Propose.** The orchestrator unloads the arXiv kit and loads
   the **spec-kit** (§5.10) plus the **dev kit** against the
   **target repo** (`blue-swallow-society` or `hermes-lite`); memory points
   at `spec + dev + api` (for `blue-swallow-society`) or `spec + dev` (for
   `hermes-lite`). `spec-specify` writes
   `specs/<feature>/spec.md` into the target repo.
4. **Clarify.** `spec-clarify` asks up to five targeted questions
   in the originating gateway. Answers fold back into `spec.md`.
5. **Plan.** `spec-plan` writes `specs/<feature>/plan.md`. For
   `blue-swallow-society` it may span `infra/`, `web/`, and `api/` in one
   plan because those sub-trees live in one repo. For
   `hermes-lite` it spans `agent/`, `plugins/`, `skills/` as
   needed. Cross-repo plans are explicitly disallowed at this
   step; a change that needs both repos becomes two coordinated
   specs with linked IDs.
6. **Tasks.** `spec-tasks` writes `specs/<feature>/tasks.md`.
   Each task names its target sub-tree, its allowed file globs,
   its change budget, and its pre-commit gate.
7. **Analyze.** `spec-analyze` validates spec/plan/tasks
   consistency. Discrepancies pause the loop.
8. **Approve.** The user is asked, in the originating gateway, to
   confirm the move from planning to implementation. This is the
   **second mandatory approval gate** (the first was the arXiv
   → spec promotion in step 2).
9. **Implement.** `spec-implement` walks `tasks.md` one task at a
   time. For each task:
   - Load the appropriate kit (web-ops for `web/` changes,
     dev + linux-vm-api for `api/`, azure-ops for `infra/`, the
     dev kit alone for `hermes-lite` source).
   - Read only the files the task's globs allow.
   - Produce a patch via `workspace.apply_patch`.
   - Run the pre-commit gate (workspace-wide: `npm run lint &&
     npm test` for `web/`, `pytest -q` for `api/` and for the
     `hermes-lite` source, `bicep build` for `infra/`).
   - Commit on the topic branch with the spec-kit-aware commit
     message (`Spec: specs/<feature>`, `Task: <task-id>`,
     `Source: discord/...`, `Session: <hermes-session-id>`,
     `Repo: <target>`).
10. **Self-pentest.** Before opening the PR, the orchestrator
    loads the **security kit** (§5.12) and runs
    `sec-static-scan` + `sec-config-review` against the diff. For
    `blue-swallow-society` PRs the scan also includes `sec-config-review`
    over the `partner-model` Bicep module. For `hermes-lite` PRs
    the scan focuses on the agent's own egress allowlist and
    redaction rules. Any finding above a configured severity is
    appended to the PR description and added to
    `security/findings/` (in `blue-swallow-society`) or surfaced in the PR
    body (for `hermes-lite`). The agent does **not** auto-fix;
    findings feed a follow-up spec.
11. **Push & PR.** `workspace.push` pushes the topic branch.
    `workspace.open_pr` opens a PR that links to the spec, the
    originating gateway message, the security scan summary, the
    diff statistics, and the **diagnostic-log digest for the
    session** (§5.14).
12. **Merge.** The user reviews and merges to `main` (in any
    surface they prefer — web UI, GitHub CLI from the TUI, or by
    asking hermes-lite to merge via `workspace.*` once the PR is
    approved).
13. **CICD or rolling pull.**
    - For `blue-swallow-society`: the single CICD pipeline deploys `infra/`,
      `web/`, `api/`, and (when changed) the partner-model VM in
      one coordinated release. Hermes-lite **does not perform the
      deploy itself**; it watches the workflow via the `github/`
      skill family and reports status to the originating gateway.
    - For `hermes-lite`: `cron/pull-and-restart.sh` performs a
      rolling pull on the cyberdeck (and on each swarm node) and
      restarts the systemd unit. There is no Azure step.
    - For `knowledge`: a `git push` makes the change available to
      collaborators and to other cyberdecks; no service restart.
14. **Verify.** Post-deploy on `blue-swallow-society`: `web-ops` runs a
    Lighthouse-style smoke check against the SWA URL;
    `linux-vm-api` hits the API health endpoint and the partner
    model's `/v1/partner/health`; the security kit runs
    `sec-auth-probe` + `sec-web-probe` against the new surface
    (within the budgets declared in `security-scope.yaml`).
    Post-pull on `hermes-lite`: `hermes-lite doctor` (§5.8) is
    invoked and its output is logged to `logs/agent.jsonl`.
15. **Self-enhance.** With the new endpoint live, the
    OpenAI-compatible adapter is reconfigured (via the `infra`
    profile) to point at the deployed API. **The default target
    for new-skill experimentation is the partner small model**;
    paid providers stay on the escalation chain. The next loop
    iteration can call the just-deployed `POST /v1/cache` (or
    consume the just-tightened `arxiv-extract` schema) as part of
    its research, planning, or implementation steps — closing
    the loop. New capabilities the agent ships become new
    capabilities the agent has.
16. **Learn.** The curator proposes skill updates from what the
    agent struggled with, drawing primarily from the diagnostic
    log streams (§5.14); trajectory capture writes the full loop
    to `~/.hermes-lite/trajectories/`; spec, knowledge-repo notes,
    and diagnostic digests stay cross-linked in `state.db` so the
    next "research X" question can recall what "implementing X"
    actually felt like, what the security probe found, and which
    tool calls failed along the way.

### 10.3 Why The Loop Stays Cheap on a 3B Model

- At most **one kit is active at a time**, so the tool surface that
  reaches the model is small and stable (kit-shaped, per §5.6).
- Each kit binds to a small set of memory profiles, so recall is
  fast and cache-friendly.
- Each spec-kit step is a discrete skill; the model never has to
  juggle "specify" and "implement" simultaneously.
- All write paths flow through `LocalRepoWorkspace` (§5.9) and
  target exactly one of the three registered repos, so even an
  over-eager 3B model cannot silently mutate the wrong sub-tree
  or the wrong repo.
- CICD owns Azure for routine deploys, so the model never needs to
  hold the entire deploy state in context.
- Routine self-call traffic targets the **partner small model**
  rather than paid providers, so iteration cost is bounded.
- Diagnostic logs (§5.14) give the curator a structured signal
  rather than asking the 3B model to introspect on its own past
  behavior in-context.
- The two mandatory human approval gates (research → spec, tasks
  → implement) cap blast radius without making the loop feel
  micromanaged.

### 10.4 Self-Enhancement Discipline

The "agent calls its own API" and "agent edits its own source"
properties are powerful and easy to misuse. Four rules keep them
sane:

1. **Adapter, not implicit trust.** The deployed API — including
   the partner small model — is reached through the existing
   OpenAI-compatible adapter: same tool-call validation,
   redaction, rate-limit tracking, and diagnostic logging. The
   agent does not get a privileged side-channel to its own API
   or to its own source.
2. **Security kit gates production traffic.** Before the next loop
   iteration is allowed to call a newly-deployed endpoint or use
   a newly-merged `hermes-lite` skill, `sec-auth-probe` and
   `sec-web-probe` (for `blue-swallow-society`) or `sec-static-scan` (for
   `hermes-lite`) must pass against it. A failed probe reverts
   the adapter to the upstream provider or pins the agent to the
   previous skill bundle until the finding is specified, planned,
   and fixed.
3. **Capabilities are recorded.** Each new endpoint hermes-lite
   ships is registered in the `api` memory profile with its
   contract, auth requirements, intended use, and partner-vs-paid
   routing rule. Each new kit version is registered in the `dev`
   profile. The orchestrator does not improvise calls; it consults
   the registry.
4. **Self-modifying changes are not exempt from review.** A spec
   that targets the `hermes-lite` repo follows the same
   spec-clarify-plan-tasks-analyze-implement-pentest-PR-merge
   sequence as a spec that targets `blue-swallow-society`. There is no
   "agent edits itself in place" path.

### 10.5 Cyberdeck and Swarm Considerations

The Jetson is a portable cyberdeck. Two behaviors follow:

- **Offline parity.** The loop above is designed to degrade
  gracefully when the cyberdeck is offline: arXiv fetch and CICD
  steps pause until connectivity returns, but research-on-cached
  -corpus, spec-kit, security static analysis, and local repo
  edits all keep working against `~/repos/blue-swallow-society`,
  `~/repos/hermes-lite`, and `~/repos/knowledge`. The TUI is the
  guaranteed surface; Discord and Open WebUI degrade to
  out-of-band.
- **Swarm-ready.** The same agent binary is intended to run on
  cheaper edge devices over a Tailscale mesh. The networking skill
  set treats Tailscale as the canonical transport for
  agent-to-agent traffic; per-device kits can be tuned to a
  narrower domain (e.g. one device specialized in security probes,
  another in arXiv). The single-process design of upstream Hermes
  is the **per-device** unit; the mesh is the multi-process layer.
  This proposal does not implement the swarm, but it pays the
  Tailscale tax up front so the swarm step does not require a
  refork.

### 10.6 Failure Hand-off

If any step cannot make progress (ambiguous spec, repeated lint
failures, exceeded budget, failed security probe, failed CICD),
the orchestrator stops in place and writes a structured `state.db`
entry. The user can resume in any gateway by saying "continue spec
`<feature>`" — the orchestrator restores the kit, profile, and
workspace, and resumes from the failing step.

## 11. Engineering Plan (Phased)

### Phase 1 — Subtraction (≈1 PBI, M)

- Fork from `main` at a known-good tag.
- Delete removed providers, gateways, plugins, skills.
- Re-run upstream tests; mark deleted tests as expected fails.
- Build a Jetson-compatible (`aarch64`) Linux wheel and `Dockerfile.lite`.
- Validate `hermes-lite doctor` against Ollama on JetPack 6.x.

**Exit criteria.** A minimal hermes-lite that runs `hermes` in
interactive TUI mode against Ollama + Ministral-3 3B on the Jetson,
with no Discord, Open WebUI, or repo write surface yet.

### Phase 2 — Additions (≈3 PBIs, M+M+M)

- Add `agent/ollama_adapter.py` and small-model system prompt profile.
- Add `agent/tool_surface.py` and kit-based tool allowlisting.
- Add Discord gateway (Linux-only, single bot, allowlisted channels).
- Add Open WebUI gateway pipeline.
- Add `plugins/local_repo_workspace/` with the `workspace.*` tool set
  and a `~/.hermes-lite/workspaces.yaml` registry (§5.9, §9).
- Add per-session JSON snapshot defaults; verify FTS5 and curator
  defaults.

**Exit criteria.** TUI, Discord, and Open WebUI all reach the same
agent session and persist to `state.db`. A registered workspace can
be read via the workspace tools (write operations still gated behind
the Phase 4 hardening).

### Phase 3 — Research → Spec → Implement → Deploy Loop (≈4 PBIs, M+M+M+M)

- Implement `skills/research/arxiv/` (discover/fetch/skim/extract/
  compare/write) and wire the `/arxiv` slash command.
- Implement `skills/development/spec-kit/` (specify/clarify/plan/
  tasks/analyze/checklist/implement/review) and wire the `/spec`
  slash command (§5.10).
- Implement `skills/software-development/web-frontend/`,
  `skills/devops/azure-ops/`, and `skills/devops/linux-vm-api/`
  (§5.11) plus the `networking/` skill set (including Tailscale).
- Implement `skills/security/red-team/` and `skills/security/
  blue-team/` and wire the `/sec` slash command (§5.12).
- Bind the bundles to the `research`, `spec`, `dev`, `web`,
  `azure`, `infra`, `api`, and `security` memory profiles (§5.7).
- Implement the arXiv → spec-kit hand-off via `spec-seed.json`
  (§8 step 10, §5.10 hand-off contract).
- Scaffold the **three first-class workspaces** and register them
  in `workspaces.yaml`:
  - `blue-swallow-society` (`infra/`, `web/`, `api/`, `specs/`, `security/`,
    single CICD workflow) — the only repo with a CICD deploy.
  - `hermes-lite` (the fork itself, including `specs/` for
    self-improvement) — validated by `tests/lite/`, no Azure
    deploy.
  - `knowledge` (papers, notes, extracts, seeds, index) — shared
    research store, no service restart.
- Wire the deployed API back into the OpenAI-compatible adapter
  so the next loop iteration consumes the just-deployed endpoint
  (§10 step 15), gated on `sec-auth-probe` + `sec-web-probe`
  passing.

**Exit criteria.** End-to-end loop reproducible on the Jetson with
no human intervention beyond the two approval gates: a Discord
directive performs arXiv research against the `knowledge` repo,
drafts a spec proposal against either `blue-swallow-society` or
`hermes-lite`, opens a PR after a passing self-pentest, merges,
CICD deploys (`blue-swallow-society`) or rolling-pull installs
(`hermes-lite`), the security kit re-probes the live surface,
and the next loop call can use the freshly-deployed endpoint or
the freshly-installed skill.

### Phase 4 — Hardening (≈1 PBI, M)

- `systemd` unit + memory caps + egress filter (allow GitHub HTTPS/SSH
  for registered remotes; allow Azure management endpoints only when
  the azure-ops kit is active).
- Enable `workspace.commit` / `workspace.push` / `workspace.open_pr`
  by default in `pr-only` mode.
- Wire approval-mode + change-budget enforcement and confirmation
  envelopes for over-budget changes and for any `az` deploy or
  `az-vm-run-command` call.
- Integrate kanban worktrees for parallel repo work and for
  multi-workspace spec-implement runs.
- Document a rebase strategy against upstream `main`.
- Add CI for the lite extras only.
- Add a tiny benchmark suite that times each skill against
  Ministral-3 3B and reports tokens/sec on Jetson.

**Exit criteria.** The unit restarts cleanly, the egress filter is
verified, a Discord directive to update a registered repo produces a
pushed branch and an open PR, an `az-swa-deploy` is gated and
audited, and the rebase doc is followed at least once successfully.

## 12. Resolved Decisions and Operational Guidance

This section records concrete answers to the open design questions
that would otherwise block implementation. Each subsection ends with
the specific knob, file, or skill that operationalizes the decision.

### 12.1 Small Models, Tool Calling, and Iteration Policy

**Decision.** Ministral-3 3B is the reference model. Hermes-lite is
model-agnostic at the adapter layer (`agent/ollama_adapter.py`,
§5.2), so swapping is a `lite-config.yaml` change. The following
alternatives are kept in the Ollama model store on the 512 GB microSD card
and benchmarked together (see Phase 4):

| Candidate | Size | Quant | Disk | Why we keep it |
| --------- | ---- | ----- | ---- | --------------- |
| `ministral-3:3b` | 3B | Q4_K_M | ~2.3 GB | Primary; strong tool-call behavior in our domain, Apache-style permissive license. |
| `qwen3:3b-instruct` | 3B | Q4_K_M | ~2.4 GB | Strong native function-calling and a built-in "thinking" mode; useful when `spec-plan` and `sec-threat-model` need extended reasoning. |
| `llama3.2:3b-instruct` | 3B | Q4_K_M | ~2.5 GB | Meta's tools/Tools-V2 schema; reference for cross-model schema compatibility. |
| `phi-4-mini:3.8b` | 3.8B | Q4_K_M | ~3.0 GB | Microsoft's small model; competitive on structured-output benchmarks. |
| `gemma3:4b-it` | 4B | Q4_K_M | ~3.4 GB | Strong on retrieval and summarization; useful for `arxiv-skim`. |
| `qwen3:7b-instruct` (escalation) | 7B | Q4_K_M | ~4.8 GB | Loaded only when the per-kit failure budget is exhausted (below); too heavy to coexist with the agent at idle. |

Only one model is resident at a time; switching is an Ollama
`/api/pull`-or-`/api/load` call.

**Tool-call discipline.** A 3B model needs aggressive, deterministic
guardrails to use tools correctly. Hermes-lite enforces:

1. **Strict JSON schemas per tool**, validated before the tool is
   dispatched. A malformed call is rejected and re-prompted with the
   schema and the validation error.
2. **Per-kit active toolset ≤ 5 tools** (`agent/tool_surface.py`,
   §5.6). The dev kit, security kit, and azure-ops kit each expose
   only their own narrow allowlist; the model never sees the full
   surface.
3. **Cache-friendly tool schemas**: schemas are emitted in a
   byte-stable order, so prompt-prefix caching survives across
   turns of the same kit.
4. **Per-kit failure budget**, default 3 consecutive malformed or
   semantically wrong tool calls inside one skill. On budget
   exhaustion the orchestrator:
   - logs the failure pattern to
     `~/.hermes-lite/queue/tool-failures.jsonl`,
   - escalates the same skill to the next model in the escalation
     chain (typically `qwen3:7b-instruct` then `claude` if remote
     access is available),
   - on success at the larger model, captures the diff between the
     small-model trajectory and the large-model trajectory so the
     curator can later propose a tightened prompt for the 3B model.
5. **Iteration is fine; failure-in-place is not.** The user has
   explicitly accepted that the loop may iterate as long as each
   iteration is using tools correctly. The iteration budget
   (§5.1, default 25) caps blast radius; the failure budget caps
   confusion.

**Operational knobs.** `lite-config.yaml` keys: `model.default`,
`model.escalation_chain`, `tool_surface.max_tools_per_kit`,
`tool_surface.failure_budget`, `iteration.max`.

### 12.2 Curator and Background Review — Deferred Queue

**Decision.** The curator and background reviewer do **not** run
inline with the conversation loop. Each loop tick enqueues curator /
reviewer work to `~/.hermes-lite/queue/curator.jsonl` and
`~/.hermes-lite/queue/review.jsonl`. The queues are flushed by
explicit user direction ("run curator", `/curate`, or a TUI menu).

**Threshold prompting.** When either queue reaches a configurable
threshold (default: 25 entries in either queue, or 4 hours of
accumulated work-units in the queue), the orchestrator emits a
structured "curator pressure" notice in the originating gateway and
asks the user to authorize a batched pass. The agent does not block
on the answer; it continues conversing until the user replies.

**Batched execution.** A `/curate` invocation:

1. Loads the **curator kit** (sole active kit) and points memory at
   the `dev` and `spec` profiles.
2. Drains the curator queue, deduplicates by skill, and proposes
   skill/system-prompt updates one batch at a time.
3. Posts each proposed change to the originating gateway for
   approval; never writes to skills, system prompts, or `state.db`
   without explicit "approved" replies.
4. On approval, applies changes through `workspace.apply_patch`
   into the **hermes-lite repo** itself (treated as just another
   registered workspace), so curator output goes through the same
   PR pipeline as application code.

**Operational knobs.** `lite-config.yaml` keys: `curator.mode:
deferred`, `curator.threshold.entries`, `curator.threshold.hours`,
`curator.gateway_notify`.

### 12.3 Open WebUI — Pinned Version

**Decision.** Pin a known-good Open WebUI release in
`gateway/platforms/openwebui/pinned-version.json` (e.g.
`v0.6.x`), include a smoke-test that runs against that exact
version in `tests/lite/`, and document the rebase procedure for
upgrading. Open WebUI is treated as an external dependency with the
same contract surface as a model provider — a version bump is a
scoped PR that runs the integration test before merging.

No "floating latest" deployment of Open WebUI is allowed.

### 12.4 Rebase Cadence — Weekly, Additive-Only

**Decision.** Rebase against upstream Hermes `main` **weekly**,
automated by a cron-driven script in `cron/rebase-upstream.sh`.

**Discipline.** Two non-negotiable rules:

1. **Never re-introduce removed surface.** The rebase script
   maintains a manifest of removed providers, gateways, skills,
   and plugins under `lite-removed.manifest.yaml`. Any rebase
   conflict that would re-add a removed path is **dropped** by
   the script and surfaced as a deletion-conflict report rather
   than a merge conflict.
2. **Always pull updates to retained surface.** Conflicts inside
   retained modules (`agent/`, `plugins/memory/`, retained
   skills, etc.) are surfaced as normal merge conflicts and
   resolved during the weekly pass. The intent is to absorb
   upstream fixes to retained components while never re-growing
   the removed surface.

**Cadence.** Weekly default; the user may request an off-cycle
rebase by saying "rebase upstream now". Rebase runs are recorded
in `state.db` so the curator can review what was absorbed.

**Operational knobs.** `cron/rebase-upstream.sh`,
`lite-removed.manifest.yaml`,
`cron/conf/rebase-cadence.yaml`.

### 12.5 arXiv Rate Limits and Knowledge Repo

**Decision.** arXiv access is **strictly** rate-limited at the
client layer (1 request / 3 s with jittered backoff, daily soft
cap, identifying `User-Agent`; see §5.4). All cached PDFs, notes,
extracts, and `spec-seed.json` envelopes live in the **dedicated
knowledge repo** (`~/repos/knowledge`) registered as one of the
three first-class workspaces hermes-lite owns (§1 premise 6,
§5.13). The knowledge repo is rebased and shared independently of
the `blue-swallow-society` and `hermes-lite` codebases, so contributors and
other cyberdecks in the Tailscale swarm can collaborate on the
shared research corpus without touching production code.

**Wikipedia ground truth.** A text-only English Wikipedia mirror is
stored at `~/.hermes-lite/corpora/wikipedia/` with an FTS5 sidecar
index, accessed through the `corpus-wiki-lookup` skill. This is the
offline fact-checking backstop when arXiv is unreachable or when a
research question is general-knowledge.

**Operational knobs.** `lite-config.yaml` keys:
`arxiv.rate_limit.requests_per_second`,
`arxiv.rate_limit.daily_cap`, `arxiv.user_agent`,
`corpora.wikipedia.path`, `workspaces.knowledge.path`.

### 12.6 Editor Surface for Copilot — Local VS Code on the Jetson

**Decision.** Use the **VS Code instance already installed on the
Jetson** as the Copilot pairing surface. When a user attaches an
HDMI display or runs VS Code through a Remote-SSH session into the
Jetson, the Copilot extension is the pairing target; hermes-lite
reaches it through the existing `agent/copilot_acp_client.py`,
`acp_adapter/`, and `acp_registry/` machinery.

**Pairing contract.** When VS Code is detected (the Copilot ACP
socket is reachable), the Copilot provider becomes available as one
of the four allowed escalations. When VS Code is not running,
Copilot is silently skipped and the escalation chain moves on to
OpenAI → Claude.

**No headless Copilot.** Hermes-lite does not attempt to drive a
headless Copilot via a synthesized editor surface. The user opens
VS Code on the cyberdeck (locally or via SSH) when they want
Copilot in the loop; otherwise the loop runs without it.

**Operational knobs.** `lite-config.yaml` keys:
`providers.copilot.require_editor`,
`providers.copilot.acp_socket_path`,
`providers.copilot.silent_skip_when_absent`.

### 12.7 Memory Provider Evolution

**Decision.** Honcho dialectic modeling and the existing memory
provider are retained as the starting point. **Memory modeling is
an explicit early target for enhancement**: after Phase 4 lands,
the first follow-up workstream will use the research → spec →
implement loop to study and improve the memory layer itself,
dogfooding hermes-lite on its own most-important component.

In the meantime, hermes-lite ships:

- a default trim policy on `state.db` (FTS5 windows kept for the
  last 90 days at full resolution, older windows summarized);
- quarterly trajectory archival to
  `~/.hermes-lite/trajectories/archive/<YYYY-QQ>.jsonl.gz`;
- a `state.db doctor` check that warns when the database exceeds
  the disk-budget slice in §7.4.

**Operational knobs.** `lite-config.yaml` keys:
`memory.trim.days_full_resolution`,
`memory.trim.summarize_older`, `memory.trajectory.archive_cadence`,
`memory.dogfood.enabled`.

### 12.8 Thermal Profile — 25 W Default, MAXN Bursts

**Decision.** The default power mode is **25 W (`nvpmodel -m 1`)**.
MAXN has been observed to sustain only **10–20 minute windows**
on the reference cyberdeck before throttling; treat MAXN as a
burst mode, not a steady state.

**Watchdog behavior.**

- The thermal watchdog polls `tegrastats` every 5 s.
- On entering a skill marked `burst: true` (e.g. `arxiv-skim`,
  `spec-implement` over a large diff, `sec-fuzz`), the watchdog
  switches to MAXN for up to 20 minutes.
- If the burst exceeds 20 minutes or temperatures cross the
  configured ceiling (default: CPU 80 °C, GPU 85 °C), the watchdog
  drops back to 25 W and surfaces a warning to the originating
  gateway.
- Sustained throttling warnings flow into the curator queue as a
  prompt to reconsider model size or skill chunking.

**Operational knobs.** `lite-config.yaml` keys:
`thermal.default_power_mode`, `thermal.burst_power_mode`,
`thermal.burst_max_minutes`, `thermal.cpu_ceiling_c`,
`thermal.gpu_ceiling_c`.

### 12.9 Repo Write Blast Radius

**Decision.** The combined defense-in-depth is accepted as
sufficient: `pr-only` default approval mode (§9.5), per-workspace
change budgets and allowed globs (§5.9), protected branches
(`main` is read-only at the tool layer), and a systemd egress
filter (§7.3) restricted to registered remotes. Single-user
workspaces may opt down to `auto` mode for low-risk repos
(typos, README updates) but the default for any new workspace is
`pr-only` and never changes silently.

The security kit (§5.12) re-validates the egress and protected-
branch claims on each loop iteration so configuration drift is
caught before a write attempt rather than after.

## 13. Why Hermes Is a Strong Base for This

Hermes-lite is a *subtractive* fork plus a small set of *additive*
plugins and skill bundles. The choice to fork Hermes rather than
write from scratch rests on five concrete properties of the upstream
codebase:

- **Single-agent-loop design.** One process, one event loop, one
  dependency tree. This is the smallest surface that still supports
  a curator, a background reviewer, persistence, and multiple
  gateways simultaneously — ideal for an 8 GB device.
- **Skill bundle pattern.** Upstream Hermes already encourages the
  exact discipline that 3B models need: load one narrow procedural
  memory at a time, then unload. The hermes-lite kits (§5.4, §5.10
  – §5.13) are a natural extension of that pattern.
- **Curator + background reviewer + FTS5 recall + Honcho memory
  provider.** These four pieces compose into a persistent working
  environment that survives across sessions. We deferred the
  curator/reviewer execution to user direction (§12.2) but kept the
  primitives intact.
- **Plugin platform with `ctx.llm`, `apply_yaml_config_fn`, and
  dynamic `sys.modules` registration.** Every new component in §5
  (Open WebUI gateway, arXiv kit, spec-kit, azure/web/linux kits,
  security kit, LocalRepoWorkspace, knowledge corpora) plugs in
  through these existing hooks. The core loop is never forked.
- **Trajectory and training surface.** Each session is captured as
  a structured trajectory under `~/.hermes-lite/trajectories/`. The
  data shape is suitable for later distillation of a bespoke 3B
  variant tuned specifically for the cyberdeck's workflows.

What hermes-lite *adds* on top of these five properties is
catalogued in §14.

## 14. Hermes Repository Modification Map

This section is the concrete answer to the question "how exactly
do we turn Hermes into hermes-lite?" It enumerates the
upstream-source paths that are **retained**, **removed**,
**modified**, or **added**, organized by top-level directory of the
upstream Hermes repo. Use this as the implementation checklist for
Phase 1 (Subtraction) and Phase 2 (Additions).

### 14.1 `agent/`

| Path | Action | Notes |
| ---- | ------ | ----- |
| `agent/conversation_loop.py` | Retain | Core loop. Untouched. |
| `agent/prompt_builder.py`, `agent/system_prompt.py`, `agent/prompt_caching.py` | Modify | Add the small-model prompt profile (§5.5); shrink role/style preamble to <300 tokens; emit byte-stable tool-schema digests for prefix caching. |
| `agent/tool_executor.py`, `agent/tool_guardrails.py`, `agent/tool_dispatch_helpers.py`, `agent/tool_result_classification.py` | Retain | Tool guardrails are the substrate for `workspace.*` (§5.9) and `/sec` (§5.12). |
| `agent/iteration_budget.py` | Modify | Add per-kit failure budget (§12.1) alongside the existing iteration budget. |
| `agent/error_classifier.py`, `agent/retry_utils.py` | Retain | Used by the per-kit failure-budget escalation. |
| `agent/redact.py`, `agent/think_scrubber.py`, `agent/message_sanitization.py` | Retain | Required by the security kit's credential redaction. |
| `agent/curator.py`, `agent/curator_backup.py`, `agent/background_review.py` | Modify | Switch from inline to **deferred queue** execution (§12.2). Add `~/.hermes-lite/queue/curator.jsonl` and `review.jsonl` writers. |
| `agent/skill_bundles.py`, `agent/skill_commands.py`, `agent/skill_preprocessing.py`, `agent/skill_utils.py` | Retain | Skill primitives; new bundles plug in. |
| `agent/context_engine.py`, `agent/context_compressor.py`, `agent/conversation_compression.py`, `agent/context_references.py`, `agent/manual_compression_feedback.py` | Retain | Context engine is preserved as-is. |
| `agent/memory_manager.py`, `agent/memory_provider.py` | Retain (early enhancement target) | Per §12.7, memory is the first follow-up enhancement workstream. |
| `agent/insights.py`, `agent/account_usage.py`, `agent/usage_pricing.py`, `agent/rate_limit_tracker.py`, `agent/nous_rate_guard.py` | Retain | Rate-limit tracker is reused by the arXiv client (§12.5). |
| `agent/markdown_tables.py`, `agent/display.py`, `agent/title_generator.py` | Retain | Used by all three surfaces (TUI, Discord, Open WebUI). |
| `agent/trajectory.py`, `agent/trajectory_compressor.py`, `agent/mini_swe_runner.py` | Retain | Trajectory pipeline; archival policy is documented in §12.7. |
| `agent/chat_completion_helpers.py` | Retain | OpenAI-compatible helper; the `blue-swallow-society` API and the partner small model are reached through this. |
| `agent/copilot_acp_client.py` | Retain | Used when local VS Code on the cyberdeck is present (§12.6). |
| `agent/anthropic_adapter.py` | Retain | Claude provider. |
| `agent/lmstudio_reasoning.py` | **Replace** | Replaced by `agent/ollama_adapter.py` (§5.2). |
| `agent/azure_identity_adapter.py`, `agent/bedrock_adapter.py`, `agent/gemini_native_adapter.py`, `agent/gemini_cloudcode_adapter.py`, `agent/gemini_schema.py`, `agent/google_code_assist.py`, `agent/google_oauth.py`, `agent/codex_runtime.py`, `agent/codex_responses_adapter.py`, `agent/moonshot_schema.py`, `agent/auxiliary_client.py`, `agent/models_dev.py`, `agent/portal_tags.py`, `agent/image_*`, `agent/video_*` | **Remove** | Out of allowlist; not loaded at runtime. |
| `agent/ollama_adapter.py` | **Add** (§5.2) | New tight Ollama client; pre-validates JSON-schema tool calls; supports per-kit failure budget. |
| `agent/tool_surface.py` | **Add** (§5.6) | Kit-aware tool allowlist; emits cache-stable schema digests. |

### 14.2 `gateway/`

| Path | Action | Notes |
| ---- | ------ | ----- |
| `gateway/session.py`, `gateway/session_context.py`, `gateway/mirror.py`, `gateway/memory_monitor.py`, `gateway/shutdown_forensics.py` | Retain | Session plumbing is shared across TUI, Discord, and Open WebUI. |
| `gateway/platforms/discord/` | Retain (modify) | Single bot, single guild, allowlisted channels; remove sticker/identity/preservation code paths. |
| `gateway/platforms/{telegram,slack,whatsapp,signal,email,yuanbao,weixin}/` | **Remove** | Out of allowlist. |
| `tui_gateway/`, `ui-tui/` | Retain | Default local surface; cyberdeck-essential. |
| `gateway/platforms/openwebui/` | **Add** (§5.3) | Pinned to the version documented in `gateway/platforms/openwebui/pinned-version.json` (§12.3). |

### 14.3 `plugins/`

| Path | Action | Notes |
| ---- | ------ | ----- |
| `plugins/browser/` | Retain | Used by arXiv fetch and by `web-frontend` / `/sec` probes. |
| `plugins/context_engine/` | Retain | |
| `plugins/kanban/` | Retain | Worktree machinery reused by `LocalRepoWorkspace` and `spec-implement`. |
| `plugins/memory/` | Retain | Profile isolation is the basis for §5.7. |
| `plugins/observability/langfuse/` | Retain (optional) | Off by default; toggled on by `lite-config.yaml` when diagnosing hard prompts. |
| `plugins/web/` | Modify | Keep only the **web search provider** components compatible with our provider allowlist; drop xAI-bound paths. |
| `plugins/github/` (if present) | Retain | Used by `spec-implement` (PR/issue/workflow operations). |
| `plugins/mcp/` (or equivalent) | Retain | Used to call the back-end API's MCP surface. |
| `plugins/{image_gen,video_gen,spotify,google_meet,teams_pipeline,hermes-achievements,web-dashboard,example-dashboard}/` | **Remove** | Out of scope. |
| `plugins/local_repo_workspace/` | **Add** (§5.9) | Sanctioned filesystem + git surface. |

### 14.4 `skills/`

| Path | Action | Notes |
| ---- | ------ | ----- |
| `skills/research/` | Retain | Existing patterns; extended by `skills/research/arxiv/` (§5.4). |
| `skills/data-science/`, `skills/software-development/`, `skills/devops/`, `skills/note-taking/`, `skills/productivity/`, `skills/dogfood/`, `skills/mcp/`, `skills/github/`, `skills/domain/`, `skills/index-cache/`, `skills/autonomous-ai-agents/` | Retain | The dev-workflow surface; entire engine of the implement loop. |
| `skills/security/` (red-team / blue-team subtrees) | Retain | **Non-negotiable** (§5.12); active probes target only the agent's own deployed surface. |
| `skills/research/arxiv/` | **Add** (§5.4) | New bundle with strict arXiv rate limit. |
| `skills/development/spec-kit/` | **Add** (§5.10) | Spec → plan → tasks → implement bundle. |
| `skills/software-development/web-frontend/` | **Add** (§5.11) | SWA-target patterns. |
| `skills/devops/azure-ops/`, `skills/devops/linux-vm-api/`, `skills/devops/networking/` | **Add** (§5.11) | Azure / VM / Tailscale operations. |
| `skills/security/red-team/` (sub-bundles) | **Add** (§5.12) | `/sec` slash command. |
| `skills/corpora/wikipedia/` | **Add** (§5.13) | `corpus-wiki-lookup` plus shared `corpus-recall`. |
| `skills/{apple,gaming,gifs,social-media,smart-home,creative,voice,tts}/` | **Remove** | Out of scope. |

### 14.5 Persistence and Long-Running

| Path | Action | Notes |
| ---- | ------ | ----- |
| `hermes_state.py`, `state.db` | Retain | Canonical session and recall store; trim policy in §12.7. |
| Per-session JSON snapshot writer | Retain | Enabled by default in `lite-config.yaml`. |
| FTS5 session search + LLM-summarized cross-session recall | Retain | Joined by a new index over the knowledge repo (§5.13). |
| Honcho dialectic user modeling | Retain (early enhancement target) | See §12.7. |
| `cron/` | Modify | Drop Windows subprocess console-hiding paths; add `cron/rebase-upstream.sh` (§12.4) and the optional Wikipedia refresh job. |
| `mini_swe_runner.py` | Retain | Sub-agent runner reused by `spec-implement` and parallel kanban worktrees. |

### 14.6 Packaging

| Path | Action | Notes |
| ---- | ------ | ----- |
| `pyproject.toml` | Modify | Drop extras for every removed provider, gateway, plugin, and skill; keep only the `[lite]` extras set. |
| `setup-hermes.sh` | **Replace** | New `scripts/install.sh` (§7.1) installs only the lite extras. |
| Windows shims (MinGit bootstrap, UTF-8 stdio shim), Homebrew formula, Termux extras, Nix flake | **Remove** | `aarch64` Linux only. |
| `Dockerfile` | Replace | `Dockerfile.lite` based on `python:3.11-slim`, image target <350 MB (§7.2). |
| `systemd/hermes-lite.service` | **Add** | Hardened unit per §7.3. |
| `lite-config.yaml`, `lite-removed.manifest.yaml`, `tests/lite/` | **Add** | Profile, removal manifest, and lite-only test suite.

## 15. One-Paragraph Pitch

Fork hermes-agent into **hermes-lite**, an `aarch64` Linux
single-user agent for a portable **NVIDIA Jetson Orin Nano 8 GB
cyberdeck** that works offline by default and unifies paid OpenAI /
Copilot / Claude access behind a personally-owned, locally-developed
API — with a **self-hosted partner small model** running on the
same Azure VM as that API, so day-to-day API-driven skill
development never burns paid quota. Hermes-lite owns **three
first-class repos** on the cyberdeck — `blue-swallow-society` (infra-as-code
+ Static Web App + Linux VM API + partner-model VM, deployed by a
single CICD pipeline), `hermes-lite` (the fork itself, so the
agent can refine its own harness through the same spec-driven
cycle), and `knowledge` (a shared research store of papers, notes,
extracts, and spec seeds, pulled locally on the Jetson and shared
with collaborators and other cyberdecks) — and drives the entire
**research → spec → implement → deploy → self-enhance loop**
across them: arXiv research seeds spec proposals (cached into
`knowledge`), a spec-kit (`/spec`) mirroring the
[speckit.org](https://speckit.org) `specify` CLI drives
spec → plan → tasks → implement against the target repo, a
security kit (`/sec`) red-teams the diff before the PR opens, the
`blue-swallow-society` CICD pipeline deploys infra, web, api, and the partner
model on merge to `main` while `hermes-lite` merges trigger a
rolling pull on every node, and the next loop iteration calls the
freshly-deployed endpoint — partner model by default, paid
providers on escalation — through the existing OpenAI-compatible
adapter, so capabilities the agent ships become capabilities the
agent has. Keep Hermes' conversation loop, TUI, memory provider,
**deferred-execution curator and background reviewer**, FTS5
recall, per-session snapshots, trajectory capture, and the entire
dev-workflow + security skill surface (`software-development/`,
`devops/`, `github/`, `mcp/`, `data-science/`, `domain/`,
`index-cache/`, `security/red-team/`), and add a **first-class
diagnostic logging layer** (`agent/diagnostics.py` plus per-stream
JSONL logs for agent / tools / providers / workspace / security /
thermal / api) so the curator and the self-improvement loop have
structured signal instead of having to introspect the 3B model
on its own past behavior.
Remove every LM provider except Ollama (local + partner on the
VM), OpenAI, GitHub Copilot (paired through the cyberdeck's local
VS Code when present), and Claude, and every chat gateway except
Discord, Open WebUI, and the local TUI — with Discord as the
**stable remote prompt source** and the SWA-backed Open WebUI as
an **experimentation endpoint** that runs alongside Discord, never
as a replacement. Slim the system prompt and tool surface so a 3B
model (Ministral-3, with documented Qwen-3 / Phi-4-mini / Llama-3.2
/ Gemma-3 alternatives kept on the 512 GB microSD card) can drive the loop
reliably one kit at a time under a strict per-kit tool-call failure
budget. Wire it all to a sanctioned
`LocalRepoWorkspace` plugin, a Tailscale-aware networking skill
set, and a registered security scope so a single Discord directive
like "research prompt caching and add a `POST /v1/cache` endpoint
to `blue-swallow-society`" — or "tighten the `arxiv-extract` JSON schema in
`hermes-lite`" — produces research notes in `knowledge`, a
`spec.md` / `plan.md` / `tasks.md` set in the target repo, the
corresponding code change, a passing pre-commit gate, a
self-pentest, an open PR, an automated CICD deploy or rolling
pull, a post-deploy probe, and a self-enhancement that the next
loop call gets to use — all with full audit in `state.db`, the
change journal, and the diagnostic logs. The result is a small,
opinionated, persistent cyberdeck agent that runs comfortably on the
Jetson under 7.5 GB resident at a thermally-stable **25 W** (with
short MAXN bursts ≤20 minutes), owns three coordinated repos
end-to-end, drives real product work safely from chat, and is
**swarm-ready**: the same binary is intended to fan out across
low-cost edge devices over Tailscale, each tuned as a narrow
expert calling the same personally-owned API and its partner
small model.
