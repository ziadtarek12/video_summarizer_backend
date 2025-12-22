"""
YouTube video downloader using yt-dlp with Google Apps Script bridge validation.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

import requests
import yt_dlp

from video_summarizer.config import get_config


class YouTubeDownloadError(Exception):
    """Raised when YouTube download fails."""
    pass


class GASBridgeError(Exception):
    """Raised when Google Apps Script bridge validation fails."""
    pass


# Regex patterns for YouTube URLs
YOUTUBE_PATTERNS = [
    r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
    r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]+',
    r'^https?://youtu\.be/[\w-]+',
    r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+',
]

# Pattern to extract video ID from URL
VIDEO_ID_PATTERNS = [
    r'(?:v=|\/)([\w-]{11})',  # Standard watch?v= or /videoId
    r'youtu\.be\/([\w-]{11})',  # Short URL
    r'embed\/([\w-]{11})',  # Embed URL
    r'shorts\/([\w-]{11})',  # Shorts URL
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


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.
    
    Args:
        url: YouTube video URL.
    
    Returns:
        The 11-character video ID, or None if not found.
    """
    for pattern in VIDEO_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def validate_with_bridge(video_id: str, bridge_url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Validate a YouTube video using the Google Apps Script bridge.
    
    Args:
        video_id: The YouTube video ID.
        bridge_url: The deployed Google Apps Script Web App URL.
        timeout: Request timeout in seconds.
    
    Returns:
        Dictionary with video metadata (title, status, etc.)
    
    Raises:
        GASBridgeError: If validation fails.
    """
    try:
        print(f"🔗 Validating video via GAS Bridge: {video_id}")
        response = requests.get(f"{bridge_url}?id={video_id}", timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "success":
            raise GASBridgeError(f"Bridge validation failed: {data.get('message', 'Unknown error')}")
        
        print(f"✅ Bridge Success! Video: {data.get('title', 'Unknown')}")
        return data
        
    except requests.exceptions.RequestException as e:
        raise GASBridgeError(f"Failed to connect to GAS bridge: {e}") from e
    except ValueError as e:
        raise GASBridgeError(f"Invalid response from GAS bridge: {e}") from e


def download_video(
    url: str,
    output_dir: Optional[str] = None,
    filename: Optional[str] = None,
    format_preference: str = "bestvideo+bestaudio/best",
    use_bridge: bool = True,
) -> str:
    """
    Download a video from YouTube using the EXACT working logic.
    
    Args:
        url: YouTube video URL.
        output_dir: Directory to save the video. If None, uses a temp directory.
        filename: Name for the output file (without extension). If None, uses video title.
        format_preference: yt-dlp format string for quality selection.
        use_bridge: If True and GAS_BRIDGE_URL is configured, validates video first.
    
    Returns:
        Path to the downloaded video file.
    
    Raises:
        YouTubeDownloadError: If the download fails.
        ValueError: If the URL is not a valid YouTube URL.
    """
    if not is_youtube_url(url):
        raise ValueError(f"Not a valid YouTube URL: {url}")
    
    config = get_config()
    
    # Extract video ID for bridge validation
    video_id = extract_video_id(url)
    video_title = None
    
    # Optional: Validate via Google Apps Script bridge
    if use_bridge and config.downloader.gas_bridge_url and video_id:
        try:
            bridge_data = validate_with_bridge(video_id, config.downloader.gas_bridge_url)
            video_title = bridge_data.get("title")
            print(f"📹 Video validated: {video_title}")
        except GASBridgeError as e:
            print(f"⚠️  Bridge validation failed: {e}")
            print("   Continuing with direct download...")
    
    # Set up output directory
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure yt-dlp options - EXACT same as working script
    if filename:
        output_template = str(output_dir / f"{filename}.%(ext)s")
    else:
        output_template = str(output_dir / "%(title)s.%(ext)s")
    
    # EXACT OPTIONS FROM WORKING SCRIPT - DO NOT MODIFY
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', 
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': False,
    }

    print(f"⬇️  Starting download via yt-dlp...")
    
    try:
        # USE ydl.download() - EXACTLY like the working script
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        for ext in ["mp4", "mkv", "webm", "m4a"]:
            if filename:
                potential_path = output_dir / f"{filename}.{ext}"
            else:
                # Look for any video file in the output directory
                for f in output_dir.iterdir():
                    if f.suffix.lower() in [".mp4", ".mkv", ".webm"]:
                        print(f"\n✅ SUCCESS: Video downloaded to {f}")
                        return str(f)
        
        # Fallback: return first video file found
        for f in output_dir.iterdir():
            if f.is_file() and f.suffix.lower() in [".mp4", ".mkv", ".webm", ".m4a"]:
                print(f"\n✅ SUCCESS: Video downloaded to {f}")
                return str(f)
        
        raise YouTubeDownloadError("Download completed but file not found")
            
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
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
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
