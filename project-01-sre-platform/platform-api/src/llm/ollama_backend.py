"""
Ollama backend — the offline fallback.

Lets a grader run `/explain` without any API key by pointing at a local
Ollama process serving a small model like qwen2.5:3b. No internet, no
credentials, no cost.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class OllamaBackend:
    name = "ollama"

    def __init__(self, endpoint: str, model: str):
        self._endpoint = endpoint.rstrip("/")
        self._model = model

    def generate(self, prompt: str, *, max_tokens: int = 256) -> str:
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.3},
        }
        with httpx.Client(timeout=5.0) as client:
            r = client.post(f"{self._endpoint}/api/generate", json=payload)
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
