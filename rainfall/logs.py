import ctypes
from ctypes import wintypes

# Load the necessary libraries
advapi32 = ctypes.WinDLL('advapi32')
kernel32 = ctypes.WinDLL('kernel32')

# Define necessary constants
MAX_BUFFER_SIZE = 1024

# Define the necessary ctypes
OpenEventLog = advapi32.OpenEventLogW
OpenEventLog.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
OpenEventLog.restype = wintypes.HANDLE

CloseEventLog = advapi32.CloseEventLog
CloseEventLog.argtypes = [wintypes.HANDLE]
CloseEventLog.restype = wintypes.BOOL

ClearEventLog = advapi32.ClearEventLogW
ClearEventLog.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR]
ClearEventLog.restype = wintypes.BOOL

GetNumberOfEventLogRecords = advapi32.GetNumberOfEventLogRecords
GetNumberOfEventLogRecords.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
GetNumberOfEventLogRecords.restype = wintypes.BOOL

GetOldestEventLogRecord = advapi32.GetOldestEventLogRecord
GetOldestEventLogRecord.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
GetOldestEventLogRecord.restype = wintypes.BOOL


def clear_event_log(log_name, server=None):
    h_log = OpenEventLog(server, log_name)
    if not h_log:
        raise ctypes.WinError()

    try:
        if not ClearEventLog(h_log, None):
            raise ctypes.WinError()
        else:
            print(f"The '{log_name}' event log has been cleared.")
    finally:
        CloseEventLog(h_log)


# Clear all common event logs
event_logs = [
    "Application",
    "Security",
    "System",
    "Setup",
    "ForwardedEvents"
]

for log in event_logs:
    try:
        clear_event_log(log)
    except Exception as e:
        print(f"Failed to clear '{log}' event log: {e}")
