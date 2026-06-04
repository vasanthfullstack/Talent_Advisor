"""Multimodal enrichment orchestrator."""
import logging
from typing import Dict, Any
from app.multimodal.media import MediaProcessor
from app.rag.pipeline import RAGPipeline
from app.rag.chunking import TextChunker

logger = logging.getLogger(__name__)


class MultimodalEnrichment:
    """Orchestrate media upload and integration with RAG."""
    
    def __init__(self):
        self.media_processor = MediaProcessor()
        self.rag_pipeline = RAGPipeline()
        self.chunker = TextChunker()
    
    def enrich_student_profile(self, image_path: str, student_id: str,
                               media_type: str = "certificate",
                               description: str = "") -> Dict[str, Any]:
        """
        Process media and integrate into student profile.
        
        Args:
            image_path: Path to media file
            student_id: Student ID
            media_type: Type of media
            description: User-provided description
            
        Returns:
            Enrichment results
        """
        try:
            # Step 1: Process media
            with open(image_path, 'rb') as f:
                media_metadata = self.media_processor.process_image(
                    image_path, 
                    student_id, 
                    media_type
                )
            
            logger.info(f"Processed media for student {student_id}: {media_metadata['media_id']}")
            
            # Step 2: Extract and chunk the OCR'd text
            extracted_text = media_metadata['extracted_text']
            
            chunks = self.chunker.chunk_text(
                extracted_text,
                metadata={
                    'student_id': student_id,
                    'source_type': 'media',
                    'media_type': media_type,
                    'media_id': media_metadata['media_id'],
                    'tags': media_metadata['tags'],
                    'description': description
                }
            )
            
            logger.info(f"Created {len(chunks)} chunks from media for student {student_id}")
            
            # Step 3: Add chunks to RAG vector store
            self.rag_pipeline.vector_store.add_chunks(chunks)
            
            return {
                'success': True,
                'media_id': media_metadata['media_id'],
                'student_id': student_id,
                'chunks_created': len(chunks),
                'tags': media_metadata['tags'],
                'extracted_text_sample': extracted_text[:200] + "...",
                'message': f"Successfully enriched student profile with {media_type}"
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich student profile: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
