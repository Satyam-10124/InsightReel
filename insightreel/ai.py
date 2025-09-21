"""AI client integration for InsightReel.

Currently supports Google Gemini via google-generativeai. If unavailable,
falls back to disabled mode automatically.
"""
from __future__ import annotations
import os
from typing import Optional

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore


class AiClient:
    """Thin wrapper around Gemini for content generation."""

    def __init__(self, model_name: str = "gemini-2.5-pro") -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        self.enabled = bool(api_key and genai)
        self._model = None
        if self.enabled:
            try:
                genai.configure(api_key=api_key)  # type: ignore[attr-defined]
                self._model = genai.GenerativeModel(model_name)  # type: ignore[attr-defined]
            except Exception:
                # If setup fails, quietly disable AI
                self.enabled = False
                self._model = None

    def generate(self, prompt: str) -> Optional[str]:
        if not self.enabled or self._model is None:
            return None
        try:
            response = self._model.generate_content(prompt)
            return getattr(response, "text", None) or None
        except Exception:
            return None
