"""YouTube utilities for InsightReel.

- Extract video ID from URLs
- Fetch metadata using yt-dlp
"""
from __future__ import annotations
from typing import Dict, Optional
import re


def get_video_id_from_url(url: str) -> Optional[str]:
    """Extract a YouTube video ID from a URL.

    Returns None if no valid ID is found.
    """
    if not isinstance(url, str):
        return None
    match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None


def canonicalize_url(url: str) -> str:
    """Return a canonical YouTube watch URL (https://www.youtube.com/watch?v={id}).

    If an ID cannot be extracted, return the original URL unchanged.
    """
    vid = get_video_id_from_url(url)
    return f"https://www.youtube.com/watch?v={vid}" if vid else url


def fetch_metadata(url: str) -> Dict[str, object]:
    """Fetch video metadata via yt-dlp without downloading the video.

    Returns a dict with keys: title, duration, channel, url
    """
    try:
        import yt_dlp  # type: ignore
    except Exception as e:  # pragma: no cover - optional at import time
        raise RuntimeError(f"yt-dlp is required: {e}")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
        "extract_flat": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise RuntimeError("Could not extract video information")

        title = str(info.get("title", "Unknown Video")).strip()
        duration = int(info.get("duration", 0) or 0)
        channel = str(info.get("uploader", "Unknown Channel")).strip()

        if not title or title == "Unknown Video":
            vid = get_video_id_from_url(url) or "video"
            title = f"Video_{vid}"
        if duration <= 0:
            duration = 600  # default 10 min

        return {
            "title": title,
            "duration": duration,
            "channel": channel,
            "url": url,
        }
