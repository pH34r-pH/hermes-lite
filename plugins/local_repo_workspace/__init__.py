"""LocalRepoWorkspace plugin for hermes-lite.

Provides the only sanctioned path for the agent to mutate code outside
~/.hermes-lite/.  Maintains a workspace registry, enforces branch hygiene,
change budgets, pre-commit gates, and structured change journals.

Reference: REDESIGN.md §5.9, §9
"""

from __future__ import annotations

import logging
from pathlib import Path

# Import tool modules to trigger side-effect registration via tools.registry
from .tools import list as _list_tool      # noqa: F401
from .tools import locate as _locate_tool  # noqa: F401
from .tools import status as _status_tool  # noqa: F401
from .tools import diff as _diff_tool      # noqa: F401
from .tools import apply_patch as _apply_patch_tool  # noqa: F401
from .tools import commit as _commit_tool  # noqa: F401
from .tools import push as _push_tool      # noqa: F401
from .tools import open_pr as _open_pr_tool  # noqa: F401

logger = logging.getLogger(__name__)


def _workspace_registry_path() -> Path:
    """Return the path to workspaces.yaml under HERMES_HOME."""
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "workspaces.yaml"
