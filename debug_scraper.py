import requests
from bs4 import BeautifulSoup

def inspect_page():
    url = "https://www.leagueofgraphs.com/champions/builds/ahri"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Inspect Matchups
        print("\n--- Matchup Inspection ---")
        for header_text in ["Counters", "Is countered by"]:
            header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and header_text in tag.get_text())
            if header:
                print(f"Found header: {header.get_text().strip()}")
                container = header.find_next('div')
                if container:
                    print(f"Found container after {header_text}")
                    # Try to find images
                    imgs = container.find_all('img')
                    print(f"Found {len(imgs)} images")
                    for i, img in enumerate(imgs[:10]):
                        print(f"  Img {i}: Alt: '{img.get('alt')}' | Src: {img.get('src')}")
                else:
                    print(f"No container found after {header_text}")
            else:
                print(f"Header '{header_text}' not found")


                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_page()
