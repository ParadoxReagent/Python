import asyncio
import ctypes
import subprocess
import sys
import platform
from typing import List, Optional, Dict, Tuple, Set, Any
import psutil
import win32com.client
import winreg
import re
import logging
import hashlib
from pathlib import Path
from datetime import datetime
import secrets
import os
from functools import wraps
import tempfile
from contextlib import contextmanager
import string
import cachetools
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import functools
import time

# Remove unused imports
# win32api, win32con, tqdm, signal, shlex are not used directly

# Constants
UNINSTALL_TIMEOUT = 300  # seconds
COLUMNS_PER_ROW = 3
MAX_CONCURRENT_UNINSTALLS = 10
MAX_PROGRAM_NAME_LENGTH = 256
MAX_RETRIES = 3
SECURE_UMASK = 0o077

# Secure WMIC commands with input validation
WMIC_CSV_COMMAND = ['wmic', 'product', 'where', 'not name=""', 'get', 'name,identifyingnumber', '/format:csv']
WMIC_UNINSTALL_BASE = 'wmic product where "IdentifyingNumber=\'{}\'" call uninstall /nointeractive'

# Additional constants
REGISTRY_UNINSTALL_PATHS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
]
MAX_MEMORY_PERCENT = 75
CHUNK_SIZE = 5
TEMP_DIR_PREFIX = 'uninstaller_'
PROCESS_TIMEOUT = 60
MAX_PATH_LENGTH = 260
ALLOWED_CHARS = set(string.ascii_letters + string.digits + ' -_.()')
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB

# Additional performance constants
CACHE_TTL = 300  # 5 minutes
CACHE_SIZE = 1000
THREAD_POOL_SIZE = multiprocessing.cpu_count() * 2
CHUNK_SIZE = 5
IO_THREAD_POOL_SIZE = 4

# Performance-optimized cache
program_cache = cachetools.TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)
thread_pool = ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE)
io_pool = ThreadPoolExecutor(max_workers=IO_THREAD_POOL_SIZE)

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass

class UninstallError(Exception):
    """Custom exception for uninstallation errors"""
    pass


class UninstallStatus:
    """Track uninstallation progress"""
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.successful = 0
        
    def update(self, success: bool):
        self.completed += 1
        if success:
            self.successful += 1
            
    @property
    def progress(self) -> str:
        return f"Progress: {self.completed}/{self.total} ({self.successful} successful)"


def set_secure_umask():
    """Set secure file permissions"""
    os.umask(SECURE_UMASK)

def verify_privileges() -> bool:
    """Enhanced privilege verification"""
    if platform.system() != 'Windows':
        raise SecurityError("This script only works on Windows systems")
        
    try:
        # Check both admin rights and integrity level
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            raise SecurityError("Administrative privileges required")
            
        # Verify process integrity level
        process = subprocess.run(['whoami', '/groups'], capture_output=True, text=True)
        if 'S-1-16-12288' not in process.stdout:  # High integrity level SID
            raise SecurityError("High integrity level required")
            
        return True
    except Exception as e:
        raise SecurityError(f"Security check failed: {e}")

@functools.lru_cache(maxsize=128)
def get_program_hash(program_name: str) -> str:
    """Cached program hash computation"""
    return hashlib.sha256(program_name.encode()).hexdigest()

def validate_program_name(name: str) -> bool:
    """Validate program name against security criteria"""
    if not name or len(name) > MAX_PROGRAM_NAME_LENGTH:
        return False
    # Only allow alphanumeric chars, spaces, and basic punctuation
    return bool(re.match(r'^[\w\s\-\.\(\)]+$', name))

@cachetools.cached(cache=program_cache)
def get_installed_programs() -> List[Tuple[str, str]]:
    """Cached and optimized program list retrieval"""
    try:
        # Run WMIC command with optimized parameters
        cmd = WMIC_CSV_COMMAND + ['/fast']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            raise SecurityError("Failed to query installed programs")

        # Use set for faster lookups
        seen_programs = set()
        programs = []
        
        # Process in chunks for better memory usage
        for line in result.stdout.splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.strip().split(',')
            if len(parts) >= 3:
                prog_id, name = parts[1].strip(), parts[2].strip()
                if validate_program_name(name) and (name, prog_id) not in seen_programs:
                    seen_programs.add((name, prog_id))
                    programs.append((name, prog_id))
                    
        return sorted(programs)
    except Exception as e:
        program_cache.clear()  # Clear cache on error
        raise SecurityError(f"Error querying programs: {e}")

def format_program_list(programs: List[str], columns: int = COLUMNS_PER_ROW) -> str:
    """Format programs list in columns for display"""
    col_width = max(len(prog) for prog in programs) + 4
    output = []
    for i in range(0, len(programs), columns):
        row = programs[i:i+columns]
        output.append(''.join(f"{i+1}:{prog:<{col_width}}" for i, prog in enumerate(row, i)))
    return '\n'.join(output)


def parse_selection(selected: str, prog_dict: Dict[str, str]) -> List[str]:
    """Parse and validate user selection"""
    if selected.lower() == 'q':
        return []
        
    selected_programs = [
        prog_dict[idx.strip()] 
        for idx in selected.split(',') 
        if idx.strip() in prog_dict
    ]
    return selected_programs


def choose_programs_to_uninstall(programs: List[str]) -> List[str]:
    """
    Allow user to choose programs with improved selection interface.
    """
    if not programs:
        print("No programs available to uninstall.")
        return []
    
    # Create a dictionary for faster lookups
    prog_dict = {str(i+1): prog for i, prog in enumerate(programs)}
    
    # Display in columns for better readability
    print(format_program_list(programs))

    while True:
        selected = input("\nEnter numbers (comma-separated) or 'q' to quit: ").strip()
        selected_programs = parse_selection(selected, prog_dict)
        if not selected_programs:
            print("No valid selections made.")
            continue
                
        print("\nSelected programs:")
        for prog in selected_programs:
            print(f"- {prog}")
        if input("\nType 'yes' to confirm: ").lower() == 'yes':
            return selected_programs


def sanitize_program_name(program: str) -> str:
    """Sanitize program name to prevent command injection"""
    # Remove any potentially dangerous characters
    sanitized = re.sub(r'[^a-zA-Z0-9\s\-_\.]', '', program)
    return shlex.quote(sanitized)

async def create_restore_point() -> bool:
    """Create system restore point before uninstallation"""
    try:
        subprocess.run([
            'powershell.exe',
            '-Command',
            'Checkpoint-Computer -Description "Before Program Uninstallation" -RestorePointType "APPLICATION_UNINSTALL"'
        ], check=True, capture_output=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create restore point: {e}")
        return False

@asyncio.coroutine
def registry_operation(func: Callable) -> Any:
    """Run registry operations in separate thread pool"""
    return func()

async def get_registry_programs() -> Set[Tuple[str, str]]:
    """Optimized registry program detection"""
    programs = set()
    
    async def process_registry_path(reg_path: str) -> Set[Tuple[str, str]]:
        path_programs = set()
        try:
            def _read_registry():
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    idx = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, idx)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    id_str = winreg.QueryValueEx(subkey, "UninstallString")[0]
                                    if validate_program_name(name):
                                        path_programs.add((name, subkey_name))
                                except WindowsError:
                                    pass
                            idx += 1
                        except WindowsError:
                            break
                return path_programs
                
            return await registry_operation(_read_registry)
        except Exception:
            return set()
            
    # Process registry paths in parallel
    results = await asyncio.gather(
        *(process_registry_path(path) for path in REGISTRY_UNINSTALL_PATHS)
    )
    
    for result in results:
        programs.update(result)
    return programs

async def get_msi_uninstall_string(program_id: str) -> Optional[str]:
    """Get MSI uninstall command"""
    try:
        installer = win32com.client.Dispatch('WindowsInstaller.Installer')
        products = installer.Products
        for product in products:
            if product == program_id:
                return f'msiexec /x {product} /qn'
    except Exception:
        return None
    return None

async def alternative_uninstall(program: Tuple[str, str]) -> bool:
    """Try alternative uninstall methods"""
    program_name, program_id = program
    
    # Try MSI uninstall
    if msi_cmd := await get_msi_uninstall_string(program_id):
        try:
            process = await asyncio.create_subprocess_shell(
                msi_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            pass
    
    # Try direct registry uninstall string
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           f"{REGISTRY_UNINSTALL_PATHS[0]}\\{program_id}") as key:
            uninstall_string = winreg.QueryValueEx(key, "UninstallString")[0]
            if uninstall_string:
                process = await asyncio.create_subprocess_shell(
                    f"{uninstall_string} /S",  # Silent mode
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                return process.returncode == 0
    except Exception:
        return False
    
    return False

class MemoryManager:
    """Manage memory usage during operations"""
    @staticmethod
    def check_memory():
        memory = psutil.virtual_memory()
        return memory.percent < MAX_MEMORY_PERCENT
    
    @staticmethod
    async def wait_for_memory():
        while not MemoryManager.check_memory():
            await asyncio.sleep(1)

class OptimizedMemoryManager(MemoryManager):
    """Enhanced memory management with predictive scaling"""
    _last_check = 0
    _check_interval = 1  # seconds
    
    @classmethod
    async def wait_for_memory(cls):
        current_time = time.time()
        if current_time - cls._last_check < cls._check_interval:
            return
            
        while not cls.check_memory():
            # Adjust semaphore dynamically
            current_memory = psutil.virtual_memory().percent
            if current_memory > 90:
                new_limit = max(1, uninstall_semaphore._value // 2)
                uninstall_semaphore._value = new_limit
            await asyncio.sleep(cls._check_interval)
            
        cls._last_check = current_time

@contextmanager
def secure_tempdir():
    """Create and clean up a secure temporary directory"""
    temp_dir = None
    try:
        # Create secure temporary directory with restricted permissions
        temp_dir = tempfile.mkdtemp(prefix=TEMP_DIR_PREFIX)
        os.chmod(temp_dir, 0o700)
        yield temp_dir
    finally:
        if temp_dir and os.path.exists(temp_dir):
            # Secure cleanup
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for name in files:
                    path = os.path.join(root, name)
                    # Overwrite file content before deletion
                    with open(path, 'wb') as f:
                        f.write(secrets.token_bytes(1024))
                    os.unlink(path)
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(temp_dir)

def sanitize_path(path: str) -> str:
    """Sanitize file paths"""
    if not path or len(path) > MAX_PATH_LENGTH:
        raise SecurityError("Invalid path length")
    
    path = os.path.normpath(path)
    if os.path.isabs(path):
        raise SecurityError("Absolute paths not allowed")
    
    if '..' in path:
        raise SecurityError("Path traversal detected")
        
    return path

def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages"""
    # Remove file paths
    message = re.sub(r'[A-Za-z]:\\[^\s]*', '[PATH]', message)
    # Remove registry keys
    message = re.sub(r'HKEY_[^\s]*', '[REGISTRY]', message)
    # Remove process IDs
    message = re.sub(r'PID \d+', '[PID]', message)
    return message

class SecureProcessManager:
    """Manage processes securely"""
    @staticmethod
    def terminate_child_processes(pid):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            gone, alive = psutil.wait_procs(children, timeout=3)
            for process in alive:
                process.kill()
        except Exception:
            pass

async def execute_secure_command(cmd: str) -> Tuple[int, str, str]:
    """Execute commands securely with isolation"""
    try:
        with secure_tempdir() as temp_dir:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir,
                # Limit process privileges
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=PROCESS_TIMEOUT
                )
                return process.returncode, stdout.decode(), stderr.decode()
            except asyncio.TimeoutError:
                SecureProcessManager.terminate_child_processes(process.pid)
                raise SecurityError("Process timeout")
    except Exception as e:
        raise SecurityError(f"Command execution error: {sanitize_error_message(str(e))}")

class SecureLogger:
    """Secure logging implementation"""
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.log_size = 0
        
    def log(self, message: str, level: str = 'INFO'):
        """Log message with size limits and sanitization"""
        if self.log_size > MAX_LOG_SIZE:
            return
            
        sanitized = sanitize_error_message(message)
        log_entry = f"{datetime.now().isoformat()} - {level} - {sanitized}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            self.log_size += len(log_entry)
        except Exception:
            pass

async def try_wmic_uninstall(program: Tuple[str, str]) -> bool:
    """Enhanced secure WMIC uninstall"""
    program_name, program_id = program
    
    # Validate program ID format
    if not re.match(r'^[{]?[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}[}]?$', program_id):
        raise SecurityError("Invalid program ID format")
    
    cmd = WMIC_UNINSTALL_BASE.format(program_id)
    
    for attempt in range(MAX_RETRIES):
        try:
            returncode, stdout, stderr = await execute_secure_command(cmd)
            if returncode == 0 and 'ReturnValue = 0' in stdout:
                return True
                
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
                
        except SecurityError:
            continue
            
    return False

from asyncio import Semaphore

uninstall_semaphore = Semaphore(MAX_CONCURRENT_UNINSTALLS)

async def rate_limited_uninstall(program: Tuple[str, str], status: UninstallStatus) -> Optional[str]:
    """Rate-limited uninstallation to prevent system overload"""
    async with uninstall_semaphore:
        return await uninstall_program(program, status)

async def uninstall_programs(programs: List[Tuple[str, str]], status: UninstallStatus) -> List[str]:
    """Optimized parallel uninstallation"""
    # Pre-validate all programs
    valid_programs = [
        prog for prog in programs 
        if validate_program_name(prog[0])
    ]
    
    # Process in optimized batches
    results = []
    for batch in [valid_programs[i:i + CHUNK_SIZE] 
                  for i in range(0, len(valid_programs), CHUNK_SIZE)]:
        batch_tasks = [
            asyncio.create_task(rate_limited_uninstall(program, status))
            for program in batch
        ]
        
        # Wait for batch completion with timeout
        try:
            batch_results = await asyncio.wait_for(
                asyncio.gather(*batch_tasks, return_exceptions=True),
                timeout=UNINSTALL_TIMEOUT * 1.5
            )
            results.extend([r for r in batch_results 
                          if r is not None and not isinstance(r, Exception)])
        except asyncio.TimeoutError:
            for task in batch_tasks:
                if not task.done():
                    task.cancel()
    
    return results

def setup_secure_logging() -> None:
    """Enhanced secure logging setup"""
    set_secure_umask()
    
    try:
        log_dir = Path.home() / "Documents" / "Python" / "uninstaller" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        # Cleanup old logs
        for old_log in log_dir.glob('*.log'):
            if old_log.stat().st_mtime < (datetime.now().timestamp() - 86400):  # 24 hours
                old_log.unlink()
        
        random_suffix = secrets.token_hex(8)
        log_file = log_dir / f"uninstaller_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random_suffix}.log"
        
        logger = SecureLogger(log_file)
        return logger
        
    except Exception as e:
        raise SecurityError(f"Logger setup failed: {sanitize_error_message(str(e))}")

# Update main_async to use new security features
async def main_async():
    settings = Settings()
    logger = SecureLogger(settings)
    system = SystemManager(settings)
    
    try:
        if not await system.verify_privileges():
            return 1
            
        uninstaller = Uninstaller(logger, settings)
        
        # Create restore point in background
        restore_point_task = asyncio.create_task(system.create_restore_point())
        
        # Get programs concurrently
        programs = await uninstaller.program_manager.get_installed_programs()
        
        if not await restore_point_task:
            if input("Failed to create restore point. Continue anyway? (yes/no): ").lower() != 'yes':
                return 1
        
        if not programs:
            logger.log("No programs found", "WARNING")
            return 0
            
        selected = system.choose_programs(sorted(programs))
        if not selected:
            return 0
            
        results = await uninstaller.batch_uninstall(selected)
        
        if results:
            logger.log(f"Successfully uninstalled {len(results)} programs")
        
        return 0
        
    except Exception as e:
        logger.log(f"Critical error: {str(e)}", "ERROR")
        return 1

def main() -> int:
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
