"""
Gemini backend — the default.

Uses Google AI Studio's free-tier Gemini 2.5 Pro by default. No paid
plan required; users obtain a key at https://aistudio.google.com and
set `GOOGLE_API_KEY`.
"""

from __future__ import annotations

import logging

from google import genai

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-pro"


class GeminiBackend:
    name = "gemini"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, prompt: str, *, max_tokens: int = 256) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config={"max_output_tokens": max_tokens, "temperature": 0.3},
        )
        text = getattr(response, "text", None) or ""
        return text.strip()
