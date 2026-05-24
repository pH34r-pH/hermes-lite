"""Memory profile namespaces for hermes-lite.

Provides per-workflow memory isolation: research, spec, dev, web, azure,
infra, api, security.  Profile activation is a first-class kit transition
event.  The security profile is write-only to the /sec kit.

Reference: REDESIGN.md §5.7
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)

CANONICAL_PROFILES = frozenset({
    "research", "spec", "dev", "web", "azure", "infra", "api", "security"
})

# Default kit→profile bindings (primary profile first)
DEFAULT_KIT_BINDINGS: Dict[str, List[str]] = {
    "arxiv": ["research"],
    "spec-kit": ["spec", "dev"],
    "web-ops": ["web", "dev", "api"],
    "azure-ops": ["azure", "infra"],
    "security": ["security"],
    "dev": ["dev"],
}


class MemoryWriteDenied(PermissionError):
    """Raised when a non-security kit attempts to write the security profile."""

    def __init__(self, kit: str, profile: str) -> None:
        super().__init__(f"Kit '{kit}' is not allowed to write profile '{profile}'")
        self.kit = kit
        self.profile = profile


@dataclass(frozen=True)
class MemoryProfile:
    """Canonical profile definition."""
    name: str
    description: str = ""
    write_allowlist: tuple[str, ...] = ()

    def __post_init__(self):
        if not re.fullmatch(r"[a-z0-9]+", self.name):
            raise ValueError(f"Profile name must be lower-case alphanumeric: {self.name}")


@dataclass
class ProfileBinding:
    """Maps kit names to one or more memory profiles."""

    bindings: Dict[str, List[str]] = field(default_factory=lambda: dict(DEFAULT_KIT_BINDINGS))

    @classmethod
    def from_config(cls, config_path: Optional[Path] = None) -> "ProfileBinding":
        if config_path is None:
            config_path = Path.home() / ".hermes-lite" / "lite-config.yaml"
        if not config_path.exists():
            return cls()
        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            logger.warning("Failed to load lite-config.yaml for memory profiles: %s", exc)
            return cls()

        raw = data.get("memory_profiles", {}).get("bindings")
        if not raw:
            return cls()

        bindings: Dict[str, List[str]] = {}
        for kit, profiles in raw.items():
            if isinstance(profiles, str):
                profiles = [profiles]
            validated = []
            for p in profiles:
                if p in CANONICAL_PROFILES:
                    validated.append(p)
                else:
                    logger.warning("Unknown profile '%s' for kit '%s'; skipping", p, kit)
            if not validated:
                logger.warning("Kit '%s' has no valid profiles; falling back to 'dev'", kit)
                validated = ["dev"]
            bindings[kit] = validated
        return cls(bindings)

    def resolve(self, kit: str) -> List[str]:
        return list(self.bindings.get(kit, ["dev"]))


class SecurityProfileGuard:
    """Enforce write-only access to the 'security' profile for the /sec kit."""

    @staticmethod
    def check_write(kit: str, profile: str) -> None:
        if profile == "security" and kit != "security":
            raise MemoryWriteDenied(kit, profile)


class ProviderNamespaceMap:
    """Translate canonical profile names to provider-specific identifiers."""

    _TABLE: Dict[str, Dict[str, str]] = {
        "honcho": {},      # profile name is used as project name directly
        "mem0": {},        # profile name is namespace directly
        "retaindb": {},    # table prefix: "research_messages" etc.
        "supermemory": {}, # profile name is collection directly
    }

    @classmethod
    def to_provider_id(cls, provider: str, profile: str) -> str:
        if provider == "retaindb":
            return f"{profile}_messages"
        return profile


class CompositeRecallQuery:
    """Query multiple bound profiles and merge results with weighting."""

    def __init__(self, bindings: ProfileBinding) -> None:
        self.bindings = bindings

    def merge_results(
        self,
        kit: str,
        results_by_profile: Dict[str, List[dict]],
    ) -> List[dict]:
        """Merge per-profile recall results, ranking primary profile higher."""
        profiles = self.bindings.resolve(kit)
        scored: List[tuple[float, dict]] = []
        for rank, profile in enumerate(profiles):
            weight = 1.0 / (1 + rank)  # primary = 1.0, secondary = 0.5, ...
            for item in results_by_profile.get(profile, []):
                meta = item.get("metadata", {})
                meta["source_profile"] = profile
                item["metadata"] = meta
                scored.append((weight, item))
        # Simple stable sort by descending weight
        scored.sort(key=lambda x: -x[0])
        return [item for _weight, item in scored]
