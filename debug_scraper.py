import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def debug_scrape(champion):
    url = f"https://www.leagueofgraphs.com/champions/builds/{champion}"
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Check Title
        print(f"Title: {soup.title.string.strip()}")
        
        # 2. Look for Item Images (Detailed)
        print("\n--- Searching for Items (Detailed) ---")
        item_imgs = soup.select('img.requireTooltip')
        for i, img in enumerate(item_imgs[:5]):
            print(f"Item {i}: src='{img.get('src')}', data-src='{img.get('data-src')}', data-original='{img.get('data-original')}', class='{img.get('class')}'")

        # 3. Inspect Runes (Active vs Inactive)
        print("\n--- Inspecting Runes (Active Check) ---")
        perks_table = soup.select_one('.perksTableOverview')
        if perks_table:
            rune_imgs = perks_table.select('img.requireTooltip')
            for i, img in enumerate(rune_imgs[:10]):
                # Check parent style or class for opacity/selection
                parent = img.parent
                print(f"Rune {i}: alt='{img.get('alt')}', style='{img.get('style')}', parent_style='{parent.get('style')}', parent_class='{parent.get('class')}'")

        # 4. Inspect Skill Order Table
        print("\n--- Inspecting Skill Order Table ---")
        # Find table with "Q", "W", "E", "R"
        tables = soup.find_all('table')
        for table in tables:
            text = table.get_text()
            if "Q" in text and "W" in text and "E" in text and "R" in text:
                print("Found potential skill table:")
                # Print first few rows
                rows = table.find_all('tr')
                for j, row in enumerate(rows[:6]):
                    print(f"Row {j}: {row.prettify()[:200]}")
                break

        # 5. Inspect Matchups Headers
        print("\n--- Inspecting Matchups Headers ---")
        headers = soup.find_all(['h2', 'h3', 'h4', 'div']) # div sometimes used for headers
        for h in headers:
            text = h.get_text().strip()
            if "Counters" in text or "countered" in text or "Win Rate" in text:
                print(f"Potential Matchup Header: '{text}' (Tag: {h.name})")
                # Print next sibling
                print(f"Next Sibling: {h.find_next().name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_scrape("ahri")

if __name__ == "__main__":
    debug_scrape("ahri")
