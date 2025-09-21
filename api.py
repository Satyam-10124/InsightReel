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
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl, validator

from insightreel.pipeline import SummarizerPipeline

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


# ---------------------------- App Setup --------------------------- #

app = FastAPI(title="InsightReel API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_pipeline() -> SummarizerPipeline:
    model_size = os.getenv("WHISPER_MODEL", "small")
    return SummarizerPipeline(model_size=model_size)


# ----------------------------- Routes ----------------------------- #

@app.get("/health")
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


@app.get("/cache/info")
async def cache_info() -> Dict[str, Any]:
    pipe = get_pipeline()
    return pipe.cache_stats()


@app.post("/cache/clear")
async def cache_clear() -> Dict[str, Any]:
    pipe = get_pipeline()
    cleared = pipe.clear_cache()
    return {"cleared": cleared}


@app.post("/summarize")
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
        result = pipe.process(str(payload.url), profile, progress=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=str(result.get("error", "Unknown error")))

    return result


# --------------------------- Entrypoint --------------------------- #

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), workers=1)
