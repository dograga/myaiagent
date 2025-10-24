"""
Quick test to verify FileHandler static methods work correctly
"""
from utils.file_handler import FileHandler
import base64

def test_validate_file_type():
    """Test file type validation"""
    print("Testing file type validation...")
    
    # Test image
    assert FileHandler.validate_file_type("test.png") == "image"
    assert FileHandler.validate_file_type("test.jpg") == "image"
    
    # Test PDF
    assert FileHandler.validate_file_type("test.pdf") == "pdf"
    
    # Test text
    assert FileHandler.validate_file_type("test.py") == "text"
    assert FileHandler.validate_file_type("test.txt") == "text"
    
    # Test unsupported
    try:
        FileHandler.validate_file_type("test.exe")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not supported" in str(e)
    
    print("✓ File type validation works!")

def test_save_and_cleanup():
    """Test saving and cleaning up temp files"""
    print("\nTesting save and cleanup...")
    
    # Create test content
    test_content = b"Hello, this is a test file!"
    filename = "test.txt"
    
    # Save temp file
    temp_path = FileHandler.save_temp_file(test_content, filename)
    print(f"  Created temp file: {temp_path}")
    
    # Verify file exists
    import os
    assert os.path.exists(temp_path), "Temp file should exist"
    
    # Verify content
    with open(temp_path, 'rb') as f:
        saved_content = f.read()
    assert saved_content == test_content, "Content should match"
    
    # Cleanup
    FileHandler.cleanup_temp_file(temp_path)
    assert not os.path.exists(temp_path), "Temp file should be deleted"
    
    print("✓ Save and cleanup works!")

def test_image_file():
    """Test image file handling"""
    print("\nTesting image file...")
    
    # Create minimal PNG
    png_data = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    
    # Validate type
    file_type = FileHandler.validate_file_type("test.png")
    assert file_type == "image"
    
    # Save
    temp_path = FileHandler.save_temp_file(png_data, "test.png")
    
    # Verify exists
    import os
    assert os.path.exists(temp_path)
    
    # Cleanup
    FileHandler.cleanup_temp_file(temp_path)
    
    print("✓ Image file handling works!")

def main():
    """Run all tests"""
    print("="*60)
    print("FileHandler Static Methods Test")
    print("="*60)
    
    try:
        test_validate_file_type()
        test_save_and_cleanup()
        test_image_file()
        
        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        print("\nThe FileHandler static methods are working correctly.")
        print("PNG and other image files should now work properly!")
        
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
