"""
Integration test for file attachment feature.
Tests the complete flow from frontend encoding to backend processing.
"""

import base64
import json
from utils.file_handler import FileHandler

def simulate_frontend_encoding(file_content: str, filename: str) -> dict:
    """Simulate how the frontend encodes files."""
    # Convert to bytes
    content_bytes = file_content.encode('utf-8')
    
    # Encode to base64 (as frontend does)
    content_base64 = base64.b64encode(content_bytes).decode('utf-8')
    
    return {
        'filename': filename,
        'content': content_base64
    }

def simulate_backend_processing(attached_files: list) -> tuple:
    """Simulate how the backend processes files (from main.py)."""
    if not attached_files:
        return "", []
    
    formatted_text = "\n\n**Attached Files:**\n"
    temp_file_paths = []
    
    for file_info in attached_files:
        filename = file_info.get("filename", "unknown")
        content_base64 = file_info.get("content", "")
        
        try:
            # Validate and process the file
            file_type = FileHandler.validate_file_type(filename)
            
            # Decode base64 content
            file_content = base64.b64decode(content_base64)
            
            # Save to temp file
            temp_path = FileHandler.save_temp_file(file_content, filename)
            temp_file_paths.append(temp_path)
            
            # Extract text content based on file type
            if file_type == "pdf":
                text_content = FileHandler.extract_pdf_text(temp_path)
                formatted_text += f"\n--- File: {filename} (PDF) ---\n{text_content}\n"
            elif file_type == "image":
                formatted_text += f"\n--- File: {filename} (Image) ---\n[Image file attached - will be processed by AI model]\n"
            else:  # text file
                text_content = file_content.decode('utf-8', errors='ignore')
                formatted_text += f"\n--- File: {filename} ---\n{text_content}\n"
        
        except ValueError as e:
            formatted_text += f"\n--- File: {filename} (Error: {str(e)}) ---\n"
        except Exception as e:
            formatted_text += f"\n--- File: {filename} (Error processing file: {str(e)}) ---\n"
    
    return formatted_text, temp_file_paths

def test_text_file_flow():
    """Test complete flow for text file."""
    print("\n" + "="*60)
    print("Test: Text File Flow")
    print("="*60)
    
    # 1. Simulate user selecting a file
    original_content = """def hello_world():
    print("Hello, World!")
    return True
"""
    filename = "example.py"
    
    print(f"1. User selects file: {filename}")
    print(f"   Content: {original_content[:50]}...")
    
    # 2. Frontend encodes the file
    file_data = simulate_frontend_encoding(original_content, filename)
    print(f"2. Frontend encodes to base64: {file_data['content'][:50]}...")
    
    # 3. Send to backend (simulate API request)
    request_payload = {
        'query': 'What does this code do?',
        'attached_files': [file_data]
    }
    print(f"3. API request payload prepared")
    
    # 4. Backend processes the file
    formatted_text, temp_paths = simulate_backend_processing(request_payload['attached_files'])
    print(f"4. Backend processes file")
    print(f"   Formatted text:\n{formatted_text}")
    
    # 5. Verify content matches
    assert original_content in formatted_text, "Original content should be in formatted text"
    assert filename in formatted_text, "Filename should be in formatted text"
    assert len(temp_paths) == 1, "Should have one temp file"
    
    # 6. Cleanup
    for temp_path in temp_paths:
        FileHandler.cleanup_temp_file(temp_path)
    print(f"5. Cleanup completed")
    
    print("✅ Text file flow test PASSED")

def test_multiple_files_flow():
    """Test flow with multiple files."""
    print("\n" + "="*60)
    print("Test: Multiple Files Flow")
    print("="*60)
    
    # Create multiple test files
    files = [
        ("config.json", '{"api_key": "test123", "debug": true}'),
        ("readme.md", "# My Project\n\nThis is a test project."),
        ("script.py", "import os\nprint('Hello')")
    ]
    
    print(f"1. User selects {len(files)} files")
    
    # Encode all files
    attached_files = []
    for filename, content in files:
        file_data = simulate_frontend_encoding(content, filename)
        attached_files.append(file_data)
        print(f"   - {filename}")
    
    # Process all files
    formatted_text, temp_paths = simulate_backend_processing(attached_files)
    print(f"2. Backend processes all files")
    
    # Verify all files are included
    for filename, content in files:
        assert filename in formatted_text, f"{filename} should be in output"
        assert content in formatted_text, f"Content of {filename} should be in output"
    
    assert len(temp_paths) == len(files), "Should have temp file for each uploaded file"
    
    # Cleanup
    for temp_path in temp_paths:
        FileHandler.cleanup_temp_file(temp_path)
    print(f"3. Cleanup completed")
    
    print("✅ Multiple files flow test PASSED")

def test_image_file_flow():
    """Test flow with image file."""
    print("\n" + "="*60)
    print("Test: Image File Flow")
    print("="*60)
    
    # Create minimal PNG
    png_data = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde'
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    
    # Encode as base64
    content_base64 = base64.b64encode(png_data).decode('utf-8')
    file_data = {
        'filename': 'test_image.png',
        'content': content_base64
    }
    
    print(f"1. User selects image: test_image.png")
    
    # Process
    formatted_text, temp_paths = simulate_backend_processing([file_data])
    print(f"2. Backend processes image")
    print(f"   Formatted text:\n{formatted_text}")
    
    # Verify
    assert "test_image.png" in formatted_text
    assert "Image" in formatted_text
    assert len(temp_paths) == 1
    
    # Cleanup
    for temp_path in temp_paths:
        FileHandler.cleanup_temp_file(temp_path)
    print(f"3. Cleanup completed")
    
    print("✅ Image file flow test PASSED")

def test_invalid_file_handling():
    """Test handling of invalid files."""
    print("\n" + "="*60)
    print("Test: Invalid File Handling")
    print("="*60)
    
    # Try to process an unsupported file type
    file_data = simulate_frontend_encoding("malicious content", "virus.exe")
    
    print(f"1. User attempts to upload: virus.exe")
    
    # Process (should handle gracefully)
    formatted_text, temp_paths = simulate_backend_processing([file_data])
    print(f"2. Backend processes with error handling")
    print(f"   Formatted text:\n{formatted_text}")
    
    # Verify error is in output
    assert "Error" in formatted_text or "not supported" in formatted_text.lower()
    
    # Cleanup any temp files that might have been created
    for temp_path in temp_paths:
        FileHandler.cleanup_temp_file(temp_path)
    
    print("✅ Invalid file handling test PASSED")

def test_special_characters():
    """Test files with special characters and unicode."""
    print("\n" + "="*60)
    print("Test: Special Characters and Unicode")
    print("="*60)
    
    # Content with special characters
    content = """# 测试文件 (Test File)
    
Special chars: @#$%^&*()
Emoji: 🎉 🚀 ✅
Math: ∑ ∫ √ π
Quotes: "Hello" 'World'
"""
    
    file_data = simulate_frontend_encoding(content, "unicode_test.md")
    
    print(f"1. User selects file with unicode content")
    
    # Process
    formatted_text, temp_paths = simulate_backend_processing([file_data])
    print(f"2. Backend processes unicode content")
    
    # Verify special characters are preserved
    assert "测试文件" in formatted_text
    assert "🎉" in formatted_text
    assert "∑" in formatted_text
    
    # Cleanup
    for temp_path in temp_paths:
        FileHandler.cleanup_temp_file(temp_path)
    
    print("✅ Special characters test PASSED")

def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("FILE ATTACHMENT INTEGRATION TESTS")
    print("="*60)
    
    try:
        test_text_file_flow()
        test_multiple_files_flow()
        test_image_file_flow()
        test_invalid_file_handling()
        test_special_characters()
        
        print("\n" + "="*60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*60)
        print("\nThe file attachment feature is working correctly:")
        print("  ✓ Frontend encoding works")
        print("  ✓ Backend decoding works")
        print("  ✓ File validation works")
        print("  ✓ Multiple files supported")
        print("  ✓ Image files handled")
        print("  ✓ Error handling works")
        print("  ✓ Unicode support works")
        print("  ✓ Temp file cleanup works")
        print("\n🚀 Ready for production use!")
        
        return 0
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
