"""Tool-surface slimmer for hermes-lite.

Exposes only the tools required by the active kit, validates schemas against
a per-kit allowlist, emits a deterministic SHA-256 digest for prefix-cache
keying, and refuses to load any tool whose module transitively imports a
removed provider.

Reference: REDESIGN.md §5.6
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ProviderRemovedError(ImportError):
    """Raised when a tool module transitively imports a removed provider."""

    def __init__(self, tool_name: str, offender: str, chain: list[str]) -> None:
        super().__init__(
            f"Tool '{tool_name}' imports removed provider '{offender}' via {chain}"
        )
        self.tool_name = tool_name
        self.offender = offender
        self.chain = chain


class SchemaValidationError(ValueError):
    """Raised when a tool schema fails allowlist or structural validation."""

    def __init__(self, tool_name: str, reason: str) -> None:
        super().__init__(f"Schema validation failed for '{tool_name}': {reason}")
        self.tool_name = tool_name
        self.reason = reason


# ---------------------------------------------------------------------------
# Allowlist loader
# ---------------------------------------------------------------------------

class KitAllowlist:
    """Maps kit names to ordered lists of allowed tool names."""

    DEFAULT_PATH = Path(__file__).with_name("tool_surface_allowlists.yaml")

    def __init__(self, path: Optional[Path | str] = None) -> None:
        self.path = Path(path) if path else self.DEFAULT_PATH
        self._mapping: dict[str, list[str]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            logger.warning("Kit allowlist not found at %s; using empty mapping.", self.path)
            self._mapping = {}
            return
        try:
            data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Failed to parse %s: %s", self.path, exc)
            self._mapping = {}
            return
        if not isinstance(data, dict):
            logger.error("Kit allowlist must be a YAML mapping: %s", self.path)
            self._mapping = {}
            return
        self._mapping = {k: (v if isinstance(v, list) else []) for k, v in data.items()}
        logger.info("Loaded allowlists for %d kit(s)", len(self._mapping))

    def reload(self) -> None:
        self._load()

    def tools_for(self, kit: str) -> list[str]:
        return list(self._mapping.get(kit, []))

    def kits(self) -> list[str]:
        return list(self._mapping.keys())


# ---------------------------------------------------------------------------
# Removed-provider denylist
# ---------------------------------------------------------------------------

class RemovedProviderDenylist:
    """Reads the denylist from lite-config.yaml."""

    def __init__(self, patterns: Optional[list[str]] = None) -> None:
        if patterns is None:
            patterns = self._load_from_config()
        self.patterns = set(patterns)

    @classmethod
    def _load_from_config(cls) -> list[str]:
        repo_root = Path(__file__).resolve().parents[1]
        config_path = repo_root / "lite-config.yaml"
        if not config_path.exists():
            logger.warning("lite-config.yaml not found; provider denylist empty.")
            return []
        try:
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Failed to load lite-config.yaml: %s", exc)
            return []
        return cfg.get("removed_providers", [])

    def is_removed(self, module_name: str) -> bool:
        norm = module_name.replace("-", "_").lower()
        for pat in self.patterns:
            if pat.lower() in norm or norm.startswith(pat.lower()):
                return True
        return False


# ---------------------------------------------------------------------------
# Import scanner
# ---------------------------------------------------------------------------

def _parse_imports(source_path: Path) -> list[str]:
    """Return top-level imported module names from a Python file."""
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    names: list[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module.split(".")[0])
    return names


def scan_imports(
    module_path: Path,
    *,
    denylist: RemovedProviderDenylist,
    max_depth: int = 3,
    _depth: int = 0,
    _seen: Optional[set[str]] = None,
) -> list[tuple[str, list[str]]]:
    """Depth-limited transitive import scan.

    Returns a list of (offender_module, import_chain) tuples where each
    offender is a removed provider detected in the transitive import graph.
    """
    if _depth > max_depth:
        return []
    if _seen is None:
        _seen = set()
    abs_path = module_path.resolve()
    if str(abs_path) in _seen:
        return []
    _seen.add(str(abs_path))

    offenders: list[tuple[str, list[str]]] = []
    direct = _parse_imports(abs_path)
    for mod in direct:
        if denylist.is_removed(mod):
            offenders.append((mod, [mod]))

    # Follow first-party imports inside the repo
    repo_root = Path(__file__).resolve().parents[1]
    for mod in direct:
        if denylist.is_removed(mod):
            continue
        candidate = repo_root / mod.replace(".", "/") + ".py"
        if candidate.exists():
            sub = scan_imports(candidate, denylist=denylist, max_depth=max_depth, _depth=_depth + 1, _seen=_seen)
            for off, chain in sub:
                offenders.append((off, [mod] + chain))
    return offenders


# ---------------------------------------------------------------------------
# ToolSurface
# ---------------------------------------------------------------------------

class ToolSurface:
    """Canonical tool-surface filter for hermes-lite."""

    def __init__(
        self,
        active_kit: str = "",
        allowlist: Optional[KitAllowlist] = None,
        denylist: Optional[RemovedProviderDenylist] = None,
    ) -> None:
        self.active_kit = active_kit
        self.allowlist = allowlist or KitAllowlist()
        self.denylist = denylist or RemovedProviderDenylist()
        self._schemas: list[dict[str, Any]] = []
        self._digest: Optional[str] = None

    # ------------------------------------------------------------------
    # Registry integration
    # ------------------------------------------------------------------

    @staticmethod
    def _get_registry_schemas() -> list[dict[str, Any]]:
        """Import tools.registry lazily to avoid circular deps."""
        try:
            from tools import registry  # type: ignore[import-not-found]
            return registry.get_definitions()  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Could not load tools.registry: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _filter_by_kit(self, schemas: list[dict[str, Any]], kit: str) -> list[dict[str, Any]]:
        allowed = set(self.allowlist.tools_for(kit))
        if not allowed:
            logger.warning("No allowlist defined for kit '%s'; exposing zero tools.", kit)
            return []
        filtered = []
        for schema in schemas:
            name = schema.get("name")
            if name in allowed:
                filtered.append(schema)
            else:
                logger.debug("Tool '%s' not in allowlist for kit '%s'; hidden.", name, kit)
        for name in allowed:
            if not any(s.get("name") == name for s in schemas):
                logger.warning("Allowlisted tool '%s' for kit '%s' not found in registry.", name, kit)
        return filtered

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def validate(cls, schema: dict[str, Any], kit_allowlist: Optional[list[str]] = None) -> None:
        name = schema.get("name")
        if not name or not isinstance(name, str):
            raise SchemaValidationError(str(name), "missing or invalid 'name' field")
        description = schema.get("description")
        if not description or not isinstance(description, str):
            raise SchemaValidationError(name, "missing or invalid 'description' field")
        params = schema.get("parameters")
        if not isinstance(params, dict):
            raise SchemaValidationError(name, "missing or invalid 'parameters' object")
        if kit_allowlist is not None and name not in kit_allowlist:
            raise SchemaValidationError(name, f"not in kit allowlist {kit_allowlist}")

    # ------------------------------------------------------------------
    # Removed-provider scan
    # ------------------------------------------------------------------

    def scan_tool_module(self, schema: dict[str, Any]) -> list[tuple[str, list[str]]]:
        """Scan the module implementing *schema* for removed-provider imports."""
        name = schema.get("name", "")
        module_path = schema.get("module_path")
        if not module_path:
            # Try to infer from registry metadata
            module_path = schema.get("function", "").split(":")[0]
        if not module_path:
            logger.debug("No module path for tool '%s'; skipping import scan.", name)
            return []
        candidate = Path(module_path)
        if not candidate.exists():
            # Relative to repo root
            repo_root = Path(__file__).resolve().parents[1]
            candidate = repo_root / (module_path.replace(".", "/") + ".py")
        if not candidate.exists():
            logger.debug("Module file not found for tool '%s' at %s; skipping import scan.", name, candidate)
            return []
        return scan_imports(candidate, denylist=self.denylist)

    # ------------------------------------------------------------------
    # Digest
    # ------------------------------------------------------------------

    @staticmethod
    def _canonical_json(schemas: list[dict[str, Any]]) -> str:
        """Deterministic JSON serialization for cache-friendly digests."""
        def sort_keys(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: sort_keys(v) for k, v in sorted(obj.items())}
            if isinstance(obj, list):
                return [sort_keys(i) for i in obj]
            return obj
        canonical = sort_keys(sorted(schemas, key=lambda s: s.get("name", "")))
        return json.dumps(canonical, separators=(",", ":"), ensure_ascii=False)

    def digest(self, schemas: Optional[list[dict[str, Any]]] = None) -> str:
        if self._digest is not None:
            return self._digest
        data = schemas if schemas is not None else self._schemas
        canonical = self._canonical_json(data)
        self._digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self._digest

    def invalidate(self) -> None:
        """Clear cached digest (call after kit switch or allowlist reload)."""
        self._schemas = []
        self._digest = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_definitions(self, active_kit: Optional[str] = None) -> list[dict[str, Any]]:
        kit = active_kit or self.active_kit
        if not kit:
            logger.warning("No active kit set; returning empty tool surface.")
            return []
        if kit != self.active_kit or not self._schemas:
            self.invalidate()
            self.active_kit = kit
            all_schemas = self._get_registry_schemas()
            filtered = self._filter_by_kit(all_schemas, kit)
            for schema in filtered:
                self.validate(schema, self.allowlist.tools_for(kit))
                offenders = self.scan_tool_module(schema)
                if offenders:
                    off, chain = offenders[0]
                    raise ProviderRemovedError(schema.get("name", ""), off, chain)
            self._schemas = filtered
        return self._schemas

    def switch_kit(self, kit: str) -> list[dict[str, Any]]:
        """Change active kit and return the new filtered definitions."""
        return self.get_definitions(kit)


# ---------------------------------------------------------------------------
# Convenience module-level helpers
# ---------------------------------------------------------------------------

def get_definitions(active_kit: str, **kw: Any) -> list[dict[str, Any]]:
    return ToolSurface(active_kit=active_kit, **kw).get_definitions()


def get_digest(active_kit: str, **kw: Any) -> str:
    surface = ToolSurface(active_kit=active_kit, **kw)
    surface.get_definitions()
    return surface.digest()
