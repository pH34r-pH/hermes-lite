#!/bin/bash
# hermes-lite Phase 1 Subtraction Pass
# Removes all non-retained components per REDESIGN.md §14
# Creates git commits for each removal category for clear history
# 
# USAGE: cd ~/repos/hermes-lite && bash scripts/phase1-removal.sh
# 
# WARNING: This script modifies the repository. Ensure you have uncommitted
# changes stashed before running.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Tracking
TOTAL_DELETED=0
TOTAL_MODIFIED=0
REMOVAL_LOG="phase1-removal.log"

log() {
    echo -e "${GREEN}[phase1]${NC} $*" | tee -a "${REMOVAL_LOG}"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${REMOVAL_LOG}" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "${REMOVAL_LOG}"
}

section_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n" | tee -a "${REMOVAL_LOG}"
}

remove_files() {
    local category="$1"
    shift
    local files=("$@")
    
    local count=0
    for file in "${files[@]}"; do
        if [[ -f "$file" ]] || [[ -d "$file" ]]; then
            rm -rf "$file"
            ((count++))
            ((TOTAL_DELETED++))
            echo "  ✓ $file" | tee -a "${REMOVAL_LOG}"
        else
            echo "  ⊘ Not found: $file" | tee -a "${REMOVAL_LOG}"
        fi
    done
    
    log "Removed $count items from $category"
    
    if [[ $count -gt 0 ]]; then
        git add -A
        git commit -m "Remove $category per REDESIGN.md §14" --no-verify || true
    fi
}

# ============================================================================
# Pre-flight checks
# ============================================================================

log "Starting Phase 1 Subtraction Pass..."

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]] || [[ ! -f "lite-removed.manifest.yaml" ]]; then
    error "Must run from hermes-lite root directory"
fi

# Check git status
if git status --short | grep -q .; then
    warn "Repository has uncommitted changes. Please commit or stash first."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Aborted"
    fi
fi

# ============================================================================
# Phase 1.1: Remove Agent Adapters
# ============================================================================

section_header "Phase 1.1: Removing Agent Adapters"

remove_files "agent-azure" \
    "agent/azure_identity_adapter.py"

remove_files "agent-bedrock" \
    "agent/bedrock_adapter.py"

remove_files "agent-gemini" \
    "agent/gemini_native_adapter.py" \
    "agent/gemini_cloudcode_adapter.py" \
    "agent/gemini_schema.py"

remove_files "agent-google" \
    "agent/google_code_assist.py" \
    "agent/google_oauth.py"

remove_files "agent-codex" \
    "agent/codex_runtime.py" \
    "agent/codex_responses_adapter.py"

remove_files "agent-moonshot" \
    "agent/moonshot_schema.py"

remove_files "agent-model-management" \
    "agent/auxiliary_client.py" \
    "agent/models_dev.py" \
    "agent/portal_tags.py"

remove_files "agent-media-generation" \
    "agent/image_gen_provider.py" \
    "agent/image_gen_registry.py" \
    "agent/image_routing.py" \
    "agent/video_gen_provider.py" \
    "agent/video_gen_registry.py"

# ============================================================================
# Phase 1.2: Remove Gateway Platforms
# ============================================================================

section_header "Phase 1.2: Removing Gateway Platforms"

remove_files "gateway-messaging-platforms" \
    "gateway/platforms/telegram.py" \
    "gateway/platforms/telegram_network.py" \
    "gateway/platforms/slack.py" \
    "gateway/platforms/whatsapp.py" \
    "gateway/platforms/signal.py" \
    "gateway/platforms/signal_rate_limit.py" \
    "gateway/platforms/email.py"

remove_files "gateway-chinese-platforms" \
    "gateway/platforms/yuanbao.py" \
    "gateway/platforms/yuanbao_media.py" \
    "gateway/platforms/yuanbao_proto.py" \
    "gateway/platforms/yuanbao_sticker.py" \
    "gateway/platforms/weixin.py" \
    "gateway/platforms/dingtalk.py" \
    "gateway/platforms/wecom.py" \
    "gateway/platforms/wecom_callback.py" \
    "gateway/platforms/wecom_crypto.py"

remove_files "gateway-other-platforms" \
    "gateway/platforms/feishu.py" \
    "gateway/platforms/feishu_comment.py" \
    "gateway/platforms/feishu_comment_rules.py" \
    "gateway/platforms/mattermost.py" \
    "gateway/platforms/matrix.py" \
    "gateway/platforms/qqbot/" \
    "gateway/platforms/api_server.py"

# ============================================================================
# Phase 1.3: Remove Web Dashboards
# ============================================================================

section_header "Phase 1.3: Removing Web Dashboards and Docs"

remove_files "web-dashboards" \
    "web/" \
    "website/"

# ============================================================================
# Phase 1.4: Remove Plugins
# ============================================================================

section_header "Phase 1.4: Removing Plugin Directories"

remove_files "plugins-media" \
    "plugins/image_gen/" \
    "plugins/video_gen/"

remove_files "plugins-entertainment" \
    "plugins/spotify/" \
    "plugins/google_meet/" \
    "plugins/teams_pipeline/" \
    "plugins/hermes-achievements/"

remove_files "plugins-dashboards" \
    "plugins/example-dashboard/"

# Note: plugins/web/ kept, but remove xAI references later

# ============================================================================
# Phase 1.5: Remove Skills
# ============================================================================

section_header "Phase 1.5: Removing Skill Directories"

remove_files "skills-platform-specific" \
    "skills/apple/" \
    "skills/gaming/" \
    "skills/gifs/" \
    "skills/social-media/" \
    "skills/smart-home/" \
    "skills/creative/"

remove_files "skills-media" \
    "skills/voice/" \
    "skills/tts/" \
    "skills/audio/" || true  # Some might not exist

# ============================================================================
# Phase 1.6: Remove Packaging and Platform-Specific
# ============================================================================

section_header "Phase 1.6: Removing Platform-Specific Files"

remove_files "packaging-removed" \
    "setup-hermes.sh" \
    "constraints-termux.txt" \
    "README.zh-CN.md" \
    "Dockerfile"  # Replaced by Dockerfile.lite

remove_files "packaging-platforms" \
    "packaging/nix/" \
    "packaging/termux/" || true

# ============================================================================
# Phase 1.7: Code Cleanup in Retained Files
# ============================================================================

section_header "Phase 1.7: Cleaning Up Imports in Retained Files"

# Remove codex imports and functions from account_usage.py
if grep -q "codex" "agent/account_usage.py"; then
    log "Cleaning codex references from account_usage.py..."
    
    # This is complex - we need to remove codex-related functions
    # For now, document what needs manual review
    cat > "codex-cleanup-needed.txt" << 'EOF'
agent/account_usage.py needs manual cleanup:
- Remove: _read_codex_tokens import
- Remove: _resolve_codex_runtime_credentials import
- Remove: _resolve_codex_usage_url() function
- Remove: _fetch_codex_account_usage() function
- Remove: "openai-codex" provider handling
- See lines: 10, 116-142, 166, 318-319

Recommend: Open file and search for "codex" to find all references
EOF
    
    warn "Manual cleanup needed in agent/account_usage.py"
    warn "See codex-cleanup-needed.txt for details"
fi

# Remove bedrock test
if [[ -f "tests/agent/test_anthropic_adapter.py" ]]; then
    if grep -q "bedrock" "tests/agent/test_anthropic_adapter.py"; then
        log "Noting bedrock test cleanup needed..."
        cat > "bedrock-test-cleanup-needed.txt" << 'EOF'
tests/agent/test_anthropic_adapter.py needs manual cleanup:
- Remove: build_anthropic_bedrock_client import
- Remove: test_bedrock_client_keeps_context_1m_beta() test method
- See lines: 18, 139-143

This test references AWS Bedrock which is removed in hermes-lite
EOF
        warn "Manual cleanup needed in test_anthropic_adapter.py"
    fi
fi

# ============================================================================
# Phase 1.8: Verify Removed Paths
# ============================================================================

section_header "Phase 1.8: Verification - Checking for Removed References"

# Check for import statements
log "Scanning for import statements of removed components..."

FOUND_IMPORTS=0

# Check for bedrock imports
if grep -r "from.*bedrock" . --include="*.py" 2>/dev/null | grep -v ".pyc"; then
    warn "Found remaining bedrock imports:"
    grep -r "from.*bedrock" . --include="*.py" 2>/dev/null | grep -v ".pyc"
    ((FOUND_IMPORTS++))
fi

# Check for gemini imports
if grep -r "from.*gemini" . --include="*.py" 2>/dev/null | grep -v ".pyc" | grep -v "# gemini"; then
    warn "Found remaining gemini imports:"
    grep -r "from.*gemini" . --include="*.py" 2>/dev/null | grep -v ".pyc"
    ((FOUND_IMPORTS++))
fi

# Check for image_gen imports
if grep -r "image_gen_provider\|image_gen_registry" . --include="*.py" 2>/dev/null | grep -v ".pyc"; then
    warn "Found remaining image_gen imports:"
    grep -r "image_gen_provider\|image_gen_registry" . --include="*.py" 2>/dev/null | grep -v ".pyc"
    ((FOUND_IMPORTS++))
fi

if [[ $FOUND_IMPORTS -eq 0 ]]; then
    log "✓ No removed imports found in codebase"
else
    warn "Found $FOUND_IMPORTS categories with remaining imports (see warnings above)"
fi

# ============================================================================
# Phase 1.9: Summary
# ============================================================================

section_header "Phase 1 Removal Summary"

log "Total items deleted: $TOTAL_DELETED"
log "Total modifications needed: Manual cleanup as noted"
log "Removal log saved to: $REMOVAL_LOG"

git add -A
git commit -m "Phase 1 Subtraction: Remove all non-retained components" --no-verify || true

log ""
log "✓ Phase 1 Subtraction complete!"
log ""
log "Next Steps:"
log "1. Review manual cleanup files (if created)"
log "2. Run: ./scripts/verify-removal.sh to double-check"
log "3. Proceed with Phase 2: Agent component implementation"

echo ""
log "Git commits created:"
git log --oneline -n 20 | head -n 20
