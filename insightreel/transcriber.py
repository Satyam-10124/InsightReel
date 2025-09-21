"""Audio transcription with Whisper for InsightReel.

Handles model loading, chunk transcription (parallel), cleaning, and caching.
"""
from __future__ import annotations
from typing import Callable, Dict, List, Optional
import os
import concurrent.futures
import multiprocessing

from .logger import get_logger
from .cache import CacheManager
from .text_cleaner import clean_transcript_advanced
from . import audio as audio_utils

logger = get_logger(__name__)

try:
    import whisper  # type: ignore
except Exception as e:  # pragma: no cover - optional dependency import at runtime
    whisper = None  # type: ignore


class Transcriber:
    """Whisper-based transcriber with parallel chunk processing."""

    def __init__(self, model_size: str = "small") -> None:
        if whisper is None:
            raise RuntimeError("openai-whisper is required. Install 'openai-whisper'.")
        # Ensure ffmpeg is discoverable by Whisper
        try:
            ffbin = getattr(audio_utils, "FFMPEG_BIN", "ffmpeg")
            if isinstance(ffbin, str) and os.path.isabs(ffbin) and os.path.exists(ffbin):
                ffdir = os.path.dirname(ffbin) or "."
                os.environ["PATH"] = ffdir + os.pathsep + os.environ.get("PATH", "")
                logger.info(f"🔧 ffmpeg available at {ffbin}")
        except Exception:
            pass
        logger.info("🔄 Loading Whisper model...")
        self.model = whisper.load_model(model_size)
        logger.info(f"✅ Whisper loaded ({model_size} model)")

    def _transcribe_single_chunk(self, chunk: Dict[str, object]) -> Optional[Dict[str, object]]:
        try:
            result = self.model.transcribe(
                chunk["file"],  # type: ignore[arg-type]
                fp16=False,
                language="en",  # Helps quality when content is English
                verbose=False,
                temperature=0.0,
                condition_on_previous_text=False,  # Prevent repetition
                no_speech_threshold=0.6,
                logprob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            )
            text = str(result.get("text", "")).strip()
            if text and len(text) > 10:
                text = clean_transcript_advanced(text)
                if len(text) > 20 and "Unable to extract" not in text and "Error processing" not in text:
                    data = {
                        "start_time": int(chunk["start_time"]),
                        "end_time": int(chunk["start_time"]) + int(chunk["duration"]),
                        "text": text,
                        "timestamp": f"{int(chunk['start_time'])//60}:{int(chunk['start_time'])%60:02d}",
                        "language": result.get("language", "unknown"),
                    }
                    # Cleanup chunk file
                    try:
                        os.remove(chunk["file"])  # type: ignore[arg-type]
                    except Exception:
                        pass
                    return data
            # Cleanup even if not enough text
            try:
                os.remove(chunk["file"])  # type: ignore[arg-type]
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Chunk transcription failed: {e}")
            try:
                os.remove(chunk["file"])  # type: ignore[arg-type]
            except Exception:
                pass
        return None

    def transcribe_chunks(
        self,
        chunks: List[Dict[str, object]],
        video_id: str,
        cache: CacheManager,
        progress: Optional[Callable[[str], None]] = None,
        sample_max_minutes: int = 20,
    ) -> List[Dict[str, object]]:
        """Transcribe chunks. Uses cache when available, else parallel processing with sampling."""
        cached = cache.load(video_id, "transcript")
        if cached:
            if progress:
                progress("📁 Using cached transcript")
            logger.info("📁 Using cached transcript")
            return cached  # type: ignore[return-value]

        # Smart sampling to limit long videos
        original_count = len(chunks)
        chunks = audio_utils.smart_sample_audio(chunks, max_minutes=sample_max_minutes)

        if progress:
            progress(f"🎤 Transcribing {len(chunks)}/{original_count} chunks in parallel...")
        logger.info(f"🎤 Transcribing {len(chunks)}/{original_count} chunks in parallel...")

        transcripts: List[Dict[str, object]] = []
        max_workers = max(1, min(multiprocessing.cpu_count() // 2, 3))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._transcribe_single_chunk, chunk): i for i, chunk in enumerate(chunks)}
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=120)
                    if result:
                        transcripts.append(result)
                    if progress:
                        progress(f"   ✅ Processed {len(transcripts)}/{len(chunks)} chunks")
                except Exception as e:
                    logger.warning(f"Future failed: {e}")
                    continue

        # Sort and cache
        transcripts.sort(key=lambda x: int(x["start_time"]))
        if transcripts:
            cache.save(video_id, "transcript", transcripts)
        if progress:
            progress(f"✅ Transcribed {len(transcripts)} segments")
        logger.info(f"✅ Transcribed {len(transcripts)} segments")
        return transcripts
