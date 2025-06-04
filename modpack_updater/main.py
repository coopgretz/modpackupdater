import os
import shutil
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import zipfile

# Set your Google Drive file ID here
GOOGLE_DRIVE_FILE_ID = 'YOUR_FILE_ID_HERE'  # TODO: Replace with your file ID
MODS_FOLDER_NAME = 'mods'
MANIFEST_NAME = 'official_mods.txt'

DOWNLOAD_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}'

class ModpackUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Modpack Updater')
        self.instance_path = tk.StringVar()

        tk.Label(root, text='Select your CurseForge instance folder:').pack(pady=5)
        tk.Entry(root, textvariable=self.instance_path, width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(root, text='Browse', command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(root, text='Update Mods', command=self.update_mods).pack(pady=20)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.instance_path.set(folder)

    def update_mods(self):
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
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, 'mods.zip')
                # Download the zip file from Google Drive
                self.download_file(DOWNLOAD_URL, zip_path)
                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                new_mods = os.path.join(tmpdir, MODS_FOLDER_NAME)
                new_manifest_path = os.path.join(new_mods, MANIFEST_NAME)
                if not os.path.isdir(new_mods):
                    messagebox.showerror('Error', 'No mods folder found in the downloaded zip!')
                    return
                if not os.path.isfile(new_manifest_path):
                    messagebox.showerror('Error', f'Manifest file {MANIFEST_NAME} not found in the downloaded mods folder!')
                    return
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
            messagebox.showinfo('Success', 'Mods folder updated successfully!')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to update mods: {e}')

    def download_file(self, url, dest):
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

def main():
    root = tk.Tk()
    app = ModpackUpdaterApp(root)
    root.mainloop()

if __name__ == '__main__':
    main() 