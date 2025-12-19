# Video Summarizer Backend

A modular Python CLI tool for transcribing Arabic videos using Whisper Large v3 and generating AI-powered summaries and clip extractions via OpenRouter.

## Features

- 🎬 **Video Transcription**: Transcribe videos to SRT format using Whisper Large v3
- 🌐 **YouTube Support**: Directly process YouTube URLs (auto-downloads)
- 🇸🇦 **Arabic Support**: Optimized for Arabic language transcription
- 📝 **AI Summarization**: Generate summaries using any OpenRouter LLM
- ✂️ **Clip Extraction**: Automatically identify and extract key moments
- 🎥 **Auto-Export**: Export clips as separate video files

## Installation

### Prerequisites

- Python 3.9+
- FFmpeg installed on your system

### Install from source

```bash
# Clone the repository
git clone <your-repo-url>
cd video_summarizer_backend

# Install in development mode
pip install -e ".[dev]"
```

### On Google Colab

```python
# Install FFmpeg
!apt-get install ffmpeg

# Install the package
!pip install -e ".[dev]"
```

## Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Required: Your OpenRouter API key
OPENROUTER_API_KEY=your_key_here

# Optional: Choose your preferred model (default uses a free model)
OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct:free

# Whisper settings (defaults are optimized for Arabic)
WHISPER_MODEL=large-v3
WHISPER_LANGUAGE=ar
```

## Usage

### Transcribe a Video

```bash
# From a local file
video-summarizer transcribe video.mp4 --output transcript.srt

# From a YouTube URL
video-summarizer transcribe "https://youtube.com/watch?v=VIDEO_ID" --output transcript.srt
```

### Summarize a Transcript

```bash
video-summarizer summarize transcript.srt --output summary.txt
```

### Extract Clips

```bash
video-summarizer extract-clips transcript.srt --video video.mp4 --output-dir ./clips
```

### Full Pipeline

Process a video through the entire pipeline (transcribe → summarize → extract clips):

```bash
video-summarizer process video.mp4 --output-dir ./output

# Or from YouTube
video-summarizer process "https://youtube.com/watch?v=VIDEO_ID" --output-dir ./output
```

This will generate:
- `output/transcript.srt` - Full transcription
- `output/summary.txt` - AI-generated summary
- `output/clips.json` - Clip metadata
- `output/clips/` - Extracted video clips

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
src/video_summarizer/
├── __init__.py
├── config.py              # Configuration management
├── transcription/
│   ├── __init__.py
│   ├── audio_extractor.py # FFmpeg audio extraction
│   ├── youtube_downloader.py # YouTube video downloading
│   ├── transcriber.py     # Whisper transcription
│   └── srt_formatter.py   # SRT format output
├── llm/
│   ├── __init__.py
│   ├── client.py          # OpenRouter API client
│   ├── prompts.py         # Prompt templates
│   ├── summarizer.py      # Summarization logic
│   └── models.py          # Data models
└── cli/
    ├── __init__.py
    └── main.py            # CLI commands
```

## License

MIT
