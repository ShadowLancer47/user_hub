import sys
import os

# Add the current directory to sys.path so we can import app
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("Successfully imported app.main")
except Exception as e:
    print(f"Error importing app.main: {e}")
    import traceback
    traceback.print_exc()
