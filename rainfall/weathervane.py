import platform
import psutil
import subprocess


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
                    return True
        except ImportError:
            pass
        return False

    def check_windows_services(service_keywords):
        try:
            import wmi
            wmi_obj = wmi.WMI()
            for service_keyword in service_keywords:
                for service in wmi_obj.query(
                        "SELECT * FROM Win32_Service WHERE DisplayName LIKE '%" + service_keyword + "%'"):
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


if is_virtual_machine():
    print("This script is running inside a virtual machine.  Nice try.")
else:
    print("This script is NOT running inside a virtual machine.  Good luck!")
    another_script_path = "skylab.py"
    try:
        subprocess.run(["python", another_script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}, while executing the other script.")