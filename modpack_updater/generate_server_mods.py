import os
import shutil

SOURCE_MODS_FOLDER = 'mods'  # Change if needed
SERVER_MODS_FOLDER = 'server_mods'
MANIFEST_NAME = 'official_mods.txt'

# List of known client-side-only mods (add more as needed)
CLIENT_SIDE_MODS = [
    'Xaeros_Minimap',
    'MouseTweaks',
    'appleskin',
    'smoothchunk',
    'VisualWorkbench',
    'EasyAnvils',
    'NaturesCompass',
    'rightclickharvest',
    'LeavesBeGone',
    'oculus',
    'emi',
    'jei',
    'craftingtweaks',
    'guideme',
    'fast-ip-ping',
    'toofast',
    'Patchouli',
    # Add more client-side mod name fragments as needed
]

def is_client_side_mod(filename):
    lower = filename.lower()
    return any(fragment.lower() in lower for fragment in CLIENT_SIDE_MODS)

def generate_server_mods(source_folder=SOURCE_MODS_FOLDER, server_folder=SERVER_MODS_FOLDER, manifest_name=MANIFEST_NAME):
    if os.path.exists(server_folder):
        shutil.rmtree(server_folder)
    os.makedirs(server_folder, exist_ok=True)
    included = []
    excluded = []
    for f in os.listdir(source_folder):
        if f.endswith('.jar'):
            if is_client_side_mod(f):
                excluded.append(f)
            else:
                shutil.copy2(os.path.join(source_folder, f), os.path.join(server_folder, f))
                included.append(f)
    # Write manifest
    manifest_path = os.path.join(server_folder, manifest_name)
    with open(manifest_path, 'w') as f:
        for jar in sorted(included):
            f.write(jar + '\n')
    print(f"Server mods generated at {server_folder} with {len(included)} mods.")
    if excluded:
        print(f"Excluded {len(excluded)} client-side mods:")
        for mod in excluded:
            print(f"  - {mod}")

if __name__ == '__main__':
    generate_server_mods() 