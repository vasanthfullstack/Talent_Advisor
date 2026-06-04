"""LLM interaction with mock support."""
import logging
from typing import List, Dict, Any
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client with mock fallback support."""
    
    def __init__(self, settings = None):
        self.settings = settings or get_settings()
        self.use_mock = self.settings.use_mock_llm
        self.model = self.settings.llm_model
        
        if not self.use_mock and self.settings.openai_api_key:
            try:
                import openai
                openai.api_key = self.settings.openai_api_key
                self.client = openai.OpenAI(api_key=self.settings.openai_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Using mock mode.")
                self.use_mock = True
                self.client = None
        else:
            self.use_mock = True
            self.client = None
    
    def generate_completion(self, prompt: str, max_tokens: int = 500) -> Dict[str, Any]:
        """
        Generate a completion using LLM or mock.
        
        Args:
            prompt: The prompt to send to LLM
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with completion and token counts
        """
        if self.use_mock:
            return self._mock_completion(prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return {
                "completion": response.choices[0].message.content,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": self.model
            }
        except Exception as e:
            logger.error(f"LLM API call failed: {e}. Falling back to mock.")
            return self._mock_completion(prompt)
    
    def _mock_completion(self, prompt: str) -> Dict[str, Any]:
        """Generate mock completion for testing."""
        logger.info("Using mock LLM completion")
        
        # Simple mock responses based on prompt content
        if "role summary" in prompt.lower():
            text = "This is a challenging senior software engineering role that requires 5+ years of experience in full-stack development, with expertise in cloud platforms, microservices architecture, and modern web frameworks. The ideal candidate will have experience with DevOps practices and team leadership."
        elif "interview question" in prompt.lower():
            text = "Describe a time when you had to refactor a complex legacy system. What approach did you take, and what were the results?"
        elif "outreach email" in prompt.lower():
            text = "Subject: Exciting Senior Engineer Opportunity at TechCorp\n\nDear [Student Name],\n\nWe are impressed by your background in full-stack development and cloud technologies. We would like to invite you to interview for our Senior Engineer position...\n\nBest regards,\nRecruiting Team"
        elif "score" in prompt.lower():
            text = "Based on the candidate's skills and experience, I rate this match at 82/100. The candidate has strong technical skills but may benefit from more leadership experience."
        else:
            text = "This is a mock response for the given prompt. In production, this would be replaced with actual LLM output."
        
        return {
            "completion": text,
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(text.split()),
            "total_tokens": len(prompt.split()) + len(text.split()),
            "model": self.model,
            "mock": True
        }
