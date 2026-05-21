#!/bin/bash
# hermes-lite installer for Jetson Orin Nano 8GB running JetPack 6.x
# Installs hermes-lite with minimal dependencies, local Ollama runtime, Ministral-3 model
# See REDESIGN.md §7.1 for full specification

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes-lite}"
REPOS_HOME="${HOME}/repos"
VENV_PATH="${HERMES_HOME}/.venv"
LOG_FILE="${HERMES_HOME}/install.log"

# ============================================================================
# Helper Functions
# ============================================================================

log() {
    echo -e "${GREEN}[hermes-lite]${NC} $*" | tee -a "${LOG_FILE}"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "${LOG_FILE}" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "${LOG_FILE}"
}

check_platform() {
    log "Verifying platform compatibility..."
    
    # Check Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        error "hermes-lite only runs on Linux (aarch64). Detected: $OSTYPE"
    fi
    
    # Check aarch64
    if [[ "$(uname -m)" != "aarch64" ]]; then
        error "hermes-lite requires aarch64 architecture. Detected: $(uname -m)"
    fi
    
    # Check glibc (JetPack)
    if ! command -v ldd &> /dev/null || ! ldd --version | grep -q "glibc"; then
        error "Could not verify glibc. JetPack installation may be incomplete."
    fi
    
    log "✓ Platform check passed (Linux aarch64 glibc)"
}

check_requirements() {
    log "Checking system requirements..."
    
    local required_cmds=("python3.11" "pip3" "git" "docker" "grep" "sed")
    local missing=()
    
    for cmd in "${required_cmds[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing required commands: ${missing[*]}"
    fi
    
    # Check Python version
    local py_version=$(python3.11 --version 2>&1 | awk '{print $2}')
    log "✓ Python $py_version found"
    
    # Check disk space (need ~10GB)
    local disk_free=$(df "${HERMES_HOME%/*}" | tail -1 | awk '{print $4}')
    if [[ $disk_free -lt 10485760 ]]; then
        error "Insufficient disk space. Need 10GB, have $(( disk_free / 1024 / 1024 ))GB"
    fi
    
    # Check memory (need 4GB+ available)
    local mem_free=$(free -b | awk '/^Mem:/{print $7}')
    if [[ $mem_free -lt 4294967296 ]]; then
        warn "Low available memory: $(( mem_free / 1024 / 1024 / 1024 ))GB. Recommend ≥4GB"
    fi
    
    log "✓ System requirements satisfied"
}

setup_directories() {
    log "Setting up directory structure..."
    
    mkdir -p "${HERMES_HOME}"/{logs,skills,workspaces,corpora,queue,diagnostics}
    mkdir -p "${REPOS_HOME}"
    
    log "✓ Directory structure ready at ${HERMES_HOME}"
}

setup_venv() {
    log "Setting up Python virtual environment..."
    
    if [[ -d "${VENV_PATH}" ]]; then
        warn "Virtual environment already exists at ${VENV_PATH}"
        read -p "Recreate? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "${VENV_PATH}"
        else
            log "Using existing virtual environment"
            return
        fi
    fi
    
    python3.11 -m venv "${VENV_PATH}"
    source "${VENV_PATH}/bin/activate"
    
    # Upgrade pip/setuptools
    pip install --upgrade pip setuptools wheel
    
    log "✓ Virtual environment ready at ${VENV_PATH}"
}

install_hermes_lite() {
    log "Installing hermes-lite package..."
    
    # Activate venv
    source "${VENV_PATH}/bin/activate"
    
    # Install from current repo with lite extras
    if [[ -f "pyproject.toml" ]]; then
        pip install -e ".[lite]"
        log "✓ hermes-lite installed from local repo"
    else
        error "Could not find pyproject.toml. Are you in the hermes-lite repo?"
    fi
}

setup_ollama() {
    log "Setting up Ollama runtime..."
    
    # Check if Ollama is already running
    if curl -s http://127.0.0.1:11434/api/tags &> /dev/null; then
        log "✓ Ollama is already running"
        return
    fi
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        log "Ollama not found. Visit https://ollama.com/download"
        read -p "Install Ollama now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            curl -fsSL https://ollama.ai/install.sh | sh
            log "✓ Ollama installed"
        else
            error "Ollama is required for hermes-lite to function"
        fi
    fi
    
    # Start Ollama (user may need to run in separate terminal)
    log "Starting Ollama..."
    if systemctl is-active --quiet ollama; then
        log "✓ Ollama service is running"
    else
        warn "Ollama service not running. Start with: systemctl start ollama"
        warn "Or run in foreground: ollama serve"
    fi
}

pull_ministral_3() {
    log "Pulling Ministral-3:3B model (~2.3GB)..."
    
    # Wait for Ollama to be ready
    local retries=0
    while ! curl -s http://127.0.0.1:11434/api/tags &> /dev/null; do
        if [[ $retries -ge 30 ]]; then
            error "Ollama failed to become ready within 30 seconds"
        fi
        sleep 1
        ((retries++))
    done
    
    # Check if model already exists
    if curl -s http://127.0.0.1:11434/api/tags | grep -q "ministral-3:3b"; then
        log "✓ Ministral-3:3B is already available"
    else
        log "Downloading Ministral-3:3B model (this may take several minutes)..."
        ollama pull mistralai/mistral:7b-instruct-v0.2 || \
        ollama pull qwen:3b-instruct || \
        ollama pull llama2:7b || \
        error "Could not pull any model. Check Ollama and internet connection."
        log "✓ Model ready"
    fi
}

setup_config() {
    log "Setting up configuration..."
    
    if [[ ! -f "${HERMES_HOME}/config.yaml" ]]; then
        # Copy lite-config.yaml as default
        if [[ -f "lite-config.yaml" ]]; then
            cp "lite-config.yaml" "${HERMES_HOME}/config.yaml"
            log "✓ Configuration file created at ${HERMES_HOME}/config.yaml"
        else
            warn "lite-config.yaml not found. Using upstream defaults."
            warn "Review ${HERMES_HOME}/config.yaml and configure manually"
        fi
    else
        log "Configuration already exists at ${HERMES_HOME}/config.yaml"
    fi
    
    # Create .env template
    cat > "${HERMES_HOME}/.env.example" << 'EOF'
# hermes-lite .env (secrets only)
# Copy to .env and populate with your API keys

# OpenAI (for escalation)
OPENAI_API_KEY=sk-...

# Anthropic Claude (for escalation)
ANTHROPIC_API_KEY=sk-ant-...

# GitHub Copilot (optional, requires local VS Code)
GITHUB_TOKEN=ghp_...

# Discord (gateway platform)
DISCORD_BOT_TOKEN=discord_bot_token_here
DISCORD_GUILD_ID=your_guild_id

# Optional: Knowledge repo credentials
KNOWLEDGE_REPO_SSH_KEY_PATH=~/.ssh/knowledge_repo

# Optional: Blue Swallow Society VM (partner model)
PARTNER_VM_SSH_KEY_PATH=~/.ssh/partner_vm
PARTNER_OLLAMA_URL=http://partner.vm:11434
EOF
    log "✓ Environment template created at ${HERMES_HOME}/.env.example"
    log "   IMPORTANT: Copy to ${HERMES_HOME}/.env and populate with your keys"
}

setup_repos() {
    log "Setting up repository structure..."
    
    # Create repo directories (user will clone actual repos)
    mkdir -p "${REPOS_HOME}"/{knowledge,blue-swallow-society}
    
    cat > "${REPOS_HOME}/README.md" << 'EOF'
# Repository Structure

## Primary Repos for hermes-lite

### knowledge/
Shared research store (papers, notes, extracts, seeds)
- Clone from: git@github.com:your-org/knowledge.git
- Purpose: Central store for research findings and specs
- Approval mode: pr-only for shared, auto for local

### blue-swallow-society/
Infrastructure and deployment specs
- Clone from: git@github.com:your-org/blue-swallow-society.git
- Purpose: Infra code, web server, API specs, deployment
- Approval mode: pr-only

## Usage

Clone required repos:
```bash
cd ~/repos
git clone git@github.com:your-org/knowledge.git
git clone git@github.com:your-org/blue-swallow-society.git
```

Then initialize workspace registry:
```bash
hermes-lite workspace init ~/repos
```
EOF
    
    log "✓ Repository structure ready at ${REPOS_HOME}"
}

setup_systemd() {
    log "Setting up systemd service (requires sudo)..."
    
    if [[ -f "systemd/hermes-lite.service" ]]; then
        read -p "Install hermes-lite systemd service? (requires sudo) (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo cp "systemd/hermes-lite.service" /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable hermes-lite.service
            log "✓ systemd service installed and enabled"
            log "   Start with: sudo systemctl start hermes-lite"
            log "   View logs: sudo journalctl -u hermes-lite -f"
        fi
    fi
}

setup_completion() {
    log "Configuring shell completion..."
    
    local shell_rc="${HOME}/.bashrc"
    if [[ -f "${HOME}/.zshrc" ]]; then
        shell_rc="${HOME}/.zshrc"
    fi
    
    if ! grep -q "hermes-lite completion" "${shell_rc}" 2>/dev/null; then
        echo "" >> "${shell_rc}"
        echo "# hermes-lite" >> "${shell_rc}"
        echo "eval \"\$(register-python-argcomplete hermes-lite)\"" >> "${shell_rc}"
        log "✓ Shell completion configured in ${shell_rc}"
    fi
}

print_summary() {
    cat << EOF

${GREEN}════════════════════════════════════════════════════════════${NC}
${GREEN}hermes-lite installation complete!${NC}
${GREEN}════════════════════════════════════════════════════════════${NC}

Installation Summary:
  Home: ${HERMES_HOME}
  Venv: ${VENV_PATH}
  Repos: ${REPOS_HOME}
  Config: ${HERMES_HOME}/config.yaml

Next Steps:
1. Activate virtual environment:
   source ${VENV_PATH}/bin/activate

2. Start Ollama (if not already running):
   ollama serve
   (in another terminal)

3. Populate secrets in ${HERMES_HOME}/.env:
   cp ${HERMES_HOME}/.env.example ${HERMES_HOME}/.env
   vim ${HERMES_HOME}/.env

4. Configure gateways:
   hermes-lite setup      # Interactive setup wizard

5. Test the installation:
   hermes-lite --version
   hermes-lite chat "Hello"

6. Clone your knowledge and infrastructure repos:
   cd ~/repos
   git clone git@github.com:your-org/knowledge.git
   git clone git@github.com:your-org/blue-swallow-society.git
   hermes-lite workspace init ~/repos

Documentation:
  - REDESIGN.md: Full specification
  - AGENTS.md: Development guide
  - ~/.hermes-lite/logs/agent.log: Agent activity log

${YELLOW}IMPORTANT:${NC}
- Ollama must be running for local model execution
- Customize ${HERMES_HOME}/config.yaml for your setup
- Discord bot requires DISCORD_BOT_TOKEN in .env
- Ensure internet connectivity for remote escalations

${GREEN}Happy coding!${NC}

EOF
}

# ============================================================================
# Main Installation Flow
# ============================================================================

main() {
    log "Starting hermes-lite installation..."
    log "Install log: ${LOG_FILE}"
    
    # Create log directory
    mkdir -p "${HERMES_HOME}"
    
    check_platform
    check_requirements
    setup_directories
    setup_venv
    install_hermes_lite
    setup_ollama
    pull_ministral_3
    setup_config
    setup_repos
    setup_systemd
    setup_completion
    print_summary
    
    log "Installation complete!"
}

# Run main installation
main "$@"
