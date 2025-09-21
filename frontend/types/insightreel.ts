export type UserType =
  | "student"
  | "professional"
  | "developer"
  | "entrepreneur"
  | "researcher"
  | "general";

export type SummaryLength = "quick" | "standard" | "detailed";

export interface UserProfile {
  type: UserType;
  name?: string;
  icon?: string;
  length: SummaryLength;
  focus?: string | null;
}

export interface TranscriptSegment {
  start_time: number;
  end_time: number;
  text: string;
  timestamp: string; // "M:SS"
  language?: string;
}

export interface KeyConcepts {
  keywords: Array<[string, number]>;
  domain_concepts: Array<[string, number]>;
  technical_terms: string[];
  action_words: string[];
  total_words: number;
  unique_words: number;
  complexity_score: number;
}

export interface SummarizeRequest {
  url: string;
  profile?: UserProfile;
  save_markdown_to_file?: boolean;
  sample_max_minutes?: number;
  max_video_seconds?: number;
}

export interface SummarizeResponse {
  success: boolean;
  summary: string;
  video_title: string;
  channel: string;
  duration: string;
  segments: number;
  processing_time: string;
  ai_enhanced: boolean;
  user_profile: UserProfile;
  cached_data_used: boolean;
  key_concepts: KeyConcepts;
  filename?: string;
}

export interface TranscribeResponse {
  video_id: string;
  segments: number;
  duration_seconds: number;
  transcripts: TranscriptSegment[];
}

export interface AudioDownloadResponse {
  video_id: string;
  audio_url: string;
  duration_seconds: number;
  cache_path: string;
}
