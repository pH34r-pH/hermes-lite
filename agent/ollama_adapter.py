"""Ollama provider adapter for hermes-lite.

Speaks directly to Ollama's /api/chat and /api/generate endpoints.
Supports streaming, JSON-schema tool-call injection, and a lightweight
token-budget estimator.  Designed for offline-first operation on a
Jetson Orin Nano or equivalent edge device.

Reference: REDESIGN.md §3.2, §5.2
"""

from __future__ import annotations

import json
import logging
import os
import re
import warnings
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Iterator, Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token budget estimator (tiktoken preferred, char fallback)
# ---------------------------------------------------------------------------

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover
    _ENCODING = None
    warnings.warn(
        "tiktoken not available; using character-based token heuristic. "
        "Install tiktoken for accurate token counting.",
        stacklevel=2,
    )


def _estimate_tokens(text: str) -> int:
    if _ENCODING is not None:
        return len(_ENCODING.encode(text))
    # Conservative fallback: ~4 characters per token for English/JSON
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class OllamaMessage:
    role: str  # system | user | assistant | tool
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class OllamaRequest:
    model: str
    messages: list[OllamaMessage]
    stream: bool = False
    tools: list[dict[str, Any]] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    system: Optional[str] = None


@dataclass
class OllamaResponse:
    assistant_text: str = ""
    reasoning_text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    done: bool = False
    model: str = ""
    total_duration_ms: Optional[int] = None


# ---------------------------------------------------------------------------
# Tool schema injector
# ---------------------------------------------------------------------------

class ToolSchemaInjector:
    """Serializes active tool schemas into a prompt appendix for Ollama."""

    @staticmethod
    def validate(schema: dict[str, Any]) -> None:
        """Ensure a schema has the minimum required fields."""
        if not isinstance(schema, dict):
            raise ValueError("Tool schema must be a JSON object (dict)")
        name = schema.get("name")
        if not name or not isinstance(name, str):
            raise ValueError(f"Tool schema missing required 'name' field: {schema}")
        if not schema.get("description"):
            raise ValueError(f"Tool schema missing required 'description' field: {name}")
        params = schema.get("parameters")
        if not isinstance(params, dict):
            raise ValueError(f"Tool schema missing required 'parameters' object: {name}")

    @classmethod
    def inject(cls, system_prompt: str, tools: list[dict[str, Any]]) -> str:
        if not tools:
            return system_prompt
        lines = [system_prompt.strip(), "", "## Available Tools", ""]
        for tool in tools:
            cls.validate(tool)
            lines.append(f"### {tool['name']}")
            lines.append(tool.get("description", ""))
            params = tool.get("parameters", {})
            if "properties" in params:
                lines.append(f"Parameters: {json.dumps(params, indent=2)}")
            lines.append("")
        lines.append(
            "When you need to call a tool, respond with a single JSON object "
            "containing 'name' and 'arguments'.  No markdown fences."
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Structured output parser
# ---------------------------------------------------------------------------

_JSON_RE = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.DOTALL)


def _parse_tool_calls(text: str, allowlist: set[str]) -> list[dict[str, Any]]:
    """Best-effort extraction of tool-call dicts from assistant text."""
    calls: list[dict[str, Any]] = []
    for match in _JSON_RE.finditer(text):
        try:
            obj = json.loads(match.group())
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        name = obj.get("name")
        if not name or name not in allowlist:
            continue
        arguments = obj.get("arguments") or obj.get("args") or {}
        if not isinstance(arguments, dict):
            arguments = {"raw": arguments}
        calls.append({"name": name, "arguments": arguments})
    return calls


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class OllamaAdapter:
    """Canonical Ollama provider adapter for hermes-lite."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "ministral-3:3b",
        context_window: int = 32768,
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.context_window = context_window
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        self._available_models: set[str] = set()

    # ------------------------------------------------------------------
    # Probing
    # ------------------------------------------------------------------

    async def _probe_models(self) -> set[str]:
        if self._available_models:
            return self._available_models
        try:
            resp = await self._client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            self._available_models = {m["name"] for m in data.get("models", [])}
        except Exception as exc:
            logger.warning("Ollama model probe failed: %s", exc)
        return self._available_models

    def _assert_model_available(self) -> None:
        if self.model not in self._available_models:
            logger.warning(
                "Model '%s' not reported by Ollama /api/tags.  "
                "If the model is not loaded, run: ollama pull %s",
                self.model,
                self.model,
            )

    # ------------------------------------------------------------------
    # Token budget
    # ------------------------------------------------------------------

    def estimate_token_budget(self, request: OllamaRequest) -> dict[str, int]:
        """Return usage estimate: prompt_tokens, max_response_tokens, remaining."""
        prompt_text = "\n".join(
            f"{m.role}: {m.content}" for m in request.messages
        )
        prompt_tokens = _estimate_tokens(prompt_text)
        tool_text = json.dumps(request.tools, separators=(",", ":"))
        tool_tokens = _estimate_tokens(tool_text)
        total_prompt = prompt_tokens + tool_tokens
        # Reserve 20% headroom for KV-cache growth and system overhead
        max_response = int(self.context_window * 0.8) - total_prompt
        return {
            "prompt_tokens": total_prompt,
            "tool_tokens": tool_tokens,
            "max_response_tokens": max(max_response, 256),
            "remaining": self.context_window - total_prompt - max(max_response, 256),
        }

    # ------------------------------------------------------------------
    # Request builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_chat_body(request: OllamaRequest) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": request.model or request.options.get("model", ""),
            "messages": [
                {"role": m.role, "content": m.content}
                for m in request.messages
            ],
            "stream": request.stream,
        }
        if request.system:
            body["system"] = request.system
        if request.tools:
            # Ollama does not natively support OpenAI-style tool calling;
            # schemas are injected into the prompt by ToolSchemaInjector.
            # We pass them here in case a downstream Ollama version adds
            # native support.
            body["tools"] = request.tools
        if request.options:
            body["options"] = request.options
        return body

    @staticmethod
    def _build_generate_body(prompt: str, model: str, options: dict[str, Any]) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": options.get("stream", False),
        }
        if "system" in options:
            body["system"] = options["system"]
        if "options" in options:
            body["options"] = options["options"]
        return body

    # ------------------------------------------------------------------
    # Generate (non-streaming)
    # ------------------------------------------------------------------

    async def stream_chat(
        self,
        request: OllamaRequest,
        tool_allowlist: Optional[set[str]] = None,
    ) -> AsyncIterator[OllamaResponse]:
        await self._probe_models()
        self._assert_model_available()

        request.stream = True
        body = self._build_chat_body(request)
        async with self._client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json=body,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = data.get("message", {})
                assistant_text = message.get("content", "")

                parsed_calls: list[dict[str, Any]] = []
                native_calls = message.get("tool_calls", [])
                if native_calls:
                    parsed_calls = [
                        {"name": c["function"]["name"], "arguments": json.loads(c["function"]["arguments"])}
                        for c in native_calls
                        if isinstance(c, dict) and "function" in c
                    ]
                elif assistant_text and tool_allowlist:
                    parsed_calls = _parse_tool_calls(assistant_text, tool_allowlist)

                yield OllamaResponse(
                    assistant_text=assistant_text,
                    tool_calls=parsed_calls,
                    done=data.get("done", False),
                    model=data.get("model", self.model),
                    total_duration_ms=data.get("total_duration"),
                )

    # ------------------------------------------------------------------
    # Generate (non-streaming)
    # ------------------------------------------------------------------

    async def generate(self, prompt: str, options: Optional[dict[str, Any]] = None) -> OllamaResponse:
        await self._probe_models()
        self._assert_model_available()

        opts = options or {}
        body = self._build_generate_body(prompt, self.model, opts)
        resp = await self._client.post(
            f"{self.base_url}/api/generate",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        return OllamaResponse(
            assistant_text=data.get("response", ""),
            done=data.get("done", True),
            model=data.get("model", self.model),
            total_duration_ms=data.get("total_duration"),
        )

    # ------------------------------------------------------------------
    # Generate (streaming)
    # ------------------------------------------------------------------

    async def stream_generate(
        self, prompt: str, options: Optional[dict[str, Any]] = None
    ) -> AsyncIterator[OllamaResponse]:
        await self._probe_models()
        self._assert_model_available()

        opts = options or {}
        opts["stream"] = True
        body = self._build_generate_body(prompt, self.model, opts)
        async with self._client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=body,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                yield OllamaResponse(
                    assistant_text=data.get("response", ""),
                    done=data.get("done", False),
                    model=data.get("model", self.model),
                    total_duration_ms=data.get("total_duration"),
                )

    # ------------------------------------------------------------------
    # Chat — supports both OllamaRequest (native) and kwargs (upstream compat)
    # ------------------------------------------------------------------

    async def chat(
        self,
        request: Optional[OllamaRequest] = None,
        *,
        tool_allowlist: Optional[set[str]] = None,
        **upstream_kwargs: Any,
    ) -> OllamaResponse | dict[str, Any]:
        """Canonical chat entry point.

        When called with an *OllamaRequest* (hermes-lite native), returns
        an *OllamaResponse*.  When called with keyword arguments from
        upstream ``chat_completion_helpers.py``, returns an OpenAI-shaped
        dict for backwards compatibility.
        """
        if upstream_kwargs:
            return self._chat_compat(tool_allowlist=tool_allowlist, **upstream_kwargs)
        if request is None:
            raise TypeError("chat() requires either an OllamaRequest or keyword arguments")
        return await self._chat_native(request, tool_allowlist)

    async def _chat_native(
        self,
        request: OllamaRequest,
        tool_allowlist: Optional[set[str]] = None,
    ) -> OllamaResponse:
        await self._probe_models()
        self._assert_model_available()

        body = self._build_chat_body(request)
        resp = await self._client.post(
            f"{self.base_url}/api/chat",
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        message = data.get("message", {})
        assistant_text = message.get("content", "")

        # Ollama native tool_calls (future-proof)
        native_calls = message.get("tool_calls", [])
        parsed_calls: list[dict[str, Any]] = []
        if native_calls:
            parsed_calls = [
                {"name": c["function"]["name"], "arguments": json.loads(c["function"]["arguments"])}
                for c in native_calls
                if isinstance(c, dict) and "function" in c
            ]
        elif assistant_text and tool_allowlist:
            # Fallback: parse JSON blobs from assistant text
            parsed_calls = _parse_tool_calls(assistant_text, tool_allowlist)

        return OllamaResponse(
            assistant_text=assistant_text,
            tool_calls=parsed_calls,
            done=data.get("done", True),
            model=data.get("model", self.model),
            total_duration_ms=data.get("total_duration"),
        )

    def _chat_compat(
        self,
        *,
        model: Optional[str] = None,
        messages: Optional[list[dict[str, Any]]] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        ollama_num_ctx: Optional[int] = None,
        **_: Any,
    ) -> dict[str, Any]:
        """Synchronous compatibility wrapper used by chat_completion_helpers.py."""
        import asyncio

        _model = model or self.model
        _messages = [
            OllamaMessage(role=m.get("role", "user"), content=m.get("content", ""))
            for m in (messages or [])
        ]
        _tools = tools or []
        options: dict[str, Any] = {}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if temperature is not None:
            options["temperature"] = temperature
        if ollama_num_ctx is not None:
            options["num_ctx"] = ollama_num_ctx

        request = OllamaRequest(
            model=_model,
            messages=_messages,
            tools=_tools,
            options=options,
        )

        response = asyncio.run(self._chat_native(request))

        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response.assistant_text or None,
                        "tool_calls": [
                            {
                                "id": f"call_{i}",
                                "type": "function",
                                "function": {
                                    "name": c["name"],
                                    "arguments": json.dumps(c["arguments"]),
                                },
                            }
                            for i, c in enumerate(response.tool_calls)
                        ] or None,
                    },
                    "finish_reason": "stop" if response.done else "length",
                    "index": 0,
                }
            ],
            "model": response.model or _model,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> OllamaAdapter:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Helpers for Hermes integration
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> OllamaAdapter:
        """Factory that builds an adapter from the merged lite config."""
        provider_cfg = cfg.get("provider", {}).get("ollama", {})
        return cls(
            base_url=provider_cfg.get("base_url", os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")),
            model=provider_cfg.get("model", cfg.get("model", "ministral-3:3b")),
            context_window=provider_cfg.get("context_window", 32768),
            timeout=provider_cfg.get("timeout", 120.0),
        )
