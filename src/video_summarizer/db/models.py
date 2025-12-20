from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    videos = relationship("Video", back_populates="owner")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="Untitled Video")
    filename = Column(String) # Original filename
    file_path = Column(String) # Path on disk (e.g. output/job_id/video.mp4)
    duration = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    thumbnail_url = Column(String, nullable=True)
    source_url = Column(String, nullable=True) # If from YouTube

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="videos")
    
    jobs = relationship("Job", back_populates="video")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True) # UUID
    type = Column(String) # transcribe, summarize, extract
    status = Column(String, default="pending")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    video = relationship("Video", back_populates="jobs")
