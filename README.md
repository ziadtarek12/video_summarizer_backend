# Video Summarizer

A full-stack application for transcribing, summarizing, and extracting clips from videos using AI. Features a modern React frontend and FastAPI backend with user authentication and video library management.

## ✨ Features

### Core Processing
- 🎬 **Video Transcription** - Transcribe videos using Whisper Large v3
- 🌐 **YouTube Support** - Process YouTube URLs directly (auto-download)
- 🇸🇦 **Multi-Language** - Arabic and English language support
- 🤖 **Multi-Provider LLM** - Google AI (Gemini) or OpenRouter
- 📝 **AI Summarization** - Generate summaries in original or translated language
- ✂️ **Clip Extraction** - Automatically identify and extract key moments
- 🔗 **Clip Merging** - Combine extracted clips into a single video
- 💬 **Video Chat** - Interactive Q&A about video content with streaming

### Web Application
- 🎨 **Modern UI** - Glassmorphism design with dark mode
- 🔐 **User Authentication** - Register/login with JWT tokens
- 📚 **Video Library** - Save processed videos for reuse
- 💾 **Data Persistence** - Cached summaries, clips, and transcripts
- ⬇️ **Clip Downloads** - Download extracted video clips
- ⚙️ **Configurable** - Select AI provider, model, and language settings

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+ (for frontend development)
- FFmpeg installed on your system

### Installation

```bash
# Clone the repository
git clone https://github.com/ziadtarek12/video_summarizer_backend.git
cd video_summarizer_backend

# Install Python dependencies
pip install -r requirements.txt
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start the backend server (auto-installs frontend deps if needed)
python run_backend.py

# Open http://localhost:8000 in your browser
```

For development with hot reload:
```bash
# Terminal 1: Backend
uvicorn src.video_summarizer.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with:

```env
# LLM Provider: "google" or "openrouter"
LLM_PROVIDER=google

# Google AI Studio (https://aistudio.google.com/)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-1.5-flash

# OpenRouter (https://openrouter.ai/)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct:free

# Available Models (comma-separated, shown in UI dropdown)
# Google models: gemini-1.5-flash, gemini-1.5-pro, gemini-2.0-flash
# OpenRouter models: meta-llama/llama-3.1-70b-instruct:free, openai/gpt-4o-mini
AVAILABLE_LLM_MODELS=gemini-1.5-flash,gemini-1.5-pro,meta-llama/llama-3.1-70b-instruct:free

# Whisper settings
WHISPER_MODEL=large-v3
WHISPER_LANGUAGE=ar  # ar or en
WHISPER_DEVICE=auto

# Auth
SECRET_KEY=your-secret-key-here

# Optional: YouTube cookies for age-restricted videos
# Place cookies.txt in project root
```

## 📖 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/register` | POST | Create new user account |
| `/api/login` | POST | Login and get JWT token |

### Video Processing
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/transcribe/file` | POST | Upload and transcribe video file |
| `/api/transcribe/url` | POST | Transcribe from YouTube URL |
| `/api/transcribe/existing` | POST | Re-transcribe library video with new settings |
| `/api/summarize` | POST | Generate AI summary from transcript |
| `/api/extract-clips` | POST | Extract and optionally merge video clips |
| `/api/chat/start` | POST | Start chat session about video |
| `/api/chat/message` | POST | Send message to chat session |

### Library Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/library` | GET | Get user's video library |
| `/api/videos/{id}` | GET | Get video details with cached results |
| `/api/clips/download` | GET | Download extracted clip file |

### Configuration
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get available languages and models |

## 🖥️ CLI Usage

The application also includes a CLI for command-line usage:

```bash
# Transcribe
video-summarizer transcribe video.mp4 -o transcript.srt
video-summarizer transcribe "https://youtube.com/watch?v=ID" -o transcript.srt

# Summarize
video-summarizer summarize transcript.srt --output-language english

# Extract clips
video-summarizer extract-clips transcript.srt --video video.mp4 --num-clips 5 --merge

# Chat
video-summarizer chat transcript.srt

# Full pipeline
video-summarizer process video.mp4 --output-dir ./output --merge
```

## 🏗️ Project Structure

```
video_summarizer_backend/
├── src/video_summarizer/
│   ├── api/                    # FastAPI Backend
│   │   ├── main.py            # API routes and endpoints
│   │   └── auth.py            # JWT authentication
│   ├── db/                     # Database Layer
│   │   ├── database.py        # SQLAlchemy setup
│   │   └── models.py          # User, Video, Job models
│   ├── transcription/          # Video Processing
│   │   ├── audio_extractor.py # FFmpeg audio extraction
│   │   ├── youtube_downloader.py
│   │   ├── transcriber.py     # Whisper transcription
│   │   └── srt_formatter.py
│   ├── llm/                    # AI/LLM Integration
│   │   ├── client.py          # Multi-provider LLM client
│   │   ├── summarizer.py      # Summarization logic
│   │   ├── clip_extractor.py  # Clip extraction & merging
│   │   ├── chat.py            # Chat session management
│   │   ├── prompts.py         # Prompt templates
│   │   └── models.py          # Clip, Summary data models
│   ├── cli/                    # CLI Interface
│   │   └── main.py
│   └── config.py              # Configuration management
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── pages/             # Dashboard, Login, Register
│   │   ├── components/        # UI Components
│   │   ├── hooks/             # React hooks (useVideoProcessing)
│   │   └── services/          # API client
│   └── dist/                  # Production build
├── output/                     # Generated files
├── videos.db                   # SQLite database
└── run_backend.py             # Application entry point
```

## 🧪 Development

### Running Tests
```bash
pytest tests/ -v
```

### Building Frontend
```bash
cd frontend
npm install
npm run build
```

## 📄 License

MIT
