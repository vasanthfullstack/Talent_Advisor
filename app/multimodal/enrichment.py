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

    def _extract_certificate_keywords(self, text: str, media_type: str) -> list:
        """
        Extract certificate/media-specific keywords for better searchability.
        
        Adds keywords like 'certificate', 'achievement', 'credential', etc.
        """
        keywords = []
        text_lower = text.lower()
        
        # Add media type indicators
        if 'certificate' in text_lower or media_type.lower() in ['certificate', 'cert']:
            keywords.extend(['certificate', 'certified', 'credential', 'achievement'])
        
        if 'portfolio' in text_lower or media_type.lower() == 'portfolio':
            keywords.extend(['portfolio', 'project', 'showcase', 'work sample'])
        
        # Extract specific certifications mentioned
        certifications = {
            'aws': ['aws certified', 'amazon web services', 'aws solutions architect', 'aws developer'],
            'azure': ['azure certified', 'microsoft azure', 'azure architect'],
            'kubernetes': ['kubernetes', 'ckad', 'cka', 'container orchestration'],
            'gcp': ['google cloud', 'gcp certified', 'professional cloud architect'],
            'security': ['security+', 'cissp', 'cetrified ethical hacker', 'ceh'],
            'data': ['data scientist', 'data engineer', 'big data', 'spark', 'hadoop']
        }
        
        for cert_type, variations in certifications.items():
            if any(var in text_lower for var in variations):
                keywords.append(cert_type)
        
        # Add skills mentioned in text
        if 'machine learning' in text_lower or 'tensorflow' in text_lower or 'pytorch' in text_lower:
            keywords.extend(['machine learning', 'ai', 'deep learning', 'ml'])
        
        return keywords
    
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
            # Enhance metadata with searchable keywords
            enhanced_tags = self._extract_certificate_keywords(extracted_text, media_type)
            
            chunks = self.chunker.chunk_text(
                extracted_text,
                metadata={
                    'student_id': student_id,
                    'source_type': 'media',
                    'media_type': media_type,
                    'media_id': media_metadata['media_id'],
                    'tags': list(set(media_metadata['tags'] + enhanced_tags)),  # Merge tags
                    'description': description,
                    'searchable_keywords': ' '.join(enhanced_tags),  # For full-text search
                    'is_certificate': media_type.lower() in ['certificate', 'cert', 'credential']
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
