import logging
import shutil
from pathlib import Path
from typing import Optional
from .settings import settings

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self) -> None:
        self.base_path = settings.FILES_BASE_PATH
        self.output_path = settings.OUTPUT_BASE_PATH
    
    def ensure_directories(self) -> None:
        """
        Ensures reading and writing directories exist.
        """
        if not self.output_path.exists():
            logger.info(f"Creating output directory: {self.output_path}")
            self.output_path.mkdir(parents=True, exist_ok=True)
            
    def resolve_path(self, relative_path: str) -> Path:
        """
        Resolves a relative path (from DB) to an absolute path on the filesystem.
        """
        # Cleanup path if it starts with / or ./
        clean_path = relative_path.lstrip("/").lstrip("./")
        full_path = self.base_path / clean_path
        return full_path

    def get_output_dir(self, doc_source_id: str, question_id: str) -> Path:
        """
        Returns the specific directory for a question's outputs.
        Creates it if it doesn't exist.
        """
        # Sanitize IDs to be safe directory names
        safe_doc_id = "".join(c for c in str(doc_source_id) if c.isalnum() or c in ('-', '_'))
        safe_q_id = "".join(c for c in str(question_id) if c.isalnum() or c in ('-', '_'))
        
        path = self.output_path / safe_doc_id / safe_q_id
        path.mkdir(parents=True, exist_ok=True)
        return path

file_manager = FileManager()
