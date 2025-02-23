import psutil
import asyncio
import subprocess
from typing import Tuple, Optional
from ..config.settings import Settings

class ProcessManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        
    async def execute_command(self, cmd: str) -> Tuple[int, str, str]:
        """Execute command with proper cleanup"""
        process = None
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.settings.PROCESS_TIMEOUT
            )
            return process.returncode, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            if process:
                await self.terminate_process_tree(process.pid)
            raise
            
    async def terminate_process_tree(self, pid: int) -> None:
        """Terminate process and all children"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
                    
            # Wait for children to terminate
            gone, alive = psutil.wait_procs(children, timeout=3)
            
            # Kill any remaining processes
            for process in alive:
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
                    
            # Finally terminate parent
            if parent.is_running():
                parent.terminate()
                parent.wait(timeout=3)
                
        except psutil.NoSuchProcess:
            pass
