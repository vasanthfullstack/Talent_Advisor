"""Multimodal enrichment API endpoints."""
import logging
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.core.models import MediaUploadResponse
from app.multimodal.enrichment import MultimodalEnrichment
from app.core.observability import ChainStep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resumes", tags=["multimodal"])

# Initialize enrichment
enrichment = MultimodalEnrichment()


@router.post("/upload-media", response_model=MediaUploadResponse, 
             summary="Upload media for student profile enrichment")
async def upload_media(
    file: UploadFile = File(...),
    student_id: str = Form(...),
    media_type: str = Form("certificate"),
    description: str = Form("")
):
    """
    Upload an image file (certificate, portfolio screenshot) to enrich student profile.
    
    The image is processed with OCR, and extracted text becomes searchable in RAG.
    
    Args:
        file: Image file (PNG, JPG)
        student_id: Student ID
        media_type: Type of media (certificate, portfolio, etc.)
        description: Optional description
        
    Returns:
        MediaUploadResponse with extraction results
    """
    try:
        # Validate file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {allowed_extensions}"
            )
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        try:
            with ChainStep("enrich_student_profile") as step:
                result = enrichment.enrich_student_profile(
                    image_path=tmp_path,
                    student_id=student_id,
                    media_type=media_type,
                    description=description
                )
                step.log_metadata(
                    student_id=student_id,
                    media_type=media_type,
                    success=result.get('success')
                )
            
            if not result['success']:
                raise HTTPException(status_code=500, detail=result.get('error'))
            
            return MediaUploadResponse(
                media_id=result['media_id'],
                student_id=student_id,
                media_type=media_type,
                extracted_text=result['extracted_text_sample'],
                tags=result['tags'],
                status="success"
            )
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Media upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Multimodal Enrichment Pipeline"
    }
