from app.tools.lol_tool.scraper import scrape_champion
import json
import sys

try:
    print("Calling scrape_champion('ahri')...")
    data = scrape_champion("ahri")
    
    if data is None:
        print("scrape_champion returned None (Handled Error)")
        sys.exit(0)
        
    print("Data received. Attempting JSON serialization...")
    try:
        json_str = json.dumps(data)
        print("JSON serialization successful.")
        print(f"Data size: {len(json_str)} bytes")
    except TypeError as e:
        print(f"JSON Serialization Failed: {e}")
        # Find non-serializable items
        print("Inspecting data for non-serializable items...")
        # Recursive check could go here, but let's just print type of keys
        sys.exit(1)
        
except Exception as e:
    print(f"Unhandled Exception during execution: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
