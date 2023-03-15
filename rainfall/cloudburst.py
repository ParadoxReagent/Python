import win32serviceutil
import win32service
import win32com.client

# List of critical services to exclude
critical_services = ["lsass", "wininit", "smss", "csrss", "winlogon", "Print Spooler"]

# Get a list of all running services
services = win32com.client.Dispatch("WbemScripting.SWbemLocator")
services = services.ConnectServer(".", "root\cimv2")
services = services.ExecQuery("SELECT * FROM Win32_Service WHERE State = 'Running'")


# Print the name of each running service
for service in services:
    print(service.Name)


# Stop non-critical services
for service in services:
    if service.Name.lower() not in critical_services:
        try:
            print("Stopping service:", service.Name)
            win32serviceutil.StopService(service.Name)
        except win32service.error as e:
            # Handle errors when stopping a service
            print(f"Failed to stop service {service.Name}: {e}")
