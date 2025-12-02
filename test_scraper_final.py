from app.tools.lol_tool.scraper import scrape_champion
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

def test_scraper():
    print("Testing scraper for 'Ahri'...")
    data = scrape_champion("ahri")
    
    if data:
        print(f"Champion: {data['name']}")
        print("Items:")
        for category, items in data['items'].items():
            print(f"  {category.capitalize()}: {len(items)} items")
            for item in items:
                print(f"    - {item['name']}")
        
        print("Runes:")
        if "primary" in data["runes"]:
            print(f"  Primary: {len(data['runes']['primary'])} runes")
            for rune in data["runes"]["primary"]:
                print(f"    - {rune['name']} (ID: {rune.get('id')}) | Icon: {rune['icon']}")
        if "secondary" in data["runes"]:
            print(f"  Secondary: {len(data['runes']['secondary'])} runes")
            for rune in data["runes"]["secondary"]:
                print(f"    - {rune['name']} (ID: {rune.get('id')}) | Icon: {rune['icon']}")
        if "stats" in data["runes"]:
            print(f"  Stats: {len(data['runes']['stats'])} runes")
            for rune in data["runes"]["stats"]:
                print(f"    - {rune['name']} (ID: {rune.get('id')}) | Icon: {rune['icon']}")
    else:
        print("Scraper returned None")

if __name__ == "__main__":
    test_scraper()
