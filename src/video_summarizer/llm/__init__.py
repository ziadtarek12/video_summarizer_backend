"""
LLM module for video summarization and clip extraction.

Provides functionality for:
- Connecting to OpenRouter API
- Generating video summaries
- Extracting key clips with timestamps
"""

from video_summarizer.llm.client import OpenRouterClient
from video_summarizer.llm.models import Clip, Summary
from video_summarizer.llm.summarizer import VideoSummarizer

__all__ = [
    "OpenRouterClient",
    "Clip",
    "Summary",
    "VideoSummarizer",
]
