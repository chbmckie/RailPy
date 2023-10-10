import tkinter as tk
from tkinter import ttk
import csv

def update_listbox(event):
    search_text = search_entry.get().lower()
    listbox.delete(0, tk.END)
    for item in items:
        if search_text in item.lower():
            listbox.insert(tk.END, item)

# Create the main application window
root = tk.Tk()
root.title("Searchable Dropdown List")

# Create a label and an entry widget for searching
search_label = tk.Label(root, text="Search:")
search_label.pack()

search_entry = tk.Entry(root)
search_entry.pack()

# Read the CSV file and extract values from the second column
csv_file = "assets/ukCrsCodes.csv"
items = []

try:
    with open(csv_file, "r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 2:
                items.append(row[1].title())
except FileNotFoundError:
    print(f"CSV file '{csv_file}' not found.")

# Create a listbox and a scrollbar
listbox = tk.Listbox(root, selectmode=tk.SINGLE, height=10)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=listbox.yview)
listbox.config(yscrollcommand=scrollbar.set)

# Populate the listbox with items
for item in items:
    listbox.insert(tk.END, item)

# Center the listbox in the window
listbox.pack(side="top", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Bind the search entry to the update_listbox function when text changes
search_entry.bind("<KeyRelease>", update_listbox)

# Start the Tkinter main loop
root.mainloop()
