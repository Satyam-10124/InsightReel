"""
InsightReel core package

Lightweight, modular building blocks for YouTube transcription and summarization.

Main entrypoints:
- SummarizerPipeline: end-to-end processing pipeline
- prompt_user_profile: interactive CLI helper to collect user preferences
"""
from .pipeline import SummarizerPipeline
from .preferences import USER_TYPES, prompt_user_profile

__all__ = [
    "SummarizerPipeline",
    "USER_TYPES",
    "prompt_user_profile",
]
