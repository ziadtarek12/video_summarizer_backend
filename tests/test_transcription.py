"""
Tests for the transcription module.
"""

import pytest
from pathlib import Path

from video_summarizer.transcription.transcriber import TranscriptionSegment
from video_summarizer.transcription.srt_formatter import (
    format_timestamp,
    format_as_srt,
    parse_srt,
    save_srt,
    load_srt,
)
from video_summarizer.transcription.youtube_downloader import is_youtube_url


class TestFormatTimestamp:
    """Tests for timestamp formatting."""
    
    def test_zero_timestamp(self):
        """Test formatting of zero timestamp."""
        assert format_timestamp(0) == "00:00:00,000"
    
    def test_simple_seconds(self):
        """Test simple seconds formatting."""
        assert format_timestamp(5.5) == "00:00:05,500"
    
    def test_minutes(self):
        """Test minutes formatting."""
        assert format_timestamp(65.123) == "00:01:05,123"
    
    def test_hours(self):
        """Test hours formatting."""
        assert format_timestamp(3661.5) == "01:01:01,500"
    
    def test_large_timestamp(self):
        """Test large timestamp formatting."""
        assert format_timestamp(36000) == "10:00:00,000"
    
    def test_negative_timestamp(self):
        """Negative timestamps should be treated as zero."""
        assert format_timestamp(-5) == "00:00:00,000"
    
    def test_millisecond_precision(self):
        """Test millisecond precision."""
        assert format_timestamp(1.001) == "00:00:01,001"
        assert format_timestamp(1.999) == "00:00:01,999"


class TestFormatAsSrt:
    """Tests for SRT formatting."""
    
    def test_empty_segments(self):
        """Test with empty segment list."""
        assert format_as_srt([]) == ""
    
    def test_single_segment(self, sample_segments):
        """Test with a single segment."""
        result = format_as_srt([sample_segments[0]])
        
        assert "1\n" in result
        assert "00:00:00,000 --> 00:00:05,500" in result
        assert "مرحباً بكم في هذا الفيديو" in result
    
    def test_multiple_segments(self, sample_segments):
        """Test with multiple segments."""
        result = format_as_srt(sample_segments)
        
        # Check all indices
        assert "1\n" in result
        assert "2\n" in result
        assert "3\n" in result
        
        # Check all texts
        for segment in sample_segments:
            assert segment.text in result
    
    def test_arabic_content(self, sample_segments):
        """Test that Arabic content is preserved correctly."""
        result = format_as_srt(sample_segments)
        
        # Verify Arabic text is present and not corrupted
        assert "مرحباً" in result
        assert "الفيديو" in result


class TestParseSrt:
    """Tests for SRT parsing."""
    
    def test_parse_basic_srt(self, sample_srt_content):
        """Test parsing basic SRT content."""
        segments = parse_srt(sample_srt_content)
        
        assert len(segments) == 3
        assert segments[0].start == 0.0
        assert segments[0].end == 5.5
        assert "مرحباً" in segments[0].text
    
    def test_parse_timestamps(self, sample_srt_content):
        """Test timestamp parsing accuracy."""
        segments = parse_srt(sample_srt_content)
        
        assert segments[1].start == 5.5
        assert segments[1].end == 12.3
    
    def test_roundtrip(self, sample_segments):
        """Test that format -> parse produces same segments."""
        srt_content = format_as_srt(sample_segments)
        parsed = parse_srt(srt_content)
        
        assert len(parsed) == len(sample_segments)
        
        for orig, parsed_seg in zip(sample_segments, parsed):
            assert abs(orig.start - parsed_seg.start) < 0.01
            assert abs(orig.end - parsed_seg.end) < 0.01
            assert orig.text == parsed_seg.text


class TestSaveLoadSrt:
    """Tests for SRT file I/O."""
    
    def test_save_and_load(self, sample_segments, temp_dir):
        """Test saving and loading SRT files."""
        output_path = temp_dir / "test.srt"
        
        save_srt(sample_segments, output_path)
        
        assert output_path.exists()
        
        loaded = load_srt(output_path)
        
        assert len(loaded) == len(sample_segments)
    
    def test_utf8_encoding(self, sample_segments, temp_dir):
        """Test that UTF-8 encoding is used for Arabic content."""
        output_path = temp_dir / "test_arabic.srt"
        
        save_srt(sample_segments, output_path)
        
        # Read raw bytes to verify encoding
        with open(output_path, "rb") as f:
            content = f.read()
        
        # UTF-8 encoded Arabic should be present
        assert len(content) > 0
        
        # Decode and verify content
        text = content.decode("utf-8")
        assert "مرحباً" in text


class TestYouTubeUrlDetection:
    """Tests for YouTube URL detection."""
    
    def test_standard_youtube_url(self):
        """Test standard YouTube video URL."""
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert is_youtube_url("http://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert is_youtube_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
    
    def test_short_youtube_url(self):
        """Test short YouTube URL (youtu.be)."""
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert is_youtube_url("http://youtu.be/dQw4w9WgXcQ")
    
    def test_youtube_shorts(self):
        """Test YouTube Shorts URL."""
        assert is_youtube_url("https://www.youtube.com/shorts/abcd1234")
        assert is_youtube_url("https://youtube.com/shorts/xyz789")
    
    def test_youtube_embed(self):
        """Test YouTube embed URL."""
        assert is_youtube_url("https://www.youtube.com/embed/dQw4w9WgXcQ")
    
    def test_non_youtube_urls(self):
        """Test that non-YouTube URLs are rejected."""
        assert not is_youtube_url("https://vimeo.com/123456")
        assert not is_youtube_url("https://example.com/video")
        assert not is_youtube_url("not-a-url")
        assert not is_youtube_url("/local/path/video.mp4")
    
    def test_empty_and_invalid(self):
        """Test empty and invalid inputs."""
        assert not is_youtube_url("")
        assert not is_youtube_url("youtube.com")  # Missing protocol
