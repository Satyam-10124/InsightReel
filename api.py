"""FastAPI server for InsightReel

Exposes HTTP endpoints to summarize YouTube videos using the modular
SummarizerPipeline. Suitable for Railway deployment.

Routes:
- GET  /health           -> basic health and status
- GET  /cache/info       -> cache stats
- POST /cache/clear      -> clear cache
- POST /summarize        -> summarize a YouTube URL

Run locally:
  uvicorn api:app --host 0.0.0.0 --port 8000

Environment:
- GEMINI_API_KEY (optional) to enable AI summaries
- WHISPER_MODEL  (optional) one of: tiny, base, small, medium, large (default: small)
"""
from __future__ import annotations
import os
from functools import lru_cache
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, HttpUrl, validator

from insightreel.pipeline import SummarizerPipeline
from insightreel.cache import CacheManager
from insightreel import youtube as youtube_utils
from insightreel import audio as audio_utils
from insightreel.transcriber import Transcriber
from insightreel.analysis import extract_key_concepts

# ------------------------ API Key Middleware ----------------------- #

class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, api_key: Optional[str] = None, exempt_paths: Optional[List[str]] = None) -> None:
        super().__init__(app)
        self.api_key = api_key
        self.exempt = set(exempt_paths or ["/", "/health", "/docs", "/openapi.json"])

    async def dispatch(self, request: Request, call_next):
        # Disabled if no API key configured
        if not self.api_key:
            return await call_next(request)

        path = request.url.path
        if path in self.exempt or request.method == "OPTIONS":
            return await call_next(request)

        key = request.headers.get("X-API-KEY")
        if key != self.api_key:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        return await call_next(request)

# ----------------------------- Models ----------------------------- #

class UserProfile(BaseModel):
    type: str = Field(
        default="general",
        description="User role/profile",
        pattern=r"^(student|professional|developer|entrepreneur|researcher|general)$",
    )
    name: Optional[str] = None
    icon: Optional[str] = None
    length: str = Field(default="standard", pattern=r"^(quick|standard|detailed)$")
    focus: Optional[str] = None

    @validator("type")
    def normalize_type(cls, v: str) -> str:
        return v.lower()

    @validator("length")
    def normalize_length(cls, v: str) -> str:
        return v.lower()

    def filled(self) -> Dict[str, Any]:
        defaults = {
            "student": {"name": "Student", "icon": "🎓"},
            "professional": {"name": "Business Professional", "icon": "💼"},
            "developer": {"name": "Developer", "icon": "🔧"},
            "entrepreneur": {"name": "Entrepreneur", "icon": "🚀"},
            "researcher": {"name": "Researcher", "icon": "📚"},
            "general": {"name": "General Audience", "icon": "🌟"},
        }
        base = defaults.get(self.type, defaults["general"]).copy()
        if self.name:
            base["name"] = self.name
        if self.icon:
            base["icon"] = self.icon
        base["type"] = self.type
        base["length"] = self.length
        base["focus"] = self.focus
        return base


class SummarizeRequest(BaseModel):
    url: HttpUrl
    profile: Optional[UserProfile] = Field(default=None, description="User profile for personalization")
    save_markdown_to_file: bool = Field(default=False, description="Save summary to a markdown file on the server")
    sample_max_minutes: int = Field(default=20, ge=5, le=120, description="Cap transcription duration by sampling")
    max_video_seconds: int = Field(default=3 * 3600, ge=60, le=8 * 3600)
    canonicalize: bool = Field(default=True, description="Canonicalize YouTube URL to avoid playlist/consent issues")
    use_cookies: bool = Field(default=False, description="Use server-provisioned YouTube cookies for gated videos")


class TranscribeRequest(BaseModel):
    url: HttpUrl
    sample_max_minutes: int = Field(default=20, ge=5, le=120)
    model_size: str = Field(default="small", description="Whisper model size")
    canonicalize: bool = Field(default=True)
    use_cookies: bool = Field(default=False)


class AnalyzeFromTranscriptsRequest(BaseModel):
    transcripts: List[Dict[str, Any]] = Field(..., description="List of transcript segments with 'text' and 'timestamp'")


class PipelineRunRequest(BaseModel):
    url: HttpUrl
    profile: Optional[UserProfile] = None
    sample_max_minutes: int = Field(default=20, ge=5, le=120)
    max_video_seconds: int = Field(default=3 * 3600, ge=60, le=8 * 3600)
    save_markdown_to_file: bool = False
    canonicalize: bool = Field(default=True)
    use_cookies: bool = Field(default=False)


class AudioDownloadRequest(BaseModel):
    url: HttpUrl
    canonicalize: bool = Field(default=True)
    use_cookies: bool = Field(default=False)


# ---------------------------- App Setup --------------------------- #

app = FastAPI(title="InsightReel API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(APIKeyMiddleware, api_key=os.getenv("API_KEY"))


@lru_cache(maxsize=1)
def get_pipeline() -> SummarizerPipeline:
    model_size = os.getenv("WHISPER_MODEL", "small")
    return SummarizerPipeline(model_size=model_size)


# ----------------------------- Routes ----------------------------- #

@app.get("/health", tags=["system"])
async def health() -> Dict[str, Any]:
    try:
        pipe = get_pipeline()
        return {
            "status": "ok",
            "ai_enabled": bool(getattr(pipe, "ai", None) and getattr(pipe.ai, "enabled", False)),
            "whisper_model": os.getenv("WHISPER_MODEL", "small"),
            "cache": pipe.cache_stats(),
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/", response_class=HTMLResponse, tags=["system"])
async def welcome() -> HTMLResponse:
    model = os.getenv("WHISPER_MODEL", "small")
    workers = os.getenv("MAX_TRANSCRIBE_WORKERS", "1")
    example_base = "https://insight-reel-production.up.railway.app"
    html = f"""
    <html>
      <head><title>InsightReel API</title></head>
      <body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px;">
        <h1>InsightReel API</h1>
        <p>Welcome! See <a href="/docs">/docs</a> for the interactive API docs.</p>
        <h2>Build-time Config</h2>
        <ul>
          <li>WHISPER_MODEL: <code>{model}</code></li>
          <li>MAX_TRANSCRIBE_WORKERS: <code>{workers}</code></li>
        </ul>
        <h2>Quick Examples (curl)</h2>
        <pre>
BASE={example_base}
curl -sS "$BASE/health" | jq

curl -sS -X POST "$BASE/audio/download" \
  -H "Content-Type: application/json" \
  -d '{{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ", "canonicalize": true}}' | jq

curl -L "$BASE/audio/dQw4w9WgXcQ" -o audio.wav
        </pre>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/cache/info", tags=["cache"])
async def cache_info() -> Dict[str, Any]:
    pipe = get_pipeline()
    return pipe.cache_stats()


@app.post("/cache/clear", tags=["cache"])
async def cache_clear() -> Dict[str, Any]:
    pipe = get_pipeline()
    cleared = pipe.clear_cache()
    return {"cleared": cleared}


@app.post("/summarize", tags=["summary"])
async def summarize(payload: SummarizeRequest) -> Dict[str, Any]:
    pipe = get_pipeline()

    profile = payload.profile.filled() if payload.profile else {
        "type": "general",
        "name": "General Audience",
        "icon": "🌟",
        "length": "standard",
        "focus": None,
    }

    try:
        url_to_use = youtube_utils.canonicalize_url(str(payload.url)) if payload.canonicalize else str(payload.url)
        result = pipe.process(
            url_to_use,
            profile,
            progress=None,
            max_video_seconds=payload.max_video_seconds,
            sample_max_minutes=payload.sample_max_minutes,
            save_markdown_to_file=payload.save_markdown_to_file,
            use_cookies=payload.use_cookies,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=str(result.get("error", "Unknown error")))

    return result


# ----------------------- YouTube Utility Routes ----------------------- #

@app.get("/youtube/id", tags=["youtube"])
async def youtube_id(url: HttpUrl) -> Dict[str, Any]:
    vid = youtube_utils.get_video_id_from_url(str(url))
    if not vid:
        raise HTTPException(status_code=400, detail="Could not extract video ID")
    return {"video_id": vid}


@app.get("/youtube/metadata", tags=["youtube"])
async def youtube_metadata(url: HttpUrl, canonicalize: bool = True) -> Dict[str, Any]:
    try:
        the_url = youtube_utils.canonicalize_url(str(url)) if canonicalize else str(url)
        info = youtube_utils.fetch_metadata(the_url)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metadata fetch failed: {e}")


# ------------------------- Audio Routes ------------------------- #

@app.post("/audio/download", tags=["audio"])
async def audio_download(payload: AudioDownloadRequest) -> Dict[str, Any]:
    url_str = str(payload.url)
    if payload.canonicalize:
        url_str = youtube_utils.canonicalize_url(url_str)
    vid = youtube_utils.get_video_id_from_url(url_str)
    if not vid:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    pipe = get_pipeline()
    audio_path = audio_utils.download_audio(url_str, vid, pipe.cache, use_cookies=payload.use_cookies)
    dur = audio_utils.get_audio_duration(audio_path)
    return {
        "video_id": vid,
        "audio_url": f"/audio/{vid}",
        "duration_seconds": int(dur),
        "cache_path": audio_path,
    }


@app.get("/audio/{video_id}", response_class=FileResponse, tags=["audio"])
async def audio_stream(video_id: str = Path(..., description="YouTube video ID")):
    pipe = get_pipeline()
    audio_path = pipe.cache.load(video_id, "audio")
    if not audio_path:
        raise HTTPException(status_code=404, detail="Audio not found in cache. POST /audio/download with the URL first.")
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file missing")
    return FileResponse(path=audio_path, media_type="audio/wav", filename=f"{video_id}.wav")


# ---------------------- Transcription Routes ---------------------- #

@app.post("/transcribe", tags=["transcription"])
async def transcribe(payload: TranscribeRequest) -> Dict[str, Any]:
    url_str = str(payload.url)
    if payload.canonicalize:
        url_str = youtube_utils.canonicalize_url(url_str)
    vid = youtube_utils.get_video_id_from_url(url_str)
    if not vid:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    cache = CacheManager()
    audio_path = audio_utils.download_audio(url_str, vid, cache, use_cookies=payload.use_cookies)
    duration = audio_utils.get_audio_duration(audio_path)
    chunks = audio_utils.split_audio(audio_path, duration)

    try:
        transcriber = Transcriber(model_size=payload.model_size)
        transcripts = transcriber.transcribe_chunks(
            chunks, vid, cache, progress=None, sample_max_minutes=payload.sample_max_minutes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    return {
        "video_id": vid,
        "segments": len(transcripts),
        "duration_seconds": int(duration),
        "transcripts": transcripts,
    }


# ------------------------- Analysis Routes ------------------------- #

@app.post("/analyze/from-transcripts", tags=["analysis"])
async def analyze_from_transcripts(payload: AnalyzeFromTranscriptsRequest) -> Dict[str, Any]:
    try:
        concepts = extract_key_concepts(payload.transcripts)
        return concepts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


# ------------------------- Pipeline Runner ------------------------- #

@app.post("/pipeline/run", tags=["pipeline"])
async def pipeline_run(payload: PipelineRunRequest) -> Dict[str, Any]:
    pipe = get_pipeline()
    profile = payload.profile.filled() if payload.profile else {
        "type": "general",
        "name": "General Audience",
        "icon": "🌟",
        "length": "standard",
        "focus": None,
    }
    try:
        url_to_use = youtube_utils.canonicalize_url(str(payload.url)) if payload.canonicalize else str(payload.url)
        result = pipe.process(
            url_to_use,
            profile,
            progress=None,
            max_video_seconds=payload.max_video_seconds,
            sample_max_minutes=payload.sample_max_minutes,
            save_markdown_to_file=payload.save_markdown_to_file,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {e}")
# --------------------------- Entrypoint --------------------------- #

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), workers=1)
