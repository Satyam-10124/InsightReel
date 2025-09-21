"""Typed structures for InsightReel.

These dataclasses make the pipeline easier to understand and type.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class TranscriptSegment:
    file: Optional[str]
    start_time: int
    end_time: int
    duration: int
    text: str
    timestamp: str
    language: Optional[str] = None


KeyConcepts = Dict[str, Any]
