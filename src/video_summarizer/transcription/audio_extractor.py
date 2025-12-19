"""
Audio extraction from video files using FFmpeg.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class AudioExtractionError(Exception):
    """Raised when audio extraction fails."""
    pass


def extract_audio(
    video_path: str,
    output_path: Optional[str] = None,
    sample_rate: int = 16000,
    mono: bool = True,
) -> str:
    """
    Extract audio from a video file using FFmpeg.
    
    Args:
        video_path: Path to the input video file.
        output_path: Path for the output audio file. If None, creates a temp file.
        sample_rate: Audio sample rate in Hz (default: 16000 for Whisper).
        mono: If True, convert to mono audio (default: True for Whisper).
    
    Returns:
        Path to the extracted audio file.
    
    Raises:
        AudioExtractionError: If FFmpeg fails or input file doesn't exist.
        FileNotFoundError: If the input video file doesn't exist.
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Generate output path if not provided
    if output_path is None:
        # Create temp file with .wav extension
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
    
    output_path = Path(output_path)
    
    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "pcm_s16le",  # PCM 16-bit
        "-ar", str(sample_rate),  # Sample rate
        "-y",  # Overwrite output
    ]
    
    if mono:
        cmd.extend(["-ac", "1"])  # Mono audio
    
    cmd.append(str(output_path))
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise AudioExtractionError(
            f"FFmpeg failed to extract audio: {e.stderr}"
        ) from e
    except FileNotFoundError:
        raise AudioExtractionError(
            "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
        )
    
    return str(output_path)


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of a video in seconds using FFprobe.
    
    Args:
        video_path: Path to the video file.
    
    Returns:
        Duration in seconds.
    
    Raises:
        AudioExtractionError: If FFprobe fails.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        raise AudioExtractionError(f"Failed to get video duration: {e}") from e
