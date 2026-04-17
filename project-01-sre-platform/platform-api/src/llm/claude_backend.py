"""
Claude backend — stub.

Reserved for Project 02 where agentic behaviour justifies a more capable
managed model. Intentionally not implemented in Project 01 so the free-
tier default (Gemini) and offline fallback (Ollama) cover the narrative.
"""

from __future__ import annotations


class ClaudeBackend:
    name = "claude"

    def __init__(self) -> None:
        raise NotImplementedError(
            "ClaudeBackend is reserved for Project 02 (ai-sre-agent). "
            "Use LLM_BACKEND=gemini or LLM_BACKEND=ollama in Project 01."
        )

    def generate(self, prompt: str, *, max_tokens: int = 256) -> str:  # pragma: no cover
        raise NotImplementedError
