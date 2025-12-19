"""
YouTube video downloader using yt-dlp.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Optional


class YouTubeDownloadError(Exception):
    """Raised when YouTube download fails."""
    pass


# Regex patterns for YouTube URLs
YOUTUBE_PATTERNS = [
    r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
    r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
    r'^https?://youtu\.be/[\w-]+',
    r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+',
]


def is_youtube_url(url: str) -> bool:
    """
    Check if a string is a valid YouTube URL.
    
    Args:
        url: The string to check.
    
    Returns:
        True if the string is a YouTube URL, False otherwise.
    """
    for pattern in YOUTUBE_PATTERNS:
        if re.match(pattern, url):
            return True
    return False


def download_video(
    url: str,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
    format_preference: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
) -> str:
    """
    Download a video from YouTube.
    
    Args:
        url: YouTube video URL.
        output_dir: Directory to save the video. If None, uses a temp directory.
        filename: Name for the output file (without extension). If None, uses video title.
        format_preference: yt-dlp format string for quality selection.
    
    Returns:
        Path to the downloaded video file.
    
    Raises:
        YouTubeDownloadError: If the download fails.
        ValueError: If the URL is not a valid YouTube URL.
    """
    if not is_youtube_url(url):
        raise ValueError(f"Not a valid YouTube URL: {url}")
    
    # Import yt-dlp here to avoid import errors if not installed
    try:
        import yt_dlp
    except ImportError:
        raise YouTubeDownloadError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        )
    
    # Set up output directory
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure yt-dlp options
    if filename:
        output_template = str(output_dir / f"{filename}.%(ext)s")
    else:
        output_template = str(output_dir / "%(title)s.%(ext)s")
    
    # Look for cookies.txt in project root
    cookies_path = Path("cookies.txt").resolve()
    if not cookies_path.exists():
        # Try one level up (if running from src or similar)
        cookies_path = Path("../cookies.txt").resolve()
    
    ydl_opts = {
        "format": format_preference,
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "ignoreerrors": True,
    }

    if cookies_path.exists():
        print(f"🍪 Found cookies at: {cookies_path}")
        ydl_opts["cookiefile"] = str(cookies_path)
    else:
        print(f"⚠️ No cookies.txt found. Looked at: {cookies_path}")
        print(f"   Current Working Directory: {os.getcwd()}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get the actual filename
            if filename:
                # Try common extensions
                for ext in ["mp4", "mkv", "webm"]:
                    potential_path = output_dir / f"{filename}.{ext}"
                    if potential_path.exists():
                        return str(potential_path)
            
            # Use the prepared filename from yt-dlp
            downloaded_file = ydl.prepare_filename(info)
            
            # Handle merged files (yt-dlp changes extension)
            if not Path(downloaded_file).exists():
                # Try with .mp4 extension (merged format)
                base = Path(downloaded_file).stem
                merged_path = output_dir / f"{base}.mp4"
                if merged_path.exists():
                    return str(merged_path)
            
            return downloaded_file
            
    except yt_dlp.utils.DownloadError as e:
        raise YouTubeDownloadError(f"Failed to download video: {e}") from e
    except Exception as e:
        raise YouTubeDownloadError(f"Unexpected error during download: {e}") from e


def get_video_info(url: str) -> dict:
    """
    Get information about a YouTube video without downloading.
    
    Args:
        url: YouTube video URL.
    
    Returns:
        Dictionary with video metadata (title, duration, description, etc.)
    
    Raises:
        YouTubeDownloadError: If fetching info fails.
    """
    try:
        import yt_dlp
    except ImportError:
        raise YouTubeDownloadError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        )
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "description": info.get("description", ""),
                "uploader": info.get("uploader", "Unknown"),
                "upload_date": info.get("upload_date", ""),
                "view_count": info.get("view_count", 0),
            }
    except Exception as e:
        raise YouTubeDownloadError(f"Failed to get video info: {e}") from e
