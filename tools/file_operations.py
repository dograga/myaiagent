from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import os

class FileOperationInput(BaseModel):
    file_path: str = Field(..., description="Path to the file relative to the project root")
    content: Optional[str] = Field(None, description="Content to write to the file")

class FileOperations:
    def __init__(self, root_dir: str = ".", max_file_size_mb: int = 5):
        self.root_dir = os.path.abspath(root_dir)
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes

    def _get_absolute_path(self, file_path: str) -> str:
        """Convert relative path to absolute path within the project root."""
        return os.path.join(self.root_dir, file_path)

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read content from a file with size limit."""
        abs_path = self._get_absolute_path(file_path)
        try:
            # Check file size
            file_size = os.path.getsize(abs_path)
            if file_size > self.max_file_size:
                return {
                    "status": "error",
                    "message": f"File {file_path} is too large ({file_size / 1024 / 1024:.2f}MB). Maximum size is {self.max_file_size / 1024 / 1024}MB. Consider reading specific sections or using a different approach."
                }
            
            # Try to read as text
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # If not text, return error
                return {
                    "status": "error",
                    "message": f"File {file_path} appears to be binary. Cannot read binary files."
                }
            
            # Truncate very long content for display
            if len(content) > 50000:  # 50k characters
                content = content[:50000] + "\n\n[... content truncated due to length ...]"
            
            return {"status": "success", "content": content}
        except FileNotFoundError:
            return {"status": "error", "message": f"File {file_path} not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def write_file(self, file_path: str, content: str) -> Dict[str, str]:
        """Write content to a file. Creates the file if it doesn't exist."""
        abs_path = self._get_absolute_path(file_path)
        try:
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w') as f:
                f.write(content)
            return {"status": "success", "message": f"File {file_path} written successfully"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def append_to_file(self, file_path: str, content: str) -> Dict[str, str]:
        """Append content to a file."""
        abs_path = self._get_absolute_path(file_path)
        try:
            with open(abs_path, 'a') as f:
                f.write(content)
            return {"status": "success", "message": f"Content appended to {file_path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def delete_file(self, file_path: str) -> Dict[str, str]:
        """Delete a file."""
        abs_path = self._get_absolute_path(file_path)
        try:
            if os.path.exists(abs_path):
                os.remove(abs_path)
                return {"status": "success", "message": f"File {file_path} deleted"}
            return {"status": "error", "message": f"File {file_path} does not exist"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_directory(self, dir_path: str = ".") -> Dict[str, Any]:
        """List contents of a directory."""
        abs_path = self._get_absolute_path(dir_path)
        try:
            items = os.listdir(abs_path)
            return {"status": "success", "items": items}
        except Exception as e:
            return {"status": "error", "message": str(e)}
