# Multi-stage Dockerfile for InsightReel API (FastAPI + Uvicorn)
# Base image: slim Python (CPU only)

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# System deps: minimal, no ffmpeg since we use imageio-ffmpeg bundled binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt ./

# Pre-install CPU-only PyTorch to avoid pulling CUDA-heavy builds
# See: https://pytorch.org/get-started/locally/
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.3.1+cpu

# Install remaining deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose API port
EXPOSE ${PORT}

# Healthcheck (simple)
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsSL http://127.0.0.1:${PORT}/health || exit 1

# Start FastAPI (single worker recommended due to Whisper model memory)
CMD ["/bin/sh", "-c", "exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
