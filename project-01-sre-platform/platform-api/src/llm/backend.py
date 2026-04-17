"""
Pluggable LLM backend — Adapter pattern.

Not tied to any single provider. The factory reads env to choose between
Gemini (default), Ollama, and Claude. If the chosen backend can't be
built (missing API key, unreachable host), the factory returns None and
the caller degrades gracefully.

See shared/adr/0011-pluggable-llm-backend.md.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMBackend(Protocol):
    """Minimal generation interface shared by all providers."""

    name: str

    def generate(self, prompt: str, *, max_tokens: int = 256) -> str: ...


def make_backend(name: str | None = None) -> LLMBackend | None:
    """
    Build a backend from env. Returns None if unconfigured or unavailable.

    - LLM_BACKEND env var selects the provider (default: 'gemini').
    - Each provider reads its own credentials from env.
    """
    name = (name or os.environ.get("LLM_BACKEND", "gemini")).lower()

    try:
        if name == "gemini":
            from .gemini_backend import GeminiBackend

            key = os.environ.get("GOOGLE_API_KEY")
            if not key:
                logger.warning("GOOGLE_API_KEY not set; /explain will degrade")
                return None
            return GeminiBackend(api_key=key)

        if name == "ollama":
            from .ollama_backend import OllamaBackend

            return OllamaBackend(
                endpoint=os.environ.get("OLLAMA_ENDPOINT", "http://host.docker.internal:11434"),
                model=os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"),
            )

        if name == "claude":
            from .claude_backend import ClaudeBackend

            return ClaudeBackend()
    except Exception:
        logger.exception("failed to construct LLM backend %s", name)
        return None

    logger.warning("unknown LLM backend %r", name)
    return None
