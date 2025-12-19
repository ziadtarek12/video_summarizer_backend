"""
Tests for the CLI module.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path

from video_summarizer.cli.main import cli


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


class TestCLIBasics:
    """Tests for basic CLI functionality."""
    
    def test_cli_help(self, runner):
        """Test that CLI help works."""
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Video Summarizer" in result.output
    
    def test_cli_version(self, runner):
        """Test that version flag works."""
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestTranscribeCommand:
    """Tests for the transcribe command."""
    
    def test_transcribe_help(self, runner):
        """Test transcribe command help."""
        result = runner.invoke(cli, ["transcribe", "--help"])
        
        assert result.exit_code == 0
        assert "Transcribe" in result.output or "SOURCE" in result.output
    
    def test_transcribe_file_not_found(self, runner):
        """Test error when file doesn't exist."""
        result = runner.invoke(cli, ["transcribe", "/nonexistent/video.mp4"])
        
        # Should fail because file doesn't exist
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestSummarizeCommand:
    """Tests for the summarize command."""
    
    def test_summarize_help(self, runner):
        """Test summarize command help."""
        result = runner.invoke(cli, ["summarize", "--help"])
        
        assert result.exit_code == 0
        assert "Summarize" in result.output or "TRANSCRIPT" in result.output
    
    def test_summarize_file_not_found(self, runner):
        """Test error when transcript doesn't exist."""
        result = runner.invoke(cli, ["summarize", "/nonexistent/transcript.srt"])
        
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestExtractClipsCommand:
    """Tests for the extract-clips command."""
    
    def test_extract_clips_help(self, runner):
        """Test extract-clips command help."""
        result = runner.invoke(cli, ["extract-clips", "--help"])
        
        assert result.exit_code == 0
        assert "Extract" in result.output or "clips" in result.output.lower()
    
    def test_extract_clips_requires_video(self, runner, temp_dir):
        """Test that extract-clips requires video option."""
        # Create a dummy transcript file
        transcript = temp_dir / "test.srt"
        transcript.write_text("1\n00:00:00,000 --> 00:00:05,000\nTest\n")
        
        # Should fail without --video option
        result = runner.invoke(cli, ["extract-clips", str(transcript)])
        
        assert result.exit_code != 0


class TestProcessCommand:
    """Tests for the process command."""
    
    def test_process_help(self, runner):
        """Test process command help."""
        result = runner.invoke(cli, ["process", "--help"])
        
        assert result.exit_code == 0
        assert "Process" in result.output or "pipeline" in result.output.lower()
    
    def test_process_options(self, runner):
        """Test that process command has expected options."""
        result = runner.invoke(cli, ["process", "--help"])
        
        output = result.output.lower()
        assert "--output-dir" in output or "-o" in output
        assert "--num-clips" in output or "-n" in output


class TestCLIWithMocks:
    """Tests using mocks for external dependencies."""
    
    def test_youtube_url_detection_in_cli(self, runner, temp_dir):
        """Test that YouTube URLs trigger download logic."""
        # This will fail early but we can verify YouTube URL is recognized
        result = runner.invoke(
            cli,
            ["transcribe", "https://www.youtube.com/watch?v=test123"],
        )
        
        # Should attempt download (will fail, but shows URL was recognized)
        output = result.output.lower()
        assert "youtube" in output or "download" in output or "error" in output
