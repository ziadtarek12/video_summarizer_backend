"""
Prompt templates for video summarization and clip extraction.
"""

SUMMARIZE_SYSTEM_PROMPT = """You are an expert video content analyst. Your task is to analyze video transcripts and provide comprehensive summaries.

You should:
1. Identify the main topic and themes of the video
2. Extract the most important points and insights
3. Summarize the content clearly and concisely
4. Preserve the original language and cultural context

Always respond in the same language as the transcript."""

SUMMARIZE_USER_PROMPT = """Please analyze the following video transcript and provide:

1. A comprehensive summary of the video content (2-3 paragraphs)
2. A list of 5-10 key points from the video

Transcript:
---
{transcript}
---

Provide your response in the following JSON format:
{{
    "summary": "Your comprehensive summary here...",
    "key_points": [
        "Key point 1",
        "Key point 2",
        ...
    ]
}}"""

EXTRACT_CLIPS_SYSTEM_PROMPT = """You are an expert video editor and content curator. Your task is to identify the most important and engaging moments in a video based on its transcript.

You should identify clips that:
1. Contain key insights or important information
2. Are engaging or emotionally impactful
3. Can stand alone as meaningful content
4. Are appropriately sized (typically 15-120 seconds)

For each clip, provide accurate timestamps based on the SRT timing in the transcript."""

EXTRACT_CLIPS_USER_PROMPT = """Analyze the following video transcript (in SRT format) and identify the {num_clips} most important clips to extract.

For each clip, provide:
- Start and end timestamps (in seconds)
- A short, engaging title
- A brief description of why this clip is important
- An importance score from 1-10

Transcript:
---
{transcript}
---

Respond with a JSON array of clips:
{{
    "clips": [
        {{
            "start": 0.0,
            "end": 30.0,
            "title": "Clip Title",
            "description": "Why this clip is important",
            "importance": 8
        }},
        ...
    ]
}}

Important: Use the exact timestamps from the SRT entries. The start and end should be in seconds (float)."""


def get_summarize_prompt(transcript: str) -> tuple[str, str]:
    """
    Get the system and user prompts for summarization.
    
    Args:
        transcript: The video transcript text.
    
    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    return (
        SUMMARIZE_SYSTEM_PROMPT,
        SUMMARIZE_USER_PROMPT.format(transcript=transcript),
    )


def get_extract_clips_prompt(transcript: str, num_clips: int = 5) -> tuple[str, str]:
    """
    Get the system and user prompts for clip extraction.
    
    Args:
        transcript: The video transcript in SRT format.
        num_clips: Number of clips to extract.
    
    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    return (
        EXTRACT_CLIPS_SYSTEM_PROMPT,
        EXTRACT_CLIPS_USER_PROMPT.format(transcript=transcript, num_clips=num_clips),
    )
