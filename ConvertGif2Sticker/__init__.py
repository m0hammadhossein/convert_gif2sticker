from pathlib import Path

# Define base directory
BASE_DIR = Path(__file__).parent

# Create 'files' directory if it doesn't exist
files_dir = BASE_DIR / 'files'
files_dir.mkdir(exist_ok=True)