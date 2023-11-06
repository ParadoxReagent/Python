# finds and deletes backups

import os

# Define a list of file extensions to delete
extensions = ['.VHD', '.bac', '.bak', '.wbcat', '.bkf', '.set', '.win', '.dsk']

# Define a list of filename patterns to delete
patterns = ['Backup*.*', 'backup*.*']

# Define the directory to delete files from
directory = r'C:\path\to\directory'

# Recursively delete all files matching the specified extensions and patterns
for root, dirs, files in os.walk(directory):
    for file in files:
        if any(file.endswith(ext) for ext in extensions) or any(pattern in file for pattern in patterns):
            os.remove(os.path.join(root, file))
