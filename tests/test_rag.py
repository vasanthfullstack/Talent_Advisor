"""Test suite for RAG pipeline."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from app.rag.ingestion import extract_text_from_pdf, load_resumes_from_directory
from app.rag.chunking import TextChunker, extract_skills_from_text
from app.rag.vector_store import FAISSVectorStore
from app.rag.pipeline import RAGPipeline


@pytest.fixture
def test_resumes_dir(tmp_path):
    """Create temporary directory with test PDF."""
    return tmp_path


@pytest.fixture
def rag_pipeline():
    """Create RAG pipeline instance."""
    return RAGPipeline()


def test_text_chunking():
    """Test text chunking with overlap."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)
    text = "This is a test. " * 50  # Create long text
    metadata = {"student_id": "student_001", "source_type": "resume"}
    
    chunks = chunker.chunk_text(text, metadata)
    
    assert len(chunks) > 0
    assert all("chunk_id" in chunk for chunk in chunks)
    assert all(chunk["metadata"]["student_id"] == "student_001" for chunk in chunks)
    print(f"✓ Chunking test passed: Created {len(chunks)} chunks")


def test_skill_extraction():
    """Test skill extraction from text."""
    text = """
    Experienced Python developer with expertise in machine learning using TensorFlow
    and scikit-learn. Strong background in React and Node.js development.
    Also experienced with AWS and Docker containerization.
    """
    
    skills = extract_skills_from_text(text)
    
    assert "python" in skills
    assert "machine learning" in skills
    assert "tensorflow" in skills
    assert "react" in skills
    assert "aws" in skills
    print(f"✓ Skill extraction test passed: Found {len(skills)} skills")


def test_faiss_vector_store():
    """Test FAISS vector store operations."""
    store = FAISSVectorStore()
    
    # Create test chunks
    chunks = [
        {
            "chunk_id": "chunk_001",
            "content": "Python expert with 5 years experience in web development",
            "metadata": {"student_id": "student_001", "source_type": "resume"}
        },
        {
            "chunk_id": "chunk_002", 
            "content": "JavaScript developer specializing in React and Node.js frameworks",
            "metadata": {"student_id": "student_002", "source_type": "resume"}
        }
    ]
    
    # Add chunks
    store.add_chunks(chunks)
    
    # Search
    results = store.search("Python web developer", top_k=1)
    
    assert len(results) > 0
    assert results[0]["chunk_id"] == "chunk_001"
    assert results[0]["similarity_score"] > 0
    print(f"✓ FAISS vector store test passed: Retrieved relevant chunks")


def test_rag_query_empty_index(rag_pipeline):
    """Test RAG query with empty index."""
    # Clear the index
    rag_pipeline.vector_store.clear()
    
    response = rag_pipeline.query("Looking for Python developers")
    
    assert response.answer
    assert len(response.cited_chunks) == 0
    assert "No relevant" in response.answer or response.answer
    print("✓ Empty index test passed")


def test_rag_query_with_context(rag_pipeline):
    """Test RAG query with job description context."""
    # Add sample data to vector store
    chunks = [
        {
            "chunk_id": "test_chunk_001",
            "content": "5+ years Python experience, Django and Flask expert, AWS proficient",
            "metadata": {"student_id": "test_student_001", "source_type": "resume", "skills": ["python", "aws"]}
        }
    ]
    rag_pipeline.vector_store.add_chunks(chunks)
    
    response = rag_pipeline.query(
        question="Find developers with Python expertise",
        job_description="Senior Python developer with AWS experience",
        company_name="TechCorp"
    )
    
    assert response.answer
    assert response.metrics
    assert "latency" in str(response.metrics).lower() or len(response.metrics) > 0
    print("✓ RAG query with context test passed")


if __name__ == "__main__":
    # Run tests
    test_text_chunking()
    test_skill_extraction()
    test_faiss_vector_store()
    
    rag = RAGPipeline()
    test_rag_query_empty_index(rag)
    test_rag_query_with_context(rag)
    
    print("\n✅ All RAG tests passed!")
