"""Transcript cleaning utilities.

Provides both a basic and an advanced cleaner. The advanced variant is
more aggressive against filler and repetitive text and used by default.
"""
from __future__ import annotations
import re
from typing import Optional
from .logger import get_logger

logger = get_logger(__name__)


def clean_transcript_basic(text: str) -> str:
    """Basic transcript cleanup with professional tone adjustments."""
    if not text:
        return ""
    try:
        # Remove excessive repetitions
        text = re.sub(r"\b(\w+)(\s+\1\b){2,}", r"\1", text)
        # Remove filler/casual expressions
        casual_patterns = [
            r"\b(?i:um|uh|er|ah|eh|oh|hmm|mmm|ugh)\b",
            r"\b(?i:you know|like|actually|basically|literally|obviously|definitely)\b",
            r"\b(?i:sort of|kind of|a bit|a little|pretty much)\b",
            r"\b(?i:yes,?\s*my\s*god,?\s*yes|oh\s*my\s*god|jesus|christ)\b",
            r"\b(?i:yeah|yep|nah|nope|okay|ok|alright|right)\s*[,.]?\s*",
            r"\b(?i:so\s*anyway|anyway|well\s*anyway)\b",
        ]
        for pattern in casual_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        # Remove annotations/sfx
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\(.*?\)", "", text)
        text = re.sub(r"<.*?>", "", text)
        # Trailing fragments
        text = re.sub(r"\s*\.\.\.\s*$", ".", text)
        text = re.sub(r"\s*,\s*$", ".", text)
        text = re.sub(r"\s*and\s*$", ".", text)
        text = re.sub(r"\s*but\s*$", ".", text)
        text = re.sub(r"\s*so\s*$", ".", text)
        # Spacing/punct
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r"([,.!?;:])\s*([,.!?;:])", r"\1", text)
        # Capitalize sentences
        text = text.strip()
        if text:
            sentences = re.split(r"[.!?]+", text)
            cleaned = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 3:
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    sentence = re.sub(r"\b(?i:gonna)\b", "going to", sentence)
                    sentence = re.sub(r"\b(?i:wanna)\b", "want to", sentence)
                    sentence = re.sub(r"\b(?i:gotta)\b", "need to", sentence)
                    sentence = re.sub(r"\b(?i:kinda)\b", "somewhat", sentence)
                    sentence = re.sub(r"\b(?i:sorta)\b", "somewhat", sentence)
                    cleaned.append(sentence)
            text = ". ".join(cleaned)
            if text and text[-1] not in ".!?":
                text += "."
        return text
    except Exception as e:
        logger.warning(f"Text cleaning error: {e}")
        return str(text).strip() if text else ""


def clean_transcript_advanced(text: str) -> str:
    """Advanced cleaner: reduces repetition, normalizes sentences, removes filler."""
    if not text:
        return ""
    try:
        text = re.sub(r"\b(\w+)(\s+\1\b){3,}", r"\1", text)
        words = text.split()
        cleaned_words = []
        i = 0
        while i < len(words):
            w = words[i]
            count = 1
            while i + count < len(words) and words[i + count] == w:
                count += 1
            cleaned_words.extend([w] * min(count, 2))
            i += count
        text = " ".join(cleaned_words)
        text = re.sub(r"\b(\w{1,3})\s+(\1\s+){2,}", r"\1 ", text)
        casual_patterns = [
            r"\b(?i:um|uh|er|ah|eh|oh|hmm|mmm|ugh)\b",
            r"\b(?i:you know|like|actually|basically|literally|obviously|definitely)\b",
            r"\b(?i:sort of|kind of|a bit|a little|pretty much)\b",
            r"\b(?i:yes,?\s*my\s*god,?\s*yes|oh\s*my\s*god|jesus|christ)\b",
            r"\b(?i:yeah|yep|nah|nope|okay|ok|alright|right)\s*[,.]?\s*",
            r"\b(?i:so\s*anyway|anyway|well\s*anyway)\b",
        ]
        for pattern in casual_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\(.*?\)", "", text)
        text = re.sub(r"<.*?>", "", text)
        text = re.sub(r"\s*\.\.\.\s*$", ".", text)
        text = re.sub(r"\s*,\s*$", ".", text)
        text = re.sub(r"\s*and\s*$", ".", text)
        text = re.sub(r"\s*but\s*$", ".", text)
        text = re.sub(r"\s*so\s*$", ".", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r"([,.!?;:])\s*([,.!?;:])", r"\1", text)
        sentences = re.split(r"[.!?]+", text)
        good = []
        for s in sentences:
            s = s.strip()
            if len(s) > 10:
                tokens = s.split()
                if len(set(tokens)) > len(tokens) * 0.3:
                    s = re.sub(r"\b(?i:gonna)\b", "going to", s)
                    s = re.sub(r"\b(?i:wanna)\b", "want to", s)
                    s = re.sub(r"\b(?i:gotta)\b", "need to", s)
                    s = re.sub(r"\b(?i:kinda)\b", "somewhat", s)
                    s = re.sub(r"\b(?i:sorta)\b", "somewhat", s)
                    s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
                    good.append(s)
        if good:
            text = ". ".join(good)
            if text and text[-1] not in ".!?":
                text += "."
        else:
            text = "Unable to extract meaningful content from this segment."
        return text
    except Exception as e:
        logger.warning(f"Text cleaning error: {e}")
        return "Error processing transcript segment."
