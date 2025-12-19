"""
LLM module for video summarization and clip extraction.

Provides functionality for:
- Connecting to OpenRouter API
- Connecting to Google AI Studio (Gemini)
- Generating video summaries
- Extracting key clips with timestamps
- Chatting about video content
"""

from video_summarizer.llm.client import (
    OpenRouterClient,
    GoogleAIClient,
    get_llm_client,
    LLMClientError,
)
from video_summarizer.llm.models import Clip, Summary
from video_summarizer.llm.summarizer import VideoSummarizer
from video_summarizer.llm.chat import ChatSession, create_chat_session
from video_summarizer.llm.clip_extractor import merge_clips

__all__ = [
    "OpenRouterClient",
    "GoogleAIClient",
    "get_llm_client",
    "LLMClientError",
    "Clip",
    "Summary",
    "VideoSummarizer",
    "ChatSession",
    "create_chat_session",
    "merge_clips",
]
