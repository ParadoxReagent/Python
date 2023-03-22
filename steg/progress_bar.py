import tkinter as tk


class ProgressBar(tk.Frame):
    def __init__(self, parent, width=300, height=20, bg="white", progress_color="blue", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.width = width
        self.height = height
        self.bg = bg
        self.progress_color = progress_color
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg=self.bg)
        self.progress = self.canvas.create_rectangle(0, 0, 0, self.height, fill=self.progress_color)
        self.canvas.pack()

    def set_progress(self, percentage):
        self.canvas.coords(self.progress, 0, 0, self.width * percentage, self.height)
        self.update_idletasks()
