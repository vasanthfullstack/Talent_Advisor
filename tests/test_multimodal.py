"""Test suite for multimodal enrichment."""
import pytest
import tempfile
from pathlib import Path
from PIL import Image
from app.multimodal.media import MediaProcessor
from app.multimodal.enrichment import MultimodalEnrichment


@pytest.fixture
def test_image_file():
    """Create a temporary test image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(tmp.name)
        yield tmp.name
        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)


@pytest.fixture
def invalid_image_file():
    """Create an invalid image file."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(b"This is not an image")
        tmp.flush()
        yield tmp.name
        Path(tmp.name).unlink(missing_ok=True)


@pytest.fixture
def media_processor():
    """Create media processor instance."""
    return MediaProcessor()


def test_image_processing_success(media_processor, test_image_file):
    """Test successful image processing."""
    result = media_processor.process_image(
        image_path=test_image_file,
        student_id="student_001",
        media_type="certificate"
    )
    
    assert result
    assert result["media_id"]
    assert result["student_id"] == "student_001"
    assert result["media_type"] == "certificate"
    assert result["extracted_text"]
    assert isinstance(result["tags"], list)
    print(f"✓ Image processing success test passed")
    print(f"  - Media ID: {result['media_id']}")
    print(f"  - Tags: {result['tags']}")


def test_image_processing_invalid_file(media_processor, invalid_image_file):
    """Test unhappy path: invalid image file."""
    with pytest.raises(Exception):
        media_processor.process_image(
            image_path=invalid_image_file,
            student_id="student_001",
            media_type="certificate"
        )
    
    print("✓ Invalid image file test passed (correctly raised exception)")


def test_ocr_text_extraction(media_processor):
    """Test OCR text extraction."""
    from app.core.config import Settings
    from unittest.mock import patch
    
    # Test with mock OCR
    text = media_processor._mock_ocr("test_certificate.png")
    
    assert text
    assert len(text) > 0
    print(f"✓ OCR text extraction test passed")
    print(f"  - Extracted text sample: {text[:80]}...")


def test_skill_tag_extraction(media_processor):
    """Test skill tag extraction from text."""
    text = """
    AWS Certified Solutions Architect
    Expertise in:
    - Machine Learning with TensorFlow
    - React and Node.js development
    - Kubernetes and Docker
    - Python programming
    """
    
    tags = media_processor._extract_tags_from_text(text)
    
    assert "python" in tags or len(tags) > 0
    assert isinstance(tags, list)
    print(f"✓ Skill tag extraction test passed: Found {len(tags)} tags")
    print(f"  - Tags: {tags}")


def test_multimodal_enrichment_success(test_image_file):
    """Test end-to-end multimodal enrichment (success path)."""
    enrichment = MultimodalEnrichment()
    
    result = enrichment.enrich_student_profile(
        image_path=test_image_file,
        student_id="student_001",
        media_type="certificate",
        description="AWS Solutions Architect Certification"
    )
    
    assert result["success"]
    assert result["media_id"]
    assert result["student_id"] == "student_001"
    assert result["chunks_created"] > 0
    assert isinstance(result["tags"], list)
    print(f"✓ Multimodal enrichment success test passed")
    print(f"  - Chunks created: {result['chunks_created']}")
    print(f"  - Tags: {result['tags']}")


def test_multimodal_enrichment_failure():
    """Test unhappy path: enrichment with nonexistent file."""
    enrichment = MultimodalEnrichment()
    
    result = enrichment.enrich_student_profile(
        image_path="/nonexistent/path/image.png",
        student_id="student_001",
        media_type="certificate"
    )
    
    assert not result["success"]
    assert "error" in result
    print("✓ Multimodal enrichment failure test passed (correctly handled error)")


if __name__ == "__main__":
    # Create test image manually
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img = Image.new('RGB', (100, 100), color='red')
        img.save(tmp.name)
        test_path = tmp.name
    
    processor = MediaProcessor()
    
    try:
        test_image_processing_success(processor, test_path)
        test_ocr_text_extraction(processor)
        test_skill_tag_extraction(processor)
        test_multimodal_enrichment_success(test_path)
        test_multimodal_enrichment_failure()
        print("\n✅ All multimodal tests passed!")
    finally:
        Path(test_path).unlink(missing_ok=True)
