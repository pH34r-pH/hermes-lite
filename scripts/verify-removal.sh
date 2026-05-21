#!/bin/bash
# hermes-lite Phase 1 Verification
# Verifies that all removed components have been successfully deleted
# and no dangling references remain
#
# USAGE: cd ~/repos/hermes-lite && bash scripts/verify-removal.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

log_ok() {
    echo -e "${GREEN}✓${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*"
    ((ERRORS++))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $*"
    ((WARNINGS++))
}

check_file_removed() {
    local file="$1"
    local name="$2"
    
    if [[ -e "$file" ]]; then
        log_error "File still exists: $file ($name)"
    else
        log_ok "Removed: $file"
    fi
}

check_dir_removed() {
    local dir="$1"
    local name="$2"
    
    if [[ -d "$dir" ]]; then
        log_error "Directory still exists: $dir ($name)"
        ls -la "$dir" | head -5
    else
        log_ok "Removed: $dir"
    fi
}

check_import_absent() {
    local pattern="$1"
    local name="$2"
    
    if grep -r "$pattern" . --include="*.py" 2>/dev/null | grep -v ".pyc" | grep -v "test" | grep -v "^Binary"; then
        log_error "Found import: $name"
        echo "  References:"
        grep -r "$pattern" . --include="*.py" 2>/dev/null | grep -v ".pyc" | head -3
    else
        log_ok "No imports: $name"
    fi
}

section_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

# ============================================================================
# Check Agent Adapters
# ============================================================================

section_header "Verifying Agent Adapter Removals"

check_file_removed "agent/azure_identity_adapter.py" "Azure"
check_file_removed "agent/bedrock_adapter.py" "Bedrock"
check_file_removed "agent/gemini_native_adapter.py" "Gemini"
check_file_removed "agent/gemini_cloudcode_adapter.py" "Gemini Cloud"
check_file_removed "agent/gemini_schema.py" "Gemini Schema"
check_file_removed "agent/google_code_assist.py" "Google Code"
check_file_removed "agent/google_oauth.py" "Google OAuth"
check_file_removed "agent/codex_runtime.py" "Codex Runtime"
check_file_removed "agent/codex_responses_adapter.py" "Codex Adapter"
check_file_removed "agent/moonshot_schema.py" "Moonshot"
check_file_removed "agent/auxiliary_client.py" "Auxiliary"
check_file_removed "agent/models_dev.py" "Models Dev"
check_file_removed "agent/portal_tags.py" "Portal"
check_file_removed "agent/image_gen_provider.py" "Image Gen"
check_file_removed "agent/image_gen_registry.py" "Image Registry"
check_file_removed "agent/image_routing.py" "Image Routing"
check_file_removed "agent/video_gen_provider.py" "Video Gen"
check_file_removed "agent/video_gen_registry.py" "Video Registry"

# ============================================================================
# Check Gateway Platforms
# ============================================================================

section_header "Verifying Gateway Platform Removals"

check_file_removed "gateway/platforms/telegram.py" "Telegram"
check_file_removed "gateway/platforms/slack.py" "Slack"
check_file_removed "gateway/platforms/whatsapp.py" "WhatsApp"
check_file_removed "gateway/platforms/signal.py" "Signal"
check_file_removed "gateway/platforms/email.py" "Email"
check_file_removed "gateway/platforms/yuanbao.py" "Yuanbao"
check_file_removed "gateway/platforms/weixin.py" "WeChat"
check_file_removed "gateway/platforms/dingtalk.py" "DingTalk"
check_dir_removed "gateway/platforms/qqbot/" "QQBot"

# ============================================================================
# Check Web and Website
# ============================================================================

section_header "Verifying Web Dashboard Removals"

check_dir_removed "web/" "Web Dashboard"
check_dir_removed "website/" "Documentation Website"

# ============================================================================
# Check Plugins
# ============================================================================

section_header "Verifying Plugin Removals"

check_dir_removed "plugins/image_gen/" "Image Gen Plugin"
check_dir_removed "plugins/video_gen/" "Video Gen Plugin"
check_dir_removed "plugins/spotify/" "Spotify Plugin"
check_dir_removed "plugins/google_meet/" "Google Meet Plugin"
check_dir_removed "plugins/hermes-achievements/" "Achievements Plugin"

# ============================================================================
# Check Skills
# ============================================================================

section_header "Verifying Skill Removals"

check_dir_removed "skills/apple/" "Apple Skills"
check_dir_removed "skills/gaming/" "Gaming Skills"
check_dir_removed "skills/gifs/" "GIF Skills"
check_dir_removed "skills/social-media/" "Social Media Skills"
check_dir_removed "skills/smart-home/" "Smart Home Skills"
check_dir_removed "skills/creative/" "Creative Skills"
check_dir_removed "skills/voice/" "Voice Skills"
check_dir_removed "skills/tts/" "Text-to-Speech Skills"

# ============================================================================
# Check Packaging
# ============================================================================

section_header "Verifying Packaging Changes"

check_file_removed "setup-hermes.sh" "Setup Script"
check_file_removed "constraints-termux.txt" "Termux Constraints"
check_file_removed "Dockerfile" "Old Dockerfile (replaced by Dockerfile.lite)"

# ============================================================================
# Check for Dangling Imports
# ============================================================================

section_header "Checking for Dangling Imports and References"

check_import_absent "bedrock_adapter" "Bedrock adapter import"
check_import_absent "gemini.*_adapter" "Gemini adapter import"
check_import_absent "codex.*_adapter" "Codex adapter import"
check_import_absent "azure_identity_adapter" "Azure adapter import"
check_import_absent "image_gen_provider" "Image gen import"
check_import_absent "video_gen_provider" "Video gen import"

# ============================================================================
# Check for Removed Platforms in Gateway Init
# ============================================================================

section_header "Checking Gateway Platform References"

if [[ -f "gateway/__init__.py" ]]; then
    if grep -q "telegram\|slack\|whatsapp" "gateway/__init__.py"; then
        log_error "Removed platforms still referenced in gateway/__init__.py"
    else
        log_ok "No removed platforms in gateway/__init__.py"
    fi
fi

# ============================================================================
# Check Retained Key Files
# ============================================================================

section_header "Verifying Retained Critical Files"

declare -a retained_files=(
    "agent/conversation_loop.py"
    "agent/prompt_builder.py"
    "agent/anthropic_adapter.py"
    "agent/copilot_acp_client.py"
    "gateway/platforms/discord.py"
    "tui_gateway/"
    "ui-tui/"
    "hermes_state.py"
)

for file in "${retained_files[@]}"; do
    if [[ -e "$file" ]]; then
        log_ok "Retained: $file"
    else
        log_error "Missing retained file: $file"
    fi
done

# ============================================================================
# Check New Files Created
# ============================================================================

section_header "Verifying New hermes-lite Files"

declare -a new_files=(
    "lite-config.yaml"
    "lite-removed.manifest.yaml"
    "Dockerfile.lite"
    "systemd/hermes-lite.service"
    "scripts/install-lite.sh"
)

for file in "${new_files[@]}"; do
    if [[ -e "$file" ]]; then
        log_ok "Created: $file"
    else
        log_error "Missing new file: $file"
    fi
done

# ============================================================================
# Summary
# ============================================================================

section_header "Verification Summary"

if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ All verification checks passed!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    if [[ $WARNINGS -gt 0 ]]; then
        echo ""
        echo "⚠  $WARNINGS warnings found - review above"
    fi
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}✗ Verification failed with $ERRORS errors${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    exit 1
fi
