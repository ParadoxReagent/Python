import platform
import ctypes
import subprocess
from typing import List, Tuple
from ..config.settings import Settings

class SystemManager:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def verify_privileges(self) -> bool:
        """Verify system privileges"""
        if platform.system() != 'Windows':
            return False
        
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                return False
                
            process = subprocess.run(['whoami', '/groups'], capture_output=True, text=True)
            return 'S-1-16-12288' in process.stdout
            
        except Exception:
            return False

    async def create_restore_point(self) -> bool:
        """Create system restore point"""
        try:
            result = subprocess.run([
                'powershell.exe',
                '-Command',
                'Checkpoint-Computer -Description "Before Program Uninstallation" -RestorePointType "APPLICATION_UNINSTALL"'
            ], check=True, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def choose_programs(self, programs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Interactive program selection"""
        if not programs:
            return []
            
        # Display programs
        for i, (name, _) in enumerate(programs, 1):
            print(f"{i}: {name}")
            
        try:
            selection = input("\nEnter numbers (comma-separated) or 'q' to quit: ")
            if selection.lower() == 'q':
                return []
                
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected = [programs[i] for i in indices if 0 <= i < len(programs)]
            
            if not selected:
                return []
                
            print("\nSelected programs:")
            for name, _ in selected:
                print(f"- {name}")
                
            if input("\nConfirm (yes/no): ").lower() == 'yes':
                return selected
                
        except (ValueError, IndexError):
            pass
            
        return []
