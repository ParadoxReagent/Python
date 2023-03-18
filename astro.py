import cv2
import numpy as np
import astroalign as aa
import glob
import os
from skimage import exposure
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar

# Preprocess, stack, and enhance functions remain the same

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Astrophotography Stacker")
        self.geometry("450x250")

        self.input_label = tk.Label(self, text="Input Directory:")
        self.input_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        self.output_label = tk.Label(self, text="Output Directory:")
        self.output_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        self.scale_label = tk.Label(self, text="Scale Percentage:")
        self.scale_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.scale_var = tk.IntVar(value=50)

        self.input_entry = tk.Entry(self, textvariable=self.input_var, width=40)
        self.input_entry.grid(row=0, column=1, padx=10, pady=10)

        self.output_entry = tk.Entry(self, textvariable=self.output_var, width=40)
        self.output_entry.grid(row=1, column=1, padx=10, pady=10)

        self.scale_entry = tk.Entry(self, textvariable=self.scale_var, width=40)
        self.scale_entry.grid(row=2, column=1, padx=10, pady=10)

        self.browse_input_button = tk.Button(self, text="Browse", command=self.browse_input)
        self.browse_input_button.grid(row=0, column=2, padx=10, pady=10)

        self.browse_output_button = tk.Button(self, text="Browse", command=self.browse_output)
        self.browse_output_button.grid(row=1, column=2, padx=10, pady=10)

        self.process_button = tk.Button(self, text="Process Images", command=self.process_images)
        self.process_button.grid(row=3, column=0, columnspan=3, pady=20)

        self.progress = Progressbar(self, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=3, pady=10)

    def browse_input(self):
        directory = filedialog.askdirectory()
        if directory:
            self.input_var.set(directory)

    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_var.set(directory)

    def process_images(self):
        input_dir = self.input_var.get()
        output_dir = self.output_var.get()
        scale_percent = self.scale_var.get()

        if not input_dir or not output_dir:
            messagebox.showerror("Error", "Please select both input and output directories.")
            return

        try:
            self.progress["value"] = 0
            self.update_idletasks()

            main(input_dir, output_dir, scale_percent, progress_callback=self.update_progress)

            self.progress["value"] = 100
            self.update_idletasks()

            messagebox.showinfo("Astrophotography Stacker", "Image processing complete!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_progress(self, progress):
        self.progress["value"] = progress
        self.update_idletasks()

def main(input_dir, output_dir, scale_percent, progress_callback=None):
    # Read images
    image_files = glob.glob(os.path.join(input_dir, '*.jpg'))
    images = [cv2.imread(image_file) for image_file in image_files]

    # Preprocess images
    preprocessed_images = [preprocess_image(image, scale_percent) for image in images]
    if progress_callback: progress_callback(25)

    # Align images
    reference_image = preprocessed_images[0]
    aligned_images = [aa.register(reference_image, image)[0] for image in preprocessed_images[1:]]
    if progress_callback: progress_callback(50)

    # Stack images
    stacked_image = stack_images([reference_image] + aligned_images)
    if progress_callback: progress_callback(75)

    # Convert the stacked image to 8-bit
    stacked_image_8bit = cv2.normalize(stacked_image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # Enhance image
    enhanced_image = enhance_image(stacked_image_8bit)

    # Save the output image
    os.makedirs(output_dir, exist_ok=True)
    cv2.imwrite(os.path.join(output_dir, 'stacked_enhanced_image.png'), enhanced_image)

if __name__ == "__main__":
    app = App()
    app.mainloop()
