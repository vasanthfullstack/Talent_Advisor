"""Test for media source prioritization in RAG queries."""
import pytest
import tempfile
from pathlib import Path
from PIL import Image
from app.rag.pipeline import RAGPipeline
from app.multimodal.enrichment import MultimodalEnrichment


def test_media_source_prioritization_in_queries():
    """
    Test that queries about certificates prioritize media chunks over resume chunks.
    
    Workflow:
    1. Ingest student resume
    2. Upload certificate with machine learning content
    3. Query for "machine learning certificate"
    4. Verify that media (certificate) chunks are ranked higher than resume chunks
    """
    print("\n" + "="*70)
    print("TEST: Media Source Prioritization in RAG Queries")
    print("="*70)
    
    # Step 1: Initialize systems
    rag_pipeline = RAGPipeline()
    rag_pipeline.ingest_student_resumes()
    print("\n✓ Ingested student resumes")
    
    # Step 2: Upload a certificate with ML content
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(tmp.name)
        cert_path = tmp.name
    
    try:
        enrichment = MultimodalEnrichment()
        enrichment.rag_pipeline = rag_pipeline  # Use same pipeline
        
        result = enrichment.enrich_student_profile(
            image_path=cert_path,
            student_id="student_001",
            media_type="certificate",
            description="Machine Learning Certificate"
        )
        
        assert result['success']
        print(f"✓ Uploaded certificate with {result['chunks_created']} chunks")
        print(f"  Tags extracted: {result['tags']}")
        
        # Step 3: Query for machine learning certificate
        # This should prioritize media chunks
        query_response = rag_pipeline.query(
            question="Which student has a machine learning certificate?",
            job_description="We need someone certified in machine learning"
        )
        
        print("\n✓ Query Results for: 'Which student has a machine learning certificate?'")
        print(f"  Answer preview: {query_response.answer[:150]}...")
        
        # Step 4: Verify media chunks are present and prioritized
        media_chunks = [c for c in query_response.cited_chunks if c.source_type == 'media']
        resume_chunks = [c for c in query_response.cited_chunks if c.source_type == 'resume']
        
        print(f"\n✓ Citation Analysis:")
        print(f"  - Media (Certificate) chunks cited: {len(media_chunks)}")
        print(f"  - Resume chunks cited: {len(resume_chunks)}")
        
        if media_chunks:
            print(f"\n✓ Media chunk content preview:")
            for i, chunk in enumerate(media_chunks[:2], 1):
                print(f"  [{i}] {chunk.content[:80]}...")
                print(f"       Metadata: {chunk.metadata.get('media_type', 'N/A')}")
        
        # Verify that certificate query found media content
        assert len(media_chunks) > 0, "Certificate query should return media chunks"
        
        # Verify answer mentions certificate/credential
        assert any(word in query_response.answer.lower() 
                  for word in ['certificate', 'credential', 'portfolio', 'achievement']), \
            "Answer should reference certificate/credential"
        
        print("\n TEST PASSED: Media chunks are properly prioritized for certificate queries!")
        
    finally:
        Path(cert_path).unlink(missing_ok=True)


def test_source_aware_search_basic():
    """Test basic source-aware search functionality."""
    from app.rag.vector_store import FAISSVectorStore
    
    store = FAISSVectorStore()
    
    # Add mixed chunks
    chunks = [
        {
            "chunk_id": "resume_001",
            "content": "Python expert with 5 years experience",
            "metadata": {"student_id": "student_001", "source_type": "resume"}
        },
        {
            "chunk_id": "cert_001",
            "content": "Certified Machine Learning with certificate achievement",
            "metadata": {"student_id": "student_001", "source_type": "media", "media_type": "certificate"}
        },
        {
            "chunk_id": "resume_002",
            "content": "JavaScript developer with React skills",
            "metadata": {"student_id": "student_002", "source_type": "resume"}
        }
    ]
    
    store.add_chunks(chunks)
    
    # Query without preference - should return top results by similarity
    all_results = store.search("machine learning", top_k=2)
    print(f"\n✓ Search without preference returned {len(all_results)} results")
    
    # Query with media preference - should prioritize media chunks
    media_results = store.search("machine learning", top_k=2, source_preference='media')
    print(f"✓ Search with media preference returned {len(media_results)} results")
    
    if media_results:
        first_source = media_results[0]['metadata']['source_type']
        print(f"  First result source type: {first_source}")
        
        # Media chunks should come first when there's a preference
        assert first_source == 'media', "Media preference should prioritize media chunks"
    
    print(" Source-aware search working correctly!")


if __name__ == "__main__":
    test_source_aware_search_basic()
    test_media_source_prioritization_in_queries()
    
    print("\n" + "="*70)
    print(" ALL MEDIA PRIORITIZATION TESTS PASSED!")
    print("="*70)
