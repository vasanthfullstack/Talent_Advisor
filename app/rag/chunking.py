"""Text chunking and preprocessing."""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """Text chunking with overlap."""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Full text to chunk
            metadata: Metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []
        text = text.strip()
        
        # Split by sentences/paragraphs for better semantics
        sentences = text.replace('\n', ' ').split('. ')
        current_chunk = ""
        chunk_id = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunk_data = {
                        "chunk_id": f"{metadata.get('student_id', 'unknown')}_chunk_{chunk_id}",
                        "content": current_chunk.strip(),
                        "metadata": {
                            **metadata,
                            "chunk_index": chunk_id,
                            "chunk_size": len(current_chunk)
                        }
                    }
                    chunks.append(chunk_data)
                    chunk_id += 1
                    # Keep overlap
                    current_chunk = sentence + ". " if len(sentence) < self.chunk_size else ""
                else:
                    # Handle case where single sentence is too long
                    current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunk_data = {
                "chunk_id": f"{metadata.get('student_id', 'unknown')}_chunk_{chunk_id}",
                "content": current_chunk.strip(),
                "metadata": {
                    **metadata,
                    "chunk_index": chunk_id,
                    "chunk_size": len(current_chunk)
                }
            }
            chunks.append(chunk_data)
        
        logger.info(f"Created {len(chunks)} chunks for student {metadata.get('student_id', 'unknown')}")
        return chunks


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extract skill tags from resume text.
    
    This is a simple heuristic; can be enhanced with NLP.
    """
    common_skills = [
        'python', 'java', 'javascript', 'typescript', 'sql', 'mongodb',
        'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git',
        'machine learning', 'deep learning', 'nlp', 'computer vision',
        'data analysis', 'statistics', 'pandas', 'numpy', 'scikit-learn',
        'agile', 'scrum', 'rest api', 'graphql', 'microservices',
        'ci/cd', 'jenkins', 'gitlab', 'github', 'devops'
    ]
    
    text_lower = text.lower()
    found_skills = [skill for skill in common_skills if skill in text_lower]
    return list(set(found_skills))  # Remove duplicates
