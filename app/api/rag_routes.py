"""RAG API endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.core.models import RAGQuery, RAGResponse
from app.rag.pipeline import RAGPipeline
from app.core.observability import ChainStep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rag", tags=["rag"])

# Initialize pipeline
rag_pipeline = RAGPipeline()


@router.post("/ingest", summary="Ingest student resumes")
async def ingest_resumes():
    """
    Ingest all student resumes from the configured directory.
    """
    try:
        with ChainStep("ingest_resumes") as step:
            rag_pipeline.ingest_student_resumes()
            step.log_metadata(status="success")
        
        return {
            "status": "success",
            "message": "Student resumes ingested successfully"
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=RAGResponse, summary="Query student database")
async def query_rag(request: RAGQuery):
    """
    Query the RAG pipeline for student information.
    
    Returns grounded answers with cited chunks and observability metrics.
    """
    try:
        with ChainStep("rag_query") as step:
            response = rag_pipeline.query(
                question=request.question,
                job_description=request.job_description,
                company_name=request.company_name
            )
            step.log_metadata(
                chunks_retrieved=len(response.cited_chunks),
                company=request.company_name
            )
        
        return response
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "RAG Pipeline"
    }
