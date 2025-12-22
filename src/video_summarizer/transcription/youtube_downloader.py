"""
YouTube video downloader using yt-dlp with optional Google Apps Script bridge validation.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

import requests


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
    
    This helps bypass age-gating and provides validated video metadata.
    
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
    Download a video from YouTube.
    
    Optionally validates the video using a Google Apps Script bridge first,
    which helps bypass age-gating and provides validated metadata.
    
    Args:
        url: YouTube video URL.
        output_dir: Directory to save the video. If None, uses a temp directory.
        filename: Name for the output file (without extension). If None, uses video title.
        format_preference: yt-dlp format string for quality selection.
            Default: "bestvideo+bestaudio/best" merges best video + audio.
        use_bridge: If True and GAS_BRIDGE_URL is configured, validates video first.
    
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
    
    
    config = get_config()
    
    # Optional: Validate via Google Apps Script bridge
    video_title = None
    if use_bridge and config.downloader.gas_bridge_url:
        video_id = extract_video_id(url)
        if video_id:
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
    
    # Configure yt-dlp options
    if filename:
        output_template = str(output_dir / f"{filename}.%(ext)s")
    else:
        # Use video title from bridge or let yt-dlp extract it
        output_template = str(output_dir / "%(title)s.%(ext)s")
    
    # Get base options with authentication (browser/cookies file)
    ydl_opts = _get_base_ydl_opts()
    
    # Add download-specific options matching the user's preferred format
    ydl_opts.update({
        "format": format_preference,  # Default: "bestvideo+bestaudio/best"
        "outtmpl": output_template,
        "noplaylist": True,  # Don't download playlists
        "merge_output_format": "mp4",  # Merge to mp4
        "quiet": False,  # Show download progress
    })

    print(f"⬇️  Starting download via yt-dlp...")
    
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
            
            # Handle merged files (yt-dlp changes extension to mp4)
            if not Path(downloaded_file).exists():
                # Try with .mp4 extension (merged format)
                base = Path(downloaded_file).stem
                merged_path = output_dir / f"{base}.mp4"
                if merged_path.exists():
                    return str(merged_path)
            
            final_title = video_title or info.get("title", "Unknown")
            print(f"\n✅ SUCCESS: Video '{final_title}' downloaded!")
            
            return downloaded_file
            
    except yt_dlp.utils.DownloadError as e:
        raise YouTubeDownloadError(f"Failed to download video: {e}") from e
    except Exception as e:
        raise YouTubeDownloadError(f"Unexpected error during download: {e}") from e

from video_summarizer.config import get_config


def _get_base_ydl_opts() -> dict:
    """
    Get base yt-dlp options with authentication configuration.
    
    Returns:
        Dictionary of yt-dlp options.
    """
    config = get_config()
    
    # Search for cookies.txt in likely locations
    possible_paths = [
        Path(os.getcwd()) / "cookies.txt",
        Path(__file__).parents[3] / "cookies.txt", # src/video_summarizer -> root
        Path("/teamspace/studios/this_studio/video_summarizer_backend/cookies.txt") # Absolute fallback
    ]
    
    cookies_path = None
    for path in possible_paths:
        if path.exists():
            cookies_path = path
            break
            
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios"]
            }
        }
    }
    
    # Add proxy if configured
    if config.downloader.proxy:
        print(f"🌐 Using Proxy: {config.downloader.proxy}")
        ydl_opts["proxy"] = config.downloader.proxy
    
    # Add authentication configuration
    if cookies_path:
        print(f"🍪 Found cookies at: {cookies_path}")
        ydl_opts["cookiefile"] = str(cookies_path)
    else:
        print("⚠️  No cookies.txt found!")
        print("   If you are running on a server/online machine, you MUST:")
        print("   1. Export cookies from your local browser (use 'Get cookies.txt LOCALLY' extension)")
        print(f"   2. Upload the file to: {os.getcwd()}/cookies.txt")
        print("   Attempting to download without auth (may fail for age-gated/premium content)...")
        
    return ydl_opts


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
    
    ydl_opts = _get_base_ydl_opts()
    
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
