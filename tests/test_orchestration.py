"""Test suite for orchestration chain."""
import pytest
from app.orchestration.chain import PromptChainOrchestrator
from app.orchestration.llm_client import LLMClient


@pytest.fixture
def orchestrator():
    """Create orchestrator instance."""
    return PromptChainOrchestrator()


@pytest.fixture
def llm_client():
    """Create LLM client instance."""
    return LLMClient()


def test_llm_mock_completion(llm_client):
    """Test mock LLM completion."""
    prompt = "Generate a role summary for Senior Engineer"
    response = llm_client.generate_completion(prompt)
    
    assert "completion" in response
    assert response["completion"]
    assert response["model"]
    assert "tokens" in str(response).lower() or "total" in response
    print(f"✓ LLM mock completion test passed")


def test_role_summary_generation(orchestrator):
    """Test role summary generation."""
    summary = orchestrator._generate_role_summary(
        company_name="TechCorp",
        job_title="Senior Software Engineer",
        job_description="Looking for experienced engineer with 5+ years experience in cloud platforms"
    )
    
    assert summary
    assert len(summary) > 0
    assert isinstance(summary, str)
    print(f"✓ Role summary generation test passed: {summary[:100]}...")


def test_student_scoring(orchestrator):
    """Test student scoring logic."""
    from app.core.models import RAGChunk
    
    chunks = [
        RAGChunk(
            chunk_id="chunk_001",
            content="5 years Python experience, Django expert, AWS knowledge",
            source_type="resume",
            student_id="student_001",
            metadata={"skills": ["python", "aws"]}
        )
    ]
    
    candidates = [
        {
            "student_id": "student_001",
            "name": "John Developer",
            "chunks": chunks
        }
    ]
    
    scored = orchestrator._score_candidates(
        candidates=candidates,
        chunks=chunks,
        job_title="Senior Python Developer",
        job_description="Looking for Python expert with AWS experience",
        max_candidates=1
    )
    
    assert len(scored) > 0
    assert scored[0].score >= 0 and scored[0].score <= 100
    assert scored[0].student_id == "student_001"
    print(f"✓ Student scoring test passed: Score = {scored[0].score}")


def test_interview_question_generation(orchestrator):
    """Test interview question generation."""
    questions = orchestrator._generate_interview_questions(
        student_id="student_001",
        resume_excerpt="5 years Python experience with Django and Flask. Built multiple REST APIs.",
        job_description="Senior Python Developer with API design experience"
    )
    
    assert len(questions) > 0
    assert len(questions) <= 3
    assert all(hasattr(q, "question_text") for q in questions)
    assert all(hasattr(q, "evidence_citation") for q in questions)
    print(f"✓ Interview question generation test passed: Generated {len(questions)} questions")


def test_outreach_email_generation(orchestrator):
    """Test outreach email generation."""
    email = orchestrator._generate_outreach_email(
        student_name="John Developer",
        resume_excerpt="5 years Python experience, AWS certified",
        company_name="TechCorp",
        job_title="Senior Engineer"
    )
    
    assert email
    assert len(email) > 50
    assert isinstance(email, str)
    print(f"✓ Outreach email generation test passed: {email[:100]}...")


def test_prompt_chain_orchestration_e2e(orchestrator):
    """Test end-to-end orchestration workflow."""
    response = orchestrator.orchestrate_company_hiring(
        company_name="TechCorp",
        job_description="Senior Python developer with 5+ years experience, AWS knowledge",
        job_title="Senior Software Engineer",
        max_candidates=3
    )
    
    assert response.company_name == "TechCorp"
    assert response.job_title == "Senior Software Engineer"
    assert response.role_summary
    assert isinstance(response.top_students, list)
    assert response.metrics
    
    print(f"✓ Orchestration end-to-end test passed:")
    print(f"  - Company: {response.company_name}")
    print(f"  - Role Summary: {response.role_summary[:100]}...")
    print(f"  - Top candidates: {len(response.top_students)}")
    if response.top_students:
        print(f"  - Top candidate score: {response.top_students[0].score}")


if __name__ == "__main__":
    client = LLMClient()
    test_llm_mock_completion(client)
    
    orch = PromptChainOrchestrator()
    test_role_summary_generation(orch)
    test_student_scoring(orch)
    test_interview_question_generation(orch)
    test_outreach_email_generation(orch)
    test_prompt_chain_orchestration_e2e(orch)
    
    print("\n✅ All orchestration tests passed!")
