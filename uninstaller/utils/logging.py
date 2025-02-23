from pathlib import Path
import re
from datetime import datetime
from ..config.settings import Settings

class SecureLogger:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.log_file = self._setup_log_file()
        self.log_size = 0

    def _setup_log_file(self) -> Path:
        """Setup secure log file"""
        log_dir = self.settings.LOG_DIR
        log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Cleanup old logs
        for old_log in log_dir.glob('*.log'):
            if old_log.stat().st_mtime < (datetime.now().timestamp() - 86400):
                old_log.unlink()
        
        random_suffix = secrets.token_hex(8)
        log_file = log_dir / f"uninstaller_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random_suffix}.log"
        return log_file

    def log(self, message: str, level: str = 'INFO') -> None:
        """Log message securely"""
        if self.log_size > self.settings.MAX_LOG_SIZE:
            return
            
        sanitized = self._sanitize_message(message)
        log_entry = f"{datetime.now().isoformat()} - {level} - {sanitized}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            self.log_size += len(log_entry)
        except Exception:
            pass

    def _sanitize_message(self, message: str) -> str:
        """Remove sensitive information from messages"""
        message = re.sub(r'[A-Za-z]:\\[^\s]*', '[PATH]', message)
        message = re.sub(r'HKEY_[^\s]*', '[REGISTRY]', message)
        message = re.sub(r'PID \d+', '[PID]', message)
        return message
