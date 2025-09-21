# InsightReel Frontend Integration Guide

This guide shows how to integrate a frontend (React/Next.js or any SPA) with the InsightReel backend, including:
- An idiomatic TypeScript SDK over the API
- UI/UX patterns for audio, transcripts, and summaries
- Recommended frontend libraries and example snippets
- Performance and cost knobs to keep things fast and inexpensive

Backend base URL: https://insight-reel-production.up.railway.app
Docs: https://insight-reel-production.up.railway.app/docs

## 1) Quick Start

- Set a base URL env var in your frontend (e.g. Next.js):
  - .env.local
    - `NEXT_PUBLIC_API_BASE=https://insight-reel-production.up.railway.app`
- Add libraries:
  - Data fetching: `@tanstack/react-query`
  - Forms & validation: `react-hook-form`, `zod`
  - Markdown: `react-markdown`, `remark-gfm`
  - Optional audio waveform: `wavesurfer.js`

## 2) Minimal TypeScript SDK

Create `lib/insightreel.ts` in your frontend:

```ts
// lib/insightreel.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;

export type UserProfile = {
  type: 'student' | 'professional' | 'developer' | 'entrepreneur' | 'researcher' | 'general';
  name?: string;
  icon?: string;
  length?: 'quick' | 'standard' | 'detailed';
  focus?: string | null;
};

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health failed: ${res.status}`);
  return res.json();
}

export async function getYoutubeId(url: string) {
  const res = await fetch(`${API_BASE}/youtube/id?url=${encodeURIComponent(url)}`);
  if (!res.ok) throw new Error('youtube/id failed');
  return res.json() as Promise<{ video_id: string }>;
}

export async function getYoutubeMetadata(url: string) {
  const res = await fetch(`${API_BASE}/youtube/metadata?url=${encodeURIComponent(url)}`);
  if (!res.ok) throw new Error('youtube/metadata failed');
  return res.json() as Promise<{ title: string; duration: number; channel: string; url: string }>;
}

export async function postAudioDownload(url: string) {
  const res = await fetch(`${API_BASE}/audio/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error('audio/download failed');
  return res.json() as Promise<{ video_id: string; audio_url: string; duration_seconds: number; cache_path: string }>;
}

export async function getAudioWav(videoId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}${`/audio/${videoId}`}`);
  if (!res.ok) throw new Error('audio stream failed');
  return res.blob();
}

export async function postTranscribe(url: string, sampleMaxMinutes = 20, modelSize: 'tiny' | 'base' | 'small' | 'medium' | 'large' = 'small') {
  const res = await fetch(`${API_BASE}/transcribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, sample_max_minutes: sampleMaxMinutes, model_size: modelSize }),
  });
  if (!res.ok) throw new Error('transcribe failed');
  return res.json() as Promise<{ video_id: string; segments: number; duration_seconds: number; transcripts: Array<any> }>;
}

export async function postSummarize(url: string, profile?: UserProfile, opts?: { sampleMaxMinutes?: number; maxVideoSeconds?: number; saveMarkdownToFile?: boolean }) {
  const res = await fetch(`${API_BASE}/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      profile,
      sample_max_minutes: opts?.sampleMaxMinutes ?? 20,
      max_video_seconds: opts?.maxVideoSeconds ?? 10800,
      save_markdown_to_file: opts?.saveMarkdownToFile ?? false,
    }),
  });
  if (!res.ok) throw new Error('summarize failed');
  return res.json();
}

export async function postPipelineRun(url: string, profile?: UserProfile, opts?: { sampleMaxMinutes?: number; maxVideoSeconds?: number; saveMarkdownToFile?: boolean }) {
  const res = await fetch(`${API_BASE}/pipeline/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      profile,
      sample_max_minutes: opts?.sampleMaxMinutes ?? 20,
      max_video_seconds: opts?.maxVideoSeconds ?? 10800,
      save_markdown_to_file: opts?.saveMarkdownToFile ?? false,
    }),
  });
  if (!res.ok) throw new Error('pipeline/run failed');
  return res.json();
}

export async function postAnalyzeFromTranscripts(transcripts: Array<{ text: string; timestamp?: string }>) {
  const res = await fetch(`${API_BASE}/analyze/from-transcripts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcripts }),
  });
  if (!res.ok) throw new Error('analyze/from-transcripts failed');
  return res.json();
}
```

## 3) React Integration Patterns

### 3.1 Data fetching with React Query

```tsx
// components/SummarizeForm.tsx
import { useMutation } from '@tanstack/react-query';
import { postPipelineRun } from '@/lib/insightreel';

export function SummarizeForm() {
  const { mutate, data, isPending, error } = useMutation({
    mutationFn: (url: string) => postPipelineRun(url, { type: 'general', length: 'quick', focus: null }),
  });

  return (
    <div>
      <input id="url" placeholder="Paste YouTube URL" />
      <button onClick={() => mutate((document.getElementById('url') as HTMLInputElement).value)} disabled={isPending}>
        {isPending ? 'Summarizing…' : 'Summarize'}
      </button>
      {error && <p style={{ color: 'red' }}>{String(error)}</p>}
      {data && <pre>{data.summary}</pre>}
    </div>
  );
}
```

### 3.2 Render Markdown summary

```tsx
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function SummaryView({ markdown }: { markdown: string }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>;
}
```

### 3.3 Download and play WAV audio

```tsx
import { useEffect, useState } from 'react';
import { postAudioDownload, getAudioWav } from '@/lib/insightreel';

export function AudioPlayer({ url }: { url: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let revoke: string | null = null;
    (async () => {
      const { video_id } = await postAudioDownload(url);
      const blob = await getAudioWav(video_id);
      const objectUrl = URL.createObjectURL(blob);
      revoke = objectUrl;
      setSrc(objectUrl);
    })();
    return () => {
      if (revoke) URL.revokeObjectURL(revoke);
    };
  }, [url]);

  return src ? <audio controls src={src} /> : <p>Loading audio…</p>;
}
```

### 3.4 Optional: Waveform with WaveSurfer.js

```tsx
import WaveSurfer from 'wavesurfer.js';
import { useEffect, useRef } from 'react';

export function Waveform({ audioUrl }: { audioUrl: string }) {
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const ws = WaveSurfer.create({ container: ref.current, waveColor: '#ddd', progressColor: '#4f46e5' });
    ws.load(audioUrl);
    return () => ws.destroy();
  }, [audioUrl]);
  return <div ref={ref} style={{ height: 96 }} />;
}
```

### 3.5 Transcript timeline UI

- Show timestamped segments (`transcripts[]` from `/transcribe`)
- Make each segment clickable -> seek audio element to that time
- Filter/search transcript text live with Fuse.js (optional)

```tsx
export function TranscriptList({ segments, onSeek }: { segments: Array<{ timestamp: string; text: string }>; onSeek: (sec: number) => void }) {
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      {segments.map((s, i) => (
        <div key={i} onClick={() => {
          const [m, sec] = s.timestamp.split(':').map(Number);
          onSeek(m * 60 + sec);
        }} style={{ cursor: 'pointer' }}>
          <strong>{s.timestamp}</strong> — {s.text}
        </div>
      ))}
    </div>
  );
}
```

## 4) UX Patterns and Ideas

- **Progress-first UX**: Immediately show metadata (`/youtube/metadata`) and kick off `audio/download` + `pipeline/run` in the background, updating status messages.
- **Local history**: Store recent URLs and generated summaries in `localStorage` (e.g., with Zustand) for instant recall even if the server cache is cold.
- **Share actions**: Copy link, download Markdown, export to Notion/Docs.
- **Error fallback**: If `/pipeline/run` fails, still show metadata and a button to try `/transcribe` only.
- **Sampling knobs**: Expose `sample_max_minutes` and `WHISPER_MODEL` choices in a settings drawer.
- **Streaming audio**: Use `getAudioWav` and create an object URL for an `<audio>` tag; optionally cache using the browser Cache API.
- **Markdown rendering**: Use `react-markdown` + `remark-gfm` and a copy-to-clipboard button.

## 5) Error Handling

- Network errors -> show a toast and an inline retry button.
- HTTP 4xx -> validate the URL, highlight the field.
- HTTP 5xx -> show “We’re working on it” and a link to status/logs.
- For long videos, guide users to enable sampling (e.g., 10–15 minutes) to reduce time.

## 6) Performance & Cost Tips (Frontend)

- Prefer `WHISPER_MODEL=base` or `tiny` on the backend for low-memory plans, and expose that choice in UI.
- Default `sample_max_minutes` to 10–20; allow power users to increase.
- Reuse server cache: re-summarizing the same video is near-instant.
- Avoid parallelizing heavy operations in the UI; queue requests per video.

## 7) End-to-End Example Flow

1. User pastes a YouTube URL
2. Frontend calls `/youtube/metadata` and shows title/channel/duration
3. Frontend triggers `/audio/download` and `/pipeline/run` (shows spinner)
4. When `/pipeline/run` returns, render Markdown summary and optional transcript
5. Provide “Download audio” and “Open in player” actions

## 8) Optional Enhancements

- Add API key (X-API-KEY) in frontend and backend for basic auth
- Add rate limiting and CAPTCHA for public forms
- Add job progress endpoints (SSE or WebSocket) for real-time progress updates
- Multi-language toggle if you enable Whisper language auto-detect

---

If you want, I can scaffold a small Next.js example that uses this SDK and patterns (pages for summarize, transcribe, and an audio player).
