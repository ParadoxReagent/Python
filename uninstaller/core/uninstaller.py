from typing import List, Tuple, Optional
import asyncio
from ..config.settings import Settings
from ..utils.logging import SecureLogger
from ..utils.system import SystemManager
from .program_manager import ProgramManager
from .security import SecurityManager

class Uninstaller:
    def __init__(self, logger: SecureLogger, settings: Settings):
        self.logger = logger
        self.settings = settings
        self.security = SecurityManager(settings)
        self.program_manager = ProgramManager(settings)
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_UNINSTALLS)
    
    async def uninstall_program(self, program: Tuple[str, str]) -> Optional[str]:
        async with self.semaphore:
            return await self.program_manager.uninstall(program)
    
    async def batch_uninstall(self, programs: List[Tuple[str, str]]) -> List[str]:
        results = []
        for batch in self._create_batches(programs):
            batch_results = await self._process_batch(batch)
            results.extend(batch_results)
        return results
    
    def _create_batches(self, programs: List[Tuple[str, str]]) -> List[List[Tuple[str, str]]]:
        return [
            programs[i:i + self.settings.CHUNK_SIZE]
            for i in range(0, len(programs), self.settings.CHUNK_SIZE)
        ]
    
    async def _process_batch(self, batch: List[Tuple[str, str]]) -> List[str]:
        tasks = [
            asyncio.create_task(self.uninstall_program(program))
            for program in batch
        ]
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.settings.UNINSTALL_TIMEOUT * 1.5
            )
            return [r for r in results if r is not None and not isinstance(r, Exception)]
        except asyncio.TimeoutError:
            for task in tasks:
                if not task.done():
                    task.cancel()
            return []
