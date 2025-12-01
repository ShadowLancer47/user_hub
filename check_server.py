import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())

try:
    from app.main import app
    client = TestClient(app)
    
    print("Sending GET request to / ...")
    response = client.get("/")
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Root endpoint returned 200 OK.")
    else:
        print("Failed!")
        print(response.text)
        
except Exception as e:
    print(f"Error during request: {e}")
    import traceback
    traceback.print_exc()
