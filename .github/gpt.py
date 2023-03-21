import requests
import json
import logging
import threading
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog
import os
import re

API_KEY = os.environ.get("CHATGPT_API_KEY")
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# set CHATGPT_API_KEY="your_api_key_here"
# python your_script_name.py


class ChatGPTAPIError(Exception):
    pass


def send_message(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "prompt": prompt,
        "max_tokens": 100
    }

    response = requests.post(API_ENDPOINT, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        return response_data["choices"][0]["text"].strip()
    else:
        raise ChatGPTAPIError(f"Error {response.status_code}: {response.text}")


class ChatGPTGUI(Tk):
    def __init__(self):
        super().__init__()

        self.title("ChatGPT")
        self.geometry("500x500")

        self.setup_menu()
        self.setup_chat_history()
        self.setup_user_entry()
        self.setup_send_button()

    def setup_menu(self):
        menu = Menu(self)
        self.config(menu=menu)

        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Conversation", command=self.save_conversation_history)
        file_menu.add_command(label="Load Conversation", command=self.load_conversation_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        edit_menu = Menu(menu)
        menu.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)

        view_menu = Menu(menu)
        menu.add_cascade(label="View", menu=view_menu)
        self.dark_var = BooleanVar()
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_var, command=self.toggle_dark_mode)

    def setup_chat_history(self):
        self.chat_history = ScrolledText(self, wrap=WORD, undo=True, state=DISABLED)
        self.chat_history.pack(padx=5, pady=5, fill=BOTH, expand=True)

    def setup_user_entry(self):
        self.user_entry = Entry(self)
        self.user_entry.pack(padx=5, pady=5, fill=X, expand=False)
        self.user_entry.bind("<Return>", self.submit_message)

    def setup_send_button(self):
        send_button = Button(self, text="Send", command=self.submit_message)
        send_button.pack(padx=5, pady=5, fill=X, expand=False)

    def save_conversation_history(self):
        file = filedialog.asksaveasfile(defaultextension=".txt")
        if file:
            conversation_text = self.chat_history.get(1.0, END)
            file.write(conversation_text)
            file.close()

    def load_conversation_history(self):
        file = filedialog.askopenfile()
        if file:
            self.chat_history.config(state=NORMAL)
            self.chat_history.delete(1.0, END)
            self.chat_history.insert(END, file.read())
            self.chat_history.config(state=DISABLED)
            file.close()

    def submit_message(self, event=None):
        user_input = self.user_entry.get()
        self.user_entry.delete(0, END)
        self.chat_history.config(state=NORMAL)
        self.chat_history.insert(END, f"You: {user_input}\n")
        self.chat_history.see(END)
        self.chat_history.config(state=DISABLED)

        threading.Thread(target=self.threaded_submit_message, args=(user_input,)).start()

    def threaded_submit_message(self, user_input):
        try:
            response = send_message(user_input)
            self.chat_history.config(state=NORMAL)
            self.chat_history.insert(END, f"ChatGPT: {response}\n")
            self.chat_history.see(END)
            self.chat_history.config(state=DISABLED)
        except ChatGPTAPIError as e:
            self.chat_history.config(state=NORMAL)
            self.chat_history.insert(END, f"Error: {e}\n")
            self.chat_history.see(END)
            self.chat_history.config(state=DISABLED)

    def toggle_dark_mode(self):
        if self.dark_var.get():
            self.chat_history.config(bg='#333333', fg='#ffffff')
            self.config(bg='#333333')
            self.user_entry.config(bg='#333333', fg='#ffffff')
        else:
            self.chat_history.config(bg='#ffffff', fg='#000000')
            self.config(bg='#f0f0f0')
            self.user_entry.config(bg='#ffffff', fg='#000000')

    def undo(self):
        self.chat_history.config(state=NORMAL)
        self.chat_history.edit_undo()
        self.chat_history.config(state=DISABLED)

    def redo(self):
        self.chat_history.config(state=NORMAL)
        self.chat_history.edit_redo()
        self.chat_history.config(state=DISABLED)


if __name__ == "__main__":
    app = ChatGPTGUI()
    app.mainloop()
