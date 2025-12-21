
import os
import shutil
import uuid
from typing import Dict, Optional, Any, List
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from video_summarizer.transcription import (
    is_youtube_url,
    download_video,
    extract_audio,
    WhisperTranscriber,
    save_srt,
    format_as_srt
)
from video_summarizer.llm import VideoSummarizer, create_chat_session
from video_summarizer.llm.clip_extractor import extract_clips as extract_video_clips, save_clips_metadata, merge_clips

# DB & Auth Imports
from video_summarizer.db import models, database, get_db
from video_summarizer.api import auth
from video_summarizer.config import get_config, ALLOWED_LANGUAGES

# --- Constants & Helper Classes ---

class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# --- Background Tasks ---

def process_transcription(job_id: str, source: str, model: str, language: str, device: str, user_id: int):
    # Create a new session for background task
    db = database.SessionLocal()
    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            return
        
        # Validate language - only ar and en allowed
        config = get_config()
        validated_language = config.whisper.validate_language(language)
        
        # Helper to update job in DB
        def update_job(status, result=None, error=None):
            job.status = status
            job.updated_at = datetime.utcnow()
            if result:
                # Merge existing result with new result
                current = dict(job.result) if job.result else {}
                current.update(result)
                job.result = current
            if error:
                job.error = error
            db.commit()

        update_job(JobStatus.PROCESSING, {"step": "Starting transcription pipeline..."})
        output_dir = Path(f"output/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. Handle Source (Download or File)
            video_path = source
            title = "Uploaded Video"
            source_url = None
            
            if is_youtube_url(source):
                update_job(JobStatus.PROCESSING, {"step": "Downloading video..."})
                video_info = download_video(source, output_dir=str(output_dir)) 
                video_path = video_info
                title = f"YouTube Video {job_id[:8]}"
                source_url = source
                
            # Create Video Entry in DB
            db_video = models.Video(
                title=title,
                filename=Path(video_path).name,
                file_path=str(video_path),
                source_url=source_url,
                user_id=user_id
            )
            db.add(db_video)
            db.commit()
            db.refresh(db_video)
            
            # Link Job to Video
            job.video_id = db_video.id
            db.commit()

            # 2. Extract Audio
            update_job(JobStatus.PROCESSING, {"step": "Extracting audio..."})
            audio_path = extract_audio(video_path)
                
            # 3. Transcribe (using large-v3 model enforced in config)
            update_job(JobStatus.PROCESSING, {"step": f"Transcribing audio ({validated_language})..."})
            transcriber = WhisperTranscriber(language=validated_language, device=device)
            segments = transcriber.transcribe(audio_path)
            
            # Save SRT
            srt_path = output_dir / "transcript.srt"
            save_srt(segments, srt_path)
            
            # Save Raw Text
            text_path = output_dir / "transcript.txt"
            plain_text = "\n".join(seg.text for seg in segments)
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(plain_text)
            
            # Update Video with transcript data for library reuse
            db_video.transcript_text = plain_text
            db_video.transcript_path = str(text_path)
            db.commit()

            # Cleanup
            if os.path.exists(audio_path):
                os.unlink(audio_path)

            update_job(JobStatus.COMPLETED, {
                "message": "Transcription successful",
                "step": "Completed",
                "video_path": video_path,
                "video_id": db_video.id,
                "transcript_path": str(srt_path),
                "segments_count": len(segments),
                "transcript_text": plain_text
            })

        except Exception as e:
            update_job(JobStatus.FAILED, error=str(e))
            
    finally:
        db.close()


# --- Database Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 VIDEO SUMMARIZER v0.2.0 STARTING")
    print(f"📁 PROJECT ROOT: {project_root}")
    print(f"🌐 SERVING FRONTEND FROM: {static_dir}")
    # Create Tables
    models.Base.metadata.create_all(bind=database.engine)
    # Ensure output dir
    Path("output").mkdir(exist_ok=True)
    yield

app = FastAPI(title="Video Summarizer API", version="0.2.0", lifespan=lifespan)

# --- Configuration ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for simplicity, or restrict to localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
frontend_dist = project_root / "frontend" / "dist"
frontend_src = project_root / "frontend"

if frontend_dist.exists():
    static_dir = frontend_dist
    print(f"✨ Serving production frontend from: {static_dir}")
else:
    static_dir = frontend_src # Only js folder usually exists here
    print(f"⚠️  Production build not found. Serving from: {static_dir}")

# Mount 'output' for accessing generated files
app.mount("/output", StaticFiles(directory="output"), name="output")

# Mount assets if they exist (Vite structure)
if (static_dir / "assets").exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

# Include Auth Router
app.include_router(auth.router)

# --- Config Endpoint ---

@app.get("/api/config")
def get_app_config():
    """Return available languages and LLM models for frontend configuration."""
    config = get_config()
    return {
        "languages": ALLOWED_LANGUAGES,
        "models": config.llm.available_models,
        "default_language": "ar",
        "default_model": config.llm.model
    }

# --- Video Details Endpoint for Library Reuse ---

@app.get("/api/videos/{video_id}")
def get_video_details(
    video_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get video details including transcript for reuse."""
    video = db.query(models.Video).filter(
        models.Video.id == video_id,
        models.Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Try to get transcript from video record or load from file
    transcript_text = video.transcript_text
    if not transcript_text and video.transcript_path:
        try:
            with open(video.transcript_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()
        except:
            pass
    
    return {
        "id": video.id,
        "title": video.title,
        "filename": video.filename,
        "file_path": video.file_path,
        "duration": video.duration,
        "created_at": video.created_at,
        "source_url": video.source_url,
        "transcript_text": transcript_text,
        "transcript_path": video.transcript_path
    }

# --- API Models ---

class TranscribeRequest(BaseModel):
    url: str
    language: Optional[str] = None
    model: Optional[str] = None
    device: Optional[str] = "auto"

class SummarizeRequest(BaseModel):
    transcript_text: Optional[str] = None # Prefer passing text directly now
    transcript_path: Optional[str] = None
    output_language: str = "english"
    provider: str = "google"
    model: Optional[str] = None

class ChatStartRequest(BaseModel):
    transcript_text: Optional[str] = None
    transcript_path: Optional[str] = None
    provider: Optional[str] = "google"
    model: Optional[str] = None

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class ExtractClipsRequest(BaseModel):
    transcript_path: Optional[str] = None
    transcript_text: Optional[str] = None  # Allow passing text directly
    video_path: str
    num_clips: int = 5
    merge: bool = True
    provider: str = "google"
    model: Optional[str] = None

# --- Protected Endpoints ---

@app.get("/api/library")
def get_library(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Video).filter(models.Video.user_id == current_user.id).all()

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    # Making this public-ish or we can verify user ownership if we link job->video->user
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "result": job.result,
        "error": job.error,
        "updated_at": job.updated_at
    }

@app.post("/api/transcribe/url")
def transcribe_url(
    request: TranscribeRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    job_id = str(uuid.uuid4())
    new_job = models.Job(id=job_id, type="transcribe", status=JobStatus.PENDING)
    db.add(new_job)
    db.commit()
    
    background_tasks.add_task(
        process_transcription, 
        job_id, 
        request.url, 
        request.model, 
        request.language, 
        request.device,
        current_user.id
    )
    return {"job_id": job_id, "status": "pending"}

@app.post("/api/transcribe/file")
def transcribe_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    device: Optional[str] = Form("auto"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    job_id = str(uuid.uuid4())
    new_job = models.Job(id=job_id, type="transcribe", status=JobStatus.PENDING)
    db.add(new_job)
    db.commit()
    
    job_dir = Path(f"output/{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = job_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(
        process_transcription, 
        job_id, 
        str(file_path), 
        model, 
        language, 
        device,
        current_user.id
    )
    return {"job_id": job_id, "status": "pending"}

# --- Summarize, Chat, Clips (Basic Implementation without DB Persistence for now) ---
# For this iteration, we keep them simple, but they should really be Jobs too.

@app.post("/api/summarize")
def summarize_endpoint(request: SummarizeRequest):
    """Generate a summary from transcript text."""
    try:
        text = request.transcript_text
        if not text and request.transcript_path:
             if os.path.exists(request.transcript_path):
                 with open(request.transcript_path, "r", encoding="utf-8") as f:
                     text = f.read()
        
        if not text:
             raise HTTPException(status_code=400, detail="Transcript text required")

        print(f"[Summarize] Provider: {request.provider}, Model: {request.model}, Language: {request.output_language}")
        print(f"[Summarize] Transcript length: {len(text)} chars")
        
        summarizer = VideoSummarizer(provider=request.provider, model=request.model)
        summary = summarizer.summarize(text, output_language=request.output_language)
        
        return {
            "text": summary.text,
            "key_points": summary.key_points
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[Summarize ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")

# Chat Sessions (In-memory is fine for transient chat)
chat_sessions: Dict[str, Any] = {}

@app.post("/api/chat/start")
def start_chat(request: ChatStartRequest):
    """Start a new chat session about a video transcript."""
    session_id = str(uuid.uuid4())
    
    # Get transcript text - try text first, then fall back to file path
    text = request.transcript_text
    if not text and request.transcript_path:
        if os.path.exists(request.transcript_path):
            with open(request.transcript_path, "r", encoding="utf-8") as f:
                text = f.read()
    
    if not text:
        raise HTTPException(status_code=400, detail="Transcript text or path required")
    
    print(f"[Chat Start] Provider: {request.provider}, Model: {request.model}")
    print(f"[Chat Start] Transcript length: {len(text)} chars")
    
    session = create_chat_session(transcript=text, provider=request.provider, model=request.model)
    chat_sessions[session_id] = session
    return {"session_id": session_id}

@app.post("/api/chat/message")
def chat_message(request: ChatMessageRequest):
    session = chat_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    async def generate():
        for token in session.chat_stream(request.message):
            yield token
    
    return StreamingResponse(generate(), media_type="text/plain")

@app.post("/api/extract-clips")
def extract_clips_endpoint(request: ExtractClipsRequest):
    """Extract important clips from a video based on transcript."""
    try:
        # Get transcript text
        text = request.transcript_text
        if not text and request.transcript_path:
            if os.path.exists(request.transcript_path):
                with open(request.transcript_path, "r", encoding="utf-8") as f:
                    text = f.read()
        
        if not text:
            raise HTTPException(status_code=400, detail="Transcript text or path required")
        
        if not os.path.exists(request.video_path):
            raise HTTPException(status_code=400, detail=f"Video file not found: {request.video_path}")
        
        print(f"[Extract Clips] Provider: {request.provider}, Model: {request.model}, Num clips: {request.num_clips}")
        print(f"[Extract Clips] Transcript length: {len(text)} chars, Video: {request.video_path}")
        
        # Use VideoSummarizer to extract clips
        summarizer = VideoSummarizer(provider=request.provider, model=request.model)
        clips = summarizer.extract_clips(text, num_clips=request.num_clips)
        
        # Convert clips to serializable format - use Clip model's to_dict()
        clips_data = [clip.to_dict() for clip in clips]
        
        # Optionally extract and merge actual video clips
        output_clips = []
        if clips_data:
            from pathlib import Path
            output_dir = Path("output") / "clips" / str(uuid.uuid4())[:8]
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Extract individual clips
                extracted = extract_video_clips(request.video_path, clips, str(output_dir))
                output_clips = extracted
                
                # Merge if requested
                if request.merge and len(extracted) > 1:
                    merged_path = merge_clips(extracted, str(output_dir / "merged.mp4"))
                    output_clips.append({"type": "merged", "path": merged_path})
            except Exception as e:
                # If extraction fails, just return clip metadata
                print(f"Clip extraction failed: {e}")
        
        return {
            "clips": clips_data,
            "extracted_files": output_clips,
            "message": f"Found {len(clips_data)} important clips"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # If the request is for an API endpoint that doesn't exist, let it fall through to 404
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
        
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Frontend not found. Please run 'npm run build' in frontend/."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
