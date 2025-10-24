"""
Test script for file attachment feature.
This script tests the file handler utility and backend integration.
"""

import base64
import os
from utils.file_handler import FileHandler

def test_file_validation():
    """Test file type validation."""
    print("Testing file type validation...")
    
    # Test valid files
    assert FileHandler.validate_file_type("test.txt") == "text"
    assert FileHandler.validate_file_type("test.py") == "text"
    assert FileHandler.validate_file_type("test.pdf") == "pdf"
    assert FileHandler.validate_file_type("test.jpg") == "image"
    assert FileHandler.validate_file_type("test.png") == "image"
    
    # Test invalid files
    try:
        FileHandler.validate_file_type("test.exe")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not supported" in str(e).lower()
    
    print("✓ File validation tests passed")

def test_temp_file_operations():
    """Test temp file save and cleanup."""
    print("\nTesting temp file operations...")
    
    # Create test content
    test_content = b"Hello, this is a test file!"
    filename = "test.txt"
    
    # Save temp file
    temp_path = FileHandler.save_temp_file(test_content, filename)
    print(f"  Created temp file: {temp_path}")
    
    # Verify file exists and has correct content
    assert os.path.exists(temp_path), "Temp file should exist"
    with open(temp_path, 'rb') as f:
        saved_content = f.read()
    assert saved_content == test_content, "Content should match"
    
    # Cleanup
    FileHandler.cleanup_temp_file(temp_path)
    assert not os.path.exists(temp_path), "Temp file should be deleted"
    
    print("✓ Temp file operations tests passed")

def test_pdf_extraction():
    """Test PDF text extraction (if PyPDF2 is available)."""
    print("\nTesting PDF text extraction...")
    
    try:
        import PyPDF2
        
        # Create a simple PDF for testing
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        import io
        
        # Create PDF in memory
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Test PDF Content")
        c.drawString(100, 730, "This is a test document.")
        c.save()
        
        # Save to temp file
        pdf_content = buffer.getvalue()
        temp_path = FileHandler.save_temp_file(pdf_content, "test.pdf")
        
        # Extract text
        text = FileHandler.extract_pdf_text(temp_path)
        print(f"  Extracted text: {text[:100]}...")
        
        assert "Test PDF Content" in text or "test" in text.lower(), "Should extract text from PDF"
        
        # Cleanup
        FileHandler.cleanup_temp_file(temp_path)
        
        print("✓ PDF extraction tests passed")
    except ImportError as e:
        print(f"⚠ Skipping PDF tests (missing dependency: {e})")

def test_base64_encoding():
    """Test base64 encoding/decoding workflow."""
    print("\nTesting base64 encoding workflow...")
    
    # Simulate frontend encoding
    original_content = "This is a test file content with special chars: 你好 🎉"
    encoded = base64.b64encode(original_content.encode('utf-8')).decode('utf-8')
    
    # Simulate backend decoding
    decoded_bytes = base64.b64decode(encoded)
    decoded_content = decoded_bytes.decode('utf-8')
    
    assert decoded_content == original_content, "Content should match after encoding/decoding"
    
    print("✓ Base64 encoding tests passed")

def test_image_file():
    """Test image file handling."""
    print("\nTesting image file handling...")
    
    # Create a simple 1x1 pixel PNG
    import struct
    
    # Minimal PNG file (1x1 red pixel)
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    
    # Save and verify
    temp_path = FileHandler.save_temp_file(png_data, "test.png")
    assert os.path.exists(temp_path), "Image file should be saved"
    
    # Verify file type
    file_type = FileHandler.validate_file_type("test.png")
    assert file_type == "image", "Should detect as image"
    
    # Cleanup
    FileHandler.cleanup_temp_file(temp_path)
    
    print("✓ Image file tests passed")

def main():
    """Run all tests."""
    print("=" * 60)
    print("File Attachment Feature Tests")
    print("=" * 60)
    
    try:
        test_file_validation()
        test_temp_file_operations()
        test_base64_encoding()
        test_image_file()
        test_pdf_extraction()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
