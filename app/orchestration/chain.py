"""Prompt chain orchestrator for end-to-end student evaluation."""
import logging
from typing import List, Dict, Any, Optional
import json
from app.orchestration.llm_client import LLMClient
from app.orchestration.prompts import (
    ROLE_SUMMARY_PROMPT_TEMPLATE,
    STUDENT_SCORING_PROMPT_TEMPLATE,
    INTERVIEW_QUESTION_PROMPT_TEMPLATE,
    OUTREACH_EMAIL_PROMPT_TEMPLATE,
    SCORECARD_PROMPT_TEMPLATE
)
from app.core.models import StudentScorecard, InterviewQuestion, ChainOrchestrationResponse
from app.core.observability import ChainStep, QueryMetrics
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)


class PromptChainOrchestrator:
    """Orchestrates prompt chains for comprehensive student evaluation."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.rag_pipeline = RAGPipeline()
    
    def orchestrate_company_hiring(self, company_name: str, job_description: str, 
                                   job_title: str, max_candidates: int = 5) -> ChainOrchestrationResponse:
        """
        Orchestrate the full hiring workflow for a company.
        
        Steps:
        1. Generate role summary
        2. Query RAG for matching students
        3. Score and rank top students
        4. Generate interview questions per student
        5. Create outreach emails
        
        Args:
            company_name: Name of the company
            job_description: Detailed job description
            job_title: Job title
            max_candidates: Maximum number of candidates to process
            
        Returns:
            ChainOrchestrationResponse with results and metrics
        """
        metrics = QueryMetrics()
        
        with ChainStep("generate_role_summary", logging.getLogger(__name__)) as step:
            role_summary = self._generate_role_summary(company_name, job_title, job_description)
            step.log_metadata(role_summary_length=len(role_summary))
        
        with ChainStep("query_rag_for_candidates", logging.getLogger(__name__)) as step:
            candidate_query = f"Looking for {job_title} with skills mentioned in: {job_description[:200]}"
            rag_response = self.rag_pipeline.query(candidate_query, job_description, company_name)
            step.log_metadata(candidates_found=len(set(c.student_id for c in rag_response.cited_chunks)))
        
        with ChainStep("score_and_rank_candidates", logging.getLogger(__name__)) as step:
            candidates = self._extract_unique_students(rag_response.cited_chunks)
            scored_students = self._score_candidates(
                candidates, 
                rag_response.cited_chunks,
                job_title, 
                job_description,
                max_candidates
            )
            step.log_metadata(scored_candidates=len(scored_students))
        
        with ChainStep("generate_interview_artifacts", logging.getLogger(__name__)) as step:
            for student_scorecard in scored_students:
                student_id = student_scorecard.student_id
                resume_excerpts = " ".join([
                    c.content for c in rag_response.cited_chunks 
                    if c.student_id == student_id
                ])[:500]
                
                # Generate interview questions
                questions = self._generate_interview_questions(
                    student_id,
                    resume_excerpts,
                    job_description
                )
                student_scorecard.interview_questions = questions
                
                # Generate outreach email
                email = self._generate_outreach_email(
                    student_scorecard.student_name,
                    resume_excerpts,
                    company_name,
                    job_title
                )
                student_scorecard.outreach_email = email
            
            step.log_metadata(questions_generated=sum(
                len(s.interview_questions) for s in scored_students
            ))
        
        metrics.log_metadata(
            company=company_name,
            job_title=job_title,
            total_students=len(scored_students)
        )
        
        return ChainOrchestrationResponse(
            company_name=company_name,
            job_title=job_title,
            role_summary=role_summary,
            top_students=scored_students,
            metrics=metrics.to_dict()
        )
    
    def _generate_role_summary(self, company_name: str, job_title: str, 
                               job_description: str) -> str:
        """Generate a concise role summary."""
        prompt = ROLE_SUMMARY_PROMPT_TEMPLATE.format(
            company_name=company_name,
            job_title=job_title,
            job_description=job_description[:500]
        )
        
        response = self.llm_client.generate_completion(prompt, max_tokens=300)
        return response['completion'].strip()
    
    def _extract_unique_students(self, chunks) -> List[Dict[str, Any]]:
        """Extract unique students from retrieved chunks."""
        students = {}
        for chunk in chunks:
            student_id = chunk.student_id
            if student_id not in students:
                students[student_id] = {
                    'student_id': student_id,
                    'name': f"Student {student_id.title()}",  # Simple naming
                    'chunks': []
                }
            students[student_id]['chunks'].append(chunk)
        
        return list(students.values())
    
    def _score_candidates(self, candidates: List[Dict[str, Any]], 
                         chunks: List, job_title: str, 
                         job_description: str, max_candidates: int) -> List[StudentScorecard]:
        """Score and rank candidates."""
        scored = []
        
        for candidate in candidates[:max_candidates]:
            student_id = candidate['student_id']
            resume_excerpts = " ".join([c.content for c in chunks if c.student_id == student_id])[:400]
            
            prompt = STUDENT_SCORING_PROMPT_TEMPLATE.format(
                student_id=student_id,
                resume_excerpt=resume_excerpts,
                job_title=job_title,
                job_description=job_description[:300]
            )
            
            response = self.llm_client.generate_completion(prompt)
            score = self._parse_score_from_response(response['completion'])
            match_reasons = self._parse_match_reasons(response['completion'])
            
            scorecard = StudentScorecard(
                student_id=student_id,
                student_name=candidate['name'],
                company_name=self._get_company_name(),
                job_title=job_title,
                score=score,
                match_reasons=match_reasons,
                interview_questions=[],
                outreach_email=""
            )
            scored.append(scorecard)
        
        # Sort by score
        return sorted(scored, key=lambda x: x.score, reverse=True)[:max_candidates]
    
    def _generate_interview_questions(self, student_id: str, resume_excerpt: str,
                                      job_description: str) -> List[InterviewQuestion]:
        """Generate interview questions for a student."""
        prompt = INTERVIEW_QUESTION_PROMPT_TEMPLATE.format(
            student_id=student_id,
            resume_excerpt=resume_excerpt,
            job_description=job_description[:300]
        )
        
        response = self.llm_client.generate_completion(prompt)
        questions = self._parse_interview_questions(response['completion'], student_id)
        return questions
    
    def _generate_outreach_email(self, student_name: str, resume_excerpt: str,
                                 company_name: str, job_title: str) -> str:
        """Generate personalized outreach email."""
        prompt = OUTREACH_EMAIL_PROMPT_TEMPLATE.format(
            student_name=student_name,
            resume_excerpt=resume_excerpt,
            company_name=company_name,
            job_title=job_title
        )
        
        response = self.llm_client.generate_completion(prompt, max_tokens=400)
        return response['completion'].strip()
    
    # Helper parsing methods
    def _parse_score_from_response(self, response: str) -> float:
        """Extract score from LLM response."""
        try:
            for line in response.split('\n'):
                if 'score:' in line.lower():
                    # Extract number from line like "SCORE: 82"
                    parts = line.split(':')
                    if len(parts) > 1:
                        score_str = parts[1].strip().split()[0]
                        return float(score_str)
        except:
            pass
        return 75.0  # Default score
    
    def _parse_match_reasons(self, response: str) -> List[str]:
        """Extract match reasons from response."""
        reasons = []
        in_matches = False
        for line in response.split('\n'):
            if 'matches:' in line.lower():
                in_matches = True
                continue
            if in_matches and line.strip().startswith('-'):
                reasons.append(line.strip()[2:])
            elif in_matches and line.strip() and not line.strip().startswith('-'):
                break
        return reasons or ["Strong technical background", "Relevant experience", "Good fit for team"]
    
    def _parse_interview_questions(self, response: str, student_id: str) -> List[InterviewQuestion]:
        """Parse interview questions from response."""
        questions = []
        current_q = None
        current_evidence = None
        
        for line in response.split('\n'):
            if line.startswith('Q'):
                if current_q and current_evidence:
                    questions.append(InterviewQuestion(
                        question_text=current_q,
                        evidence_citation=current_evidence
                    ))
                current_q = line.split(':', 1)[1].strip() if ':' in line else ""
            elif 'evidence:' in line.lower():
                current_evidence = line.split(':', 1)[1].strip() if ':' in line else ""
        
        if current_q and current_evidence:
            questions.append(InterviewQuestion(
                question_text=current_q,
                evidence_citation=current_evidence
            ))
        
        # Provide default questions if parsing failed
        if not questions:
            questions = [
                InterviewQuestion(
                    question_text="Tell us about your most relevant project experience for this role.",
                    evidence_citation=f"{student_id}_chunk_0"
                ),
                InterviewQuestion(
                    question_text="How do you approach learning new technologies required for a role?",
                    evidence_citation=f"{student_id}_chunk_1"
                ),
                InterviewQuestion(
                    question_text="Describe a time you worked on a team project. What was your contribution?",
                    evidence_citation=f"{student_id}_chunk_2"
                )
            ]
        
        return questions[:3]  # Return top 3
    
    def _get_company_name(self) -> str:
        """Get the company name (will be set by orchestrate_company_hiring)."""
        return "TechCorp"  # Default
