#!/bin/bash
# ============================================================================
# Hermes Lite Installer — Linux-only
# ============================================================================
# Usage:
#   scripts/install.sh
#
# Requirements:
#   - Linux (uname == Linux)
#   - Python 3.11+
#   - git, curl
#
# ============================================================================

set -e

if [ "$(uname -s)" != "Linux" ]; then
    echo "Error: hermes-lite is Linux-only. This installer does not support $(uname -s)."
    exit 1
fi

PYTHON_CMD=""
for cmd in python3.11 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        version="$($cmd -V 2>&1 | awk '{print $2}')"
        major="${version%%.*}"
        minor="${version#*.}"
        minor="${minor%%.*}"
        if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.11+ is required but not found."
    echo "Install Python 3.11 (e.g. sudo apt install python3.11 python3.11-venv) and retry."
    exit 1
fi

echo "Using Python: $PYTHON_CMD ($($PYTHON_CMD -V))"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$HOME/.hermes-lite/venv"
BIN_DIR="$HOME/.local/bin"

# Recreate venv if it exists but looks stale (no pip or wrong Python version)
_needs_recreate=false
if [ -d "$VENV_DIR" ]; then
    if [ ! -f "$VENV_DIR/bin/pip" ]; then
        _needs_recreate=true
    else
        _venv_python="$VENV_DIR/bin/python"
        _venv_version="$($_venv_python -V 2>&1 | awk '{print $2}')"
        if [ "$_venv_version" != "$($PYTHON_CMD -V 2>&1 | awk '{print $2}')" ]; then
            _needs_recreate=true
        fi
    fi
fi

if [ "$_needs_recreate" = true ]; then
    echo "Recreating stale venv at $VENV_DIR ..."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating venv at $VENV_DIR ..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Upgrade pip inside venv
python -m pip install --quiet --upgrade pip

echo "Installing hermes-agent[lite] from $REPO_ROOT ..."
cd "$REPO_ROOT"
pip install --quiet -e ".[lite]"

# Ensure ~/.local/bin exists and symlink hermes-lite entrypoint
mkdir -p "$BIN_DIR"
ENTRYPOINT="$VENV_DIR/bin/hermes-lite"
SYMLINK="$BIN_DIR/hermes-lite"

if [ -L "$SYMLINK" ] || [ -e "$SYMLINK" ]; then
    rm -f "$SYMLINK"
fi
ln -s "$ENTRYPOINT" "$SYMLINK"

# Also symlink hermes for convenience
HERMES_SYMLINK="$BIN_DIR/hermes"
if [ -L "$HERMES_SYMLINK" ] || [ -e "$HERMES_SYMLINK" ]; then
    rm -f "$HERMES_SYMLINK"
fi
ln -s "$VENV_DIR/bin/hermes" "$HERMES_SYMLINK" 2>/dev/null || true

# Ensure ~/.local/bin is on PATH
_shell_rc=""
if [ -n "${BASH_VERSION:-}" ]; then
    _shell_rc="$HOME/.bashrc"
elif [ -n "${ZSH_VERSION:-}" ]; then
    _shell_rc="$HOME/.zshrc"
fi

if [ -n "$_shell_rc" ] && [ -f "$_shell_rc" ]; then
    if ! grep -q "$BIN_DIR" "$_shell_rc" 2>/dev/null; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$_shell_rc"
        echo "Added $BIN_DIR to PATH in $_shell_rc"
    fi
fi

# Systemd unit installation (graceful skip when systemctl missing)
if command -v systemctl >/dev/null 2>&1; then
    SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_USER_DIR"
    if [ -f "$REPO_ROOT/systemd/hermes-lite.service" ]; then
        cp "$REPO_ROOT/systemd/hermes-lite.service" "$SYSTEMD_USER_DIR/hermes-lite.service"
        systemctl --user daemon-reload
        echo "Installed systemd user unit: hermes-lite.service"
        echo "Enable with: systemctl --user enable hermes-lite.service"
    fi
else
    echo "systemctl not found; skipping systemd unit installation."
fi

echo ""
echo "✓ hermes-lite installed at $SYMLINK"
echo "  Run: hermes-lite --version"
echo "  Or:  hermes-lite lite doctor"
