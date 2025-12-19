
import os
import shutil
import uuid
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from video_summarizer.transcription import (
    is_youtube_url,
    download_video,
    extract_audio,
    WhisperTranscriber,
    save_srt,
    format_as_srt
)

# --- Job Management ---

class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job:
    def __init__(self, job_id: str, type: str):
        self.id = job_id
        self.type = type
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.files: Dict[str, str] = {}  # Map of file type to path

    def update(self, status: str, result: Any = None, error: str = None):
        self.status = status
        self.updated_at = datetime.now()
        if result:
            self.result = result
        if error:
            self.error = error

jobs: Dict[str, Job] = {}

def create_job(type: str) -> Job:
    job_id = str(uuid.uuid4())
    job = Job(job_id, type)
    jobs[job_id] = job
    return job

def get_job(job_id: str) -> Job:
    return jobs.get(job_id)

# --- Background Tasks ---

def process_transcription(job_id: str, source: str, model: str, language: str, device: str):
    job = get_job(job_id)
    if not job:
        return
    
    job.update(JobStatus.PROCESSING)
    output_dir = Path(f"output/{job_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Handle Source (Download or File)
        video_path = source
        if is_youtube_url(source):
            try:
                # job.update(JobStatus.PROCESSING, result={"step": "Downloading video..."})
                video_path = download_video(source, output_dir=str(output_dir))
                job.files["video"] = video_path
            except Exception as e:
                raise Exception(f"Download failed: {str(e)}")
        
        # 2. Extract Audio
        # job.update(JobStatus.PROCESSING, result={"step": "Extracting audio..."})
        try:
            audio_path = extract_audio(video_path)
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
            
        # 3. Transcribe
        # job.update(JobStatus.PROCESSING, result={"step": "Transcribing..."})
        try:
            transcriber = WhisperTranscriber(model=model, language=language, device=device)
            # This is blocking, might take a while
            segments = transcriber.transcribe(audio_path)
            
            # Save SRT
            srt_path = output_dir / "transcript.srt"
            save_srt(segments, srt_path)
            job.files["transcript"] = str(srt_path)
            
            # Save Raw Text (for summary later)
            text_path = output_dir / "transcript.txt"
            plain_text = "\\n".join(seg.text for seg in segments)
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(plain_text)
            job.files["text"] = str(text_path)

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
        finally:
            # Cleanup audio
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.unlink(audio_path)

        job.update(JobStatus.COMPLETED, result={
            "message": "Transcription successful", 
            "video_path": video_path,
            "transcript_path": str(srt_path),
            "segments_count": len(segments)
        })

    except Exception as e:
        job.update(JobStatus.FAILED, error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create output directory
    Path("output").mkdir(exist_ok=True)
    yield
    # Shutdown: Clean up? (Optional)

app = FastAPI(title="Video Summarizer API", version="0.1.0", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for accessing clips/videos if needed)
app.mount("/output", StaticFiles(directory="output"), name="output")

# Models
class TranscribeRequest(BaseModel):
    url: str
    language: Optional[str] = None
    model: Optional[str] = None
    device: Optional[str] = "auto"

class ProcessRequest(BaseModel):
    url: str
    output_language: str = "english"
    num_clips: int = 5
    merge: bool = True
    provider: str = "google"

# Resolve paths
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent
frontend_dir = project_root / "frontend"

# Routes
@app.get("/")
async def root():
    return FileResponse(frontend_dir / "index.html")

# Mount frontend assets
app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="frontend_js")

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "type": job.type,
        "status": job.status,
        "result": job.result,
        "error": job.error,
        "files": job.files,
        "updated_at": job.updated_at
    }

@app.post("/api/transcribe/url")
async def transcribe_url(request: TranscribeRequest, background_tasks: BackgroundTasks):
    job = create_job("transcribe")
    background_tasks.add_task(
        process_transcription, 
        job.id, 
        request.url, 
        request.model, 
        request.language, 
        request.device
    )
    return {"job_id": job.id, "status": "pending"}


from fastapi.responses import StreamingResponse
from video_summarizer.llm import VideoSummarizer, create_chat_session

# ... (Job classes) ...

# --- Chat Session Management ---
chat_sessions: Dict[str, Any] = {}

class ChatStartRequest(BaseModel):
    transcript_path: Optional[str] = None
    transcript_text: Optional[str] = None
    provider: Optional[str] = "google"
    model: Optional[str] = None

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class SummarizeRequest(BaseModel):
    transcript_path: Optional[str] = None
    transcript_text: Optional[str] = None
    output_language: str = "english"
    provider: str = "google"
    model: Optional[str] = None

# ... (Previous routes) ...

@app.post("/api/summarize")
async def summarize(request: SummarizeRequest):
    # This is relatively fast so we *could* do it synchronously, 
    # but for consistency let's use a background job if it takes > 5-10s.
    # LLM summarization can take 10-30s. So background job is better.
    
    job = create_job("summarize")
    
    # We can use a lambda or partial, but let's define a helper
    async def run_summarization(job_id, req):
        job = get_job(job_id)
        job.update(JobStatus.PROCESSING)
        
        try:
            # Get text
            text = req.transcript_text
            if not text and req.transcript_path:
                with open(req.transcript_path, "r", encoding="utf-8") as f:
                    # We might need to parse SRT if it's an SRT file
                    # CLI does: plain_text = "\n".join(seg.text for seg in segments)
                    # Let's assume the transcribe job saved a .txt version or we assume SRT handling
                    # For simplicity, let's load SRT if .srt
                    if req.transcript_path.endswith('.srt'):
                        from video_summarizer.transcription.srt_formatter import load_srt
                        segments = load_srt(req.transcript_path)
                        text = "\n".join(seg.text for seg in segments)
                    else:
                        text = f.read()
            
            if not text:
                raise Exception("No transcript provided or file is empty")

            summarizer = VideoSummarizer(provider=req.provider, model=req.model)
            summary = summarizer.summarize(text, output_language=req.output_language)
            
            result = {
                "text": summary.text,
                "key_points": summary.key_points
            }
            job.update(JobStatus.COMPLETED, result=result)
            
        except Exception as e:
            job.update(JobStatus.FAILED, error=str(e))

    # Add to existing background tasks mechanism in FastAPI
    # (Since I need to pass this into the endpoint, I need to modify the signature)
    # I'll modify the endpoint below.
    return {"job_id": job.id, "status": "pending"}

# Redefining the endpoint to include BackgroundTasks
@app.post("/api/summarize")
async def summarize_endpoint(request: SummarizeRequest, background_tasks: BackgroundTasks):
    job = create_job("summarize")
    
    async def run_summarization_task(job_id, req):
        job = get_job(job_id)
        job.update(JobStatus.PROCESSING)
        try:
             # Get text
            text = req.transcript_text
            if not text and req.transcript_path:
                with open(req.transcript_path, "r", encoding="utf-8") as f:
                    if req.transcript_path.endswith('.srt'):
                        from video_summarizer.transcription.srt_formatter import load_srt
                        segments = load_srt(req.transcript_path)
                        text = "\\n".join(seg.text for seg in segments)
                    else:
                        text = f.read()
            
            if not text:
                raise Exception("No transcript provided")

            summarizer = VideoSummarizer(provider=req.provider, model=req.model)
            summary = summarizer.summarize(text, output_language=req.output_language)
            
            job.update(JobStatus.COMPLETED, result={
                "text": summary.text,
                "key_points": summary.key_points
            })
        except Exception as e:
            job.update(JobStatus.FAILED, error=str(e))

    background_tasks.add_task(run_summarization_task, job.id, request)
    return {"job_id": job.id, "status": "pending"}


@app.post("/api/chat/start")
async def start_chat(request: ChatStartRequest):
    session_id = str(uuid.uuid4())
    
    try:
        text = request.transcript_text
        if not text and request.transcript_path:
             with open(request.transcript_path, "r", encoding="utf-8") as f:
                    if request.transcript_path.endswith('.srt'):
                        from video_summarizer.transcription.srt_formatter import load_srt
                        segments = load_srt(request.transcript_path)
                        text = "\\n".join(seg.text for seg in segments)
                    else:
                        text = f.read()
                        
        if not text:
            raise HTTPException(status_code=400, detail="Transcript required")

        session = create_chat_session(
            transcript=text,
            provider=request.provider,
            model=request.model
        )
        chat_sessions[session_id] = session
        return {"session_id": session_id, "message": "Chat session started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/message")
async def chat_message(request: ChatMessageRequest):
    session = chat_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # For simplicity, we are returning a simple stream response
    # In a real app we might use Server Sent Events (SSE) but StreamingResponse works for simple text stream
    
    async def generate_response():
        try:
            for token in session.chat_stream(request.message):
                yield token
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(generate_response(), media_type="text/plain")


from video_summarizer.llm.clip_extractor import extract_clips, save_clips_metadata, merge_clips

class ExtractClipsRequest(BaseModel):
    transcript_path: Optional[str] = None
    video_path: str
    num_clips: int = 5
    merge: bool = True
    reencode: bool = False
    provider: str = "google"
    model: Optional[str] = None

@app.post("/api/extract-clips")
async def extract_clips_endpoint(request: ExtractClipsRequest, background_tasks: BackgroundTasks):
    job = create_job("extract_clips")
    
    async def run_extract_clips(job_id, req):
        job = get_job(job_id)
        job.update(JobStatus.PROCESSING)
        output_dir = Path(f"output/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
             # Load transcript
            srt_content = ""
            if req.transcript_path:
                from video_summarizer.transcription.srt_formatter import load_srt
                # Need to handle if path is invalid
                if not os.path.exists(req.transcript_path):
                     raise Exception(f"Transcript not found: {req.transcript_path}")
                
                segments = load_srt(req.transcript_path)
                srt_content = format_as_srt(segments)
            else:
                 raise Exception("Transcript path required")

            # Extract clips using LLM
            summarizer = VideoSummarizer(provider=req.provider, model=req.model)
            clips = summarizer.extract_clips(srt_content, num_clips=req.num_clips)
            
            # Save metadata
            metadata_path = output_dir / "clips.json"
            save_clips_metadata(clips, metadata_path)
            
            # Extract video clips
            clips_dir = output_dir / "clips"
            extracted = extract_clips(
                video_path=req.video_path,
                clips=clips,
                output_dir=str(clips_dir),
                reencode=req.reencode,
            )
            
            result = {
                "clips_metadata": str(metadata_path),
                "clips_dir": str(clips_dir),
                "clips_count": len(extracted),
                "merged_video": None
            }

            # Merge if requested
            if req.merge and extracted:
                merged_path = output_dir / "merged_clips.mp4"
                merge_clips(extracted, str(merged_path), reencode=True)
                result["merged_video"] = str(merged_path)

            job.update(JobStatus.COMPLETED, result=result)

        except Exception as e:
            job.update(JobStatus.FAILED, error=str(e))
            
    background_tasks.add_task(run_extract_clips, job.id, request)
    return {"job_id": job.id, "status": "pending"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

