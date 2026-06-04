"""RAG query and retrieval logic."""
import logging
from typing import List, Dict, Any, Optional
from app.rag.ingestion import load_resumes_from_directory
from app.rag.chunking import TextChunker, extract_skills_from_text
from app.rag.vector_store import FAISSVectorStore
from app.core.models import RAGResponse, RAGChunk
from app.core.observability import QueryMetrics
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG pipeline orchestrator."""
    
    def __init__(self, settings = None):
        self.settings = settings or get_settings()
        self.vector_store = FAISSVectorStore(
            embedding_model=self.settings.embedding_model,
            index_path=self.settings.faiss_index_path,
            metadata_path=self.settings.metadata_path
        )
        self.chunker = TextChunker(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap
        )
    
    def ingest_student_resumes(self):
        """Ingest all student resumes from the configured directory."""
        logger.info(f"Starting resume ingestion from {self.settings.student_profiles_path}")
        
        resumes = load_resumes_from_directory(self.settings.student_profiles_path)
        
        if not resumes:
            logger.warning("No resumes found for ingestion")
            return
        
        total_chunks = 0
        for student_id, filename, text_content in resumes:
            # Extract metadata
            skills = extract_skills_from_text(text_content)
            
            metadata = {
                'student_id': student_id,
                'source_type': 'resume',
                'source_file': filename,
                'skills': skills
            }
            
            # Chunk the text
            chunks = self.chunker.chunk_text(text_content, metadata)
            total_chunks += len(chunks)
            
            # Add to vector store
            self.vector_store.add_chunks(chunks)
        
        logger.info(f"Ingestion complete: {total_chunks} total chunks from {len(resumes)} resumes")
    
    def query(self, question: str, job_description: Optional[str] = None, 
              company_name: Optional[str] = None) -> RAGResponse:
        """
        Execute a RAG query.
        
        Args:
            question: Recruiter question
            job_description: Optional job description for context
            company_name: Optional company name
            
        Returns:
            RAGResponse with grounded answer and citations
        """
        metrics = QueryMetrics()
        
        # Prepare search query
        search_query = question
        if job_description:
            search_query = f"{question} {job_description}"
        
        # Retrieve relevant chunks
        retrieved_chunks = self.vector_store.search(
            search_query, 
            top_k=self.settings.top_k_retrieval
        )
        metrics.retrieval_time = 0.1  # Mock timing
        
        if not retrieved_chunks:
            return RAGResponse(
                answer="No relevant student information found for this query.",
                cited_chunks=[],
                metrics=metrics.to_dict()
            )
        
        # Generate grounded answer from retrieved chunks
        answer = self._generate_grounded_answer(question, retrieved_chunks, job_description)
        
        # Convert to RAGChunk models
        cited_chunks = [
            RAGChunk(
                chunk_id=chunk['chunk_id'],
                content=chunk['content'],
                source_type=chunk['metadata']['source_type'],
                student_id=chunk['metadata']['student_id'],
                metadata=chunk['metadata']
            )
            for chunk in retrieved_chunks
        ]
        
        metrics.log_metadata(retrieved_chunks=len(retrieved_chunks), query_length=len(search_query))
        
        return RAGResponse(
            answer=answer,
            cited_chunks=cited_chunks,
            metrics=metrics.to_dict()
        )
    
    def _generate_grounded_answer(self, question: str, chunks: List[Dict[str, Any]], 
                                   job_description: Optional[str] = None) -> str:
        """
        Generate a grounded answer from retrieved chunks.
        
        In production, this would call an LLM. Here we create a synthesis.
        """
        if not chunks:
            return "No information available."
        
        # Extract relevant information from chunks
        students_mentioned = {}
        for chunk in chunks:
            student_id = chunk['metadata']['student_id']
            if student_id not in students_mentioned:
                students_mentioned[student_id] = []
            students_mentioned[student_id].append(chunk['content'][:200])
        
        # Build answer
        answer_parts = [f"Based on student profiles, here are relevant candidates:"]
        for student_id, excerpts in students_mentioned.items():
            answer_parts.append(f"\n• Student {student_id}:")
            for excerpt in excerpts[:2]:
                answer_parts.append(f"  - {excerpt}...")
        
        if job_description:
            answer_parts.append(f"\nFor the role requirement: {job_description[:100]}...")
        
        return "\n".join(answer_parts)
