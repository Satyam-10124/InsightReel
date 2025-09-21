"""Logging utilities for InsightReel.

Centralized logger configuration to ensure consistent formatting across CLI and web.
"""
from __future__ import annotations
import logging
from typing import Optional

_DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
_configured = False


def configure_logging(level: int = logging.INFO, fmt: Optional[str] = None) -> None:
    """Configure root logging once.

    Safe to call multiple times; only the first call takes effect.
    """
    global _configured
    if _configured:
        return
    logging.basicConfig(level=level, format=fmt or _DEFAULT_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger with ensured global configuration."""
    configure_logging()
    return logging.getLogger(name)
