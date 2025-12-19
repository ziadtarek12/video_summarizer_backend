"""
Configuration management for Video Summarizer.

Loads settings from environment variables and provides defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class WhisperConfig:
    """Configuration for Whisper transcription."""
    
    model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "large-v3"))
    language: str = field(default_factory=lambda: os.getenv("WHISPER_LANGUAGE", "ar"))
    device: str = field(default_factory=lambda: os.getenv("WHISPER_DEVICE", "auto"))
    compute_type: str = field(default_factory=lambda: os.getenv("WHISPER_COMPUTE_TYPE", "float16"))


@dataclass
class LLMConfig:
    """Configuration for OpenRouter LLM."""
    
    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-70b-instruct:free"))
    base_url: str = "https://openrouter.ai/api/v1"
    max_tokens: int = field(default_factory=lambda: int(os.getenv("OPENROUTER_MAX_TOKENS", "4096")))
    temperature: float = field(default_factory=lambda: float(os.getenv("OPENROUTER_TEMPERATURE", "0.7")))


@dataclass
class OutputConfig:
    """Configuration for output settings."""
    
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "./output"))


@dataclass
class Config:
    """Main configuration class combining all settings."""
    
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    def validate(self) -> list[str]:
        """Validate the configuration and return list of errors."""
        errors = []
        
        if not self.llm.api_key:
            errors.append("OPENROUTER_API_KEY is required but not set")
        
        return errors


def get_config() -> Config:
    """Get the current configuration."""
    return Config()
