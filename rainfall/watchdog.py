import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            print(f"Directory modified: {event.src_path}")
        else:
            print(f"File modified: {event.src_path}")

    def on_created(self, event):
        if event.is_directory:
            print(f"Directory created: {event.src_path}")
        else:
            print(f"File created: {event.src_path}")

    def on_deleted(self, event):
        if event.is_directory:
            print(f"Directory deleted: {event.src_path}")
        else:
            print(f"File deleted: {event.src_path}")


if __name__ == "__main__":
    directory_to_monitor = input("Enter the directory to monitor: ")

    if not os.path.isdir(directory_to_monitor):
        print("Invalid directory. Please enter a valid directory path.")
        exit(1)

    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, directory_to_monitor, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
