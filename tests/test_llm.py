"""
Tests for the LLM module.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from video_summarizer.llm.models import Clip, Summary
from video_summarizer.llm.prompts import get_summarize_prompt, get_extract_clips_prompt


class TestClipModel:
    """Tests for the Clip data model."""
    
    def test_clip_creation(self):
        """Test creating a Clip object."""
        clip = Clip(
            start=10.0,
            end=30.0,
            title="Test Clip",
            description="A test",
            importance=8,
        )
        
        assert clip.start == 10.0
        assert clip.end == 30.0
        assert clip.title == "Test Clip"
        assert clip.importance == 8
    
    def test_clip_duration(self):
        """Test duration property."""
        clip = Clip(start=10.0, end=30.0, title="Test")
        assert clip.duration == 20.0
    
    def test_clip_to_dict(self):
        """Test converting clip to dictionary."""
        clip = Clip(
            start=10.0,
            end=30.0,
            title="Test Clip",
            description="Description",
            importance=7,
        )
        
        data = clip.to_dict()
        
        assert data["start"] == 10.0
        assert data["end"] == 30.0
        assert data["title"] == "Test Clip"
        assert data["description"] == "Description"
        assert data["importance"] == 7
        assert data["duration"] == 20.0
    
    def test_clip_from_dict(self):
        """Test creating clip from dictionary."""
        data = {
            "start": 15.5,
            "end": 45.5,
            "title": "From Dict",
            "description": "Created from dict",
            "importance": 9,
        }
        
        clip = Clip.from_dict(data)
        
        assert clip.start == 15.5
        assert clip.end == 45.5
        assert clip.title == "From Dict"
        assert clip.importance == 9
    
    def test_clip_defaults(self):
        """Test default values for optional fields."""
        clip = Clip(start=0, end=10, title="Minimal")
        
        assert clip.description == ""
        assert clip.importance == 5


class TestSummaryModel:
    """Tests for the Summary data model."""
    
    def test_summary_creation(self):
        """Test creating a Summary object."""
        summary = Summary(
            text="This is a summary",
            key_points=["Point 1", "Point 2"],
            language="ar",
        )
        
        assert summary.text == "This is a summary"
        assert len(summary.key_points) == 2
        assert summary.language == "ar"
    
    def test_summary_to_dict(self):
        """Test converting summary to dictionary."""
        summary = Summary(
            text="Summary text",
            key_points=["Key 1", "Key 2"],
        )
        
        data = summary.to_dict()
        
        assert data["text"] == "Summary text"
        assert data["key_points"] == ["Key 1", "Key 2"]
    
    def test_summary_from_dict(self):
        """Test creating summary from dictionary."""
        data = {
            "text": "Loaded summary",
            "key_points": ["Point A", "Point B", "Point C"],
            "language": "en",
        }
        
        summary = Summary.from_dict(data)
        
        assert summary.text == "Loaded summary"
        assert len(summary.key_points) == 3
        assert summary.language == "en"


class TestPrompts:
    """Tests for prompt generation."""
    
    def test_summarize_prompt_contains_transcript(self):
        """Test that transcript is included in prompt."""
        transcript = "This is the video transcript content."
        
        system, user = get_summarize_prompt(transcript)
        
        assert transcript in user
        assert len(system) > 0
    
    def test_summarize_prompt_requests_json(self):
        """Test that prompt requests JSON output."""
        system, user = get_summarize_prompt("Test transcript")
        
        assert "JSON" in user or "json" in user
    
    def test_extract_clips_prompt_contains_transcript(self):
        """Test that transcript is included in clip extraction prompt."""
        transcript = "1\n00:00:00,000 --> 00:00:05,000\nTest content"
        
        system, user = get_extract_clips_prompt(transcript, num_clips=3)
        
        assert transcript in user
        assert "3" in user  # Number of clips
    
    def test_extract_clips_prompt_requests_timestamps(self):
        """Test that prompt requests timestamp information."""
        system, user = get_extract_clips_prompt("Test", num_clips=5)
        
        assert "timestamp" in user.lower() or "start" in user.lower()


class TestClipMetadata:
    """Tests for clip metadata serialization."""
    
    def test_save_and_load_clips(self, sample_clips, temp_dir):
        """Test saving and loading clip metadata."""
        from video_summarizer.llm.clip_extractor import (
            save_clips_metadata,
            load_clips_metadata,
        )
        
        output_path = temp_dir / "clips.json"
        
        save_clips_metadata(sample_clips, output_path)
        
        assert output_path.exists()
        
        loaded = load_clips_metadata(output_path)
        
        assert len(loaded) == len(sample_clips)
        
        for orig, loaded_clip in zip(sample_clips, loaded):
            assert orig.start == loaded_clip.start
            assert orig.end == loaded_clip.end
            assert orig.title == loaded_clip.title
    
    def test_clips_json_format(self, sample_clips, temp_dir):
        """Test that clips are saved in correct JSON format."""
        from video_summarizer.llm.clip_extractor import save_clips_metadata
        
        output_path = temp_dir / "clips.json"
        
        save_clips_metadata(sample_clips, output_path)
        
        with open(output_path, "r") as f:
            data = json.load(f)
        
        assert "clips" in data
        assert "total_clips" in data
        assert data["total_clips"] == len(sample_clips)
