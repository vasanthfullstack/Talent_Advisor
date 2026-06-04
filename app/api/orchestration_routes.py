"""Orchestration API endpoints."""
import logging
from fastapi import APIRouter, HTTPException
from app.core.models import ChainOrchestrationRequest, ChainOrchestrationResponse
from app.orchestration.chain import PromptChainOrchestrator
from app.core.observability import ChainStep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])

# Initialize orchestrator
orchestrator = PromptChainOrchestrator()


@router.post("/company-hiring", response_model=ChainOrchestrationResponse, 
             summary="Orchestrate company hiring workflow")
async def orchestrate_company_hiring(request: ChainOrchestrationRequest):
    """
    Orchestrate the full hiring workflow for a company.
    
    Includes:
    1. Role summary generation
    2. Candidate retrieval and scoring
    3. Interview question generation
    4. Outreach email creation
    """
    try:
        with ChainStep("company_hiring_orchestration") as step:
            response = orchestrator.orchestrate_company_hiring(
                company_name=request.company_name,
                job_description=request.job_description,
                job_title=request.job_title,
                max_candidates=request.max_candidates
            )
            step.log_metadata(
                company=request.company_name,
                candidates=len(response.top_students)
            )
        
        return response
    except Exception as e:
        logger.error(f"Orchestration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Orchestration Pipeline"
    }
