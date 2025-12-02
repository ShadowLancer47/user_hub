import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_champion(champion_name: str):
    """
    Scrapes LeagueOfGraphs for champion data.
    """
    champion_name = champion_name.lower().replace(" ", "").replace("'", "").replace(".", "")
    # Handle special cases like wukong -> monkeyking if needed, but LoG usually handles standard names well.
    # Nunu & Willump -> nunu
    if champion_name == "nunu&willump": champion_name = "nunu"
    if champion_name == "renata" or champion_name == "renataglasc": champion_name = "renata"

    url = f"https://www.leagueofgraphs.com/champions/builds/{champion_name}"
    logger.info(f"Fetching data from {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to fetch data: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        data = {
            "name": champion_name,
            "icon": f"https://ddragon.leagueoflegends.com/cdn/img/champion/tiles/{champion_name.capitalize()}_0.jpg", # Fallback/Generic
            "items": [],
            "runes": {"primary": [], "secondary": []},
            "skills": [],
            "matchups": {"good": [], "bad": []}
        }

        # --- Items ---
        # Initialize categories
        data["items"] = {
            "starting": [],
            "core": [],
            "final": [],
            "boots": []
        }
        
        ddragon_ver = "14.23.1"
        
        # Find all item rows
        rows = soup.select('div.iconsRow')
        logger.info(f"Found {len(rows)} item rows")
        
        for row in rows:
            # Find the preceding header/label
            # We use find_previous to get the nearest header regardless of nesting
            header = row.find_previous(['h2', 'h3', 'h4'])
            
            if header:
                text = header.get_text().strip().lower()
                logger.info(f"Row header text: '{text}'")
                
                category = None
                if "starting" in text:
                    category = "starting"
                elif "core" in text:
                    category = "core"
                elif "end game" in text or "final" in text:
                    category = "final"
                elif "boots" in text:
                    category = "boots"
                
                if category:
                    imgs = row.select('img.requireTooltip')
                    seen_in_cat = set()
                    
                    # Special handling for Core Items:
                    # If there are 4 items, the first one is likely an "Early Item" (component).
                    # We will move it to a new category "early".
                    if category == "core" and len(imgs) >= 4:
                        # Process the first item as "early"
                        first_img = imgs[0]
                        tooltip_var = first_img.get('tooltip-var', '')
                        alt_text = first_img.get('alt', '')
                        
                        if 'item-' in tooltip_var:
                            item_id = tooltip_var.replace('item-', '')
                            if alt_text:
                                icon_url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_ver}/img/item/{item_id}.png"
                                if "early" not in data["items"]:
                                    data["items"]["early"] = []
                                data["items"]["early"].append({
                                    "name": alt_text,
                                    "icon": icon_url
                                })
                        
                        # Process the rest as "core"
                        imgs = imgs[1:]
                    
                    for img in imgs:
                        tooltip_var = img.get('tooltip-var', '')
                        alt_text = img.get('alt', '')
                        
                        if 'item-' in tooltip_var:
                            item_id = tooltip_var.replace('item-', '')
                            if alt_text and alt_text not in seen_in_cat:
                                seen_in_cat.add(alt_text)
                                icon_url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_ver}/img/item/{item_id}.png"
                                
                                data["items"][category].append({
                                    "name": alt_text,
                                    "icon": icon_url
                                })
                                
                                # Limit items per category as requested
                                if category in ["starting", "core", "final"] and len(data["items"][category]) >= 3:
                                    break
                                if category == "boots" and len(data["items"][category]) >= 1:
                                    break

        # --- Runes ---
        # Fetch Rune Mapping from DDragon
        rune_map = {}
        try:
            # Get latest DDragon version
            versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
            ddragon_ver = requests.get(versions_url).json()[0]
            
            rune_json_url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_ver}/data/en_US/runesReforged.json"
            rune_data = requests.get(rune_json_url).json()
            for tree in rune_data:
                # Map tree icon? Maybe later.
                for slot in tree['slots']:
                    for rune in slot['runes']:
                        rune_map[str(rune['id'])] = rune['icon']
        except Exception as e:
            logger.error(f"Failed to fetch rune mapping: {e}")
            # Fallback version if fetch fails, though likely rune fetch will fail too
            ddragon_ver = "13.24.1" 

        # Look for all perksTableOverview tables
        perks_tables = soup.select('.perksTableOverview')
        selected_runes = []
        
        if perks_tables:
            for perks_table in perks_tables:
                # Find all images that require tooltip
                imgs = perks_table.select('img.requireTooltip')
                
                for img in imgs:
                    # Check parent opacity to determine if selected
                    parent = img.parent
                    style = parent.get('style', '')
                    opacity = 1.0
                    if 'opacity' in style:
                        try:
                            opacity = float(style.split('opacity:')[1].split(';')[0].strip())
                        except:
                            pass
                    
                    # If opacity is high (selected), process it
                    if opacity > 0.5:
                        alt = img.get('alt', 'Unknown')
                        class_list = img.get('class', [])
                        
                        # Extract ID from class (e.g., perk-8112-48)
                        rune_id = None
                        for cls in class_list:
                            if cls.startswith('perk-'):
                                parts = cls.split('-')
                                if len(parts) >= 2:
                                    rune_id = parts[1]
                                    break
                        
                        icon_url = ""
                        if rune_id and rune_id in rune_map:
                            icon_url = f"https://ddragon.leagueoflegends.com/cdn/img/{rune_map[rune_id]}"
                        
                        selected_runes.append({
                            "name": alt,
                            "icon": icon_url,
                            "id": rune_id
                        })
            
            logger.info(f"Found {len(selected_runes)} selected runes.")
            
            # Categorize Runes
            # Expected: 4 Primary, 2 Secondary, 3 Shards (Stats)
            # Note: Shards might not be in runesReforged.json (they are stat mods).
            # Stat mods IDs: 5001, 5002, 5003, 5005, 5007, 5008
            # We might need a separate mapping or fallback for shards.
            # Shard icons are usually: https://ddragon.leagueoflegends.com/cdn/img/perk-images/StatMods/{ID}.png
            
            # Let's handle Shards manually if they are missing from map
            for rune in selected_runes:
                if not rune['icon'] and rune['id']:
                    # Try StatMod path
                    rune['icon'] = f"https://ddragon.leagueoflegends.com/cdn/img/perk-images/StatMods/StatMods{rune['id']}Icon.png"
                    # Some IDs might map differently, but this is a good guess for common shards.
                    # Actually, let's verify shard IDs.
                    # 5008: Adaptive Force -> StatModsAdaptiveForceIcon.png
                    # 5005: Attack Speed -> StatModsAttackSpeedIcon.png
                    # 5002: Armor -> StatModsArmorIcon.png
                    # 5003: Magic Resist -> StatModsMagicResIcon.png
                    # 5001: Health -> StatModsHealthScalingIcon.png
                    # 5007: Haste -> StatModsCDRScalingIcon.png
                    
                    # Simple map for shards
                    shard_map = {
                        "5008": "StatModsAdaptiveForceIcon.png",
                        "5005": "StatModsAttackSpeedIcon.png",
                        "5002": "StatModsArmorIcon.png",
                        "5003": "StatModsMagicResIcon.png",
                        "5001": "StatModsHealthScalingIcon.png",
                        "5007": "StatModsCDRScalingIcon.png"
                    }
                    if rune['id'] in shard_map:
                         rune['icon'] = f"https://ddragon.leagueoflegends.com/cdn/img/perk-images/StatMods/{shard_map[rune['id']]}"

            # Assign to data
            # We assume the order is Primary -> Secondary -> Shards
            if len(selected_runes) >= 4:
                data["runes"]["primary"] = selected_runes[:4]
            if len(selected_runes) >= 6:
                data["runes"]["secondary"] = selected_runes[4:6]
            # We can also add shards if we want, but the UI currently only has Primary/Secondary sections.
            # The user asked for "same scheme", so maybe we should add shards?
            # For now, let's stick to Primary/Secondary as the UI supports it.
            # If the user wants shards, we can add a "stats" section later.
            # Wait, the user said "fix the rune tab".
            # I'll add shards to "secondary" for now or create a new key if the UI can handle it.
            # The UI loops through primary and secondary.
            # I'll just put shards in secondary for now to ensure they show up, or ignore them if it breaks layout.
            # Let's just do Primary (4) and Secondary (2) for now to be safe, as that's what the UI expects.
            # But wait, if I have 9 runes, and I only show 6, the user might complain.
            # I'll add a "stats" key to data and update UI to show it.
            
            if len(selected_runes) >= 9:
                 data["runes"]["stats"] = selected_runes[6:9]

        # --- Skills ---
        # Parse the skill order
        # Look for "Skill Order" header
        skill_header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and "Skill Order" in tag.get_text())
        
        if skill_header:
            container = skill_header.find_next('div')
            if container:
                spells = container.select('.championSpell')
                skill_order_keys = []
                for spell in spells:
                    text = spell.get_text().strip()
                    if text in ['Q', 'W', 'E', 'R']:
                        skill_order_keys.append(text)
                
                # Fetch Champion Data for Spell Images
                try:
                    # DDragon requires proper capitalization for keys (e.g. "Ahri", "MonkeyKing")
                    # We have champion_name which is lowercased/stripped.
                    # We can try to guess or use the one from the page if available, but DDragon usually works with capitalized first letter for most.
                    # Exception: Wukong -> MonkeyKing, etc.
                    # Let's try to use the name we have, capitalized.
                    # If it fails, we might need a mapping or just show no image.
                    
                    # Better approach: Get all champs list to find the real key
                    # But that's heavy. Let's try simple capitalization first.
                    # "nunu" -> "Nunu" (DDragon might expect "Nunu")
                    
                    ddragon_champ_name = champion_name.capitalize()
                    # Special cases
                    if champion_name == "wukong": ddragon_champ_name = "MonkeyKing"
                    if champion_name == "kogmaw": ddragon_champ_name = "KogMaw"
                    if champion_name == "reksai": ddragon_champ_name = "RekSai"
                    # ... add more as needed or rely on basic cap
                    
                    champ_url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_ver}/data/en_US/champion/{ddragon_champ_name}.json"
                    champ_data_resp = requests.get(champ_url)
                    
                    spell_map = {}
                    if champ_data_resp.status_code == 200:
                        c_data = champ_data_resp.json()['data'][ddragon_champ_name]
                        # Spells are in order Q, W, E, R
                        spells_list = c_data['spells']
                        if len(spells_list) >= 4:
                            spell_map['Q'] = spells_list[0]['image']['full']
                            spell_map['W'] = spells_list[1]['image']['full']
                            spell_map['E'] = spells_list[2]['image']['full']
                            spell_map['R'] = spells_list[3]['image']['full']
                    
                    # Construct skill objects
                    final_skills = []
                    for key in skill_order_keys:
                        icon = ""
                        if key in spell_map:
                            icon = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_ver}/img/spell/{spell_map[key]}"
                        
                        final_skills.append({
                            "key": key,
                            "icon": icon
                        })
                    
                    if final_skills:
                        data["skills"] = final_skills[:4]

                except Exception as e:
                    logger.error(f"Failed to fetch spell images: {e}")
                    # Fallback to just keys
                    data["skills"] = [{"key": k, "icon": ""} for k in skill_order_keys[:4]]

        
        if not data["skills"]:
             # Fallback to old method if new one fails
             pass

        # --- Matchups ---
        # Look for "Counters" and "Is countered by" headers
        # These are usually h3 or div with specific text.
        
        def format_champion_name_for_ddragon(name):
            # Remove spaces, apostrophes, periods
            clean_name = name.replace(" ", "").replace("'", "").replace(".", "")
            # Special cases
            special_cases = {
                "Wukong": "MonkeyKing",
                "RenataGlasc": "Renata",
                "Nunu&Willump": "Nunu",
                "KogMaw": "KogMaw",
                "RekSai": "RekSai",
                "LeBlanc": "Leblanc", # DDragon uses Leblanc usually, but let's check. Actually LeBlanc is often LeBlanc. 
                                      # Checking common ones: Cho'Gath -> ChoGath, Kai'Sa -> KaiSa.
                                      # Wukong -> MonkeyKing is the big one.
            }
            return special_cases.get(clean_name, clean_name)

        def extract_matchups(header_text):
            # Find header containing text
            header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and header_text in tag.get_text())
            champs = []
            if header:
                # Look for the next table or list
                # Often it's a div containing rows
                container = header.find_next('div')
                if container:
                    # Look for images with alt text
                    imgs = container.find_all('img')
                    for img in imgs:
                        alt = img.get('alt')
                        if alt:
                            # Use DDragon URL
                            formatted_name = format_champion_name_for_ddragon(alt.strip())
                            icon_url = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_ver}/img/champion/{formatted_name}.png"
                            champs.append({'name': alt.strip(), 'icon': icon_url})
                        if len(champs) >= 5: break
            return champs

        data["matchups"]["good"] = extract_matchups("Counters")
        data["matchups"]["bad"] = extract_matchups("Is countered by")
        
        return data

    except Exception as e:
        logger.error(f"Error scraping {champion_name}: {e}")
        return None

if __name__ == "__main__":
    # Test run
    print(scrape_champion("ahri"))
