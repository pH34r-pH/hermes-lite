# Phase 1: Hermes-Lite Subtraction Pass

## Overview

Phase 1 is the **removal/subtraction** phase of the REDESIGN.md specification. This phase removes all components incompatible with the Jetson Orin Nano 8GB cyberdeck deployment model.

**Status**: ⚠️  Configuration & scaffolding created, ready for removal execution

**Duration**: Single pass, non-reversible (though rebase strategy exists in §12.4)

---

## What's Been Completed ✅

### Configuration Files
- **lite-config.yaml** (320+ lines) - Complete configuration profile for hermes-lite
  - 5-tier escalation chain (ollama → partner → copilot → openai → anthropic)
  - Deferred-queue mode for curator and background review
  - Memory profiles bound to kits (research, spec, dev, web, azure, infra, api, security)
  - arXiv 1-req/3sec rate limiting
  - Thermal management for Jetson (25W default, MAXN bursts ≤20 min)
  - Egress filtering and workspace approval modes

### Infrastructure Files
- **Dockerfile.lite** (220+ lines)
  - Base: python:3.11-slim
  - Target: <350MB image
  - Security hardened: ProtectHome=tmpfs, ProtectSystem=strict
  - Memory limits: MemoryHigh=4G, MemoryMax=5.5G
  - Built with [lite] extras only (removed providers excluded)

- **systemd/hermes-lite.service** (180+ lines)
  - Non-root user execution (hermes:hermes)
  - Resource limits and security hardening
  - Thermal management integration
  - Comprehensive operator documentation

### Scripts
- **scripts/install-lite.sh** (350+ lines)
  - Platform validation (Linux aarch64 only)
  - Virtual environment setup
  - Ollama runtime management
  - Ministral-3:3B model pull
  - Configuration initialization

- **scripts/phase1-removal.sh** (300+ lines)
  - Automated removal of all non-retained components
  - Category-organized git commits for clear history
  - Validation at each step

- **scripts/verify-removal.sh** (200+ lines)
  - Post-removal verification script
  - Checks for dangling imports and references
  - Validates retained critical files

### Manifest
- **lite-removed.manifest.yaml** (200+ lines)
  - Complete listing of removed paths
  - Organized by category (providers, gateways, plugins, skills)
  - Rebase safety rules for weekly upstream sync

---

## Phase 1 Removal Scope

### Agent Adapters to Remove (18 files)
```
agent/azure_identity_adapter.py           # Azure Foundry
agent/bedrock_adapter.py                  # AWS Bedrock
agent/gemini_*.py                         # Google Gemini (3 files)
agent/google_*.py                         # Google services (2 files)
agent/codex_*.py                          # OpenAI Codex (2 files)
agent/moonshot_schema.py                  # Moonshot/Kimi
agent/auxiliary_client.py                 # Auxiliary provider
agent/models_dev.py                       # Provider picker
agent/portal_tags.py                      # Nous Portal
agent/*gen_*.py                           # Image/video generation (5 files)
```

### Gateway Platforms to Remove (23 platform files)
```
gateway/platforms/telegram.py             # Messaging (telegram_network too)
gateway/platforms/slack.py                # Messaging
gateway/platforms/whatsapp.py             # Messaging
gateway/platforms/signal.py               # Messaging (signal_rate_limit too)
gateway/platforms/email.py                # Messaging
gateway/platforms/yuanbao.py              # Chinese platform (+ media, proto, sticker)
gateway/platforms/weixin.py               # Chinese platform
gateway/platforms/dingtalk.py             # Chinese platform
gateway/platforms/wecom.py                # Chinese platform (+ callback, crypto)
gateway/platforms/feishu.py               # Chinese platform (+ comment, rules)
gateway/platforms/mattermost.py           # Team platform
gateway/platforms/matrix.py               # Protocol
gateway/platforms/qqbot/                  # Chinese platform (directory)
gateway/platforms/api_server.py           # Web dashboard (depends on web/)
```

### Web Dashboard to Remove
```
web/                                       # Bundled dashboard
website/                                   # Docusaurus documentation
```

### Plugins to Remove (5 directories)
```
plugins/image_gen/                        # Image generation
plugins/video_gen/                        # Video generation
plugins/spotify/                          # Entertainment
plugins/google_meet/                      # Video platform
plugins/hermes-achievements/              # Gamification
plugins/teams_pipeline/                   # Microsoft Teams
plugins/example-dashboard/                # Reference dashboard
```

### Skills to Remove (8 directories)
```
skills/apple/                             # Apple platform
skills/gaming/                            # Gaming
skills/gifs/                              # GIF generation
skills/social-media/                      # Social platforms
skills/smart-home/                        # IoT/home automation
skills/creative/                          # Creative tools
skills/voice/                             # Voice/audio
skills/tts/                               # Text-to-speech
```

### Packaging and Platform-Specific
```
setup-hermes.sh                           # Replaced by install-lite.sh
Dockerfile                                # Replaced by Dockerfile.lite
constraints-termux.txt                    # Termux removed
README.zh-CN.md                           # Non-English removed
packaging/nix/                            # Nix packaging
packaging/termux/                         # Termux packaging
All Windows subprocess code                # Windows removed
All macOS-specific code                   # macOS removed
```

---

## What's Retained ✅

**Core Conversation Engine**
- agent/conversation_loop.py (untouched)
- agent/prompt_builder.py (modified for small models)
- agent/system_prompt.py (modified for small models)
- agent/prompt_caching.py (modified)

**Providers (Filtered)**
- agent/anthropic_adapter.py (Claude for escalation)
- agent/copilot_acp_client.py (Copilot when local VS Code present)
- agent/chat_completion_helpers.py (OpenAI compatibility)

**Gateways (Filtered)**
- gateway/platforms/discord.py (single bot, allowlisted channels)
- tui_gateway/ (local TUI)
- ui-tui/ (local TUI frontend)

**Persistence**
- hermes_state.py (session store)
- Trajectory capture
- FTS5 indexing

**Skills** (Domain retained, removals above)
- skills/research/
- skills/software-development/
- skills/devops/
- skills/github/
- skills/mcp/
- skills/security/
- And other non-removed domains

**Plugins** (Category retained)
- plugins/memory/ (Honcho for user modeling)
- plugins/browser/ (arXiv, smoke checks)
- plugins/context_engine/
- plugins/kanban/ (worktree machinery)
- plugins/observability/ (Langfuse optional)
- plugins/mcp/
- plugins/github/

---

## Execution Steps

### Step 1: Review Configuration
```bash
# Check the configuration options
cat lite-config.yaml | head -100
```

### Step 2: Run Phase 1 Removal (DESTRUCTIVE)
```bash
cd ~/repos/hermes-lite

# Backup current state first!
git stash
git branch backup/phase0-baseline

# Run removal script
bash scripts/phase1-removal.sh
```

This will:
1. Delete all removed files
2. Create category-organized git commits
3. Attempt import cleanup (manual review needed for some)
4. Create verification checklist files

### Step 3: Verify Removal
```bash
bash scripts/verify-removal.sh
```

This validates:
- ✓ All removed files are gone
- ✓ No dangling imports
- ✓ Retained files still present
- ✓ New files created

### Step 4: Manual Cleanup (if needed)
Review files flagged by verify-removal.sh:
- agent/account_usage.py - Remove codex functions
- tests/agent/test_anthropic_adapter.py - Remove bedrock test

### Step 5: Commit and Test
```bash
git add -A
git commit -m "Phase 1: Manual import cleanup"

# Run tests to ensure core still works
scripts/run_tests.sh tests/agent/ -q
```

---

## What's Next (Phase 2)

**Phase 2 begins once Phase 1 removals are verified complete.**

Phase 2 will implement the new core components:

1. **agent/ollama_adapter.py** - Tight Ollama integration with JSON-schema validation
2. **agent/tool_surface.py** - Kit-based tool allowlisting
3. **agent/diagnostics.py** - Structured JSONL logging
4. **gateway/platforms/openwebui/** - Open WebUI integration (pinned version)
5. **plugins/local_repo_workspace/** - Workspace.* tools with pr-only mode
6. **skills/research/arxiv/** - arXiv discovery with rate limiting
7. **skills/development/spec-kit/** - Constitution-driven spec-to-code workflow
8. **skills/devops/** - Azure ops, Linux VM API, networking
9. **skills/security/** - Red team and blue team bundles

---

## Key Design Decisions

| Decision | Rationale | Reference |
|----------|-----------|-----------|
| 5-tier escalation chain | Minimize local resource use, escalate only when needed | §3.1 |
| 3 gateways max (Discord, OpenWebUI, TUI) | Minimal complexity, focused on essential surfaces | §3.3 |
| Curator in deferred queue mode | Prevent processing delays during main agent loop | §12.2 |
| Per-kit failure budget of 3 | Fail fast to escalation rather than infinite retries | §12.1 |
| 1 req/3sec arXiv rate limit | Avoid IP bans, research repo isolation | §5.4, §12.5 |
| Kit-based memory profiles | Workflow isolation, prevents memory bleed | §5.7 |
| pr-only workspace approval mode | Prevents accidental repo changes | §12.9 |
| 25W default thermal mode | Minimize heat and power draw on Jetson | §12.8 |

---

## Troubleshooting

### If removal script fails mid-way
```bash
# Check git status
git status

# See what was committed
git log --oneline -n 20

# Revert to before removal
git reset --hard HEAD~10  # or specific commit
```

### If verification fails
```bash
# See what's still present
bash scripts/verify-removal.sh 2>&1 | grep "✗"

# Manually remove remaining files
rm -rf <path>
```

### If imports are still broken
```bash
# Find all remaining problematic imports
grep -r "codex\|bedrock\|gemini" agent/ --include="*.py" | grep -v "__pycache__"

# Remove manually or with sed:
sed -i '/^from.*codex/d' agent/account_usage.py
```

---

## Files This Phase Creates

✅ Configuration
- lite-config.yaml
- lite-removed.manifest.yaml

✅ Scripts
- scripts/install-lite.sh
- scripts/install-lite.sh (executable)
- scripts/phase1-removal.sh
- scripts/verify-removal.sh

✅ Infrastructure
- Dockerfile.lite
- systemd/hermes-lite.service

📝 Documentation
- phase1-removal.md (this file)
- codex-cleanup-needed.txt (generated if needed)
- bedrock-test-cleanup-needed.txt (generated if needed)

---

## Validation Checklist

After Phase 1 completion, verify:

- [ ] All agent adapters removed
- [ ] All gateway platforms except discord removed
- [ ] web/ and website/ directories removed
- [ ] All removed plugin directories gone
- [ ] All removed skill directories gone
- [ ] No dangling imports (run verify-removal.sh)
- [ ] No Dockerfile or setup-hermes.sh (replaced)
- [ ] lite-config.yaml present
- [ ] Dockerfile.lite present
- [ ] systemd/hermes-lite.service present
- [ ] scripts/install-lite.sh present
- [ ] Manual cleanup files reviewed and resolved
- [ ] Core tests still pass (scripts/run_tests.sh)

---

## References

- REDESIGN.md §14 - Removal specification
- REDESIGN.md §3 - Allowed components
- REDESIGN.md §7 - Deployment infrastructure
- REDESIGN.md §12 - Critical decisions

---

## Questions or Issues?

See REDESIGN.md for full specification and rationale for each removal.
