"""Open WebUI pipeline adapter for hermes-lite.

Registers as an Open WebUI pipeline that bridges conversations into
Hermes sessions.  Implements the inlet/outlet hook protocol, maps
Open WebUI conversation IDs to Hermes session IDs, enforces an
allowlist, and streams assistant responses back as markdown.

Reference: REDESIGN.md §10
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
import textwrap
import time
import uuid
from typing import Any, AsyncGenerator, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OWUI_META_PREFIX = "owui_session"
"""Prefix for state_meta keys that store Open WebUI → Hermes mappings."""

_MAX_STREAM_CHUNK_SIZE = 4096
"""Max characters per SSE chunk before forced splitting."""

# ---------------------------------------------------------------------------
# Session mapper
# ---------------------------------------------------------------------------

class SessionMapper:
    """Bidirectional mapping between Open WebUI conversation IDs and Hermes
    session IDs.  Persists to a simple JSON file in ~/.hermes-lite/state/
    and integrates with state.db for cross-gateway visibility."""

    def __init__(self, state_dir: Optional[str] = None) -> None:
        self.state_dir = state_dir or os.path.expanduser("~/.hermes-lite/state")
        os.makedirs(self.state_dir, mode=0o700, exist_ok=True)
        self._path = os.path.join(self.state_dir, "openwebui-sessions.json")
        self._map: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                self._map = json.load(fh)
        except Exception as exc:
            logger.warning("Failed to load session map: %s", exc)
            self._map = {}

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as fh:
                json.dump(self._map, fh, indent=2)
        except Exception as exc:
            logger.warning("Failed to save session map: %s", exc)

    def _ensure_db(self):
        """Lazy-load SessionDB for state.db integration."""
        try:
            from hermes_state import SessionDB
            return SessionDB()
        except Exception as exc:
            logger.debug("SessionDB unavailable for OWUI mapping: %s", exc)
            return None

    def _meta_key(self, owui_id: str) -> str:
        return f"{_OWUI_META_PREFIX}:{owui_id}"

    def to_hermes(self, owui_id: str) -> str:
        """Return the Hermes session ID for *owui_id*, creating one if needed.

        Writes the mapping to both the local JSON file and state.db so
        other gateways (TUI, Discord) can resolve the session."""
        if owui_id not in self._map:
            self._map[owui_id] = f"owui-{uuid.uuid4().hex[:16]}"
            self._save()
        hermes_id = self._map[owui_id]
        # Cross-gateway visibility: persist to state.db
        db = self._ensure_db()
        if db is not None:
            try:
                db.set_meta(self._meta_key(owui_id), hermes_id)
                # Ensure the session row exists with openwebui origin
                db.ensure_session(hermes_id, source="openwebui")
            except Exception as exc:
                logger.warning("Failed to persist OWUI mapping to state.db: %s", exc)
        return hermes_id

    def to_hermes_db(self, owui_id: str) -> Optional[str]:
        """Lookup a Hermes session ID from state.db (cross-gateway resolver)."""
        db = self._ensure_db()
        if db is None:
            return None
        try:
            return db.get_meta(self._meta_key(owui_id))
        except Exception as exc:
            logger.warning("Failed to query OWUI mapping from state.db: %s", exc)
            return None

    def to_owui(self, hermes_id: str) -> Optional[str]:
        for owui, hid in self._map.items():
            if hid == hermes_id:
                return owui
        return None

    def remove(self, owui_id: str) -> None:
        self._map.pop(owui_id, None)
        self._save()
        db = self._ensure_db()
        if db is not None:
            try:
                # state_meta has no delete API; overwrite with empty to signal removal
                db.set_meta(self._meta_key(owui_id), "")
            except Exception as exc:
                logger.debug("Failed to clear OWUI mapping from state.db: %s", exc)


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------

class UserAllowlist:
    """Reads allowed Open WebUI user IDs from lite-config.yaml or env."""

    def __init__(self) -> None:
        self.allowed: set[str] = set()
        self._load()

    def _load(self) -> None:
        # Try env variable first
        env = os.environ.get("OPENWEBUI_ALLOWED_USERS", "")
        if env:
            self.allowed = {u.strip() for u in env.split(",") if u.strip()}
            return
        # Fall back to lite-config
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(repo_root, "lite-config.yaml")
        if not os.path.exists(config_path):
            return
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh)
            owui = cfg.get("gateway", {}).get("openwebui", {})
            users = owui.get("allowed_users", [])
            if isinstance(users, list):
                self.allowed = set(users)
        except Exception as exc:
            logger.warning("Failed to read Open WebUI allowlist from config: %s", exc)

    def is_allowed(self, user_id: str) -> bool:
        if not self.allowed:
            # Empty allowlist = allow all (dev default)
            return True
        return user_id in self.allowed


# ---------------------------------------------------------------------------
# Markdown formatting helper
# ---------------------------------------------------------------------------

class OpenWebUIMarkdownFormatter:
    """Convert agent output into Open WebUI-friendly markdown.

    - Fenced code blocks with language tags
    - Citation references (arXiv IDs as markdown links)
    - Comparison tables in markdown pipe syntax
    - Reasoning content collapsed in <details> blocks
    """

    _ARXIV_RE = re.compile(
        r"(?<![\w\-/])arXiv:([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)"
        r"|(?<![\w\-/])arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)",
        re.IGNORECASE,
    )
    _CODE_FENCE_RE = re.compile(r"```[a-zA-Z0-9_+-]*\n")
    _UNclosed_BACKTICK_RE = re.compile(r"```[a-zA-Z0-9_+-]*$")
    _TABLE_ROW_RE = re.compile(r"^\|?.*\|.*\|?$")
    _HTML_TAG_RE = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)[^>]*>.*?<\/\1>", re.DOTALL)

    @classmethod
    def format_citations(cls, text: str) -> str:
        """Turn arXiv mentions into markdown links."""
        def _repl(m: re.Match) -> str:
            arxiv_id = m.group(1) or m.group(2)
            return f"[arXiv:{arxiv_id}](https://arxiv.org/abs/{arxiv_id})"
        return cls._ARXIV_RE.sub(_repl, text)

    @classmethod
    def format_code_blocks(cls, text: str) -> str:
        """Ensure inline code blocks have language tags when a language can be inferred."""
        # Simple heuristic: if a block starts with a common language identifier comment,
        # ensure it's fenced with that language.
        lines = text.split("\n")
        out: list[str] = []
        in_fence = False
        fence_lang = ""
        for line in lines:
            if line.strip().startswith("```"):
                in_fence = not in_fence
                if in_fence:
                    fence_lang = line.strip()[3:].strip()
                out.append(line)
                continue
            if in_fence and fence_lang == "" and line.strip().startswith("#"):
                # Heuristic: shell/python comment inside untagged fence
                if line.strip().startswith("#!/") or line.strip().startswith("# python"):
                    fence_lang = "python"
            out.append(line)
        return "\n".join(out)

    @classmethod
    def format_tables(cls, text: str) -> str:
        """Re-align markdown pipe tables and fix malformed rows."""
        try:
            from agent.markdown_tables import realign_markdown_tables
            return realign_markdown_tables(text)
        except Exception:
            # Fallback: ensure rows start and end with |
            lines = text.split("\n")
            out: list[str] = []
            for line in lines:
                stripped = line.strip()
                if "|" in stripped and not stripped.startswith("|"):
                    stripped = "| " + stripped
                if "|" in stripped and not stripped.endswith("|"):
                    stripped = stripped + " |"
                out.append(stripped)
            return "\n".join(out)

    @classmethod
    def format_reasoning(cls, text: str, collapse: bool = True) -> str:
        """Collapse reasoning blocks inside <details> or strip them."""
        # Look for explicit reasoning markers
        reasoning_patterns = [
            ("<thinking>", "</thinking>"),
            ("<reasoning>", "</reasoning>"),
            ("--- reasoning ---", "--- end reasoning ---"),
        ]
        for start_tag, end_tag in reasoning_patterns:
            if start_tag in text and end_tag in text:
                parts = []
                cursor = 0
                while True:
                    s = text.find(start_tag, cursor)
                    if s == -1:
                        parts.append(text[cursor:])
                        break
                    e = text.find(end_tag, s + len(start_tag))
                    if e == -1:
                        parts.append(text[cursor:])
                        break
                    parts.append(text[cursor:s])
                    reasoning_body = text[s + len(start_tag):e].strip()
                    if collapse:
                        parts.append(
                            f"<details><summary>Reasoning</summary>\n\n{reasoning_body}\n\n</details>"
                        )
                    # else strip entirely
                    cursor = e + len(end_tag)
                text = "".join(parts)
        return text

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Escape raw HTML, repair unclosed backticks, cleanup malformed tables."""
        # Repair unclosed backticks at end of text
        if text.count("```") % 2 != 0:
            text = text + "\n```"
        # Escape raw HTML that isn't already in <details> or other safe tags
        # We allow a small safelist of tags Open WebUI renders natively
        safe_tags = {"details", "summary", "br", "hr"}
        def _escape_html(m: re.Match) -> str:
            tag = m.group(1).lower()
            if tag in safe_tags:
                return m.group(0)
            return html.escape(m.group(0))
        text = cls._HTML_TAG_RE.sub(_escape_html, text)
        # Cleanup any | | | rows that might be malformed
        return text

    @classmethod
    def format(cls, text: str, collapse_reasoning: bool = True) -> str:
        """Run the full formatting pipeline."""
        text = cls.sanitize(text)
        text = cls.format_code_blocks(text)
        text = cls.format_citations(text)
        text = cls.format_tables(text)
        text = cls.format_reasoning(text, collapse=collapse_reasoning)
        # Apply redaction before it reaches the browser
        try:
            from agent.redact import redact_sensitive_text
            text = redact_sensitive_text(text, force=True)
        except Exception as exc:
            logger.warning("Redaction failed in OWUI formatter: %s", exc)
        return text


# ---------------------------------------------------------------------------
# Message formatting helper
# ---------------------------------------------------------------------------

class OpenWebUIMessageFormatter:
    """Map Open WebUI conversation roles to Hermes session roles and back."""

    # Open WebUI uses OpenAI-compatible roles: system, user, assistant, tool
    # Hermes sessions store: system, user, assistant, tool
    _ROLE_MAP = {
        "system": "system",
        "user": "user",
        "assistant": "assistant",
        "tool": "tool",
    }

    @classmethod
    def to_hermes_message(cls, owui_msg: dict[str, Any]) -> dict[str, Any]:
        """Convert an Open WebUI message dict to Hermes session message format."""
        role = cls._ROLE_MAP.get(owui_msg.get("role", "user"), "user")
        content = owui_msg.get("content", "")
        hermes_msg: dict[str, Any] = {"role": role, "content": content}
        if "name" in owui_msg:
            hermes_msg["name"] = owui_msg["name"]
        if "tool_calls" in owui_msg:
            hermes_msg["tool_calls"] = owui_msg["tool_calls"]
        if "tool_call_id" in owui_msg:
            hermes_msg["tool_call_id"] = owui_msg["tool_call_id"]
        return hermes_msg

    @classmethod
    def from_hermes_message(cls, hermes_msg: dict[str, Any]) -> dict[str, Any]:
        """Convert a Hermes session message back to Open WebUI dict format."""
        role = hermes_msg.get("role", "user")
        owui_msg: dict[str, Any] = {"role": role, "content": hermes_msg.get("content", "")}
        if "name" in hermes_msg:
            owui_msg["name"] = hermes_msg["name"]
        if "tool_calls" in hermes_msg:
            owui_msg["tool_calls"] = hermes_msg["tool_calls"]
        if "tool_call_id" in hermes_msg:
            owui_msg["tool_call_id"] = hermes_msg["tool_call_id"]
        return owui_msg

    @classmethod
    def map_roles(cls, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Map a list of Open WebUI messages to Hermes session messages."""
        return [cls.to_hermes_message(m) for m in messages]


# ---------------------------------------------------------------------------
# SSE pipeline stream
# ---------------------------------------------------------------------------

class OpenWebUISSEStream:
    """SSE formatter for Open WebUI streaming responses.

    Yields OpenAI-compatible chat.completion.chunk SSE events
    that Open WebUI's frontend renders natively.
    """

    def __init__(self, completion_id: Optional[str] = None) -> None:
        self.completion_id = completion_id or f"chatcmpl-{uuid.uuid4().hex[:24]}"
        self.created = int(time.time())

    def _sse_line(self, data: dict[str, Any]) -> str:
        return f"data: {json.dumps(data)}\n\n"

    def role_chunk(self, role: str = "assistant") -> str:
        return self._sse_line({
            "id": self.completion_id,
            "object": "chat.completion.chunk",
            "created": self.created,
            "model": "hermes-lite",
            "choices": [{"index": 0, "delta": {"role": role}, "finish_reason": None}],
        })

    def content_chunk(self, content: str) -> str:
        return self._sse_line({
            "id": self.completion_id,
            "object": "chat.completion.chunk",
            "created": self.created,
            "model": "hermes-lite",
            "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
        })

    def done_chunk(self) -> str:
        return self._sse_line({
            "id": self.completion_id,
            "object": "chat.completion.chunk",
            "created": self.created,
            "model": "hermes-lite",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        })

    @classmethod
    def split_chunks(cls, text: str, max_size: int = _MAX_STREAM_CHUNK_SIZE) -> list[str]:
        """Split *text* into chunks that fit within *max_size* UTF-8 bytes."""
        if len(text.encode("utf-8")) <= max_size:
            return [text]
        chunks: list[str] = []
        while text:
            # Find the largest codepoint prefix that fits
            lo, hi = 0, len(text)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if len(text[:mid].encode("utf-8")) <= max_size:
                    lo = mid
                else:
                    hi = mid - 1
            chunk = text[:lo]
            text = text[lo:]
            if chunk:
                chunks.append(chunk)
        return chunks


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class Pipeline:
    """Open WebUI pipeline for Hermes-Lite.

    Install in Open WebUI via Admin → Pipelines → Add Pipeline →
    paste this module's file path or use the pip package.

    Required env vars:
      - HERMES_LITE_HOME  (default: ~/.hermes-lite)
    Optional:
      - OPENWEBUI_ALLOWED_USERS  (comma-separated user IDs)
    """

    def __init__(self) -> None:
        self.name = "Hermes-Lite"
        self.mapper = SessionMapper()
        self.allowlist = UserAllowlist()
        self._busy_sessions: set[str] = set()
        self._busy_lock = asyncio.Lock()
        logger.info("Hermes-Lite Open WebUI pipeline initialized")

    # ------------------------------------------------------------------
    # Open WebUI pipeline hooks
    # ------------------------------------------------------------------

    async def inlet(self, body: dict[str, Any], user: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Called before the LLM processes a user message.

        Enforces allowlist, maps conversation ID to Hermes session, and
        injects a system message describing the Hermes context.
        """
        user_id = (user or {}).get("id", "")
        if not self.allowlist.is_allowed(user_id):
            logger.warning("Rejected Open WebUI request from disallowed user %s", user_id)
            raise PermissionError(f"User {user_id} is not in the Hermes-Lite allowlist")

        conv_id = body.get("chat_id") or body.get("id") or str(uuid.uuid4())
        session_id = self.mapper.to_hermes(conv_id)

        messages = body.get("messages", [])
        if messages and messages[0].get("role") != "system":
            messages.insert(0, {
                "role": "system",
                "content": (
                    f"You are Hermes-Lite, running through Open WebUI. "
                    f"Session: {session_id}. "
                    f"Use tools to act; do not describe intentions without acting."
                ),
            })
        body["messages"] = messages
        body["_hermes_session_id"] = session_id
        # Cross-gateway: write session origin metadata to state.db
        await self._ensure_session_in_db(session_id, conv_id, user_id)
        return body

    async def _ensure_session_in_db(self, session_id: str, conv_id: str, user_id: str) -> None:
        """Ensure the mapped session exists in state.db with openwebui origin."""
        db = self.mapper._ensure_db()
        if db is None:
            return
        try:
            db.ensure_session(session_id, source="openwebui", user_id=user_id or "unknown")
            # Persist the conversation mapping in state_meta
            db.set_meta(self.mapper._meta_key(conv_id), session_id)
        except Exception as exc:
            logger.warning("Failed to ensure OWUI session in state.db: %s", exc)

    async def outlet(self, body: dict[str, Any], user: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Called after the LLM produces a response.

        Logs the turn for diagnostics and strips internal metadata.
        """
        # Strip internal metadata before returning to Open WebUI
        body.pop("_hermes_session_id", None)
        return body

    async def on_startup(self) -> None:
        logger.info("Hermes-Lite pipeline starting up")

    async def on_shutdown(self) -> None:
        logger.info("Hermes-Lite pipeline shutting down")

    # ------------------------------------------------------------------
    # Open WebUI streaming pipe
    # ------------------------------------------------------------------

    async def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: list[dict[str, Any]],
        body: dict[str, Any],
    ) -> str | AsyncGenerator[str, None]:
        """Main Open WebUI pipeline entry point.

        Returns a plain string for non-streaming mode or an async generator
        yielding SSE chunks for streaming mode.
        """
        session_id = body.get("_hermes_session_id", "")
        stream = body.get("stream", False)

        if stream:
            return self._pipe_stream(user_message, messages, session_id)
        return await self._pipe_sync(user_message, messages, session_id)

    async def _pipe_sync(self, user_message: str, messages: list[dict[str, Any]], session_id: str) -> str:
        """Non-streaming response: run agent loop and return formatted markdown."""
        raw_response = await self._run_agent(user_message, messages, session_id)
        return OpenWebUIMarkdownFormatter.format(raw_response)

    async def _pipe_stream(
        self,
        user_message: str,
        messages: list[dict[str, Any]],
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """Streaming response: yield SSE chunks as the agent produces output."""
        streamer = OpenWebUISSEStream()
        yield streamer.role_chunk("assistant")

        # Run agent loop and collect response (Open WebUI pipelines typically
        # receive the full response from the upstream LLM; we chunk it).
        raw_response = await self._run_agent(user_message, messages, session_id)
        formatted = OpenWebUIMarkdownFormatter.format(raw_response)

        for chunk in OpenWebUISSEStream.split_chunks(formatted):
            yield streamer.content_chunk(chunk)

        yield streamer.done_chunk()
        yield "data: [DONE]\n\n"

    async def _run_agent(
        self,
        user_message: str,
        messages: list[dict[str, Any]],
        session_id: str,
    ) -> str:
        """Invoke the Hermes agent loop and return the raw assistant response.

        Concurrent messages for the same session are queued; this method
        blocks until any prior turn for *session_id* finishes.
        """
        async with self._busy_lock:
            if session_id in self._busy_sessions:
                logger.info("Queueing message for busy session %s", session_id)
                # Wait until the session is free
                while session_id in self._busy_sessions:
                    await asyncio.sleep(0.1)
            self._busy_sessions.add(session_id)

        try:
            formatted_messages = OpenWebUIMessageFormatter.map_roles(messages)
            # Persist user message to state.db for cross-gateway visibility
            await self._append_message_db(session_id, "user", user_message)
            # Delegate to agent loop
            response = await self._invoke_agent(user_message, formatted_messages, session_id)
            # Persist assistant message to state.db
            await self._append_message_db(session_id, "assistant", response)
            # Validate the response before returning
            if not isinstance(response, str):
                response = str(response) if response else ""
            return response
        except Exception as exc:
            logger.exception("Agent loop failed for session %s: %s", session_id, exc)
            return (
                "⚠️ An error occurred while processing your request. "
                "The failure has been logged; please try again or contact the admin."
            )
        finally:
            async with self._busy_lock:
                self._busy_sessions.discard(session_id)

    async def _invoke_agent(
        self,
        user_message: str,
        messages: list[dict[str, Any]],
        session_id: str,
    ) -> str:
        """Actually call the AIAgent interface.

        This is a placeholder that attempts to import run_agent.AIAgent.
        In a full deployment the gateway runner wires an agent instance.
        """
        try:
            from run_agent import AIAgent
            agent = AIAgent(
                platform="openwebui",
                session_id=session_id,
            )
            return agent.chat(user_message)
        except Exception as exc:
            logger.warning("Failed to invoke AIAgent for OWUI: %s", exc)
            # Fallback echo so the pipeline doesn't crash Open WebUI
            return "(Hermes-Lite agent is not yet fully wired — this is a placeholder response.)"

    async def _append_message_db(self, session_id: str, role: str, content: str) -> None:
        """Append a turn to state.db for cross-gateway visibility."""
        db = self.mapper._ensure_db()
        if db is None:
            return
        try:
            db.append_message(session_id, role=role, content=content)
        except Exception as exc:
            logger.debug("Failed to append OWUI message to state.db: %s", exc)

    # ------------------------------------------------------------------
    # Hermes integration helpers
    # ------------------------------------------------------------------

    def stream_response(self, markdown_chunks: list[str]) -> str:
        """Concatenate assistant markdown chunks for Open WebUI display."""
        return "\n".join(markdown_chunks)


# ---------------------------------------------------------------------------
# Gateway adapter wrapper
# ---------------------------------------------------------------------------

class OpenWebUIAdapter:
    """Thin wrapper that presents the Pipeline as a gateway.platforms adapter.

    This allows gateway/run.py to treat Open WebUI the same way it treats
    Discord — as a surface that feeds into the shared agent loop.
    """

    def __init__(self) -> None:
        self.pipeline = Pipeline()

    @property
    def name(self) -> str:
        return "openwebui"

    async def start(self) -> None:
        await self.pipeline.on_startup()

    async def stop(self) -> None:
        await self.pipeline.on_shutdown()

    async def send(self, chat_id: str, text: str, *, metadata: Optional[dict] = None) -> None:
        """Send a formatted message back to Open WebUI.

        This is invoked by the gateway runner when the agent has a response
        that needs to be delivered to the browser.
        """
        formatted = OpenWebUIMarkdownFormatter.format(text)
        logger.info("[openwebui → %s] %d chars", chat_id, len(formatted))
        # Open WebUI adapter does not have an independent outbound socket;
        # responses travel through the pipeline pipe() return value.

    async def send_typing(self, chat_id: str, metadata: Optional[dict] = None) -> None:
        """No-op for Open WebUI — typing indicators are handled by the pipeline stream."""
        pass
