"""Data models for the application."""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class StudentProfile(BaseModel):
    """Student profile data model."""
    student_id: str
    name: str
    resume_path: str
    skills: List[str] = []
    experience_years: int = 0
    education: str = ""
    media_attachments: List[Dict[str, Any]] = []
    last_updated: datetime = None


class RAGQuery(BaseModel):
    """RAG query request."""
    question: str
    job_description: Optional[str] = None
    company_name: Optional[str] = None
    top_k: Optional[int] = 5


class RAGChunk(BaseModel):
    """Retrieved document chunk."""
    chunk_id: str
    content: str
    source_type: str  # 'resume', 'media', etc.
    student_id: str
    metadata: Dict[str, Any]


class RAGResponse(BaseModel):
    """RAG query response."""
    answer: str
    cited_chunks: List[RAGChunk]
    metrics: Dict[str, Any]


class InterviewQuestion(BaseModel):
    """Interview question tied to student."""
    question_text: str
    evidence_citation: str  # Reference to chunk_id
    difficulty: str = "medium"


class StudentScorecard(BaseModel):
    """Scorecard for a student for a specific company/role."""
    student_id: str
    student_name: str
    company_name: str
    job_title: str
    score: float  # 0-100
    match_reasons: List[str]
    interview_questions: List[InterviewQuestion]
    outreach_email: str


class ChainOrchestrationRequest(BaseModel):
    """Request for prompt chain orchestration."""
    company_name: str
    job_description: str
    job_title: str
    max_candidates: int = 5


class ChainOrchestrationResponse(BaseModel):
    """Response from prompt chain orchestration."""
    company_name: str
    job_title: str
    role_summary: str
    top_students: List[StudentScorecard]
    metrics: Dict[str, Any]


class MediaUploadRequest(BaseModel):
    """Request to upload media."""
    student_id: str
    media_type: str  # 'certificate', 'portfolio', etc.
    description: str = ""


class MediaUploadResponse(BaseModel):
    """Response from media upload."""
    media_id: str
    student_id: str
    media_type: str
    extracted_text: str
    tags: List[str]
    status: str
