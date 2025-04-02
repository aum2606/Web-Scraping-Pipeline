import os
import sys
from pathlib import Path

# Get the absolute path of the project root directory
project_root = Path(__file__).parent.absolute()

# Add the project root to Python path
sys.path.insert(0, str(project_root))

# Import and run the main function
from src.main import ScraperApp

if __name__ == "__main__":
    app = ScraperApp()
    app.run(run_immediately=True, use_scheduler=True) 