import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import shutil
import importlib.util
import ast
import re
import csv
from datetime import datetime

class InteractiveCleanupDashboard:
    def __init__(self, master):
        self.master = master
        master.title("Interactive Cleanup Dashboard - NOAH (Beta) ")
        master.geometry("1200x800")

        # Main frame
        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Directory selection
        self.dir_frame = tk.Frame(self.main_frame)
        self.dir_frame.pack(fill=tk.X)

        self.dir_label = tk.Label(self.dir_frame, text="Selected Directory:")
        self.dir_label.pack(side=tk.LEFT)

        self.dir_path = tk.StringVar()
        self.dir_entry = tk.Entry(self.dir_frame, textvariable=self.dir_path, width=70)
        self.dir_entry.pack(side=tk.LEFT, padx=5)

        self.browse_button = tk.Button(self.dir_frame, text="Browse", command=self.browse_directory)
        self.browse_button.pack(side=tk.LEFT)

        # Analyze button
        self.analyze_button = tk.Button(self.main_frame, text="Analyze Directory", command=self.analyze_directory)
        self.analyze_button.pack(pady=10)

        # Notebook for different views
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Duplicate files tab
        self.duplicate_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.duplicate_frame, text="Duplicate Files")

        # Duplicate files treeview
        self.duplicate_tree = ttk.Treeview(self.duplicate_frame, columns=(
            "filename", "path", "size", "last_modified"
        ), show="headings")
        self.setup_duplicate_tree()

        # Dependencies tab
        self.dependencies_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dependencies_frame, text="Dependencies")

        # Dependencies treeview
        self.dependencies_tree = ttk.Treeview(self.dependencies_frame, columns=(
            "file", "imports", "local_dependencies"
        ), show="headings")
        self.setup_dependencies_tree()

        # Sorting and grouping controls
        self.setup_sorting_controls()

        # Delete selected button
        self.delete_button = tk.Button(self.main_frame, text="Delete Selected Files", command=self.delete_selected_files)
        self.delete_button.pack(pady=10)

        # Export Selected Files to CSV

        self.export_button = tk.Button(self.main_frame, text="Export Selected Files to CSV", command=self.export_to_csv)
        self.export_button.pack(pady=10)

    def export_to_csv(self):
        # Get selected items from the duplicate files tree
        selected_files = self.duplicate_tree.selection()
        
        if not selected_files:
            messagebox.showinfo("Info", "No files selected for export")
            return

        # Create the filename with a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"data_{timestamp}.csv"

        # Prepare the data to be written into the CSV
        rows = []
        for item in selected_files:
            file_details = self.duplicate_tree.item(item)['values']
            rows.append([file_details[0], file_details[1], file_details[2], file_details[3]])  # [filename, path, size, last_modified]

        # Write to CSV
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Filename", "Path", "Size (MB)", "Last Modified"])  # Write header
                writer.writerows(rows)  # Write selected rows
            messagebox.showinfo("Export Complete", f"Selected files have been exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while exporting to CSV: {str(e)}")


    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_path.set(directory)

    def setup_duplicate_tree(self):
        # Configure duplicate files treeview columns
        columns = [
            ("filename", "Filename", 200),
            ("path", "Path", 300),
            ("size", "Size (MB)", 100),
            ("last_modified", "Last Modified", 150)
            
        ]

        for col, title, width in columns:
            self.duplicate_tree.heading(col, text=title, command=lambda c=col: self.sort_column(self.duplicate_tree, c, False))
            self.duplicate_tree.column(col, width=width, anchor=tk.W)

        # Add scrollbar
        duplicate_scrollbar = ttk.Scrollbar(self.duplicate_frame, orient=tk.VERTICAL, command=self.duplicate_tree.yview)
        self.duplicate_tree.configure(yscroll=duplicate_scrollbar.set)
        duplicate_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.duplicate_tree.pack(fill=tk.BOTH, expand=True)

    def setup_dependencies_tree(self):
        # Configure dependencies treeview columns
        columns = [
            ("file", "File", 300),
            ("imports", "Imports", 200),
            ("local_dependencies", "Local Dependencies", 300)
        ]

        for col, title, width in columns:
            self.dependencies_tree.heading(col, text=title, command=lambda c=col: self.sort_column(self.dependencies_tree, c, False))
            self.dependencies_tree.column(col, width=width, anchor=tk.W)

        # Add scrollbar
        dependencies_scrollbar = ttk.Scrollbar(self.dependencies_frame, orient=tk.VERTICAL, command=self.dependencies_tree.yview)
        self.dependencies_tree.configure(yscroll=dependencies_scrollbar.set)
        dependencies_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dependencies_tree.pack(fill=tk.BOTH, expand=True)

    def setup_sorting_controls(self):
        # Sorting and grouping frame
        sort_frame = tk.Frame(self.main_frame)
        sort_frame.pack(fill=tk.X, pady=5)

        # Duplicate files sorting
        tk.Label(sort_frame, text="Duplicate Files Sort By:").pack(side=tk.LEFT)
        self.duplicate_sort_var = tk.StringVar(value="filename")
        duplicate_sort_options = ["filename", "path", "size", "last_modified"]
        duplicate_sort_dropdown = ttk.Combobox(sort_frame, textvariable=self.duplicate_sort_var, 
                                       values=duplicate_sort_options, state="readonly")

        duplicate_sort_dropdown.pack(side=tk.LEFT, padx=5)

        # Dependencies sorting
        tk.Label(sort_frame, text="  Dependencies Sort By:").pack(side=tk.LEFT)
        self.dependencies_sort_var = tk.StringVar(value="file")
        dependencies_sort_options = ["file", "imports", "local_dependencies"]
        dependencies_sort_dropdown = ttk.Combobox(sort_frame, textvariable=self.dependencies_sort_var, 
                                                  values=dependencies_sort_options, state="readonly")
        dependencies_sort_dropdown.pack(side=tk.LEFT, padx=5)

    def analyze_directory(self):
        directory = self.dir_path.get()
        if not directory:
            messagebox.showerror("Error", "Please select a directory first")
            return

        # Clear existing data
        for tree in [self.duplicate_tree, self.dependencies_tree]:
            for i in tree.get_children():
                tree.delete(i)

        # Analyze duplicates
        duplicates = self.find_duplicates(directory)
        for file_info in duplicates:
            self.duplicate_tree.insert("", tk.END, values=(
                file_info['filename'], 
                file_info['path'], 
                file_info['size'], 
                file_info['last_modified']
            ))

        # Analyze dependencies
        dependencies = self.analyze_dependencies(directory)
        for dep in dependencies:
            self.dependencies_tree.insert("", tk.END, values=(
                dep['file'], 
                ", ".join(dep['imports']), 
                ", ".join(dep['local_dependencies'])
            ))

    def find_duplicates(self, directory):
        file_details = {}
        duplicates = []

        # Walk through the directory and collect file information
        for root, _, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)

                # Skip certain system and hidden files
                if filename.startswith('.') or filename in ['desktop.ini', 'Thumbs.db']:
                    continue

                try:
                    file_stat = os.stat(filepath)
                    file_size = file_stat.st_size
                    last_modified = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                    # Use a tuple (name, size) as the key to group duplicates
                    key = (filename, file_size)

                    if key not in file_details:
                        file_details[key] = []
                    file_details[key].append({
                        'filename': filename,
                        'path': filepath,
                        'size': f"{file_size / (1024 * 1024):.2f} MB",  # Size in MB
                        'last_modified': last_modified
                    })
                except (PermissionError, FileNotFoundError):
                    continue

        # Identify duplicates
        for key, files in file_details.items():
            if len(files) > 1:  # If more than one file has the same name and size, it's a duplicate
                duplicates.extend(files)

        # Sort based on user selection
        sort_key = self.duplicate_sort_var.get()
        if sort_key not in ['filename', 'path', 'size', 'last_modified']:
            sort_key = 'filename'  # Default to filename if invalid key
        return sorted(duplicates, key=lambda x: x[sort_key], reverse=True)


    def analyze_dependencies(self, directory):
        python_files = []
        
        # Find all Python files
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.py'):
                    python_files.append(os.path.join(root, filename))
        
        dependencies = []
        
        for filepath in python_files:
            try:
                with open(filepath, 'r') as file:
                    content = file.read()
                    
                    # Parse imports
                    imports = self.extract_imports(content)
                    
                    # Find local dependencies
                    local_dependencies = self.find_local_dependencies(filepath, python_files)
                    
                    dependencies.append({
                        'file': filepath,
                        'imports': imports,
                        'local_dependencies': local_dependencies
                    })
            except Exception:
                continue
        
        # Sort based on user's selection
        sort_key = self.dependencies_sort_var.get()
        return sorted(dependencies, key=lambda x: x[sort_key])

    def extract_imports(self, content):
        imports = []
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}.{node.names[0].name}" if node.module else node.names[0].name)
        
        return list(set(imports))

    def find_local_dependencies(self, current_file, all_python_files):
        local_dependencies = []
        current_dir = os.path.dirname(current_file)
        
        for file in all_python_files:
            if file != current_file:
                module_name = os.path.splitext(os.path.basename(file))[0]
                
                # Check if the module is in the same directory or a subdirectory
                if os.path.commonpath([current_dir, file]) == current_dir:
                    local_dependencies.append(module_name)
        
        return local_dependencies

    def sort_column(self, tree, col, reverse):
        # Sorting function for treeview columns
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        
        try:
            # Try numeric sorting first
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # Fallback to string sorting
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)
        
        # Switch the heading so that next sort is in the opposite direction
        tree.heading(col, command=lambda: self.sort_column(tree, col, not reverse))

    def delete_selected_files(self):
        # Get selected items from duplicate files
        selected_duplicates = self.duplicate_tree.selection()
        
        if not selected_duplicates:
            messagebox.showinfo("Info", "No files selected for deletion")
            return

        # Confirm deletion
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to delete the selected files?")
        if not confirm:
            return

        deleted_count = 0
        log_entries = []
        
        for item in selected_duplicates:
            file_details = self.duplicate_tree.item(item)['values']
            filepath = file_details[1]  # Path is the second column
            
            try:
                os.remove(filepath)
                deleted_count += 1
                log_entries.append(filepath)  # Add the path to log entries
                self.duplicate_tree.delete(item)  # Remove entry from the treeview
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete {filepath}: {str(e)}")

        # Log the deleted files
        if log_entries:
            with open("logs.txt", "a") as log_file:  # Open in append mode
                log_file.write(f"Deleted Files - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n")
                for entry in log_entries:
                    log_file.write(f"{entry}\n")
                log_file.write("\n")  # Add a blank line for better readability

        # Re-analyze directory to refresh duplicates
        self.analyze_directory()

        messagebox.showinfo("Complete", f"Deleted {deleted_count} files")

def main():
    root = tk.Tk()
    app = InteractiveCleanupDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()