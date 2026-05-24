#!/bin/bash
# ============================================================================
# Pull ministral-3:3b for hermes-lite
# ============================================================================
# Ensures the model is present before exiting.
# Waits for any in-progress pull to complete.
#
# Usage:
#   scripts/pull-ministral-3.sh
# ============================================================================

set -e

MODEL="ministral-3:3b"
TIMEOUT=600

if ! command -v ollama >/dev/null 2>&1; then
    echo "Error: ollama is not installed. Run scripts/bootstrap-ollama.sh first."
    exit 1
fi

# Check if model already exists
if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$MODEL"; then
    echo "✓ Model $MODEL already present."
    exit 0
fi

# Detect if another pull is in progress (ollama ps shows running processes)
_wait_for_in_progress() {
    local waited=0
    while ollama ps 2>/dev/null | grep -q "pulling"; do
        if [ "$waited" -ge "$TIMEOUT" ]; then
            echo ""
            echo "Error: timed out waiting for another pull to complete."
            exit 1
        fi
        sleep 5
        waited=$((waited + 5))
        echo -n "."
    done
}

if ollama ps 2>/dev/null | grep -q "pulling"; then
    echo -n "Another pull is in progress; waiting"
    _wait_for_in_progress
    echo ""
fi

echo "Pulling $MODEL ..."
ollama pull "$MODEL"

# Verify presence
if ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$MODEL"; then
    echo "✓ Model $MODEL is ready."
    exit 0
else
    echo "Error: $MODEL does not appear in 'ollama list' after pull."
    exit 1
fi
