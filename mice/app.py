import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, PhotoImage, Label
from deepof_utils import create_project_folder, load_config, start_deepof, load_project, preprocess_and_save
import subprocess
import os
import pickle
import pandas as pd

#===================================================================================================
# GLOBAL VARIABLES

current_config_path = None

#===================================================================================================
# GUI

def create_gui():
    root = tk.Tk()
    root.title("DeepOF GUI")
    
    root.geometry('800x900')  # size of the window

    background_image = PhotoImage(file=r'C:\Users\maxca\Documents\EPFL\lab_carmen\mice\deepOF_logo.png')
    background_label = Label(root, image=background_image)
    background_label.place(x=0, y=0, relwidth=1, relheight=1)
    
    # Add a label with instructions
    instructions = "Welcome to the DeepOF GUI. Please choose an action below:"
    instruction_label = tk.Label(root, text=instructions, wraplength=400)  # Wraplength breaks the line at 400px
    instruction_label.pack(pady=20)  # Add some padding around the label
    # Buttons    
    btn_open_deeplabcut = tk.Button(root, text="Open DeepLabCut", command=open_deeplabcut)
    btn_open_deeplabcut.pack(pady=10)
    
    btn_create_project = tk.Button(root, text="Create Project", command=create_project_gui)
    btn_create_project.pack(pady=10)

    btn_load_project = tk.Button(root, text="Load Project", command=load_project_gui)
    btn_load_project.pack(pady=10)
    
    btn_open_config = tk.Button(root, text="Open Config File", command=open_config_file)
    btn_open_config.pack(pady=10)
    
    btn_open_project_folder = tk.Button(root, text="Open Project Folder", command=open_project_folder)
    btn_open_project_folder.pack(pady=10)
    
    btn_start_deepof = tk.Button(root, text="Start DeepOF", command=start_deepof_gui)
    btn_start_deepof.pack(pady=10)
    
    btn_preprocess = tk.Button(root, text="Preprocess Data", command=preprocess_data)
    btn_preprocess.pack(pady=20)
    
    btn_open_help = tk.Button(root, text="Help", command=open_help_file, bg="gray", fg="orange")
    btn_open_help.pack(pady=20)

    background_label.image = background_image
    
    root.mainloop()


#===================================================================================================
# BUTTONS

def open_help_file():
    help_path = 'help.txt'
    try:
        os.startfile(help_path)  # Works on Windows, opens the file with the default application
    except AttributeError:
        # For macOS and Linux, you can use subprocess to open a file with the default application
        import subprocess
        subprocess.call(('open', help_path))  # macOS
        # subprocess.call(('xdg-open', help_path))  # Linux
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open the help file: {str(e)}")


def preprocess_data():
    global current_config_path
    project_path = os.path.dirname(current_config_path)
    pickle_path = os.path.join(project_path, 'supervised_data.pkl')
    filepath_freq = os.path.join(project_path, 'behavior_frequencies.xlsx')
    filepath_duration = os.path.join(project_path, 'behavior_duration.xlsx')
    try:
        with open(pickle_path, 'rb') as f:
            supervised = pickle.load(f)
        preprocess_and_save(supervised, filepath_freq=filepath_freq, filepath_duration=filepath_duration)
        messagebox.showinfo("Success", "Data preprocessing completed successfully.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to preprocess data: {str(e)}")

def open_deeplabcut():
    try:
        # Open a new command prompt and run DeepLabCut in its environment
        command = 'start cmd.exe /k "conda activate deeplabcut && python -m deeplabcut"'
        subprocess.Popen(command, shell=True)
        messagebox.showinfo("DeepLabCut", "Launching DeepLabCut in its Conda environment.")
    except Exception as e:
        messagebox.showerror("Error", "Failed to launch DeepLabCut.\n" + str(e))

def create_project_gui():
    global current_config_path
    project_name = simpledialog.askstring("Project Name", "Enter the name of the project:")
    if project_name:
        project_path, config_path = create_project_folder(project_name)
        current_config_path = config_path
        messagebox.showinfo("Project Created", f"Project created at {project_path}")

def open_config_file():
    global current_config_path
    if current_config_path and os.path.exists(current_config_path):
        # Open the config file in Notepad
        subprocess.run(['notepad', current_config_path])
    else:
        # Show error message if the config path is not set or file doesn't exist
        messagebox.showerror("Error", "No configuration file loaded. Please load or create a project first.")

def start_deepof_gui():
    folder_path = os.path.dirname(current_config_path)
    if folder_path:
        start_deepof(folder_path)
        messagebox.showinfo("DeepOF Started", "DeepOF processing has started.")

def load_project_gui():
    global current_config_path
    folder_path = filedialog.askdirectory(title="Select Project Folder")
    if folder_path:
        config_path = os.path.join(folder_path, 'config.yaml')
        if os.path.exists(config_path):
            current_config_path = config_path
            load_project(folder_path)
            messagebox.showinfo("Project Loaded", f"Project loaded from {folder_path}")
        else:
            messagebox.showerror("Error", "No config.yaml found in the selected directory.")

def open_project_folder():
    current_project_path = os.path.dirname(current_config_path)
    print(current_project_path)
    if current_project_path and os.path.exists(current_project_path):
        # Open the folder in the default file explorer
        os.startfile(current_project_path)
        # subprocess.run(['explorer', current_project_path], check=True)
    else:
        # Error handling if the path is not set or doesn't exist
        messagebox.showerror("Error", "No project folder is loaded or the path does not exist.")

    
if __name__ == "__main__":
    create_gui()
