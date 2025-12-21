"""
Video summarization and clip extraction using LLM.
"""

from typing import List, Optional, Union

from video_summarizer.llm.client import get_llm_client, LLMClient, GoogleAIClient, OpenRouterClient
from video_summarizer.llm.models import Clip, Summary
from video_summarizer.llm.prompts import get_summarize_prompt, get_extract_clips_prompt
from video_summarizer.config import get_config


class VideoSummarizer:
    """
    Handles video summarization and clip extraction using an LLM.
    
    Supports both Google AI Studio (Gemini) and OpenRouter for LLM access.
    """
    
    def __init__(
        self,
        client: Optional[LLMClient] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the video summarizer.
        
        Args:
            client: Optional pre-configured LLM client.
            provider: LLM provider ("google" or "openrouter"). Defaults to config.
            model: Optional model override.
            api_key: Optional API key override.
        """
        if client:
            self.client = client
        else:
            self.client = get_llm_client(provider=provider, model=model, api_key=api_key)
    
    def summarize(self, transcript: str, output_language: str = "original") -> Summary:
        """
        Generate a summary of the video from its transcript.
        
        Args:
            transcript: The video transcript (plain text or SRT).
            output_language: "original" for video language, "english" to translate.
        
        Returns:
            Summary object with text and key points.
        """
        system_prompt, user_prompt = get_summarize_prompt(transcript, output_language)
        
        response = self.client.complete_json(
            prompt=user_prompt,
            system=system_prompt,
        )
        
        return Summary(
            text=response.get("summary", ""),
            key_points=response.get("key_points", []),
        )
    
    def extract_clips(
        self,
        transcript: str,
        num_clips: int = 5,
        min_duration: float = 10.0,
        max_duration: float = 120.0,
    ) -> List[Clip]:
        """
        Extract important clips from the video based on its transcript.
        
        Args:
            transcript: The video transcript in SRT format (with timestamps).
            num_clips: Number of clips to extract.
            min_duration: Minimum clip duration in seconds.
            max_duration: Maximum clip duration in seconds.
        
        Returns:
            List of Clip objects with timestamps and metadata.
        """
        system_prompt, user_prompt = get_extract_clips_prompt(transcript, num_clips)
        
        response = self.client.complete_json(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=4000,  # Clips need more tokens for multiple descriptions
        )
        
        clips = []
        raw_clips = response.get("clips", [])
        
        for clip_data in raw_clips:
            try:
                clip = Clip.from_dict(clip_data)
                
                # Filter by duration constraints
                if min_duration <= clip.duration <= max_duration:
                    clips.append(clip)
                elif clip.duration < min_duration:
                    # Extend short clips if possible
                    clip.end = clip.start + min_duration
                    clips.append(clip)
                elif clip.duration > max_duration:
                    # Truncate long clips
                    clip.end = clip.start + max_duration
                    clips.append(clip)
                    
            except (KeyError, ValueError) as e:
                # Skip invalid clip data
                continue
        
        # Sort by importance (highest first)
        clips.sort(key=lambda c: c.importance, reverse=True)
        
        return clips[:num_clips]
    
    def process(
        self,
        transcript: str,
        num_clips: int = 5,
        output_language: str = "original",
    ) -> tuple[Summary, List[Clip]]:
        """
        Process a transcript to generate both summary and clips.
        
        Args:
            transcript: The video transcript in SRT format.
            num_clips: Number of clips to extract.
            output_language: "original" for video language, "english" to translate.
        
        Returns:
            Tuple of (Summary, List[Clip]).
        """
        summary = self.summarize(transcript, output_language=output_language)
        clips = self.extract_clips(transcript, num_clips=num_clips)
        
        return summary, clips
