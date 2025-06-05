import os
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import zipfile
import re

# Set your Google Drive file ID here
GOOGLE_DRIVE_FILE_ID = '1IzzV-MZ9l11r8ZbjOt-2rn9qvhUYaV23'  # TODO: Replace with your file ID
MODS_FOLDER_NAME = 'mods'
MANIFEST_NAME = 'official_mods.txt'

# List of known client-side-only mods
CLIENT_SIDE_MODS = [
    'Xaeros_Minimap',
    'XaerosWorldMap',
    'MouseTweaks',
    'appleskin',
    'smoothchunk',
    'VisualWorkbench',
    'NaturesCompass',
    'rightclickharvest',
    'LeavesBeGone',
    'oculus',
    'emi',
    'jei',
    'craftingtweaks',
    'fast-ip-ping',
    'toofast',
    'Controlling',
    'EnchantmentDescriptions',
    'Searchables',
    'embeddium',
    'freecam'
]

DOWNLOAD_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}'

def is_client_side_mod(filename):
    """Check if a mod is client-side only, ignoring case"""
    filename_lower = filename.lower()
    return any(mod.lower() in filename_lower for mod in CLIENT_SIDE_MODS)

class ModpackUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Modpack Updater')
        self.instance_path = tk.StringVar()
        self.mode = tk.StringVar(value="client")  # Default to client mode

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instance selection
        ttk.Label(main_frame, text='Select your CurseForge instance folder:').pack(pady=5)
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill=tk.X, pady=5)
        ttk.Entry(path_frame, textvariable=self.instance_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text='Browse', command=self.browse_folder).pack(side=tk.LEFT, padx=5)

        # Mode selection
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(pady=10)
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Client", variable=self.mode, value="client").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Server", variable=self.mode, value="server").pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.pack(pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # Update button
        self.update_button = ttk.Button(main_frame, text='Update Mods', command=self.update_mods)
        self.update_button.pack(pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.instance_path.set(folder)

    def filter_server_mods(self, mods_path):
        """Filter out client-side mods from the mods folder"""
        temp_folder = os.path.join(mods_path, 'temp_server_mods')
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        os.makedirs(temp_folder, exist_ok=True)
        
        included = []
        excluded = []
        
        # Move all mods to temp folder
        for f in os.listdir(mods_path):
            if f.endswith('.jar'):
                shutil.move(os.path.join(mods_path, f), os.path.join(temp_folder, f))
        
        # Copy only server mods back
        for f in os.listdir(temp_folder):
            if f.endswith('.jar'):
                if is_client_side_mod(f):
                    excluded.append(f)
                else:
                    shutil.copy2(os.path.join(temp_folder, f), os.path.join(mods_path, f))
                    included.append(f)
        
        # Clean up temp folder
        shutil.rmtree(temp_folder)
        
        # Update manifest
        manifest_path = os.path.join(mods_path, MANIFEST_NAME)
        with open(manifest_path, 'w') as f:
            for jar in sorted(included):
                f.write(jar + '\n')
        
        return included, excluded

    def update_progress(self, current, total):
        """Update the progress bar and label"""
        percentage = (current / total) * 100
        self.progress_var.set(percentage)
        self.progress_label.config(text=f"Downloading: {percentage:.1f}%")
        self.root.update_idletasks()

    def download_file(self, url, dest):
        session = requests.Session()
        
        # First request to get the confirmation token
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        # Check if we got the virus scan warning page
        if 'Virus scan warning' in response.text:
            # Extract the download URL from the form
            download_url = re.search(r'action="([^"]+)"', response.text).group(1)
            form_data = {
                'id': GOOGLE_DRIVE_FILE_ID,
                'export': 'download',
                'confirm': 't',
                'uuid': re.search(r'name="uuid" value="([^"]+)"', response.text).group(1)
            }
            
            # Make the download request
            response = session.get(download_url, params=form_data, stream=True)
            response.raise_for_status()
        
        # Get the total file size
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        # Download the file with progress bar
        with open(dest, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    size = f.write(chunk)
                    downloaded += size
                    self.update_progress(downloaded, total_size)

    def update_mods(self):
        # Disable the update button during download
        self.update_button.config(state='disabled')
        self.progress_var.set(0)
        self.progress_label.config(text="Starting download...")
        
        try:
            instance_dir = self.instance_path.get()
            if not instance_dir or not os.path.isdir(instance_dir):
                messagebox.showerror('Error', 'Please select a valid instance folder.')
                return
            mods_path = os.path.join(instance_dir, MODS_FOLDER_NAME)
            if not os.path.isdir(mods_path):
                messagebox.showerror('Error', f'No mods folder found in {instance_dir}')
                return
            old_manifest_path = os.path.join(mods_path, MANIFEST_NAME)
            old_manifest = set()
            if os.path.isfile(old_manifest_path):
                with open(old_manifest_path, 'r') as f:
                    old_manifest = set(line.strip() for line in f if line.strip())
            
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, 'mods.zip')
                # Download the zip file from Google Drive
                self.download_file(DOWNLOAD_URL, zip_path)
                
                # Update progress label for extraction
                self.progress_label.config(text="Extracting mods...")
                self.root.update_idletasks()
                
                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                new_mods = os.path.join(tmpdir, MODS_FOLDER_NAME)
                new_manifest_path = os.path.join(new_mods, MANIFEST_NAME)
                
                # Check if mods folder exists in the extracted files
                if not os.path.isdir(new_mods):
                    messagebox.showerror('Error', 'No mods folder found in the downloaded zip!')
                    return
                
                # Create manifest if it doesn't exist
                if not os.path.isfile(new_manifest_path):
                    # Create manifest from the mods in the folder
                    with open(new_manifest_path, 'w') as f:
                        for mod in os.listdir(new_mods):
                            if mod.endswith('.jar'):
                                f.write(mod + '\n')
                
                # Read the new manifest
                with open(new_manifest_path, 'r') as f:
                    new_manifest = set(line.strip() for line in f if line.strip())
                
                # Remove mods that were in the old manifest but not in the new manifest
                for mod in old_manifest - new_manifest:
                    mod_path = os.path.join(mods_path, mod)
                    if os.path.isfile(mod_path):
                        os.remove(mod_path)
                
                # Copy new/updated mods from new_mods to mods_path
                for mod in new_manifest:
                    src = os.path.join(new_mods, mod)
                    dst = os.path.join(mods_path, mod)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                
                # Save the new manifest to the user's mods folder
                shutil.copy2(new_manifest_path, old_manifest_path)

                # If server mode is selected, filter out client-side mods
                if self.mode.get() == "server":
                    self.progress_label.config(text="Filtering server mods...")
                    self.root.update_idletasks()
                    included, excluded = self.filter_server_mods(mods_path)
                    messagebox.showinfo('Success', 
                        f'Server mods updated successfully!\n'
                        f'Included {len(included)} server mods\n'
                        f'Excluded {len(excluded)} client-side mods')
                else:
                    messagebox.showinfo('Success', 'Client mods updated successfully!')

        except Exception as e:
            messagebox.showerror('Error', f'Failed to update mods: {e}')
        finally:
            # Re-enable the update button and reset progress
            self.update_button.config(state='normal')
            self.progress_var.set(0)
            self.progress_label.config(text="")

def main():
    root = tk.Tk()
    app = ModpackUpdaterApp(root)
    root.mainloop()

if __name__ == '__main__':
    main() 