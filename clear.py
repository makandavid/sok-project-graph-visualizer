import shutil
import os

def clear_project_files():
    """Removes __pycache__, build and egg-info directories, and sqlite Django db files."""
    print("Clearing build and cache files...")

    directories_to_remove = ['__pycache__', 'build', 'lib', '.pytest_cache']

    for root, dirs, files in os.walk('.', topdown=True):
        dirs.remove(".venv") if ".venv" in dirs else None
        dirs.remove("venv") if "venv" in dirs else None

        # Remove matching directories (including *.egg-info)
        for directory in dirs[:]:  # iterate over a copy so we can modify dirs
            dir_path = os.path.join(root, directory)
            if directory in directories_to_remove or directory.endswith('.egg-info'):
                try:
                    shutil.rmtree(dir_path)
                    print(f"Removed directory: {dir_path}")
                except Exception as e:
                    print(f"Failed to remove directory {dir_path}: {e}")
                # prevent os.walk from descending into removed directory
                try:
                    dirs.remove(directory)
                except ValueError:
                    pass

        # Remove files that happen to end with .egg-info (rare)
        for file in files:
            if file.endswith('.egg-info'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                except Exception as e:
                    print(f"Failed to remove file {file_path}: {e}")

    # Remove top-level *.egg-info directories and build/lib if still present
    for item in os.listdir('.'):
        item_path = os.path.join('.', item)
        if item.endswith('.egg-info') and os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                print(f"Removed egg-info directory: {item_path}")
            except Exception as e:
                print(f"Failed to remove egg-info directory {item_path}: {e}")
        if item == 'build':
            build_path = os.path.join('.', 'build')
            lib_path = os.path.join(build_path, 'lib')
            if os.path.exists(lib_path):
                try:
                    shutil.rmtree(lib_path)
                    print(f"Removed directory: {lib_path}")
                except Exception as e:
                    print(f"Failed to remove directory {lib_path}: {e}")

    print("Checking for Django database files...")
    db_path = os.path.join('graph_explorer', 'db.sqlite3')
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed Django database file: {db_path}")
        except Exception as e:
            print(f"Failed to remove database file {db_path}: {e}")
    else:
        print("Django database file not found. Nothing to remove.")                    

    print("Cleanup complete.")

if __name__ == "__main__":
    clear_project_files()