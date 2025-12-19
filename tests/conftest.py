"""
Pytest configuration and fixtures.
"""

import pytest
from pathlib import Path
import tempfile
import os


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_srt_content():
    """Sample SRT content for testing."""
    return """1
00:00:00,000 --> 00:00:05,500
مرحباً بكم في هذا الفيديو

2
00:00:05,500 --> 00:00:12,300
سنتحدث اليوم عن موضوع مهم جداً

3
00:00:12,300 --> 00:00:20,000
هذا المحتوى يشرح كيفية استخدام الأداة
"""


@pytest.fixture
def sample_segments():
    """Sample transcription segments for testing."""
    from video_summarizer.transcription.transcriber import TranscriptionSegment
    
    return [
        TranscriptionSegment(start=0.0, end=5.5, text="مرحباً بكم في هذا الفيديو"),
        TranscriptionSegment(start=5.5, end=12.3, text="سنتحدث اليوم عن موضوع مهم جداً"),
        TranscriptionSegment(start=12.3, end=20.0, text="هذا المحتوى يشرح كيفية استخدام الأداة"),
    ]


@pytest.fixture
def sample_clips():
    """Sample clips for testing."""
    from video_summarizer.llm.models import Clip
    
    return [
        Clip(start=0.0, end=30.0, title="Introduction", description="Video intro", importance=7),
        Clip(start=45.0, end=90.0, title="Main Topic", description="The key content", importance=9),
        Clip(start=120.0, end=150.0, title="Conclusion", description="Wrapping up", importance=6),
    ]


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "test-model")
    monkeypatch.setenv("WHISPER_MODEL", "small")
    monkeypatch.setenv("WHISPER_LANGUAGE", "ar")
