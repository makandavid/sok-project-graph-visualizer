import subprocess
import sys

def run_command(command):
    """Runs a shell command and prints the output."""
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        sys.exit(e.returncode)

def run_server():
    """Starts the Django development server."""
    print("Running migrations...")
    run_command("cd graph_explorer && python manage.py makemigrations && python manage.py migrate")
    print("Migrations complete.")
    print("Starting Django development server...")
    run_command("cd graph_explorer && python manage.py runserver")

if __name__ == "__main__":
    run_server()