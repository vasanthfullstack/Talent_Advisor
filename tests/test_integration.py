"""End-to-end integration tests."""
import pytest
import tempfile
from pathlib import Path
from PIL import Image
from app.rag.pipeline import RAGPipeline
from app.orchestration.chain import PromptChainOrchestrator
from app.multimodal.enrichment import MultimodalEnrichment


def test_end_to_end_hiring_workflow():
    """
    Test complete end-to-end workflow:
    1. Ingest resumes
    2. Query for candidates
    3. Orchestrate hiring process
    4. Generate artifacts
    """
    print("\n" + "="*60)
    print("END-TO-END HIRING WORKFLOW TEST")
    print("="*60)
    
    # Step 1: Initialize components
    rag_pipeline = RAGPipeline()
    orchestrator = PromptChainOrchestrator()
    
    # Step 2: Ingest resumes
    print("\n1. Ingesting student resumes...")
    rag_pipeline.ingest_student_resumes()
    assert len(rag_pipeline.vector_store.metadata) > 0
    print(f"   ✓ Ingested {len(rag_pipeline.vector_store.metadata)} chunks")
    
    # Step 3: RAG Query for candidates
    print("\n2. Querying for senior full-stack developers...")
    rag_response = rag_pipeline.query(
        question="Find developers with full-stack experience",
        job_description="Senior Full-Stack Engineer with Python and React experience"
    )
    assert rag_response.answer
    assert len(rag_response.cited_chunks) > 0
    print(f"   ✓ Found {len(rag_response.cited_chunks)} relevant chunks")
    
    # Step 4: Orchestrate hiring workflow
    print("\n3. Orchestrating hiring workflow for TechCorp...")
    hiring_response = orchestrator.orchestrate_company_hiring(
        company_name="TechCorp",
        job_description="Senior Full-Stack Engineer with 5+ years experience in Python, React, and AWS",
        job_title="Senior Software Engineer",
        max_candidates=3
    )
    
    assert hiring_response.company_name == "TechCorp"
    assert hiring_response.role_summary
    assert len(hiring_response.top_students) > 0
    print(f"   ✓ Generated role summary")
    print(f"   ✓ Ranked {len(hiring_response.top_students)} candidates")
    
    # Step 5: Verify artifacts generated
    print("\n4. Verifying generated artifacts...")
    for idx, student in enumerate(hiring_response.top_students[:1], 1):
        print(f"\n   Candidate {idx}: {student.student_name}")
        print(f"   - Match Score: {student.score}/100")
        print(f"   - Interview Questions: {len(student.interview_questions)}")
        print(f"   - Has Outreach Email: {bool(student.outreach_email)}")
        
        assert student.score >= 0 and student.score <= 100
        assert len(student.interview_questions) > 0
        assert student.outreach_email
        assert len(student.interview_questions) >= 3 or len(student.interview_questions) > 0
    
    print("\n✅ End-to-end hiring workflow completed successfully!")


def test_end_to_end_with_media_enrichment():
    """
    Test end-to-end workflow including media enrichment:
    1. Process media
    2. Enrich student profiles
    3. Query with enriched data
    4. Generate hiring recommendations
    """
    print("\n" + "="*60)
    print("END-TO-END WORKFLOW WITH MEDIA ENRICHMENT")
    print("="*60)
    
    # Create test certificate image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(tmp.name)
        cert_path = tmp.name
    
    try:
        # Step 1: Enrich student profile with certificate
        print("\n1. Enriching student profile with certificate...")
        enrichment = MultimodalEnrichment()
        enrichment.rag_pipeline.ingest_student_resumes()
        
        enrichment_result = enrichment.enrich_student_profile(
            image_path=cert_path,
            student_id="student_001",
            media_type="certificate",
            description="AWS Solutions Architect Certification"
        )
        
        assert enrichment_result["success"]
        assert enrichment_result["chunks_created"] > 0
        print(f"   ✓ Created {enrichment_result['chunks_created']} chunks from certificate")
        
        # Step 2: Query for AWS-certified developers
        print("\n2. Querying for AWS-certified developers...")
        rag_query = enrichment.rag_pipeline.query(
            question="Find AWS certified developers",
            job_description="AWS solutions architect needed"
        )
        
        assert rag_query.answer
        print(f"   ✓ Query completed with {len(rag_query.cited_chunks)} citations")
        
        # Step 3: Run hiring orchestration
        print("\n3. Running hiring orchestration...")
        orchestrator = PromptChainOrchestrator()
        orchestrator.rag_pipeline = enrichment.rag_pipeline
        
        hiring = orchestrator.orchestrate_company_hiring(
            company_name="CloudCorp",
            job_description="AWS Solutions Architect with certification",
            job_title="Solutions Architect",
            max_candidates=2
        )
        
        assert hiring.company_name == "CloudCorp"
        print(f"   ✓ Generated hiring recommendation for {len(hiring.top_students)} candidates")
        
        print("\n✅ End-to-end workflow with enrichment completed successfully!")
        
    finally:
        Path(cert_path).unlink(missing_ok=True)


def test_error_handling_and_resilience():
    """
    Test error handling and resilience:
    - Missing data
    - Invalid inputs
    - Empty results
    """
    print("\n" + "="*60)
    print("ERROR HANDLING AND RESILIENCE TEST")
    print("="*60)
    
    # Test 1: Empty RAG query
    print("\n1. Testing empty RAG query...")
    rag = RAGPipeline()
    rag.vector_store.clear()
    
    response = rag.query("Any query")
    assert response.answer
    assert len(response.cited_chunks) == 0
    print("   ✓ Handled empty index gracefully")
    
    # Test 2: Media enrichment with invalid file
    print("\n2. Testing media upload with invalid file...")
    enrichment = MultimodalEnrichment()
    result = enrichment.enrich_student_profile(
        image_path="/invalid/path.png",
        student_id="test"
    )
    
    assert not result["success"]
    assert "error" in result
    print("   ✓ Handled invalid file gracefully")
    
    print("\n✅ Error handling tests passed!")


if __name__ == "__main__":
    test_end_to_end_hiring_workflow()
    test_end_to_end_with_media_enrichment()
    test_error_handling_and_resilience()
    
    print("\n" + "="*60)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("="*60)
