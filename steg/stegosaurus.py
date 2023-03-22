import tkinter as tk
from tkinter import filedialog
from dct_steganography import hide_data_dct, extract_data_dct
from echo_hiding_steganography import hide_data_echo, extract_data_echo
from progress_bar import ProgressBar
import os


def browse_file():
    file_path = filedialog.askopenfilename()
    file_path_var.set(file_path)


def browse_image_audio():
    file_path = filedialog.askopenfilename()
    image_audio_path_var.set(file_path)


def perform_operation():
    operation = operation_var.get()
    file_path = file_path_var.get()
    image_audio_path = image_audio_path_var.get()
    steg_type = steg_type_var.get()

    if not os.path.isfile(file_path) or not os.path.isfile(image_audio_path):
        status_label.config(text="Error: File not found.")
        return

    if steg_type == "Image":
        if operation == "Hide":
            with open(file_path, "rb") as f:
                data = f.read()
            hide_data_dct(image_audio_path, data, progress_callback=progress_bar.set_progress)
            status_label.config(text="Data hidden in 'hidden_dct_image.jpg'")
        elif operation == "Extract":
            extracted_data = extract_data_dct(image_audio_path, progress_callback=progress_bar.set_progress)
            with open("extracted_data", "wb") as f:
                f.write(extracted_data)
            status_label.config(text="Data extracted to 'extracted_data'")
    elif steg_type == "Audio":
        if operation == "Hide":
            with open(file_path, "rb") as f:
                data = f.read()
            hide_data_echo(image_audio_path, data, progress_callback=progress_bar.set_progress)
            status_label.config(text="Data hidden in 'hidden_echo_audio.wav'")
        elif operation == "Extract":
            extracted_data = extract_data_echo(image_audio_path, progress_callback=progress_bar.set_progress)
            with open("extracted_data", "wb") as f:
                f.write(extracted_data)
            status_label.config(text="Data extracted to 'extracted_data'")


root = tk.Tk()
root.title("Steganography App")

operation_var = tk.StringVar(root)
operation_var.set("Hide")
steg_type_var = tk.StringVar(root)
steg_type_var.set("Image")

file_path_var = tk.StringVar(root)
image_audio_path_var = tk.StringVar(root)

tk.Label(root, text="Operation:").grid(row=0, column=0, sticky="w")
tk.OptionMenu(root, operation_var, "Hide", "Extract").grid(row=0, column=1, sticky="w")

tk.Label(root, text="Steganography Type:").grid(row=1, column=0, sticky="w")
tk.OptionMenu(root, steg_type_var, "Image", "Audio").grid(row=1, column=1, sticky="w")

tk.Label(root, text="Data/File to Hide/Extract:").grid(row=2, column=0, sticky="w")
tk.Entry(root, textvariable=file_path_var).grid(row=2, column=1, sticky="w")
tk.Button(root, text="Browse", command=browse_file).grid(row=2, column=2, sticky="w")

tk.Label(root, text="Image/Audio File:").grid(row=3, column=0, sticky="w")
tk.Entry(root, textvariable=image_audio_path_var).grid(row=3, column=1, sticky="w")
tk.Button(root, text="Browse", command=browse_image_audio).grid(row=3, column=2, sticky="w")

tk.Button(root, text="Perform Operation", command=perform_operation).grid(row=4, columnspan=3)

status_label = tk.Label(root, text="")
status_label.grid(row=5, columnspan=3)

progress_bar = ProgressBar(root, width=200, height=20)
progress_bar.grid(row=6, columnspan=3)

root.mainloop()
