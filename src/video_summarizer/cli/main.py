"""
CLI entry point for Video Summarizer.

Provides commands for:
- Transcribing videos (local or YouTube)
- Summarizing transcripts
- Extracting clips
- Full pipeline processing
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import click

from video_summarizer.config import get_config


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Video Summarizer - Transcribe, summarize, and extract clips from videos."""
    pass


@cli.command()
@click.argument("source")
@click.option(
    "--output", "-o",
    default=None,
    help="Output SRT file path. Defaults to <video_name>.srt",
)
@click.option(
    "--language", "-l",
    default=None,
    help="Language code (e.g., 'ar' for Arabic). Defaults to config value.",
)
@click.option(
    "--model", "-m",
    default=None,
    help="Whisper model to use (e.g., 'large-v3'). Defaults to config value.",
)
@click.option(
    "--device", "-d",
    default=None,
    type=click.Choice(["auto", "cpu", "cuda"]),
    help="Device to use for transcription. Defaults to 'auto' (tries CUDA, falls back to CPU).",
)
def transcribe(source: str, output: Optional[str], language: Optional[str], model: Optional[str], device: Optional[str]):
    """
    Transcribe a video to SRT format.
    
    SOURCE can be a local video file path or a YouTube URL.
    """
    from video_summarizer.transcription import (
        is_youtube_url,
        download_video,
        extract_audio,
        WhisperTranscriber,
        save_srt,
    )
    
    click.echo(f"🎬 Processing: {source}")
    
    # Handle YouTube URLs
    if is_youtube_url(source):
        click.echo("📥 Downloading from YouTube...")
        try:
            video_path = download_video(source)
            click.echo(f"✅ Downloaded to: {video_path}")
        except Exception as e:
            click.echo(f"❌ Download failed: {e}", err=True)
            sys.exit(1)
    else:
        video_path = source
        if not Path(video_path).exists():
            click.echo(f"❌ File not found: {video_path}", err=True)
            sys.exit(1)
    
    # Determine output path
    if output is None:
        output = str(Path(video_path).with_suffix(".srt"))
    
    # Extract audio
    click.echo("🎵 Extracting audio...")
    try:
        audio_path = extract_audio(video_path)
    except Exception as e:
        click.echo(f"❌ Audio extraction failed: {e}", err=True)
        sys.exit(1)
    
    # Transcribe
    click.echo("📝 Transcribing (this may take a while)...")
    try:
        transcriber = WhisperTranscriber(model=model, language=language, device=device)
        segments = transcriber.transcribe(audio_path)
        click.echo(f"✅ Transcribed {len(segments)} segments")
    except Exception as e:
        click.echo(f"❌ Transcription failed: {e}", err=True)
        sys.exit(1)
    
    # Save SRT
    save_srt(segments, output)
    click.echo(f"💾 Saved to: {output}")
    
    # Cleanup temp audio
    try:
        os.unlink(audio_path)
    except:
        pass


@cli.command()
@click.argument("transcript_path")
@click.option(
    "--output", "-o",
    default=None,
    help="Output file path. Defaults to summary.txt in same directory.",
)
@click.option(
    "--provider", "-p",
    default=None,
    type=click.Choice(["google", "openrouter"]),
    help="LLM provider to use. Defaults to 'google'.",
)
@click.option(
    "--model", "-m",
    default=None,
    help="LLM model to use. Defaults to config value.",
)
@click.option(
    "--output-language", "-L",
    default="original",
    type=click.Choice(["original", "english"]),
    help="Summary output language: 'original' (video language) or 'english'.",
)
def summarize(transcript_path: str, output: Optional[str], provider: Optional[str], model: Optional[str], output_language: str):
    """
    Summarize a video transcript.
    
    TRANSCRIPT_PATH should be a path to an SRT file.
    """
    from video_summarizer.transcription.srt_formatter import load_srt
    from video_summarizer.llm import VideoSummarizer
    
    # Load transcript
    if not Path(transcript_path).exists():
        click.echo(f"❌ File not found: {transcript_path}", err=True)
        sys.exit(1)
    
    click.echo(f"📖 Loading transcript: {transcript_path}")
    
    try:
        segments = load_srt(transcript_path)
        # Combine all text for summarization
        transcript_text = "\n".join(seg.text for seg in segments)
    except Exception as e:
        click.echo(f"❌ Failed to load transcript: {e}", err=True)
        sys.exit(1)
    
    # Determine output path
    if output is None:
        output = str(Path(transcript_path).with_name("summary.txt"))
    
    # Summarize
    click.echo(f"🤖 Generating summary (language: {output_language})...")
    try:
        summarizer = VideoSummarizer(provider=provider, model=model)
        summary = summarizer.summarize(transcript_text, output_language=output_language)
    except Exception as e:
        click.echo(f"❌ Summarization failed: {e}", err=True)
        sys.exit(1)
    
    # Save summary
    with open(output, "w", encoding="utf-8") as f:
        f.write(summary.text)
        f.write("\n\n---\n\nKey Points:\n")
        for i, point in enumerate(summary.key_points, 1):
            f.write(f"{i}. {point}\n")
    
    click.echo(f"💾 Saved to: {output}")
    click.echo(f"\n📋 Summary:\n{summary.text[:500]}...")


@cli.command("extract-clips")
@click.argument("transcript_path")
@click.option(
    "--video", "-v",
    required=True,
    help="Path to the video file for clip extraction.",
)
@click.option(
    "--output-dir", "-o",
    default=None,
    help="Output directory for clips. Defaults to ./clips",
)
@click.option(
    "--num-clips", "-n",
    default=5,
    type=int,
    help="Number of clips to extract.",
)
@click.option(
    "--provider", "-p",
    default=None,
    type=click.Choice(["google", "openrouter"]),
    help="LLM provider to use. Defaults to 'google'.",
)
@click.option(
    "--model", "-m",
    default=None,
    help="LLM model to use. Defaults to config value.",
)
@click.option(
    "--reencode/--no-reencode",
    default=False,
    help="Re-encode clips for accurate cuts (slower).",
)
@click.option(
    "--merge/--no-merge",
    default=False,
    help="Merge all clips into a single video file.",
)
def extract_clips_cmd(
    transcript_path: str,
    video: str,
    output_dir: Optional[str],
    num_clips: int,
    provider: Optional[str],
    model: Optional[str],
    reencode: bool,
    merge: bool,
):
    """
    Extract important clips from a video based on its transcript.
    
    TRANSCRIPT_PATH should be a path to an SRT file.
    """
    from video_summarizer.transcription.srt_formatter import load_srt, format_as_srt
    from video_summarizer.llm import VideoSummarizer
    from video_summarizer.llm.clip_extractor import extract_clips, save_clips_metadata, merge_clips
    
    # Validate inputs
    if not Path(transcript_path).exists():
        click.echo(f"❌ Transcript not found: {transcript_path}", err=True)
        sys.exit(1)
    
    if not Path(video).exists():
        click.echo(f"❌ Video not found: {video}", err=True)
        sys.exit(1)
    
    # Determine output directory
    if output_dir is None:
        output_dir = str(Path(video).parent / "clips")
    
    click.echo(f"📖 Loading transcript: {transcript_path}")
    
    try:
        segments = load_srt(transcript_path)
        # Use SRT format for LLM (includes timestamps)
        srt_content = format_as_srt(segments)
    except Exception as e:
        click.echo(f"❌ Failed to load transcript: {e}", err=True)
        sys.exit(1)
    
    # Extract clips using LLM
    click.echo(f"🤖 Identifying {num_clips} best clips...")
    try:
        summarizer = VideoSummarizer(provider=provider, model=model)
        clips = summarizer.extract_clips(srt_content, num_clips=num_clips)
    except Exception as e:
        click.echo(f"❌ Clip extraction failed: {e}", err=True)
        sys.exit(1)
    
    click.echo(f"✅ Found {len(clips)} clips")
    
    for clip in clips:
        click.echo(f"  📎 {clip.title} ({clip.start:.1f}s - {clip.end:.1f}s)")
    
    # Save metadata
    metadata_path = Path(output_dir) / "clips.json"
    save_clips_metadata(clips, metadata_path)
    click.echo(f"💾 Saved metadata to: {metadata_path}")
    
    # Extract video clips
    click.echo("✂️ Extracting video clips...")
    extracted = extract_clips(
        video_path=video,
        clips=clips,
        output_dir=output_dir,
        reencode=reencode,
    )
    
    click.echo(f"✅ Extracted {len(extracted)} clips to: {output_dir}")
    
    # Merge clips if requested
    if merge and extracted:
        click.echo("🔗 Merging clips into single video...")
        try:
            merged_path = str(Path(output_dir) / "merged_clips.mp4")
            merge_clips(extracted, merged_path, reencode=True)
            click.echo(f"✅ Merged video saved to: {merged_path}")
        except Exception as e:
            click.echo(f"⚠️ Merge failed: {e}", err=True)


@cli.command()
@click.argument("source")
@click.option(
    "--output-dir", "-o",
    default=None,
    help="Output directory. Defaults to ./output",
)
@click.option(
    "--num-clips", "-n",
    default=5,
    type=int,
    help="Number of clips to extract.",
)
@click.option(
    "--language", "-l",
    default=None,
    help="Language code (e.g., 'ar' for Arabic). Defaults to config value.",
)
@click.option(
    "--whisper-model",
    default=None,
    help="Whisper model to use. Defaults to config value.",
)
@click.option(
    "--provider", "-p",
    default=None,
    type=click.Choice(["google", "openrouter"]),
    help="LLM provider to use. Defaults to 'google'.",
)
@click.option(
    "--llm-model",
    default=None,
    help="LLM model to use. Defaults to config value.",
)
@click.option(
    "--output-language", "-L",
    default="original",
    type=click.Choice(["original", "english"]),
    help="Summary output language: 'original' or 'english'.",
)
@click.option(
    "--reencode/--no-reencode",
    default=False,
    help="Re-encode clips for accurate cuts (slower).",
)
@click.option(
    "--merge/--no-merge",
    default=False,
    help="Merge all clips into a single video file.",
)
def process(
    source: str,
    output_dir: Optional[str],
    num_clips: int,
    language: Optional[str],
    whisper_model: Optional[str],
    provider: Optional[str],
    llm_model: Optional[str],
    output_language: str,
    reencode: bool,
    merge: bool,
):
    """
    Process a video through the full pipeline.
    
    SOURCE can be a local video file path or a YouTube URL.
    
    This command will:
    1. Download video (if YouTube URL)
    2. Transcribe to SRT
    3. Generate summary
    4. Extract important clips
    """
    from video_summarizer.transcription import (
        is_youtube_url,
        download_video,
        extract_audio,
        WhisperTranscriber,
        save_srt,
        format_as_srt,
    )
    from video_summarizer.transcription.srt_formatter import load_srt
    from video_summarizer.llm import VideoSummarizer
    from video_summarizer.llm.clip_extractor import extract_clips, save_clips_metadata, merge_clips
    
    # Determine output directory
    if output_dir is None:
        output_dir = "./output"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    click.echo(f"🎬 Starting full pipeline for: {source}")
    click.echo(f"📁 Output directory: {output_dir}")
    
    # Step 1: Handle YouTube URLs
    if is_youtube_url(source):
        click.echo("\n📥 Step 1/4: Downloading from YouTube...")
        try:
            video_path = download_video(source, output_dir=str(output_dir))
            click.echo(f"✅ Downloaded to: {video_path}")
        except Exception as e:
            click.echo(f"❌ Download failed: {e}", err=True)
            sys.exit(1)
    else:
        video_path = source
        if not Path(video_path).exists():
            click.echo(f"❌ File not found: {video_path}", err=True)
            sys.exit(1)
        click.echo("\n✅ Step 1/4: Using local video file")
    
    # Step 2: Transcribe
    click.echo("\n📝 Step 2/4: Transcribing...")
    transcript_path = output_dir / "transcript.srt"
    
    try:
        audio_path = extract_audio(video_path)
        transcriber = WhisperTranscriber(model=whisper_model, language=language)
        segments = transcriber.transcribe(audio_path)
        save_srt(segments, transcript_path)
        click.echo(f"✅ Transcribed {len(segments)} segments")
        
        # Cleanup temp audio
        try:
            os.unlink(audio_path)
        except:
            pass
    except Exception as e:
        click.echo(f"❌ Transcription failed: {e}", err=True)
        sys.exit(1)
    
    # Prepare transcript content
    srt_content = format_as_srt(segments)
    plain_text = "\n".join(seg.text for seg in segments)
    
    # Step 3: Summarize
    click.echo(f"\n🤖 Step 3/4: Generating summary (language: {output_language})...")
    summary_path = output_dir / "summary.txt"
    
    try:
        summarizer = VideoSummarizer(provider=provider, model=llm_model)
        summary = summarizer.summarize(plain_text, output_language=output_language)
        
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary.text)
            f.write("\n\n---\n\nKey Points:\n")
            for i, point in enumerate(summary.key_points, 1):
                f.write(f"{i}. {point}\n")
        
        click.echo(f"✅ Summary saved to: {summary_path}")
    except Exception as e:
        click.echo(f"❌ Summarization failed: {e}", err=True)
        sys.exit(1)
    
    # Step 4: Extract clips
    click.echo(f"\n✂️ Step 4/4: Extracting {num_clips} clips...")
    clips_dir = output_dir / "clips"
    
    try:
        clips = summarizer.extract_clips(srt_content, num_clips=num_clips)
        
        # Save metadata
        metadata_path = output_dir / "clips.json"
        save_clips_metadata(clips, metadata_path)
        
        # Extract video clips
        extracted = extract_clips(
            video_path=video_path,
            clips=clips,
            output_dir=str(clips_dir),
            reencode=reencode,
        )
        
        click.echo(f"✅ Extracted {len(extracted)} clips")
        
        # Merge clips if requested
        if merge and extracted:
            click.echo("🔗 Merging clips into single video...")
            try:
                merged_path = str(output_dir / "merged_clips.mp4")
                merge_clips(extracted, merged_path, reencode=True)
                click.echo(f"✅ Merged video saved to: {merged_path}")
            except Exception as e:
                click.echo(f"⚠️ Merge failed: {e}", err=True)
                
    except Exception as e:
        click.echo(f"❌ Clip extraction failed: {e}", err=True)
        sys.exit(1)
    
    # Final summary
    click.echo("\n" + "=" * 50)
    click.echo("🎉 Pipeline complete!")
    click.echo(f"📄 Transcript: {transcript_path}")
    click.echo(f"📝 Summary: {summary_path}")
    click.echo(f"🎬 Clips: {clips_dir}")
    if merge and extracted:
        click.echo(f"🔗 Merged: {output_dir / 'merged_clips.mp4'}")
    click.echo("=" * 50)


@cli.command()
@click.argument("transcript_path")
@click.option(
    "--provider", "-p",
    default=None,
    type=click.Choice(["google", "openrouter"]),
    help="LLM provider to use. Defaults to 'google'.",
)
@click.option(
    "--model", "-m",
    default=None,
    help="LLM model to use. Defaults to config value.",
)
def chat(transcript_path: str, provider: Optional[str], model: Optional[str]):
    """
    Chat about a video using its transcript.
    
    TRANSCRIPT_PATH should be a path to an SRT file.
    
    Enter messages to ask questions about the video content.
    Type 'quit', 'exit', or 'q' to end the session.
    Type 'clear' to reset conversation history.
    """
    from video_summarizer.transcription.srt_formatter import load_srt
    from video_summarizer.llm import create_chat_session
    
    # Load transcript
    if not Path(transcript_path).exists():
        click.echo(f"❌ File not found: {transcript_path}", err=True)
        sys.exit(1)
    
    click.echo(f"📖 Loading transcript: {transcript_path}")
    
    try:
        segments = load_srt(transcript_path)
        transcript_text = "\n".join(seg.text for seg in segments)
    except Exception as e:
        click.echo(f"❌ Failed to load transcript: {e}", err=True)
        sys.exit(1)
    
    # Create chat session
    click.echo("🤖 Starting chat session...")
    click.echo("   Type 'quit' to exit, 'clear' to reset history.\n")
    
    session = create_chat_session(
        transcript=transcript_text,
        provider=provider,
        model=model,
    )
    
    # Interactive chat loop
    while True:
        try:
            user_input = click.prompt("You", prompt_suffix=": ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\n👋 Goodbye!")
            break
        
        # Handle special commands
        if user_input.lower() in ("quit", "exit", "q"):
            click.echo("👋 Goodbye!")
            break
        
        if user_input.lower() == "clear":
            session.clear_history()
            click.echo("🗑️ Conversation history cleared.\n")
            continue
        
        if not user_input.strip():
            continue
        
        # Get streaming response
        try:
            click.echo("\n🤖 Assistant: ", nl=False)
            for token in session.chat_stream(user_input):
                click.echo(token, nl=False)
            click.echo("\n")  # Add newlines after response
        except Exception as e:
            click.echo(f"\n❌ Error: {e}\n", err=True)


if __name__ == "__main__":
    cli()

