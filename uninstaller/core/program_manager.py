import winreg
from typing import Set, Tuple, List, Optional
import asyncio
from ..config.settings import Settings
from ..utils.system import ProcessManager

class ProgramManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.process_manager = ProcessManager(settings)
    
    async def get_installed_programs(self) -> Set[Tuple[str, str]]:
        wmic_programs = await self._get_wmic_programs()
        registry_programs = await self._get_registry_programs()
        return wmic_programs.union(registry_programs)
    
    async def uninstall(self, program: Tuple[str, str]) -> Optional[str]:
        name, prog_id = program
        
        # Try methods in order
        methods = [
            self._try_wmic_uninstall,
            self._try_msi_uninstall,
            self._try_registry_uninstall
        ]
        
        for method in methods:
            try:
                if await method(program):
                    return name
            except Exception:
                continue
        
        return None
    
    async def _get_wmic_programs(self) -> Set[Tuple[str, str]]:
        """Get programs using WMIC"""
        try:
            cmd = self.settings.WMIC_CSV_COMMAND + ['/fast']
            result = await self.process_manager.execute_command(cmd)
            
            if result[0] != 0:
                return set()
                
            programs = set()
            for line in result[1].splitlines()[1:]:
                if not line.strip():
                    continue
                    
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    prog_id, name = parts[1].strip(), parts[2].strip()
                    if self.security.validate_program_name(name):
                        programs.add((name, prog_id))
                        
            return programs
            
        except Exception:
            return set()
    
    async def _try_wmic_uninstall(self, program: Tuple[str, str]) -> bool:
        """Try WMIC uninstall method"""
        name, prog_id = program
        if not self.security.validate_program_id(prog_id):
            return False
            
        cmd = self.settings.WMIC_UNINSTALL_BASE.format(prog_id)
        result = await self.process_manager.execute_command(cmd)
        return result[0] == 0 and 'ReturnValue = 0' in result[1]
    
    async def _try_msi_uninstall(self, program: Tuple[str, str]) -> bool:
        """Try MSI uninstall method"""
        name, prog_id = program
        try:
            installer = win32com.client.Dispatch('WindowsInstaller.Installer')
            if prog_id in installer.Products:
                cmd = f'msiexec /x {prog_id} /qn'
                result = await self.process_manager.execute_command(cmd)
                return result[0] == 0
        except Exception:
            pass
        return False
        
    async def _get_registry_programs(self) -> Set[Tuple[str, str]]:
        # Implementation for registry program detection
        pass
