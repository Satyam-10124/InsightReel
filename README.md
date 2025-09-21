# 🎥 InsightReel — From Video to Insight, Instantly

**InsightReel** is an AI-powered YouTube summarizer that transforms long videos into concise, actionable insights personalized for your learning or professional goals.

No more scrubbing through long videos. Whether you're a student, developer, entrepreneur, or curious learner — InsightReel saves you time and delivers what matters.

---

## 🚀 Features

- 🤖 **AI-Enhanced Summaries** — Powered by Gemini or OpenAI models
- 🧑‍💼 **Personalized Focus** — For students, developers, professionals, entrepreneurs, and more
- 🧠 **Key Concepts Extraction** — Keywords, technical terms, action verbs
- ✨ **Top 3 Takeaways** — Immediate insights upfront
- 📋 **Structured Output** — Emojis, markdown, action steps, and more
- 📊 **Analytics Section** — Word count, duration, segments, and generation time
- 💬 **Quote of the Day** (optional) — Inspirational or insightful moments

- **Smart Processing**:
  - Automatic video transcription using Whisper
  - AI-enhanced summaries with Google Gemini
  - Intelligent content analysis
  - Key concept extraction
  - Technical term detection

- **Advanced Caching**:
  - Efficient video processing
  - Cached transcripts and metadata
  - Reduced processing time

## 🚀 Getting Started

### Prerequisites

```bash
# Required Python packages
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file with:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Running the App

```bash
streamlit run app.py
```
```
python main.py
```

## 📋 Usage

1. Select your user profile (Student, Developer, etc.)
2. Paste a YouTube URL
3. Customize summary length and focus (optional)
4. Click "Generate Summary"
5. View and download your personalized summary

## 🛠️ Technical Details

### Core Components

- **Frontend**: Streamlit with custom CSS
- **Video Processing**: yt-dlp
- **Transcription**: OpenAI Whisper
- **AI Summary**: Google Gemini
- **Caching System**: Local file-based cache

### Key Features

- Automatic video transcription
- Smart content analysis
- Role-based personalization
- Markdown summary export
- Progress tracking
- Cache management

## 📊 Summary Output

- Video metadata
- Duration and segments
- Key concepts and topics
- Technical terms
- Action items
- Personalized insights

## ⚙️ Configuration Options

- Summary length:
  - ⚡ Quick (2-3 min read)
  - 📋 Standard (5-7 min read)
  - 📖 Detailed (10+ min read)
- Custom focus areas
- Role-specific adaptations

## Live Link 
- https://insightreel-jjwb7htrcsurhnaduus75k.streamlit.app/

## 🔒 Limitations

- Maximum video length: 2 hours
- Requires stable internet connection
- API key needed for AI features

## 🤝 Contributing

Feel free to:
- Open issues
- Submit PRs
- Suggest improvements
- Report bugs

## Additional System Requirements:

FFmpeg needs to be installed on your system:

  -Windows: choco install ffmpeg
  -Mac: brew install ffmpeg
  -Linux: sudo apt install ffmpeg

## 🙏 Acknowledgments

- OpenAI Whisper for transcription
- Google Gemini for AI summaries
- Streamlit for the web interface
- yt-dlp for video processing

## 🔮 Future Improvements

- [ ] Multiple language support
- [ ] More user roles
- [ ] Advanced analytics
- [ ] API endpoint
- [ ] Batch processing
- [ ] Custom themes

---

## 🧱 Developer Architecture

The codebase is now modular and organized under the `insightreel/` package. Both the CLI (`main.py`) and the Streamlit app (`app.py`) depend on these reusable components.

### Core Modules (`insightreel/`)

- `logger.py`
  - Centralized logging configuration via `configure_logging()` and `get_logger()`.

- `preferences.py`
  - CLI helper `prompt_user_profile()` to collect user profile (role, length, focus).
  - Constants `USER_TYPES`, `LENGTH_TYPES`.

- `cache.py`
  - `CacheManager` to handle cache paths and JSON read/write for metadata and transcripts.
  - Also provides `clear_all()` and `stats()`.

- `youtube.py`
  - `get_video_id_from_url()` and `fetch_metadata()` (using `yt-dlp`).

- `audio.py`
  - `download_audio()` to download and normalize audio to WAV mono 16kHz.
  - `get_audio_duration()` via ffprobe with safe fallback.
  - `split_audio()` to chunk audio and `smart_sample_audio()` to limit processing for long videos.

- `text_cleaner.py`
  - `clean_transcript_basic()` and `clean_transcript_advanced()` for transcript cleanup.

- `transcriber.py`
  - `Transcriber` wraps Whisper model loading and parallel chunk transcription.

- `analysis.py`
  - `extract_key_concepts()` computes keywords, domain concepts, technical terms, action words, and basic text stats.

- `summarizer.py`
  - High-quality markdown summary creation.
  - Uses `AiClient` (Gemini) when available, otherwise falls back to a structured basic summary.

- `ai.py`
  - `AiClient` integrates with Google Generative AI (Gemini), auto-disabling when not configured.

- `pipeline.py`
  - `SummarizerPipeline` orchestrates the entire process end-to-end and returns a result dict.

### App Integration

- `app.py` (Streamlit)
  - Uses `SummarizerPipeline` via a cached loader.
  - Calls `pipeline.process(url, user_profile, progress=update_status)` to generate summaries.
  - UI remains the same, now backed by modular services.

- `main.py` (CLI)
  - Uses `SummarizerPipeline` and `prompt_user_profile()` for interactive usage.
  - Calls `pipeline.process(url, user_profile, save_markdown_to_file=True)`.

### Notes

- Caching directory: `youtube_cache/` (unchanged)
- AI summaries are enabled when `GEMINI_API_KEY` is set; otherwise basic summaries are generated.

## 🧪 Smoke Testing

After installing requirements and FFmpeg:

```
streamlit run app.py
```

Or run the CLI:

```
python main.py
```

Follow the prompts and paste a YouTube URL to verify end-to-end processing.