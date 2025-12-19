"""
Transcription module for video processing.

Provides functionality for:
- Extracting audio from video files
- Downloading videos from YouTube
- Transcribing audio using Whisper
- Formatting transcriptions as SRT
"""

from video_summarizer.transcription.audio_extractor import extract_audio
from video_summarizer.transcription.youtube_downloader import (
    download_video,
    is_youtube_url,
)
from video_summarizer.transcription.transcriber import WhisperTranscriber
from video_summarizer.transcription.srt_formatter import (
    format_as_srt,
    save_srt,
)

__all__ = [
    "extract_audio",
    "download_video",
    "is_youtube_url",
    "WhisperTranscriber",
    "format_as_srt",
    "save_srt",
]
