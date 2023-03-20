import tkinter as tk


def on_submit():
    attack_type = attack_type_var.get()
    target_ip = target_ip_var.get()
    target_port = target_port_var.get()
    num_threads = num_threads_var.get()

    print("Attack type:", attack_type)
    print("Target IP:", target_ip)
    print("Target port:", target_port)
    print("Number of threads:", num_threads)

# Create the main window
root = tk.Tk()
root.title("Example GUI")

# Variables for storing user input
attack_type_var = tk.StringVar()
target_ip_var = tk.StringVar()
target_port_var = tk.StringVar()
num_threads_var = tk.StringVar()

# Create input fields and labels
attack_type_label = tk.Label(root, text="Attack type (udp/http):")
attack_type_entry = tk.Entry(root, textvariable=attack_type_var)

target_ip_label = tk.Label(root, text="Target IP address:")
target_ip_entry = tk.Entry(root, textvariable=target_ip_var)

target_port_label = tk.Label(root, text="Target port:")
target_port_entry = tk.Entry(root, textvariable=target_port_var)

num_threads_label = tk.Label(root, text="Number of threads:")
num_threads_entry = tk.Entry(root, textvariable=num_threads_var)

submit_button = tk.Button(root, text="Submit", command=on_submit)

# Place the input fields and labels on the window
attack_type_label.grid(row=0, column=0, sticky="w")
attack_type_entry.grid(row=0, column=1)

target_ip_label.grid(row=1, column=0, sticky="w")
target_ip_entry.grid(row=1, column=1)

target_port_label.grid(row=2, column=0, sticky="w")
target_port_entry.grid(row=2, column=1)

num_threads_label.grid(row=3, column=0, sticky="w")
num_threads_entry.grid(row=3, column=1)

submit_button.grid(row=4, column=0, columnspan=2)

# Start the GUI event loop
root.mainloop()
