from fastapi.templating import Jinja2Templates
from fastapi import Request
import sys
import os

# Mock Request
class MockRequest:
    def __init__(self):
        self.scope = {"type": "http"}

try:
    print("Initializing Jinja2Templates...")
    # Ensure we are in the right directory or use absolute paths
    # The app assumes running from project root
    templates = Jinja2Templates(directory=["app/templates", "app/tools/lol_tool/templates"])
    
    print("Attempting to render lol_dashboard.html...")
    request = MockRequest()
    response = templates.TemplateResponse("lol_dashboard.html", {"request": request})
    
    print("Render successful!")
    print(f"Content length: {len(response.body)}")
    
except Exception as e:
    print(f"Template Rendering Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
