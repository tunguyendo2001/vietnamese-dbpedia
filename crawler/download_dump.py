import requests
import json
import os
import time
from tqdm import tqdm

HEADERS = {"User-Agent": "VietnameseDBpediaMini/1.0 (contact@example.com)"}
API_URL = "https://vi.wikipedia.org/w/api.php"

def fetch_category_members(category_name, limit=500, cmtype="page"):
    """Fetch members of a category with pagination support."""
    titles = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Thể loại:{category_name}",
        "cmlimit": min(limit, 500),
        "cmtype": cmtype,
        "format": "json"
    }
    
    while len(titles) < limit:
        try:
            response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
            if response.status_code != 200:
                break
            data = response.json()
        except Exception:
            break
        
        members = data.get('query', {}).get('categorymembers', [])
        if cmtype == "page":
            titles.extend(item['title'] for item in members if item['ns'] == 0)
        else:
            titles.extend(item['title'].replace("Thể loại:", "") for item in members)
        
        # Handle pagination
        if 'continue' in data:
            params['cmcontinue'] = data['continue']['cmcontinue']
        else:
            break
    
    return titles[:limit]

def fetch_category_recursive(category_name, limit=500, depth=1):
    """Fetch articles from a category and its subcategories (up to depth levels)."""
    titles = fetch_category_members(category_name, limit=limit, cmtype="page")
    
    if depth > 0:
        subcats = fetch_category_members(category_name, limit=50, cmtype="subcat")
        for subcat in subcats:
            if len(titles) >= limit:
                break
            remaining = limit - len(titles)
            sub_titles = fetch_category_recursive(subcat, limit=min(remaining, 200), depth=depth - 1)
            titles.extend(sub_titles)
    
    return titles[:limit]

def fetch_article_content(title):
    url = API_URL
    params = {
        "action": "query",
        "prop": "revisions|langlinks",
        "titles": title,
        "rvprop": "content",
        "lllimit": 500,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return None
        data = response.json()
    except Exception:
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
    # Top-level categories (will crawl 1 level of subcategories)
    top_categories = [
        "Lịch_sử_Việt_Nam",
        "Công_ty_Việt_Nam",
        "Người_Việt_Nam",
        "Nhân_vật_lịch_sử_Việt_Nam",
    ]
    
    # Specific subcategories known to have many direct articles
    direct_categories = [
        # -- Nhân vật --
        "Chính_khách_Việt_Nam",
        "Nhà_văn_Việt_Nam",
        "Nhà_thơ_Việt_Nam",
        "Nhạc_sĩ_Việt_Nam",
        "Nhà_báo_Việt_Nam",
        "Đạo_diễn_Việt_Nam",
        "Nhà_khoa_học_Việt_Nam",
        "Nhà_toán_học_Việt_Nam",
        "Nghệ_sĩ_Việt_Nam",
        "Diễn_viên_Việt_Nam",
        "Ca_sĩ_Việt_Nam",
        "Vua_Việt_Nam",
        "Sĩ_quan_Quân_đội_nhân_dân_Việt_Nam",
        # -- Tổ chức / Công ty --
        "Công_ty_cổ_phần_Việt_Nam",
        "Doanh_nghiệp_nhà_nước_Việt_Nam",
        "Nhãn_hiệu_Việt_Nam",
        "Ngân_hàng_Việt_Nam",
        "Hãng_hàng_không_Việt_Nam",
        "Công_ty_công_nghệ_thông_tin_Việt_Nam",
        "Tổng_công_ty_Việt_Nam",
        # -- Địa lý --
        "Tỉnh_thành_Việt_Nam",
        "Thành_phố_trực_thuộc_trung_ương_(Việt_Nam)",
        "Đảo_Việt_Nam",
        "Hồ_Việt_Nam",
        "Núi_Việt_Nam",
        "Đường_cao_tốc_Việt_Nam",
        # -- Giáo dục --
        "Đại_học_Việt_Nam",
        # -- Lịch sử --
        "Triều_đại_Việt_Nam",
        "Chiến_tranh_liên_quan_tới_Việt_Nam",
        # -- Văn hóa --
        "Chùa_Việt_Nam",
        "Di_tích_Việt_Nam",
        "Thể_thao_Việt_Nam",
    ]
    
    target_count = 3000
    all_titles = []
    
    print("Fetching titles from top-level categories (with subcategory crawling)...")
    for cat in top_categories:
        print(f"  Crawling: {cat}")
        titles = fetch_category_recursive(cat, limit=500, depth=1)
        all_titles.extend(titles)
        print(f"    Found {len(titles)} titles")
    
    print("Fetching titles from specific categories...")
    for cat in direct_categories:
        print(f"  Fetching: {cat}")
        titles = fetch_category_members(cat, limit=500)
        all_titles.extend(titles)
        print(f"    Found {len(titles)} titles")
    
    # Deduplicate and limit
    all_titles = list(dict.fromkeys(all_titles))[:target_count]
    print(f"\nTotal unique titles: {len(all_titles)}")
    
    os.makedirs("data/raw", exist_ok=True)
    
    # Skip already downloaded files
    existing = set(os.listdir("data/raw"))
    to_download = []
    for title in all_titles:
        filename = title.replace("/", "_").replace(" ", "_") + ".json"
        if filename not in existing:
            to_download.append(title)
    
    print(f"Already downloaded: {len(all_titles) - len(to_download)}")
    print(f"To download: {len(to_download)}")
    
    print("Downloading article contents...")
    for title in tqdm(to_download):
        data = fetch_article_content(title)
        if data:
            filename = title.replace("/", "_").replace(" ", "_") + ".json"
            with open(os.path.join("data/raw", filename), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        time.sleep(0.1)  # Be respectful to Wikipedia API

if __name__ == "__main__":
    main()
