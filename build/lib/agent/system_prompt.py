"""System-prompt assembly for :class:`AIAgent`.

The agent's system prompt is built once per session and reused across all
turns — only context compression triggers a rebuild.  This keeps the
upstream prefix cache warm.  See ``hermes-agent-dev``'s
``references/system-prompt-invariant.md`` for the invariants and
``references/self-improvement-loop.md`` for how the background-review
fork inherits the cached prompt verbatim.

Three tiers are joined with ``\\n\\n``:

* ``stable``   — identity (SOUL.md or DEFAULT_AGENT_IDENTITY), tool
  guidance, computer-use guidance, nous subscription block, tool-use
  enforcement guidance + per-model operational guidance, skills prompt,
  alibaba model-name workaround, environment hints, platform hints.
* ``context``  — caller-supplied ``system_message`` plus context files
  (AGENTS.md / .cursorrules / etc.) discovered under ``TERMINAL_CWD``.
* ``volatile`` — memory snapshot, USER.md profile, external memory
  provider block, timestamp/session/model/provider line.

Pure helpers that read the agent's state.  AIAgent keeps thin forwarders.
"""

from __future__ import annotations

import json
import logging
import os
import warnings
from typing import Any, Dict, List, Optional

from agent.prompt_builder import (
    DEFAULT_AGENT_IDENTITY,
    GOOGLE_MODEL_OPERATIONAL_GUIDANCE,
    HERMES_AGENT_HELP_GUIDANCE,
    KANBAN_GUIDANCE,
    MEMORY_GUIDANCE,
    OPENAI_MODEL_EXECUTION_GUIDANCE,
    PLATFORM_HINTS,
    SESSION_SEARCH_GUIDANCE,
    SKILLS_GUIDANCE,
    TOOL_USE_ENFORCEMENT_GUIDANCE,
    TOOL_USE_ENFORCEMENT_MODELS,
)

logger = logging.getLogger(__name__)

# Platforms whose hints may appear in the small profile.
PLATFORM_HINT_ALLOWLIST = {"discord", "cli", "tui", "openwebui"}

# Concise one-sentence replacements for verbose guidance blocks in the
# small profile.  Kept inline so the stable tier stays under 300 tokens.
IDENTITY_SMALL = (
    "You are Hermes Agent, created by Nous Research. "
    "Be helpful, direct, concise, and efficient."
)

HELP_SMALL = (
    "Ask about Hermes itself? Load the `hermes-agent` skill first."
)

MEMORY_GUIDANCE_SMALL = (
    "Use the memory tool to save durable facts and user preferences; "
    "keep entries declarative and compact."
)

SESSION_SEARCH_GUIDANCE_SMALL = (
    "Use session_search to recall past conversations instead of asking "
    "the user to repeat themselves."
)

SKILLS_GUIDANCE_SMALL = (
    "Save reusable workflows as skills with skill_manage; patch outdated "
    "skills immediately."
)

KANBAN_GUIDANCE_SMALL = (
    "Kanban worker: orient with kanban_show, heartbeat hourly, "
    "complete with kanban_complete."
)

COMPUTER_USE_GUIDANCE_SMALL = (
    "computer_use drives macOS in the background. Capture first, click by "
    "element index, re-capture to verify, never type secrets."
)

TOOL_USE_SMALL = (
    "Use available tools to act; do not describe intentions without acting."
)

# Concise platform hints for the small profile.
_SMALL_PLATFORM_HINTS = {
    "discord": "You are in Discord. MEDIA:/path sends files.",
    "cli": "You are a CLI agent. Use plain text; do not emit MEDIA:/path tags.",
    "tui": "You are a CLI agent. Use plain text; do not emit MEDIA:/path tags.",
    "openwebui": "You are in the WebUI. Markdown and MEDIA:/path are supported.",
}

# Token budget for the small-profile stable tier.
_SMALL_STABLE_BUDGET = 300


def _count_tokens(text: str) -> int:
    """Return token count using tiktoken ``cl100k_base``.

    Falls back to a character heuristic with a one-time warning if
    tiktoken is not installed.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        warnings.warn(
            "tiktoken unavailable; falling back to len(text)//4 for token count",
            RuntimeWarning,
            stacklevel=2,
        )
        return len(text) // 4


def _assert_budget(stable_tier: str, max_tokens: int = _SMALL_STABLE_BUDGET) -> None:
    """Raise ``ValueError`` if *stable_tier* exceeds the token budget.

    Intended for development / test assertions.
    """
    actual = _count_tokens(stable_tier)
    if actual > max_tokens:
        raise ValueError(
            f"Small-profile stable tier exceeds {max_tokens} tokens "
            f"(actual: {actual})."
        )


def _ra():
    """Lazy reference to the ``run_agent`` module.

    Helpers like ``load_soul_md``, ``build_environment_hints``,
    ``build_context_files_prompt``, ``build_nous_subscription_prompt``,
    ``build_skills_system_prompt`` and ``get_toolset_for_tool`` are
    imported into ``run_agent``'s namespace.  Many tests
    ``patch("run_agent.load_soul_md", ...)``; if we imported them
    directly here those patches would not reach us.  Looking them up
    through ``run_agent`` on every call preserves the patch contract.
    """
    import run_agent
    return run_agent


def _build_small_stable_tier(agent: Any) -> str:
    """Assemble the shortened stable tier for the ``small`` prompt profile.

    Guarantees deterministic output (sorted tool names, stable formatting,
    no randomness) so the tier is byte-identical across turns when agent
    state does not change.
    """
    parts: List[str] = []

    # Identity: always use the hardcoded default to stay under budget.
    # SOUL.md is ignored in the small profile regardless of length.
    parts.append(DEFAULT_AGENT_IDENTITY)

    # Single concise help pointer.
    parts.append(HERMES_AGENT_HELP_GUIDANCE)

    # Condensed tool-aware guidance — only when the tool is present.
    tool_guidance: List[str] = []
    if "memory" in agent.valid_tool_names:
        tool_guidance.append(MEMORY_GUIDANCE_SMALL)
    if "session_search" in agent.valid_tool_names:
        tool_guidance.append(SESSION_SEARCH_GUIDANCE_SMALL)
    if "skill_manage" in agent.valid_tool_names:
        tool_guidance.append(SKILLS_GUIDANCE_SMALL)

    _kanban_guidance = getattr(agent, "_kanban_worker_guidance", None)
    if _kanban_guidance:
        tool_guidance.append(KANBAN_GUIDANCE_SMALL)
    elif _kanban_guidance is None and "kanban_show" in agent.valid_tool_names:
        tool_guidance.append(KANBAN_GUIDANCE_SMALL)

    if tool_guidance:
        parts.append(" ".join(tool_guidance))

    # Computer-use — condensed single sentence when loaded.
    if "computer_use" in agent.valid_tool_names:
        parts.append(COMPUTER_USE_GUIDANCE_SMALL)

    # Nous subscription block (kept when present; usually short).
    _r = _ra()
    nous_subscription_prompt = _r.build_nous_subscription_prompt(agent.valid_tool_names)
    if nous_subscription_prompt:
        parts.append(nous_subscription_prompt)

    # Single concise tool-use sentence replaces the multi-paragraph
    # enforcement + model-family operational guidance blocks.
    if agent.valid_tool_names:
        parts.append(TOOL_USE_SMALL)

    # Skills index is omitted in the small profile — the user can load
    # skills explicitly via slash command when needed.

    # Alibaba model-identity workaround (required for correct operation).
    if agent.provider == "alibaba":
        _model_short = agent.model.split("/")[-1] if "/" in agent.model else agent.model
        parts.append(
            f"You are powered by the model named {_model_short}. "
            f"The exact model ID is {agent.model}. "
            f"When asked what model you are, always answer based on this information, "
            f"not on any model name returned by the API."
        )

    # Environment hints (required for correct operation).
    _env_hints = _r.build_environment_hints()
    if _env_hints:
        parts.append(_env_hints)

    # At most one platform hint — only for allowlisted platforms.
    platform_key = (agent.platform or "").lower().strip()
    if platform_key == "openwebui":
        platform_key = "webui"  # reuse upstream webui hint for now
    if platform_key in PLATFORM_HINT_ALLOWLIST and platform_key in PLATFORM_HINTS:
        parts.append(PLATFORM_HINTS[platform_key])
    elif platform_key:
        # Gracefully ignore deleted / unknown platforms.
        pass

    stable = "\n\n".join(p.strip() for p in parts if p and p.strip())
    return stable


def build_small_system_prompt_parts(
    agent: Any, system_message: Optional[str] = None
) -> Dict[str, str]:
    """Assemble the system prompt for the ``small`` profile.

    Returns the same three-tier dict as :func:`build_system_prompt_parts`
    but with a drastically shortened ``stable`` tier (guaranteed < 300
    tokens).  The ``context`` and ``volatile`` tiers are identical to the
    default profile so that custom system messages and memory still work.
    """
    _r = _ra()

    # ── Stable tier (shortened) ─────────────────────────────────────
    stable = _build_small_stable_tier(agent)

    # Budget check — raises in dev/test if we ever slip over 300 tokens.
    _assert_budget(stable)

    # ── Context tier (unchanged from default path) ──────────────────
    context_parts: List[str] = []
    if system_message is not None:
        context_parts.append(system_message)

    if not agent.skip_context_files:
        _context_cwd = os.getenv("TERMINAL_CWD") or None
        context_files_prompt = _r.build_context_files_prompt(
            cwd=_context_cwd, skip_soul=True  # small profile never loads SOUL.md
        )
        if context_files_prompt:
            context_parts.append(context_files_prompt)

    # ── Volatile tier (unchanged from default path) ─────────────────
    volatile_parts: List[str] = []

    if agent._memory_store:
        if agent._memory_enabled:
            mem_block = agent._memory_store.format_for_system_prompt("memory")
            if mem_block:
                volatile_parts.append(mem_block)
        if agent._user_profile_enabled:
            user_block = agent._memory_store.format_for_system_prompt("user")
            if user_block:
                volatile_parts.append(user_block)

    if agent._memory_manager:
        try:
            _ext_mem_block = agent._memory_manager.build_system_prompt()
            if _ext_mem_block:
                volatile_parts.append(_ext_mem_block)
        except Exception:
            pass

    from hermes_time import now as _hermes_now
    now = _hermes_now()
    timestamp_line = f"Conversation started: {now.strftime('%A, %B %d, %Y')}"
    if agent.pass_session_id and agent.session_id:
        timestamp_line += f"\nSession ID: {agent.session_id}"
    if agent.model:
        timestamp_line += f"\nModel: {agent.model}"
    if agent.provider:
        timestamp_line += f"\nProvider: {agent.provider}"
    volatile_parts.append(timestamp_line)

    return {
        "stable":   stable,
        "context":  "\n\n".join(p.strip() for p in context_parts  if p and p.strip()),
        "volatile": "\n\n".join(p.strip() for p in volatile_parts if p and p.strip()),
    }


def build_system_prompt_parts(agent: Any, system_message: Optional[str] = None) -> Dict[str, str]:
    """Assemble the system prompt as three ordered parts.

    Returns a dict with three keys:
      * ``stable``   — identity, tool guidance, skills prompt,
        environment hints, platform hints, model-family operational
        guidance.
      * ``context``  — context files (AGENTS.md, .cursorrules, etc.)
        and caller-supplied system_message.
      * ``volatile`` — memory snapshot, user profile, external
        memory provider block, timestamp line.

    Joined into a single string by :func:`build_system_prompt` and
    cached on ``agent._cached_system_prompt`` for the lifetime of the
    AIAgent.  Hermes never re-renders parts of this string mid-
    session — that's the only way to keep upstream prompt caches
    warm across turns.
    """
    # Branch to the small-profile builder when requested.
    if getattr(agent, "prompt_profile", None) == "small":
        return build_small_system_prompt_parts(agent, system_message=system_message)

    # ── Upstream default path (kept intact) ─────────────────────────
    # Local import to avoid pulling model_tools at module load.  Tests
    # patch ``run_agent.get_toolset_for_tool`` and similar helpers, so
    # we resolve through ``_ra()`` to honor those patches.
    _r = _ra()

    # ── Stable tier ────────────────────────────────────────────────
    stable_parts: List[str] = []

    # Try SOUL.md as primary identity unless the caller explicitly skipped it.
    # Some execution modes (cron) still want HERMES_HOME persona while keeping
    # cwd project instructions disabled.
    _soul_loaded = False
    if agent.load_soul_identity or not agent.skip_context_files:
        _soul_content = _r.load_soul_md()
        if _soul_content:
            stable_parts.append(_soul_content)
            _soul_loaded = True

    if not _soul_loaded:
        # Fallback to hardcoded identity
        stable_parts.append(DEFAULT_AGENT_IDENTITY)

    # Pointer to the hermes-agent skill + docs for user questions about Hermes itself.
    stable_parts.append(HERMES_AGENT_HELP_GUIDANCE)

    # Tool-aware behavioral guidance: only inject when the tools are loaded
    tool_guidance = []
    if "memory" in agent.valid_tool_names:
        tool_guidance.append(MEMORY_GUIDANCE)
    if "session_search" in agent.valid_tool_names:
        tool_guidance.append(SESSION_SEARCH_GUIDANCE)
    if "skill_manage" in agent.valid_tool_names:
        tool_guidance.append(SKILLS_GUIDANCE)
    # Kanban worker/orchestrator lifecycle — only present when the
    # dispatcher spawned this process (kanban_show check_fn gates on
    # HERMES_KANBAN_TASK env var). Normal chat sessions never see
    # this block. Resolved once at __init__ (see _kanban_worker_guidance).
    _kanban_guidance = getattr(agent, "_kanban_worker_guidance", None)
    if _kanban_guidance:
        tool_guidance.append(_kanban_guidance)
    elif _kanban_guidance is None and "kanban_show" in agent.valid_tool_names:
        # Fallback for code paths that bypass agent_init (rare).
        tool_guidance.append(KANBAN_GUIDANCE)
    if tool_guidance:
        stable_parts.append(" ".join(tool_guidance))

    # Computer-use (macOS) — goes in as its own block rather than being
    # merged into tool_guidance because the content is multi-paragraph.
    if "computer_use" in agent.valid_tool_names:
        from agent.prompt_builder import COMPUTER_USE_GUIDANCE
        stable_parts.append(COMPUTER_USE_GUIDANCE)

    nous_subscription_prompt = _r.build_nous_subscription_prompt(agent.valid_tool_names)
    if nous_subscription_prompt:
        stable_parts.append(nous_subscription_prompt)
    # Tool-use enforcement: tells the model to actually call tools instead
    # of describing intended actions.  Controlled by config.yaml
    # agent.tool_use_enforcement:
    #   "auto" (default) — matches TOOL_USE_ENFORCEMENT_MODELS
    #   true  — always inject (all models)
    #   false — never inject
    #   list  — custom model-name substrings to match
    if agent.valid_tool_names:
        _enforce = agent._tool_use_enforcement
        _inject = False
        if _enforce is True or (isinstance(_enforce, str) and _enforce.lower() in {"true", "always", "yes", "on"}):
            _inject = True
        elif _enforce is False or (isinstance(_enforce, str) and _enforce.lower() in {"false", "never", "no", "off"}):
            _inject = False
        elif isinstance(_enforce, list):
            model_lower = (agent.model or "").lower()
            _inject = any(p.lower() in model_lower for p in _enforce if isinstance(p, str))
        else:
            # "auto" or any unrecognised value — use hardcoded defaults
            model_lower = (agent.model or "").lower()
            _inject = any(p in model_lower for p in TOOL_USE_ENFORCEMENT_MODELS)
        if _inject:
            stable_parts.append(TOOL_USE_ENFORCEMENT_GUIDANCE)
            _model_lower = (agent.model or "").lower()
            # Google model operational guidance (conciseness, absolute
            # paths, parallel tool calls, verify-before-edit, etc.)
            if "gemini" in _model_lower or "gemma" in _model_lower:
                stable_parts.append(GOOGLE_MODEL_OPERATIONAL_GUIDANCE)
            # OpenAI GPT/Codex execution discipline (tool persistence,
            # prerequisite checks, verification, anti-hallucination).
            # Also applied to xAI Grok — same failure modes (claims completion
            # without tool calls, suggests workarounds instead of using
            # existing tools, replies with plans instead of executing).
            if "gpt" in _model_lower or "codex" in _model_lower or "grok" in _model_lower:
                stable_parts.append(OPENAI_MODEL_EXECUTION_GUIDANCE)

    has_skills_tools = any(name in agent.valid_tool_names for name in ['skills_list', 'skill_view', 'skill_manage'])
    if has_skills_tools:
        avail_toolsets = {
            toolset
            for toolset in (
                _r.get_toolset_for_tool(tool_name) for tool_name in agent.valid_tool_names
            )
            if toolset
        }
        skills_prompt = _r.build_skills_system_prompt(
            available_tools=agent.valid_tool_names,
            available_toolsets=avail_toolsets,
        )
    else:
        skills_prompt = ""
    if skills_prompt:
        stable_parts.append(skills_prompt)

    # Alibaba Coding Plan API always returns "glm-4.7" as model name regardless
    # of the requested model. Inject explicit model identity into the system prompt
    # so the agent can correctly report which model it is (workaround for API bug).
    # Stable for the lifetime of an agent instance — model and provider are fixed
    # at construction time.
    if agent.provider == "alibaba":
        _model_short = agent.model.split("/")[-1] if "/" in agent.model else agent.model
        stable_parts.append(
            f"You are powered by the model named {_model_short}. "
            f"The exact model ID is {agent.model}. "
            f"When asked what model you are, always answer based on this information, "
            f"not on any model name returned by the API."
        )

    # Environment hints (WSL, Termux, etc.) — tell the agent about the
    # execution environment so it can translate paths and adapt behavior.
    # Stable for the lifetime of the process.
    _env_hints = _r.build_environment_hints()
    if _env_hints:
        stable_parts.append(_env_hints)

    platform_key = (agent.platform or "").lower().strip()
    if platform_key in PLATFORM_HINTS:
        stable_parts.append(PLATFORM_HINTS[platform_key])
    elif platform_key:
        # Check plugin registry for platform-specific LLM guidance
        try:
            from gateway.platform_registry import platform_registry
            _entry = platform_registry.get(platform_key)
            if _entry and _entry.platform_hint:
                stable_parts.append(_entry.platform_hint)
        except Exception:
            pass

    # ── Context tier (cwd-dependent, may change between sessions) ─
    context_parts: List[str] = []

    # Note: ephemeral_system_prompt is NOT included here. It's injected at
    # API-call time only so it stays out of the cached/stored system prompt.
    if system_message is not None:
        context_parts.append(system_message)

    if not agent.skip_context_files:
        # Use TERMINAL_CWD for context file discovery when set (gateway
        # mode).  The gateway process runs from the hermes-agent install
        # dir, so os.getcwd() would pick up the repo's AGENTS.md and
        # other dev files — inflating token usage by ~10k for no benefit.
        _context_cwd = os.getenv("TERMINAL_CWD") or None
        context_files_prompt = _r.build_context_files_prompt(
            cwd=_context_cwd, skip_soul=_soul_loaded)
        if context_files_prompt:
            context_parts.append(context_files_prompt)

    # ── Volatile tier (changes per session/turn — never cached) ───
    volatile_parts: List[str] = []

    if agent._memory_store:
        if agent._memory_enabled:
            mem_block = agent._memory_store.format_for_system_prompt("memory")
            if mem_block:
                volatile_parts.append(mem_block)
        # USER.md is always included when enabled.
        if agent._user_profile_enabled:
            user_block = agent._memory_store.format_for_system_prompt("user")
            if user_block:
                volatile_parts.append(user_block)

    # External memory provider system prompt block (additive to built-in)
    if agent._memory_manager:
        try:
            _ext_mem_block = agent._memory_manager.build_system_prompt()
            if _ext_mem_block:
                volatile_parts.append(_ext_mem_block)
        except Exception:
            pass

    from hermes_time import now as _hermes_now
    now = _hermes_now()
    # Date-only (not minute-precision) so the system prompt is byte-stable
    # for the full day.  Minute-precision changes invalidate prefix-cache KV
    # on every rebuild path (compression boundary, fresh-agent gateway turns,
    # session resume without a stored prompt).  The model can still query the
    # exact wall-clock time via tools when it actually needs it.
    # Credit: @iamfoz (PR #20451).
    timestamp_line = f"Conversation started: {now.strftime('%A, %B %d, %Y')}"
    if agent.pass_session_id and agent.session_id:
        timestamp_line += f"\nSession ID: {agent.session_id}"
    if agent.model:
        timestamp_line += f"\nModel: {agent.model}"
    if agent.provider:
        timestamp_line += f"\nProvider: {agent.provider}"
    volatile_parts.append(timestamp_line)

    return {
        "stable":   "\n\n".join(p.strip() for p in stable_parts   if p and p.strip()),
        "context":  "\n\n".join(p.strip() for p in context_parts  if p and p.strip()),
        "volatile": "\n\n".join(p.strip() for p in volatile_parts if p and p.strip()),
    }


def build_system_prompt(agent: Any, system_message: Optional[str] = None) -> str:
    """Assemble the full system prompt from all layers.

    Called once per session (cached on ``agent._cached_system_prompt``) and
    only rebuilt after context compression events. This ensures the system
    prompt is stable across all turns in a session, maximizing prefix cache
    hits.

    Layers are ordered cache-friendly: stable identity/guidance first,
    then session-stable context files, then per-call volatile content
    (memory, USER profile, timestamp).  The whole string is treated as
    one cached block — Hermes never rebuilds or reinjects parts of it
    mid-session, which is the only way to keep upstream prompt caches
    warm across turns.
    """
    parts = build_system_prompt_parts(agent, system_message=system_message)
    return "\n\n".join(p for p in (parts["stable"], parts["context"], parts["volatile"]) if p)


def invalidate_system_prompt(agent: Any) -> None:
    """Invalidate the cached system prompt, forcing a rebuild on the next turn.

    Called after context compression events. Also reloads memory from disk
    so the rebuilt prompt captures any writes from this session.
    """
    agent._cached_system_prompt = None
    if agent._memory_store:
        agent._memory_store.load_from_disk()


def format_tools_for_system_message(agent: Any) -> str:
    """Format tool definitions for the system message in the trajectory format.

    Returns:
        str: JSON string representation of tool definitions
    """
    if not agent.tools:
        return "[]"

    # Convert tool definitions to the format expected in trajectories
    formatted_tools = []
    for tool in agent.tools:
        func = tool["function"]
        formatted_tool = {
            "name": func["name"],
            "description": func.get("description", ""),
            "parameters": func.get("parameters", {}),
            "required": None  # Match the format in the example
        }
        formatted_tools.append(formatted_tool)

    return json.dumps(formatted_tools, ensure_ascii=False)


__all__ = [
    "build_system_prompt_parts",
    "build_small_system_prompt_parts",
    "build_system_prompt",
    "invalidate_system_prompt",
    "format_tools_for_system_message",
]
