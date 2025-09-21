"""Audio processing utilities for InsightReel.

- Download audio with yt-dlp into cache as WAV mono 16kHz
- Inspect duration via ffprobe
- Split into chunks via ffmpeg
"""
from __future__ import annotations
import os
import shutil
import subprocess
import wave
import contextlib
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .cache import CacheManager
from .logger import get_logger

logger = get_logger(__name__)

# Use imageio-ffmpeg to ensure ffmpeg binary is available on platforms like Railway
try:
    import imageio_ffmpeg as iio_ffmpeg  # type: ignore
    FFMPEG_BIN = iio_ffmpeg.get_ffmpeg_exe()
except Exception:  # pragma: no cover - optional runtime fetch
    FFMPEG_BIN = "ffmpeg"  # fallback to system ffmpeg


def download_audio(url: str, video_id: str, cache: CacheManager, progress: Optional[Callable[[str], None]] = None) -> str:
    """Download best audio and convert to WAV mono 16kHz in cache.

    Returns path to WAV file in cache.
    """
    cached = cache.load(video_id, "audio")
    if cached and os.path.exists(cached):
        if progress:
            progress("📁 Using cached audio")
        logger.info(f"📁 Using cached audio: {cached}")
        return cached

    try:
        import yt_dlp  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"yt-dlp is required: {e}")

    paths = cache.get_paths(video_id)
    output_path = str(paths["audio"].with_suffix(""))

    if progress:
        progress("📥 Downloading audio...")
    logger.info("📥 Downloading audio...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 60,
        "retries": 2,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    final_audio_file = str(paths["audio"])
    possible_files = [output_path + ext for ext in [".wav", ".m4a", ".mp3", ".webm", ".opus"]]

    for test_file in possible_files:
        if os.path.exists(test_file):
            if not test_file.endswith(".wav"):
                cmd = [
                    FFMPEG_BIN,
                    "-i",
                    test_file,
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-y",
                    final_audio_file,
                ]
                subprocess.run(cmd, capture_output=True, timeout=60)
                try:
                    os.remove(test_file)
                except Exception:
                    pass
            else:
                shutil.move(test_file, final_audio_file)
            return final_audio_file

    raise RuntimeError("No audio file was created")


def get_audio_duration(audio_file: str) -> float:
    """Get duration of WAV in seconds using Python wave; fallback to size estimate."""
    try:
        with contextlib.closing(wave.open(audio_file, "rb")) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                duration = frames / float(rate)
                if duration > 0:
                    logger.info(f"📏 Audio duration: {duration/60:.1f} minutes")
                    return duration
    except Exception as e:
        logger.warning(f"Duration detection failed: {e}")

    try:
        file_size = os.path.getsize(audio_file)
        estimated_duration = file_size / 32000
        return max(60, estimated_duration)
    except Exception:
        return 600.0


def split_audio(input_file: str, total_duration: float, progress: Optional[Callable[[str], None]] = None) -> List[Dict[str, object]]:
    """Split audio into time-based chunks and return list of chunk dicts."""
    if total_duration <= 300:  # 5 min
        chunk_duration = 60
    elif total_duration <= 900:  # 15 min
        chunk_duration = 120
    elif total_duration <= 1800:  # 30 min
        chunk_duration = 180
    else:
        chunk_duration = 300

    if progress:
        progress(f"🔪 Splitting audio into {chunk_duration/60:.1f}min chunks...")
    logger.info(f"🔪 Splitting audio into {chunk_duration/60:.1f}min chunks...")

    chunks: List[Dict[str, object]] = []
    temp_dir = os.path.dirname(input_file)

    for start_time in range(0, int(total_duration), chunk_duration):
        chunk_file = os.path.join(temp_dir, f"chunk_{len(chunks):04d}.wav")
        actual_duration = min(chunk_duration, total_duration - start_time)
        try:
            cmd = [
                FFMPEG_BIN,
                "-i",
                input_file,
                "-ss",
                str(start_time),
                "-t",
                str(actual_duration),
                "-ac",
                "1",
                "-ar",
                "16000",
                "-y",
                "-loglevel",
                "error",
                chunk_file,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=90)
            if result.returncode == 0 and os.path.exists(chunk_file):
                file_size = os.path.getsize(chunk_file)
                if file_size > 1000:
                    chunks.append(
                        {
                            "file": chunk_file,
                            "start_time": start_time,
                            "duration": actual_duration,
                            "size": file_size,
                        }
                    )
                    if progress:
                        progress(f"   ✂️  Chunk {len(chunks)} ready")
                    logger.info(f"   ✂️  Chunk {len(chunks)} ready")
                    continue
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
        except Exception as e:
            logger.warning(f"Failed to create chunk at {start_time}s: {e}")
            continue

    if not chunks:
        raise RuntimeError("No audio chunks were created")

    if progress:
        progress(f"✅ Created {len(chunks)} audio chunks")
    logger.info(f"✅ Created {len(chunks)} audio chunks")
    return chunks


def smart_sample_audio(chunks: List[Dict[str, object]], max_minutes: int = 20) -> List[Dict[str, object]]:
    """Return a sampled subset of chunks to cap total duration near max_minutes."""
    total_duration = sum(float(c["duration"]) for c in chunks)
    if total_duration <= max_minutes * 60:
        return chunks

    target_duration = max_minutes * 60
    sample_ratio = target_duration / total_duration
    step = max(1, int(1 / sample_ratio))

    sampled: List[Dict[str, object]] = []
    if chunks:
        sampled.append(chunks[0])
        sampled.extend(chunks[1:-1:step])
        if len(chunks) > 1:
            sampled.append(chunks[-1])
    logger.info(
        f"📊 Sampled {len(sampled)}/{len(chunks)} chunks ({sum(float(c['duration']) for c in sampled)/60:.1f} min)"
    )
    return sampled
