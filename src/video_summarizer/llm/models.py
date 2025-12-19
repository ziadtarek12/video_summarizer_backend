"""
Data models for LLM outputs.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Clip:
    """
    Represents an extracted video clip with metadata.
    
    Attributes:
        start: Start time in seconds.
        end: End time in seconds.
        title: Short title for the clip.
        description: Optional longer description.
        importance: Importance score (1-10).
    """
    
    start: float
    end: float
    title: str
    description: str = ""
    importance: int = 5
    
    @property
    def duration(self) -> float:
        """Get the duration of the clip in seconds."""
        return self.end - self.start
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "start": self.start,
            "end": self.end,
            "title": self.title,
            "description": self.description,
            "importance": self.importance,
            "duration": self.duration,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Clip":
        """Create a Clip from a dictionary."""
        return cls(
            start=float(data["start"]),
            end=float(data["end"]),
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            importance=int(data.get("importance", 5)),
        )


@dataclass
class Summary:
    """
    Represents a video summary with key points.
    
    Attributes:
        text: The full summary text.
        key_points: List of key points extracted from the video.
        language: Language of the summary.
    """
    
    text: str
    key_points: List[str] = field(default_factory=list)
    language: str = "ar"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "key_points": self.key_points,
            "language": self.language,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Summary":
        """Create a Summary from a dictionary."""
        return cls(
            text=data.get("text", ""),
            key_points=data.get("key_points", []),
            language=data.get("language", "ar"),
        )
