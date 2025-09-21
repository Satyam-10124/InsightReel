"""Caching utilities for InsightReel.

Handles path conventions and read/write of cached artifacts.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional
import json


class CacheManager:
    """Manage cache files scoped by YouTube video ID.

    Cache layout in cache_dir:
      {video_id}_metadata.json
      {video_id}_audio.wav
      {video_id}_transcript.json
    """

    def __init__(self, cache_dir: str | Path = "youtube_cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_paths(self, video_id: str) -> Dict[str, Path]:
        return {
            "metadata": self.cache_dir / f"{video_id}_metadata.json",
            "audio": self.cache_dir / f"{video_id}_audio.wav",
            "transcript": self.cache_dir / f"{video_id}_transcript.json",
        }

    def save(self, video_id: str, data_type: str, data: Any) -> None:
        paths = self.get_paths(video_id)
        if data_type == "metadata":
            with open(paths["metadata"], "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        elif data_type == "transcript":
            with open(paths["transcript"], "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def load(self, video_id: str, data_type: str) -> Optional[Any]:
        paths = self.get_paths(video_id)
        if data_type == "metadata" and paths["metadata"].exists():
            with open(paths["metadata"], "r", encoding="utf-8") as f:
                return json.load(f)
        if data_type == "transcript" and paths["transcript"].exists():
            with open(paths["transcript"], "r", encoding="utf-8") as f:
                return json.load(f)
        if data_type == "audio" and paths["audio"].exists():
            return str(paths["audio"])  # return as string path
        return None

    def clear_all(self) -> int:
        count = 0
        if not self.cache_dir.exists():
            return 0
        for p in self.cache_dir.glob("*"):
            try:
                p.unlink()
                count += 1
            except Exception:
                pass
        return count

    def stats(self) -> Dict[str, Any]:
        if not self.cache_dir.exists():
            return {"exists": False, "files": 0, "size_mb": 0.0, "videos": 0}
        files = list(self.cache_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        video_ids = set()
        for file in files:
            if file.is_file():
                parts = file.stem.split("_")
                if parts:
                    video_ids.add(parts[0])
        return {
            "exists": True,
            "files": len(files),
            "size_mb": total_size / 1024 / 1024,
            "videos": len(video_ids),
            "location": str(self.cache_dir.resolve()),
        }
