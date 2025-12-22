"""
Configuration management for Video Summarizer.

Loads settings from environment variables and provides defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Literal, List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Allowed languages for transcription (Arabic and English only)
ALLOWED_LANGUAGES = {
    "ar": "Arabic",
    "en": "English"
}

# Default LLM models if not specified in .env
DEFAULT_LLM_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


@dataclass
class WhisperConfig:
    """Configuration for Whisper transcription using faster-whisper large-v3."""
    
    # Force large-v3 model for best accuracy
    model: str = "large-v3"
    language: str = field(default_factory=lambda: os.getenv("WHISPER_LANGUAGE", "ar"))
    device: str = field(default_factory=lambda: os.getenv("WHISPER_DEVICE", "auto"))
    compute_type: str = field(default_factory=lambda: os.getenv("WHISPER_COMPUTE_TYPE", "float16"))
    
    def validate_language(self, lang: str) -> str:
        """Validate and return language code. Defaults to 'ar' if invalid."""
        if lang and lang.lower() in ALLOWED_LANGUAGES:
            return lang.lower()
        return "ar"  # Default to Arabic


@dataclass
class LLMConfig:
    """Configuration for LLM (supports OpenRouter and Google AI Studio)."""
    
    # Provider: "openrouter" or "google"
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "google"))
    
    # OpenRouter settings
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    openrouter_model: str = field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-70b-instruct:free"))
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Google AI Studio settings
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    google_model: str = field(default_factory=lambda: os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"))
    
    # Common settings
    max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "8192")))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7")))
    
    @property
    def api_key(self) -> str:
        """Get the API key for the current provider."""
        if self.provider == "google":
            return self.google_api_key
        return self.openrouter_api_key
    
    @property
    def model(self) -> str:
        """Get the model for the current provider."""
        if self.provider == "google":
            return self.google_model
        return self.openrouter_model
    
    @property
    def available_models(self) -> List[str]:
        """Get list of available LLM models from environment."""
        models_str = os.getenv("AVAILABLE_LLM_MODELS", "")
        if models_str:
            return [m.strip() for m in models_str.split(",") if m.strip()]
        return DEFAULT_LLM_MODELS


@dataclass
class OutputConfig:
    """Configuration for output settings."""
    
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "./output"))
    default_num_clips: int = field(default_factory=lambda: int(os.getenv("DEFAULT_NUM_CLIPS", "5")))


@dataclass
class DownloaderConfig:
    """Configuration for video downloader (yt-dlp)."""
    
    proxy: Optional[str] = field(default_factory=lambda: os.getenv("YOUTUBE_PROXY", os.getenv("HTTP_PROXY")))
    # Google Apps Script bridge URL for video validation (optional)
    gas_bridge_url: Optional[str] = field(default_factory=lambda: os.getenv("GAS_BRIDGE_URL"))


@dataclass
class Config:
    """Main configuration class combining all settings."""
    
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    downloader: DownloaderConfig = field(default_factory=DownloaderConfig)
    
    def validate(self) -> list[str]:
        """Validate the configuration and return list of errors."""
        errors = []
        
        if self.llm.provider == "google" and not self.llm.google_api_key:
            errors.append("GOOGLE_API_KEY is required but not set")
        elif self.llm.provider == "openrouter" and not self.llm.openrouter_api_key:
            errors.append("OPENROUTER_API_KEY is required but not set")
        
        return errors


def get_config() -> Config:
    """Get the current configuration."""
    return Config()
