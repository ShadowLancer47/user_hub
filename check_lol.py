import sys
import os

sys.path.append(os.getcwd())

try:
    from app.tools.lol_tool import router
    print("Successfully imported app.tools.lol_tool.router")
except Exception as e:
    print(f"Error importing router: {e}")
    import traceback
    traceback.print_exc()
