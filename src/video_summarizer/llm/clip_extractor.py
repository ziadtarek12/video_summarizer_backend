"""
Video clip extraction using FFmpeg.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Union

from video_summarizer.llm.models import Clip


class ClipExtractionError(Exception):
    """Raised when clip extraction fails."""
    pass


def extract_clip(
    video_path: str,
    output_path: str,
    start: float,
    end: float,
    reencode: bool = False,
) -> str:
    """
    Extract a clip from a video file.
    
    Args:
        video_path: Path to the source video.
        output_path: Path for the output clip.
        start: Start time in seconds.
        end: End time in seconds.
        reencode: If True, re-encode the clip (slower but more accurate cuts).
    
    Returns:
        Path to the extracted clip.
    
    Raises:
        ClipExtractionError: If FFmpeg fails.
    """
    video_path = Path(video_path)
    output_path = Path(output_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    duration = end - start
    
    if reencode:
        # Re-encode for accurate cuts
        cmd = [
            "ffmpeg",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-y",
            str(output_path),
        ]
    else:
        # Fast copy mode (may have slight timing inaccuracies at keyframes)
        cmd = [
            "ffmpeg",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(duration),
            "-c", "copy",
            "-y",
            str(output_path),
        ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise ClipExtractionError(f"FFmpeg failed: {e.stderr}") from e
    except FileNotFoundError:
        raise ClipExtractionError(
            "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
        )
    
    return str(output_path)


def extract_clips(
    video_path: str,
    clips: List[Clip],
    output_dir: str,
    reencode: bool = False,
    filename_template: str = "clip_{index:02d}_{title}",
) -> List[str]:
    """
    Extract multiple clips from a video.
    
    Args:
        video_path: Path to the source video.
        clips: List of Clip objects with timing information.
        output_dir: Directory to save extracted clips.
        reencode: If True, re-encode clips (slower but more accurate).
        filename_template: Template for clip filenames.
    
    Returns:
        List of paths to extracted clips.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_paths = []
    
    for i, clip in enumerate(clips):
        # Sanitize title for filename
        safe_title = "".join(
            c if c.isalnum() or c in "._- " else "_"
            for c in clip.title
        ).strip()[:50]
        
        filename = filename_template.format(
            index=i + 1,
            title=safe_title,
        )
        
        # Get source extension
        source_ext = Path(video_path).suffix
        output_path = output_dir / f"{filename}{source_ext}"
        
        try:
            extracted_path = extract_clip(
                video_path=video_path,
                output_path=str(output_path),
                start=clip.start,
                end=clip.end,
                reencode=reencode,
            )
            extracted_paths.append(extracted_path)
        except ClipExtractionError as e:
            # Continue with other clips if one fails
            print(f"Warning: Failed to extract clip {i + 1}: {e}")
    
    return extracted_paths


def save_clips_metadata(
    clips: List[Clip],
    output_path: Union[str, Path],
) -> None:
    """
    Save clip metadata to a JSON file.
    
    Args:
        clips: List of Clip objects.
        output_path: Path to save the JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "clips": [clip.to_dict() for clip in clips],
        "total_clips": len(clips),
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_clips_metadata(path: Union[str, Path]) -> List[Clip]:
    """
    Load clip metadata from a JSON file.
    
    Args:
        path: Path to the JSON file.
    
    Returns:
        List of Clip objects.
    """
    path = Path(path)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return [Clip.from_dict(clip_data) for clip_data in data.get("clips", [])]
