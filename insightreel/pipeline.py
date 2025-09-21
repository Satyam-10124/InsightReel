"""End-to-end processing pipeline for InsightReel.

Uses modular components to:
1) Fetch YouTube metadata (with caching)
2) Download audio and split into chunks
3) Transcribe audio with Whisper (cached)
4) Extract key concepts
5) Generate summary (AI if available, else basic)

All heavy-lifting is here so both CLI and Streamlit can share logic.
"""
from __future__ import annotations
from typing import Callable, Dict, Optional
import time
import os
import re
import tempfile
import shutil
import gc

from .logger import get_logger
from .cache import CacheManager
from .ai import AiClient
from . import youtube
from . import audio as audio_utils
from .transcriber import Transcriber
from .analysis import extract_key_concepts
from .summarizer import create_summary

logger = get_logger(__name__)


class SummarizerPipeline:
    """High-level orchestrator for YouTube summarization."""

    def __init__(self, model_size: str = "small", cache_dir: str = "youtube_cache") -> None:
        self.cache = CacheManager(cache_dir)
        self.ai = AiClient()
        self.transcriber = Transcriber(model_size=model_size)

    # -------------------------- Cache Utilities --------------------------- #
    def cache_stats(self) -> Dict[str, object]:
        return self.cache.stats()

    def clear_cache(self) -> int:
        return self.cache.clear_all()

    # ----------------------------- Processing ---------------------------- #
    def process(
        self,
        url: str,
        user_profile: Dict[str, object],
        *,
        progress: Optional[Callable[[str], None]] = None,
        max_video_seconds: int = 3 * 3600,
        sample_max_minutes: int = 20,
        save_markdown_to_file: bool = False,
    ) -> Dict[str, object]:
        """Run the full pipeline and return results.

        Returns a dict containing keys similar to the original scripts:
          success, summary (if not saved), filename (if saved), video_title,
          channel, duration, segments, processing_time, ai_enhanced,
          user_profile, cached_data_used, key_concepts
        """
        if not url or not isinstance(url, str):
            return {"success": False, "error": "Invalid URL provided"}
        if "youtube.com" not in url and "youtu.be" not in url:
            return {"success": False, "error": "Please provide a valid YouTube URL"}

        video_id = youtube.get_video_id_from_url(url)
        if not video_id:
            return {"success": False, "error": "Could not extract video ID from URL"}

        logger.info(f"🎬 Processing video ID: {video_id}")

        start_time = time.time()
        temp_dir: Optional[str] = None

        try:
            # Temp workspace (chunk files live alongside the audio in cache though)
            temp_dir = tempfile.mkdtemp(prefix="yt_summarizer_")
            if progress:
                progress("🚀 Starting video analysis...")
            logger.info("🚀 Starting video analysis...")

            # 1) Metadata
            if progress:
                progress("📋 Extracting metadata...")
            logger.info("📋 Extracting metadata...")

            cached_metadata = self.cache.load(video_id, "metadata")
            if cached_metadata:
                if progress:
                    progress("📁 Using cached metadata")
                logger.info("📁 Using cached metadata")
                video_title = cached_metadata["title"]
                duration = int(cached_metadata["duration"])
                channel = cached_metadata["channel"]
            else:
                try:
                    info = youtube.fetch_metadata(url)
                    video_title = str(info.get("title", "Video")).strip()
                    duration = int(info.get("duration", 0) or 0)
                    channel = str(info.get("channel", "Unknown Channel")).strip()
                    self.cache.save(video_id, "metadata", info)
                except Exception as e:
                    return {"success": False, "error": f"Failed to extract video info: {str(e)[:200]}"}

            duration_str = f"{duration//60}:{duration%60:02d}"
            logger.info(f"✅ Video: {video_title[:50]}{'...' if len(video_title) > 50 else ''}")
            logger.info(f"📺 Channel: {channel}")
            logger.info(f"⏱️  Duration: {duration_str}")
            if duration > max_video_seconds:
                return {
                    "success": False,
                    "error": f"Video too long ({duration//3600}h {(duration%3600)//60}m). Maximum: {max_video_seconds//3600} hours",
                }

            # 2) Audio
            try:
                audio_file = audio_utils.download_audio(url, video_id, self.cache, progress)
                if not audio_file or not os.path.exists(audio_file):
                    raise RuntimeError("Audio download failed")
            except Exception as e:
                return {"success": False, "error": f"Audio processing failed: {str(e)[:300]}"}

            # 3) Split
            try:
                actual_duration = audio_utils.get_audio_duration(audio_file)
                chunks = audio_utils.split_audio(audio_file, actual_duration, progress)
                if not chunks:
                    raise RuntimeError("No audio chunks created")
            except Exception as e:
                return {"success": False, "error": f"Audio splitting failed: {str(e)[:300]}"}

            # 4) Transcribe
            try:
                transcripts = self.transcriber.transcribe_chunks(
                    chunks, video_id, self.cache, progress, sample_max_minutes=sample_max_minutes
                )
                if not transcripts:
                    logger.warning("No transcripts generated; creating fallback")
                    transcripts = [
                        {
                            "start_time": 0,
                            "end_time": duration,
                            "text": f"Unable to transcribe content from this video. Video title: {video_title}",
                            "timestamp": "0:00",
                        }
                    ]
            except Exception as e:
                logger.warning(f"Transcription failed: {e}")
                transcripts = [
                    {
                        "start_time": 0,
                        "end_time": duration,
                        "text": f"Transcription failed for this video. Error: {str(e)[:100]}",
                        "timestamp": "0:00",
                    }
                ]

            # 5) Analyze & summarize
            try:
                if progress:
                    progress("🔍 Analyzing content...")
                key_concepts = extract_key_concepts(transcripts)
                summary_text = create_summary(
                    transcripts,
                    video_title,
                    url,
                    duration_str,
                    key_concepts,
                    user_profile,
                    ai=self.ai,
                )
                if not summary_text or len(summary_text) < 100:
                    raise RuntimeError("Summary generation failed")
            except Exception as e:
                return {"success": False, "error": f"Summary creation failed: {str(e)[:300]}"}

            processing_time = time.time() - start_time
            if progress:
                progress(f"🎉 Analysis completed in {processing_time/60:.1f} minutes")
            logger.info(f"🎉 Analysis completed in {processing_time/60:.1f} minutes")

            result: Dict[str, object] = {
                "success": True,
                "summary": summary_text,
                "video_title": video_title,
                "channel": channel,
                "duration": duration_str,
                "segments": len(transcripts),
                "processing_time": f"{processing_time/60:.1f} minutes",
                "ai_enhanced": bool(self.ai.enabled),
                "user_profile": dict(user_profile),
                "cached_data_used": bool(cached_metadata or self.cache.load(video_id, "transcript")),
                "key_concepts": key_concepts,
            }

            if save_markdown_to_file:
                safe_title = re.sub(r"[^\w\s\-_]", "", video_title)[:30]
                safe_title = re.sub(r"\s+", "_", safe_title.strip())
                user_type = str(user_profile.get("type", "general"))
                filename = f"summary_{user_type}_{safe_title}_{int(time.time())}.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(summary_text)
                if os.path.exists(filename):
                    result["filename"] = filename
                else:
                    return {"success": False, "error": "Summary file not created"}

            return result

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)[:300]}"}

        finally:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    logger.warning(f"⚠️  Cleanup warning: {cleanup_error}")
            gc.collect()
