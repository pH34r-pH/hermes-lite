#!/bin/bash
# ============================================================================
# Ollama Bootstrap Script for hermes-lite
# ============================================================================
# Detects, downloads, installs, and starts Ollama on Linux.
# Polls http://127.0.0.1:11434 until healthy or timeout.
#
# Usage:
#   scripts/bootstrap-ollama.sh
# ============================================================================

set -e

OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
OLLAMA_URL="${OLLAMA_HOST}/api/tags"
TIMEOUT=60

_is_jetson() {
    if [ -f /etc/nv_tegra_release ] || [ -d /usr/lib/aarch64-linux-gnu/tegra ]; then
        return 0
    fi
    return 1
}

_check_healthy() {
    curl -s -o /dev/null -w "%{http_code}" "$OLLAMA_URL" 2>/dev/null || echo "000"
}

# ---------------------------------------------------------------------------
# Detect existing Ollama
# ---------------------------------------------------------------------------
if command -v ollama >/dev/null 2>&1; then
    echo "Ollama already installed: $(ollama --version 2>&1 || true)"
else
    echo "Installing Ollama ..."
    # Try official install script
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL https://ollama.com/install.sh | bash
    else
        echo "Error: curl is required to download Ollama."
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Start daemon if not running
# ---------------------------------------------------------------------------
if [ "$(_check_healthy)" = "200" ]; then
    echo "Ollama daemon already running at $OLLAMA_HOST"
    exit 0
fi

if systemctl is-active --quiet ollama 2>/dev/null; then
    echo "Ollama systemd service is active but not responding yet."
else
    echo "Starting Ollama daemon ..."
    # Prefer systemd if available
    if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files ollama.service &>/dev/null; then
        sudo systemctl start ollama || true
    else
        nohup ollama serve >/dev/null 2>&1 &
        sleep 2
    fi
fi

# ---------------------------------------------------------------------------
# Poll for health
# ---------------------------------------------------------------------------
echo -n "Waiting for Ollama to become healthy"
_elapsed=0
while [ "$(_check_healthy)" != "200" ]; do
    if [ "$_elapsed" -ge "$TIMEOUT" ]; then
        echo ""
        echo "Error: Ollama did not become healthy within ${TIMEOUT}s."
        echo "Check logs: journalctl -u ollama --no-pager -n 50"
        exit 1
    fi
    sleep 1
    _elapsed=$((_elapsed + 1))
    echo -n "."
done
echo ""
echo "✓ Ollama is healthy at $OLLAMA_HOST"

# ---------------------------------------------------------------------------
# Jetson GPU warning
# ---------------------------------------------------------------------------
if _is_jetson; then
    if ! nvidia-smi -L &>/dev/null && [ ! -f /etc/nv_tegra_release ]; then
        : # not actually a Jetson with GPU runtime
    elif [ ! -d /usr/lib/aarch64-linux-gnu/tegra ]; then
        echo "Warning: JetPack runtime libraries not detected."
        echo "For GPU inference, install JetPack and ensure nvidia-docker runtime is available."
    fi
fi
