import requests
import json
import os
from tqdm import tqdm

def fetch_category_members(category_name, limit=500):
    url = "https://vi.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Thể loại:{category_name}",
        "cmlimit": min(limit, 500),
        "format": "json"
    }
    
    titles = []
    headers = {"User-Agent": "VietnameseDBpediaMini/1.0 (contact@example.com)"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching category {category_name}: {response.status_code}")
        return []
    
    try:
        data = response.json()
    except Exception as e:
        print(f"Error parsing JSON for category {category_name}: {e}")
        return []
        
    titles = []
    if 'query' in data:
        titles = [item['title'] for item in data['query']['categorymembers'] if item['ns'] == 0]
    
    return titles

def fetch_article_content(title):
    url = "https://vi.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "revisions|langlinks",
        "titles": title,
        "rvprop": "content",
        "lllimit": 500,
        "format": "json"
    }
    
    headers = {"User-Agent": "VietnameseDBpediaMini/1.0 (contact@example.com)"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None
        
    try:
        data = response.json()
    except:
        return None
        
    pages = data.get('query', {}).get('pages', {})
    for page_id, page_data in pages.items():
        if 'revisions' in page_data:
            content = page_data['revisions'][0]['*']
            langlinks = page_data.get('langlinks', [])
            en_title = next((link['*'] for link in langlinks if link['lang'] == 'en'), None)
            return {
                "title": title,
                "content": content,
                "en_title": en_title
            }
    return None

def main():
    categories = [
        "Người_Việt_Nam", 
        "Thành_phố_Việt_Nam", 
        "Lịch_sử_Việt_Nam",
        "Sông_tại_Việt_Nam",
        "Tỉnh_Việt_Nam",
        "Nhân_vật_lịch_sử_Việt_Nam",
        "Đại_học_tại_Việt_Nam",
        "Công_ty_Việt_Nam"
    ]
    target_count = 1000
    all_titles = []
    
    print("Fetching titles from categories...")
    for cat in categories:
        titles = fetch_category_members(cat, limit=400)
        all_titles.extend(titles)
    
    all_titles = list(set(all_titles))[:target_count]
    print(f"Total titles found: {len(all_titles)}")
    
    os.makedirs("data/raw", exist_ok=True)
    
    print("Downloading article contents...")
    for title in tqdm(all_titles):
        data = fetch_article_content(title)
        if data:
            filename = title.replace("/", "_").replace(" ", "_") + ".json"
            with open(os.path.join("data/raw", filename), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
