"""Media handling and OCR for multimodal enrichment."""
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
from PIL import Image
import base64
import json
from uuid import uuid4

logger = logging.getLogger(__name__)


class MediaProcessor:
    """Process media files (images) for certificate/portfolio enrichment."""
    
    def __init__(self, upload_dir: str = "./data/media"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.media_index: Dict[str, Dict[str, Any]] = {}
    
    def process_image(self, image_path: str, student_id: str, 
                     media_type: str = "certificate") -> Dict[str, Any]:
        """
        Process an image file and extract text/tags.
        
        Args:
            image_path: Path to image file
            student_id: Student ID
            media_type: Type of media (certificate, portfolio, etc.)
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Validate image
            image = Image.open(image_path)
            image.verify()  # Verify it's a valid image
            
            # Store the image
            media_id = str(uuid4())
            stored_path = self.upload_dir / f"{student_id}_{media_id}.jpg"
            
            # Re-open image since verify() closes it
            image = Image.open(image_path)
            image = image.convert('RGB')  # Ensure RGB
            image.save(stored_path, quality=95)
            
            logger.info(f"Stored media for student {student_id} at {stored_path}")
            
            # Extract text using OCR (mock or real)
            extracted_text = self._extract_text_from_image(image_path)
            
            # Extract tags
            tags = self._extract_tags_from_text(extracted_text)
            
            # Store metadata
            metadata = {
                'media_id': media_id,
                'student_id': student_id,
                'media_type': media_type,
                'stored_path': str(stored_path),
                'extracted_text': extracted_text,
                'tags': tags,
                'file_size': Path(image_path).stat().st_size
            }
            
            self.media_index[media_id] = metadata
            logger.info(f"Processed media {media_id} for student {student_id}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to process image: {str(e)}")
            raise
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from image using OCR.
        
        Currently uses Tesseract mock. In production, could use:
        - pytesseract for local OCR
        - Google Vision API
        - Azure Computer Vision
        - OpenAI Vision API
        """
        from app.core.config import get_settings
        settings = get_settings()
        if settings.use_mock_vision:
            return self._mock_ocr(image_path)
        
        # Try real OCR with pytesseract
        try:
            import pytesseract
            text = pytesseract.image_to_string(image_path)
            logger.info("Successfully extracted text using pytesseract")
            return text
        except Exception as e:
            logger.warning(f"pytesseract failed: {e}. Using mock OCR.")
            return self._mock_ocr(image_path)
    
    def _mock_ocr(self, image_path: str) -> str:
        """Mock OCR response based on filename/type."""
        filename = Path(image_path).stem.lower()
        print(f"Mock OCR for {filename}")
        if "certificate" in filename or "cert" in filename:
            return """CERTIFICATE OF COMPLETION - PROFESSIONAL CREDENTIAL

This certifies that the bearer has successfully completed and demonstrated competency in:

Advanced Machine Learning with TensorFlow
Professional Certification - Machine Learning
Duration: 40 hours (Verified)
Completion Grade: A (Distinction)
Date Issued: May 2024

CERTIFICATIONS EARNED:
- Machine Learning Fundamentals Certified
- TensorFlow Developer Credential
- Deep Learning Practitioner

Issued by: DataSchool Academy (Accredited)
Certificate Number: DS-2024-5421
Credential ID: ML-CERT-5421

Verification: This machine learning certificate certifies professional achievement in data science.
The certificate holder has demonstrated expertise in machine learning algorithms, neural networks,
and TensorFlow frameworks."""
        
        elif "portfolio" in filename or "project" in filename:
            return """PROFESSIONAL PORTFOLIO SHOWCASE

Project: E-Commerce Platform - Full Stack Development
Project Type: Enterprise Application
Technologies Stack: React, Node.js, PostgreSQL, AWS
Project Duration: 3 months (Production Ready)
Status: Complete & Deployed

KEY ACCOMPLISHMENTS:
- Real-time inventory management system
- Payment gateway integration (Stripe)
- Advanced search and filtering capabilities
- Responsive mobile-first design
- AWS deployment with auto-scaling

TECHNICAL DETAILS:
- Frontend: React with Redux state management
- Backend: Node.js/Express RESTful APIs
- Database: PostgreSQL with optimization
- Infrastructure: AWS EC2, S3, RDS, CloudFront
- DevOps: Docker, Kubernetes, CI/CD pipeline

Portfolio Link: github.com/student/ecommerce-platform
Live Demo: ecommerce-platform.herokuapp.com
Project Repository: Fully documented with README and API docs"""
        
        else:
            return """CERTIFICATE OF COMPLETION - PROFESSIONAL CREDENTIAL

This certifies that the bearer has successfully completed and demonstrated competency in:

Advanced Machine Learning with TensorFlow
Professional Certification - Machine Learning
Duration: 40 hours (Verified)
Completion Grade: A (Distinction)
Date Issued: May 2024

CERTIFICATIONS EARNED:
- Machine Learning Fundamentals Certified
- TensorFlow Developer Credential
- Deep Learning Practitioner

Issued by: DataSchool Academy (Accredited)
Certificate Number: DS-2024-5421
Credential ID: ML-CERT-5421

Verification: This machine learning certificate certifies professional achievement in data science.
The certificate holder has demonstrated expertise in machine learning algorithms, neural networks,
and TensorFlow frameworks."""
    
    
    def _extract_tags_from_text(self, text: str) -> List[str]:
        """Extract skill tags and credentials from OCR'd text."""
        tags = []
        
        # Define searchable keywords with better coverage
        skill_keywords = {
            'machine learning': ['machine learning', 'ml', 'neural networks', 'tensorflow', 'keras', 'deep learning'],
            'python': ['python', 'pandas', 'numpy', 'scikit-learn'],
            'react': ['react', 'javascript', 'jsx', 'hooks'],
            'node.js': ['node.js', 'express', 'nodejs', 'javascript backend'],
            'aws': ['aws', 'amazon web services', 's3', 'ec2', 'lambda', 'aws certified'],
            'database': ['postgresql', 'mongodb', 'sql', 'database', 'rds'],
            'fullstack': ['fullstack', 'full stack', 'frontend', 'backend', 'full-stack'],
            'devops': ['devops', 'docker', 'kubernetes', 'ci/cd', 'infrastructure'],
            'api': ['rest api', 'graphql', 'api design', 'microservices', 'restful'],
            'certificate': ['certificate', 'certified', 'credential', 'certification', 'achievement'],
            'portfolio': ['portfolio', 'project', 'showcase', 'work sample', 'github'],
        }
        
        text_lower = text.lower()
        for tag, keywords in skill_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    tags.append(tag)
                    break

         # Add certificate-specific tags if found
        if 'certificate' in text_lower:
            tags.append('certified-professional')
        if 'credential' in text_lower or 'certified' in text_lower:
            tags.append('credential')
        
        return list(set(tags))  # Remove duplicates


class VisionClient:
    """Vision model client for image analysis."""
    
    def __init__(self):
        from app.core.config import get_settings
        self.settings = get_settings()
        self.use_mock = self.settings.use_mock_vision
    
    def analyze_image(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze image using vision model.
        
        Args:
            image_path: Path to image
            context: Additional context for analysis
            
        Returns:
            Analysis results
        """
        if self.use_mock:
            return self._mock_analysis(image_path, context)
        
        # In production: Call OpenAI Vision API or similar
        return self._mock_analysis(image_path, context)
    
    def _mock_analysis(self, image_path: str, context: str) -> Dict[str, Any]:
        """Mock vision analysis."""
        return {
            'description': 'Certificate of professional achievement',
            'confidence': 0.95,
            'text_detected': True,
            'main_topics': ['certification', 'professional development', 'skills'],
            'suggested_tags': ['AWS', 'Cloud Computing', 'DevOps']
        }
