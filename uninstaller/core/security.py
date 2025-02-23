import re
import os
from pathlib import Path
from typing import Optional
from ..config.settings import Settings

class SecurityManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        
    def validate_program_id(self, program_id: str) -> bool:
        """Validate program ID format"""
        return bool(re.match(
            r'^[{]?[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}[}]?$',
            program_id
        ))
    
    def validate_path(self, path: str) -> bool:
        """Validate file path"""
        if not path or len(path) > self.settings.MAX_PATH_LENGTH:
            return False
            
        try:
            path = os.path.normpath(path)
            return not os.path.isabs(path) and '..' not in path
        except Exception:
            return False
            
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename"""
        return re.sub(r'[^a-zA-Z0-9\-_\.]', '_', filename)
    
    def secure_path(self, base: Path, *parts: str) -> Optional[Path]:
        """Create secure path"""
        try:
            path = base
            for part in parts:
                sanitized = self.sanitize_filename(part)
                path = path / sanitized
            return path
        except Exception:
            return None
