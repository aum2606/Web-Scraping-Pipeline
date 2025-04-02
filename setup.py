import os
import sys
import subprocess
from pathlib import Path

def run_command(command):
    """Run a command and print its output."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Output: {e.output}")
        return False
    return True

def main():
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    
    # Install required packages
    print("Installing required packages...")
    if not run_command("pip install -r requirements.txt"):
        print("Failed to install required packages")
        return
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["WEATHER_API_KEY"] = "ca27add26ea1d73943098e62635feb71"
    
    # Import and run the scraper application
    print("\nStarting scraper application...")
    try:
        from src.main import ScraperApp
        app = ScraperApp()
        app.run(run_immediately=True, use_scheduler=True)
    except Exception as e:
        print(f"Error running scraper application: {e}")

if __name__ == "__main__":
    main() 