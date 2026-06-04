"""PDF ingestion and text extraction."""
from pathlib import Path
from typing import List, Tuple
import logging
import fitz

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF.
    """
    try:
        doc = fitz.open(pdf_path)

        text = ""
        for page in doc:
            text += page.get_text()

        logger.info(f"Successfully extracted text from {pdf_path}")
        return text

    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        raise


def extract_student_id_from_filename(filename: str) -> str:
    """
    Extract student ID from filename.
    
    Assumes format: synthetic_student_XX.pdf or similar
    """
    # Remove .pdf extension and extract ID part
    name_without_ext = Path(filename).stem
    return name_without_ext.replace("synthetic_", "").replace("student_", "")


def load_resumes_from_directory(directory: str) -> List[Tuple[str, str, str]]:
    """
    Load all resumes from a directory.
    
    Returns:
        List of (student_id, filename, text_content) tuples
    """
    directory_path = Path(directory)
    resumes = []
    
    if not directory_path.exists():
        logger.warning(f"Directory {directory} does not exist")
        return resumes
    
    for pdf_file in directory_path.glob("*.pdf"):
        try:
            student_id = extract_student_id_from_filename(pdf_file.name)
            text_content = extract_text_from_pdf(str(pdf_file))
            resumes.append((student_id, pdf_file.name, text_content))
            logger.info(f"Loaded resume for student {student_id}")
        except Exception as e:
            logger.error(f"Failed to load {pdf_file.name}: {str(e)}")
            continue
    
    return resumes
