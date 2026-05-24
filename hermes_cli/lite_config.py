"""
Lite configuration profile loader for hermes-lite.

Loads ``lite-config.yaml`` from the repository root, validates against a
removed-provider denylist, merges with ``~/.hermes/config.yaml``, and returns
the effective configuration dict.
"""

import copy
import logging
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.resolve()
LITE_CONFIG_PATH = REPO_ROOT / "lite-config.yaml"


class ConfigurationError(Exception):
    """Raised when the merged lite configuration references a removed provider or gateway."""


# Denylists derived from 000-provider-cleanup and 001-gateway-cleanup specs.
# Kept in sync with lite-config.yaml removed_providers / removed_gateways.
_REMOVED_PROVIDERS = frozenset({
    "azure_foundry",
    "bedrock",
    "gemini_native",
    "gemini_cloudcode",
    "codex",
    "xai",
    "moonshot",
    "minimax",
    "huggingface_hub",
    "novitaai",
    "nvidia_nim",
    "mimo",
    "openrouter",
    "zai_glm",
    "nous_portal",
    "auxiliary",
    "lmstudio",
})

_REMOVED_GATEWAYS = frozenset({
    "telegram",
    "slack",
    "whatsapp",
    "signal",
    "email",
    "yuanbao",
    "weixin",
    "wecom",
    "feishu",
    "dingtalk",
    "qqbot",
    "matrix",
    "mattermost",
    "homeassistant",
    "bluebubbles",
    "sms",
    "msgraph_webhook",
    "webhook",
})


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *overlay* into *base* (mutates base)."""
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def _flatten_config(config: Dict[str, Any], prefix: str = "") -> List[Tuple[str, Any]]:
    """Yield (dotpath, value) pairs for every leaf in a nested dict."""
    for key, value in config.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from _flatten_config(value, path)
        else:
            yield (path, value)


def _scan_offenders(config: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Return list of (dotpath, offending_value, category) for denylist hits."""
    offenders: List[Tuple[str, str, str]] = []
    seen: set = set()

    # Keys that are allowed to contain removed names (the denylist declarations themselves)
    _ALLOWLIST_KEYS = {"removed_providers", "removed_gateways"}

    for path, value in _flatten_config(config):
        # Skip the denylist declaration keys
        if path in _ALLOWLIST_KEYS or path.split(".")[-1] in _ALLOWLIST_KEYS:
            continue

        def _norm(name: str) -> str:
            return name.lower().replace("-", "_")

        # String values
        if isinstance(value, str):
            low = _norm(value)
            if low in _REMOVED_PROVIDERS:
                key = (path, value, "provider")
                if key not in seen:
                    seen.add(key)
                    offenders.append(key)
            elif low in _REMOVED_GATEWAYS:
                key = (path, value, "gateway")
                if key not in seen:
                    seen.add(key)
                    offenders.append(key)
        # List values (e.g. enabled_gateways, escalation_order)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    low = _norm(item)
                    if low in _REMOVED_PROVIDERS:
                        key = (path, item, "provider")
                        if key not in seen:
                            seen.add(key)
                            offenders.append(key)
                    elif low in _REMOVED_GATEWAYS:
                        key = (path, item, "gateway")
                        if key not in seen:
                            seen.add(key)
                            offenders.append(key)

        # Check dict-key segments (e.g. "providers.bedrock.region")
        segments = path.lower().replace("-", "_").split(".")
        for rp in _REMOVED_PROVIDERS:
            if rp in segments:
                key = (path, f"key segment '{rp}'", "provider")
                if key not in seen:
                    seen.add(key)
                    offenders.append(key)
                break

    return offenders


def validate_lite_config(config: Dict[str, Any]) -> None:
    """Validate merged lite config against removed-provider/gateway denylist.

    Raises:
        ConfigurationError: If any removed provider or gateway is referenced,
            with the exact offending key path included in the message.
    """
    offenders = _scan_offenders(config)
    if not offenders:
        return

    messages = []
    for path, value, category in offenders:
        messages.append(
            f"  [{category}] {path} references removed {category} '{value}'"
        )

    raise ConfigurationError(
        "Lite profile configuration references removed providers/gateways:\n"
        + "\n".join(messages)
    )


def get_lite_home() -> Path:
    """Return the canonical hermes-lite home directory (~/.hermes-lite)."""
    override = os.environ.get("HERMES_LITE_HOME", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".hermes-lite"


def ensure_lite_home() -> Path:
    """Create ~/.hermes-lite/ and subdirectories with 0700 permissions.

    Returns the path to the lite home directory.
    """
    home = get_lite_home()
    home.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(home, stat.S_IRWXU)  # 0700
    except OSError:
        pass

    for sub in ("queue", "snapshots", "logs"):
        d = home / sub
        d.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(d, stat.S_IRWXU)  # 0700
        except OSError:
            pass

    # Seed empty curator queue file
    curator_queue = home / "queue" / "curator.jsonl"
    if not curator_queue.exists():
        curator_queue.touch(mode=0o600)

    return home


def load_lite_config(cli_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load and merge the lite configuration profile.

    Merge order (later wins):
      1. lite-config.yaml (repo root)
      2. ~/.hermes/config.yaml (user overlay)
      3. CLI overrides (optional dict passed by caller)

    Args:
        cli_overrides: Optional dict of CLI flag overrides.

    Returns:
        The effective configuration dict.

    Raises:
        ConfigurationError: If lite-config.yaml is missing or if the merged
            config references a removed provider or gateway.
    """
    if not LITE_CONFIG_PATH.exists():
        raise ConfigurationError(
            f"lite-config.yaml not found at {LITE_CONFIG_PATH}. "
            "The lite profile requires this file."
        )

    with open(LITE_CONFIG_PATH, encoding="utf-8") as f:
        base = yaml.safe_load(f) or {}

    ensure_lite_home()

    # Load user overlay from ~/.hermes/config.yaml
    from hermes_cli.config import get_config_path, _warn_config_parse_failure

    user_path = get_config_path()
    overlay: Dict[str, Any] = {}
    if user_path.exists():
        try:
            with open(user_path, encoding="utf-8") as f:
                overlay = yaml.safe_load(f) or {}
        except Exception as exc:
            _warn_config_parse_failure(user_path, exc)
            overlay = {}

    merged = copy.deepcopy(base)
    _deep_merge(merged, overlay)

    if cli_overrides:
        _deep_merge(merged, copy.deepcopy(cli_overrides))

    validate_lite_config(merged)

    # Expand env vars (mirrors upstream load_config behaviour)
    from hermes_cli.config import _expand_env_vars
    merged = _expand_env_vars(merged)

    logger.info(
        "Lite profile active: model=%s gateways=%s max_iterations=%s",
        merged.get("model"),
        merged.get("enabled_gateways"),
        merged.get("max_iterations"),
    )

    return merged
