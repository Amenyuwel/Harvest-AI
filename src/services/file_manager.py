# file_manager.py - Single Responsibility: Handle file operations
import os
from ..interfaces import IFileManager

class FileManager(IFileManager):
    """Service for file management operations"""
    
    def __init__(self, temp_folder: str):
        self.temp_folder = temp_folder
        os.makedirs(temp_folder, exist_ok=True)
    
    def save_temp_file(self, file, filename: str) -> str:
        """Save uploaded file temporarily"""
        temp_path = os.path.join(self.temp_folder, filename)
        file.save(temp_path)
        return temp_path
    
    def read_file_bytes(self, file_path: str) -> bytes:
        """Read file as bytes"""
        with open(file_path, 'rb') as f:
            return f.read()
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(file_path)
    
    def move_file(self, source: str, destination: str):
        """Move file from source to destination"""
        import shutil
        shutil.move(source, destination)
