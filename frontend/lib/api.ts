import axios from "axios";
import type {
  SummarizeRequest,
  SummarizeResponse,
  TranscribeResponse,
  KeyConcepts,
  AudioDownloadResponse,
} from "@/types/insightreel";

const API = process.env.NEXT_PUBLIC_INSIGHTREEL_API || "http://localhost:8000";

export const client = axios.create({
  baseURL: API,
  timeout: 180_000,
});

export async function summarize(payload: SummarizeRequest): Promise<SummarizeResponse> {
  const { data } = await client.post<SummarizeResponse>("/summarize", payload);
  return data;
}

export async function transcribe(
  url: string,
  sample_max_minutes = 20,
  model_size = "small",
): Promise<TranscribeResponse> {
  const { data } = await client.post<TranscribeResponse>("/transcribe", {
    url,
    sample_max_minutes,
    model_size,
  });
  return data;
}

export async function analyzeFromTranscripts(transcripts: any[]): Promise<KeyConcepts> {
  const { data } = await client.post<KeyConcepts>("/analyze/from-transcripts", { transcripts });
  return data;
}

export async function downloadAudio(url: string): Promise<AudioDownloadResponse> {
  const { data } = await client.post<AudioDownloadResponse>("/audio/download", { url });
  return data;
}
