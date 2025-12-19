"""
SRT subtitle format utilities.
"""

from pathlib import Path
from typing import List, Union

from video_summarizer.transcription.transcriber import TranscriptionSegment


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format (HH:MM:SS,mmm).
    
    Args:
        seconds: Time in seconds.
    
    Returns:
        Formatted timestamp string.
    
    Examples:
        >>> format_timestamp(0)
        '00:00:00,000'
        >>> format_timestamp(3661.5)
        '01:01:01,500'
    """
    if seconds < 0:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def format_segment_as_srt(
    index: int,
    segment: TranscriptionSegment,
) -> str:
    """
    Format a single segment as an SRT entry.
    
    Args:
        index: 1-based index for the subtitle entry.
        segment: The transcription segment to format.
    
    Returns:
        Formatted SRT entry string.
    """
    start_ts = format_timestamp(segment.start)
    end_ts = format_timestamp(segment.end)
    
    return f"{index}\n{start_ts} --> {end_ts}\n{segment.text}\n"


def format_as_srt(segments: List[TranscriptionSegment]) -> str:
    """
    Format a list of transcription segments as an SRT subtitle file.
    
    Args:
        segments: List of transcription segments.
    
    Returns:
        Complete SRT file content as a string.
    """
    srt_entries = []
    
    for i, segment in enumerate(segments, start=1):
        entry = format_segment_as_srt(i, segment)
        srt_entries.append(entry)
    
    return "\n".join(srt_entries)


def save_srt(
    segments: List[TranscriptionSegment],
    output_path: Union[str, Path],
    encoding: str = "utf-8",
) -> None:
    """
    Save transcription segments to an SRT file.
    
    Args:
        segments: List of transcription segments.
        output_path: Path to save the SRT file.
        encoding: File encoding (default: UTF-8, good for Arabic).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    srt_content = format_as_srt(segments)
    
    with open(output_path, "w", encoding=encoding) as f:
        f.write(srt_content)


def parse_srt(content: str) -> List[TranscriptionSegment]:
    """
    Parse SRT content back into TranscriptionSegment objects.
    
    Args:
        content: SRT file content as a string.
    
    Returns:
        List of TranscriptionSegment objects.
    """
    import re
    
    segments = []
    
    # Split by double newlines (entries are separated by blank lines)
    entries = re.split(r'\n\n+', content.strip())
    
    for entry in entries:
        lines = entry.strip().split('\n')
        
        if len(lines) < 3:
            continue
        
        # Parse timestamp line
        timestamp_line = lines[1]
        match = re.match(
            r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
            timestamp_line
        )
        
        if not match:
            continue
        
        # Convert start timestamp to seconds
        start = (
            int(match.group(1)) * 3600 +
            int(match.group(2)) * 60 +
            int(match.group(3)) +
            int(match.group(4)) / 1000
        )
        
        # Convert end timestamp to seconds
        end = (
            int(match.group(5)) * 3600 +
            int(match.group(6)) * 60 +
            int(match.group(7)) +
            int(match.group(8)) / 1000
        )
        
        # Get text (may span multiple lines)
        text = '\n'.join(lines[2:])
        
        segments.append(TranscriptionSegment(
            start=start,
            end=end,
            text=text,
        ))
    
    return segments


def load_srt(path: Union[str, Path], encoding: str = "utf-8") -> List[TranscriptionSegment]:
    """
    Load an SRT file and parse it into TranscriptionSegment objects.
    
    Args:
        path: Path to the SRT file.
        encoding: File encoding (default: UTF-8).
    
    Returns:
        List of TranscriptionSegment objects.
    """
    path = Path(path)
    
    with open(path, "r", encoding=encoding) as f:
        content = f.read()
    
    return parse_srt(content)
