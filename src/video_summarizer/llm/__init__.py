"""
LLM module for video summarization and clip extraction.

Provides functionality for:
- Connecting to OpenRouter API
- Connecting to Google AI Studio (Gemini)
- Generating video summaries
- Extracting key clips with timestamps
"""

from video_summarizer.llm.client import (
    OpenRouterClient,
    GoogleAIClient,
    get_llm_client,
    LLMClientError,
)
from video_summarizer.llm.models import Clip, Summary
from video_summarizer.llm.summarizer import VideoSummarizer

__all__ = [
    "OpenRouterClient",
    "GoogleAIClient",
    "get_llm_client",
    "LLMClientError",
    "Clip",
    "Summary",
    "VideoSummarizer",
]
