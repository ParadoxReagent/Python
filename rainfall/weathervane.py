# is this virtual?

import platform
import psutil
import subprocess
import sys
import ctypes


def check_dmi_info(keywords):
    try:
        dmi_output = subprocess.check_output(['dmidecode']).decode('utf-8').lower()
        for keyword in keywords:
            if keyword.lower() in dmi_output:
                return True
    except (FileNotFoundError, subprocess.CalledProcessError, PermissionError):
        pass
    return False


def check_kernel_modules(modules):
    try:
        lsmod_output = subprocess.check_output(['lsmod']).decode('utf-8').lower()
        for module in modules:
            if module.lower() in lsmod_output:
                return True
    except (FileNotFoundError, subprocess.CalledProcessError, PermissionError):
        pass
    return False


def check_windows_vm():
    def check_windows_devices(device_keywords):
        try:
            import wmi
            wmi_obj = wmi.WMI()
            for device_keyword in device_keywords:
                for device in wmi_obj.query("SELECT * FROM Win32_PnPEntity WHERE Name LIKE '%" + device_keyword + "%'"):
                    if device:
                        return True
        except ImportError:
            pass
        return False

    def check_windows_services(service_keywords):
        try:
            import wmi
            wmi_obj = wmi.WMI()
            for service_keyword in service_keywords:
                for service in wmi_obj.query("SELECT * FROM Win32_Service WHERE DisplayName LIKE '%" + service_keyword + "%'"):
                    if service:
                        return True
        except ImportError:
            pass
        return False

    if check_windows_devices(['VBoxSVGA', 'VMware SVGA']):
        return True

    if check_windows_services(['VirtualBox Guest', 'VMware Tools']):
        return True

    try:
        import wmi
        wmi_obj = wmi.WMI()
        for disk_drive in wmi_obj.query("SELECT * FROM Win32_DiskDrive WHERE Model LIKE 'Msft Virtual Disk%'"):
            if disk_drive:
                return True
    except ImportError:
        pass

    for device in psutil.disk_partitions():
        if 'VBOX' in device.device or 'VMware' in device.device:
            return True

    return False


def check_linux_vm():
    checks = [
        ('/proc/cpuinfo', ['hypervisor', 'vmware', 'virtualbox', 'QEMU', 'KVMKVMKVM']),
        ('/sys/class/dmi/id/product_name', ['VirtualBox', 'VMware']),
        ('/sys/hypervisor/type', ['xen'])
    ]

    for filepath, keywords in checks:
        try:
            with open(filepath, 'r') as f:
                content = f.read().lower()
                for keyword in keywords:
                    if keyword.lower() in content:
                        return True
        except FileNotFoundError:
            pass

    if check_dmi_info(['VirtualBox', 'VMware', 'QEMU', 'KVM', 'Xen']):
        return True

    if check_kernel_modules(['kvm', 'vboxdrv', 'vmw_vmci', 'xen']):
        return True

    try:
        with open('/proc/bus/pci/devices', 'r') as pci_devices:
            content = pci_devices.read().lower()
            if 'virtio' in content:
                return True
    except FileNotFoundError:
        pass

    return False


def check_macos_vm():
    if check_dmi_info(['VirtualBox', 'VMware', 'Parallels']):
        return True

    try:
        with open('/usr/sbin/system_profiler', 'r') as sys_profiler:
            for line in sys_profiler:
                if 'VirtualBox' in line or 'VMware' in line or 'Parallels' in line:
                    return True
    except FileNotFoundError:
        pass

    return False


def is_virtual_machine():
    os_name = platform.system()

    if os_name == 'Windows':
        return check_windows_vm()
    elif os_name == 'Linux':
        return check_linux_vm()
    elif os_name == 'Darwin':
        return check_macos_vm()

    return False


############# Check for sandbox ################
# if platform.system() == 'Windows':
#    import winreg
#
#
#    def check_sandbox_artifacts():
#        artifacts = [
#            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Oracle\VirtualBox Guest Additions'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\VBoxGuest'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\VBoxMouse'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\VBoxService'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\VBoxSF'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\VBoxVideo'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\vmicheartbeat'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\vmicvss'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\vmicshutdown'),
#            (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\vmicexchange'),
#            # ... (add more sandbox-specific registry keys)
#        ]
#
#        for root, key_path in artifacts:
#            try:
#                with winreg.OpenKey(root, key_path):
#                    return True
#            except FileNotFoundError:
#                pass
#
#        return False
#
#    if check_sandbox_artifacts():
#        print("Sandbox artifact detected. Exiting.")
#        sys.exit(1)  # Exit the script with an error code


def check_low_system_entropy():
    import os

    entropy = os.urandom(64)
    unique_byte_count = len(set(entropy))

    return unique_byte_count < 40


if check_low_system_entropy():
    print("Low system entropy detected. Exiting.")
    sys.exit(1)  # Exit the script with an error code


def check_analysis_tools():
    analysis_tools = [
        'tcpdump', 'Wireshark', 'fiddler', 'burpsuite', 'charles',
        'idaq.exe', 'idaq64.exe', 'ollydbg', 'windbg', 'gdb',
        'x64dbg', 'x32dbg', 'x64bdg', 'x32bdg', 'ImmunityDebugger',
        'radare2', 'strace', 'ltrace', 'dnSpy', 'de4dot', 'ghidra'
    ]

    for process in psutil.process_iter(['name']):
        try:
            process_name = process.info['name']
            if process_name in analysis_tools:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return False


if check_analysis_tools():
    print("Analysis tool detected. Exiting.")
    sys.exit(1)  # Exit the script with an error code


def is_debugger_attached_windows():
    kernel32 = ctypes.windll.kernel32
    return kernel32.IsDebuggerPresent() != 0


def is_debugger_attached_linux():
    try:
        with open('/proc/self/status', 'r') as status_file:
            for line in status_file:
                if line.startswith('TracerPid:'):
                    tracer_pid = int(line.split(':', 1)[1].strip())
                    return tracer_pid != 0
    except FileNotFoundError:
        pass
    return False


def is_debugger_attached():
    os_name = platform.system()

    if os_name == 'Windows':
        return is_debugger_attached_windows()
    elif os_name == 'Linux':
        return is_debugger_attached_linux()
    else:
        # We are not checking for debuggers on other platforms
        return False


if is_debugger_attached():
    print("Debugger detected. Exiting.")
    sys.exit(1)  # Exit the script with an error code


if is_virtual_machine():
    print("This script is running inside a virtual machine.  Nice try.")
else:
    print("This script is NOT running inside a virtual machine.  Good luck!")
    another_script_path = "skylab.py"
    try:
        subprocess.run(["python", another_script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}, while executing the other script.")
