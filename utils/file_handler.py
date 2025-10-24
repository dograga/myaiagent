"""
File handler utility for processing different file types
"""
import os
import base64
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import libraries with fallbacks
try:
    from vertexai.preview.generative_models import Image, Part
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class FileHandler:
    """Handles different file types for AI model input"""
    
    # Supported file extensions
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    PDF_EXTENSIONS = {'.pdf'}
    TEXT_EXTENSIONS = {'.txt', '.py', '.js', '.jsx', '.ts', '.tsx', '.json', 
                       '.md', '.yaml', '.yml', '.xml', '.html', '.css', '.java',
                       '.c', '.cpp', '.h', '.go', '.rs', '.sh', '.bash', '.sql',
                       '.env', '.config', '.ini', '.toml', '.log'}
    
    @staticmethod
    def validate_file_type(filename: str) -> str:
        """Validate and return file type (static method for backward compatibility)"""
        ext = Path(filename).suffix.lower()
        
        if ext in FileHandler.IMAGE_EXTENSIONS:
            return 'image'
        elif ext in FileHandler.PDF_EXTENSIONS:
            return 'pdf'
        elif ext in FileHandler.TEXT_EXTENSIONS:
            return 'text'
        else:
            raise ValueError(f"File type {ext} is not supported")
    
    @staticmethod
    def save_temp_file(content: bytes, filename: str) -> str:
        """Save file content to temp directory (static method)"""
        import tempfile
        import uuid
        
        # Create temp file with unique name
        temp_dir = tempfile.gettempdir()
        unique_filename = f"file_upload_{uuid.uuid4().hex}_{filename}"
        temp_path = os.path.join(temp_dir, unique_filename)
        
        # Write content
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        return temp_path
    
    @staticmethod
    def extract_pdf_text(file_path: str) -> str:
        """Extract text from PDF file (static method)"""
        if not PDF_SUPPORT:
            return f"[PDF file] - PDF support not available. Please install PyPDF2."
        
        try:
            text_content = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(f"\n--- Page {page_num + 1} ---\n")
                    text_content.append(page.extract_text())
            
            return ''.join(text_content)
        except Exception as e:
            return f"[PDF file] - Error reading PDF: {str(e)}"
    
    @staticmethod
    def cleanup_temp_file(file_path: str) -> None:
        """Delete temporary file (static method)"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting temp file {file_path}: {e}")
    
    def __init__(self, temp_dir: str = None):
        """Initialize file handler with temp directory"""
        if temp_dir is None:
            # Create temp directory in project root
            project_root = Path(__file__).parent.parent
            temp_dir = project_root / "temp"
        
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        ext = Path(filename).suffix.lower()
        
        if ext in self.IMAGE_EXTENSIONS:
            return 'image'
        elif ext in self.PDF_EXTENSIONS:
            return 'pdf'
        elif ext in self.TEXT_EXTENSIONS:
            return 'text'
        else:
            return 'unknown'
    
    def save_temp_file(self, filename: str, content: str) -> Path:
        """
        Save file content to temp directory
        Content is expected to be base64 encoded for binary files or plain text
        """
        file_path = self.temp_dir / filename
        
        # Try to decode as base64 first (for binary files)
        try:
            file_data = base64.b64decode(content)
            with open(file_path, 'wb') as f:
                f.write(file_data)
        except Exception:
            # If base64 decode fails, save as text
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return file_path
    
    def read_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        if not PDF_SUPPORT:
            return f"[PDF file: {file_path.name}] - PDF support not available. Please install PyPDF2."
        
        try:
            text_content = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(f"\n--- Page {page_num + 1} ---\n")
                    text_content.append(page.extract_text())
            
            return ''.join(text_content)
        except Exception as e:
            return f"[PDF file: {file_path.name}] - Error reading PDF: {str(e)}"
    
    def load_image_part(self, file_path: Path) -> Optional[Any]:
        """Load image as Vertex AI Part for model input"""
        if not VERTEX_AI_AVAILABLE:
            return None
        
        try:
            image = Image.load_from_file(str(file_path))
            return Part.from_image(image)
        except Exception as e:
            print(f"Error loading image {file_path}: {e}")
            return None
    
    def process_file(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Process a file and return appropriate format for AI model
        
        Returns:
            dict with keys:
                - type: 'text', 'image', 'pdf'
                - content: text content or None for images
                - file_path: path to saved file
                - part: Vertex AI Part object for images (if available)
        """
        file_type = self.get_file_type(filename)
        
        # Save file to temp directory
        file_path = self.save_temp_file(filename, content)
        
        result = {
            'type': file_type,
            'filename': filename,
            'file_path': str(file_path),
            'content': None,
            'part': None
        }
        
        if file_type == 'image':
            # For images, create Vertex AI Part
            result['part'] = self.load_image_part(file_path)
            result['content'] = f"[Image: {filename}]"
        
        elif file_type == 'pdf':
            # For PDFs, extract text
            result['content'] = self.read_pdf(file_path)
        
        elif file_type == 'text':
            # For text files, read content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result['content'] = f.read()
            except Exception as e:
                result['content'] = f"[Error reading {filename}: {str(e)}]"
        
        else:
            result['content'] = f"[Unsupported file type: {filename}]"
        
        return result
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """Clean up old temporary files"""
        import time
        current_time = time.time()
        
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (max_age_hours * 3600):
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
    
    def format_for_model(self, processed_files: List[Dict[str, Any]], query: str) -> tuple:
        """
        Format processed files for model input
        
        Returns:
            tuple: (formatted_query, image_parts)
                - formatted_query: text query with file contents
                - image_parts: list of Vertex AI Part objects for images
        """
        image_parts = []
        text_parts = [query]
        
        if processed_files:
            text_parts.append("\n\n**Attached Files:**\n")
            
            for file_info in processed_files:
                if file_info['type'] == 'image' and file_info['part']:
                    # Collect image parts separately
                    image_parts.append(file_info['part'])
                    text_parts.append(f"\n[Image: {file_info['filename']}]")
                
                elif file_info['content']:
                    # Add text content
                    text_parts.append(f"\n--- File: {file_info['filename']} ---\n")
                    text_parts.append(file_info['content'])
                    text_parts.append("\n")
        
        formatted_query = ''.join(text_parts)
        return formatted_query, image_parts


# Global file handler instance
file_handler = FileHandler()
