"""
Whisper transcription using faster-whisper.
"""

from dataclasses import dataclass
from typing import Iterator, List, Optional

from video_summarizer.config import WhisperConfig, get_config


@dataclass
class TranscriptionSegment:
    """A segment of transcribed text with timing information."""
    
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text
    
    @property
    def duration(self) -> float:
        """Get the duration of this segment in seconds."""
        return self.end - self.start


class TranscriptionError(Exception):
    """Raised when transcription fails."""
    pass


class WhisperTranscriber:
    """
    Transcriber using faster-whisper for Whisper model inference.
    
    This class wraps faster-whisper to provide a simple interface for
    transcribing audio files, with support for language specification
    and various Whisper model sizes.
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        language: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        """
        Initialize the transcriber.
        
        Args:
            model: Whisper model to use (e.g., "large-v3", "medium", "small").
                   Defaults to config value.
            language: Language code (e.g., "ar" for Arabic). 
                      Defaults to config value.
            device: Device to use ("auto", "cuda", "cpu").
                    Defaults to config value.
            compute_type: Precision type ("float16", "int8", "float32").
                          Defaults to config value.
        """
        config = get_config().whisper
        
        self.model_name = model or config.model
        self.language = language or config.language
        self.device = device or config.device
        self.compute_type = compute_type or config.compute_type
        
        self._model = None
    
    def _load_model(self):
        """Lazy load the Whisper model."""
        if self._model is not None:
            return
        
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise TranscriptionError(
                "faster-whisper is not installed. Install it with: pip install faster-whisper"
            )
        
        try:
            # Determine device
            device = self.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self._model = WhisperModel(
                self.model_name,
                device=device,
                compute_type=self.compute_type,
            )
        except Exception as e:
            raise TranscriptionError(f"Failed to load Whisper model: {e}") from e
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> List[TranscriptionSegment]:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file.
            language: Override the default language for this transcription.
            task: "transcribe" or "translate" (translate to English).
            beam_size: Beam size for decoding.
            vad_filter: Whether to use VAD to filter out silence.
        
        Returns:
            List of TranscriptionSegment objects with timing and text.
        
        Raises:
            TranscriptionError: If transcription fails.
            FileNotFoundError: If the audio file doesn't exist.
        """
        from pathlib import Path
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self._load_model()
        
        language = language or self.language
        
        try:
            segments_iter, info = self._model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                beam_size=beam_size,
                vad_filter=vad_filter,
            )
            
            # Convert to our segment format
            segments = []
            for segment in segments_iter:
                segments.append(TranscriptionSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                ))
            
            return segments
            
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e
    
    def transcribe_streaming(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> Iterator[TranscriptionSegment]:
        """
        Transcribe an audio file with streaming output.
        
        Yields segments as they are transcribed, useful for progress reporting.
        
        Args:
            audio_path: Path to the audio file.
            language: Override the default language.
        
        Yields:
            TranscriptionSegment objects as they are generated.
        """
        from pathlib import Path
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self._load_model()
        
        language = language or self.language
        
        segments_iter, info = self._model.transcribe(
            str(audio_path),
            language=language,
            vad_filter=True,
        )
        
        for segment in segments_iter:
            yield TranscriptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
            )
