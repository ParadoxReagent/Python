import multiprocessing
from pathlib import Path

class Settings:
    # Timeouts and Limits
    UNINSTALL_TIMEOUT = 300
    PROCESS_TIMEOUT = 60
    CACHE_TTL = 300
    MAX_RETRIES = 3
    
    # Performance
    THREAD_POOL_SIZE = multiprocessing.cpu_count() * 2
    IO_THREAD_POOL_SIZE = 4
    MAX_CONCURRENT_UNINSTALLS = 10
    CHUNK_SIZE = 5
    
    # Security
    MAX_PROGRAM_NAME_LENGTH = 256
    SECURE_UMASK = 0o077
    MAX_PATH_LENGTH = 260
    MAX_LOG_SIZE = 10 * 1024 * 1024
    
    # Paths
    BASE_DIR = Path.home() / "Documents" / "Python" / "uninstaller"
    LOG_DIR = BASE_DIR / "logs"
    
    # Registry
    REGISTRY_UNINSTALL_PATHS = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
