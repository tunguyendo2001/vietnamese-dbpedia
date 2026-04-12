# wikipedia_crawler.py
import requests
import json
import time
from urllib.parse import unquote
import re


class VietnameseWikipediaCrawler:
    def __init__(self):
        self.base_url = "https://vi.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Vietnamese-DBpedia-Bot/1.0 (https://github.com/vietnamese-dbpedia; contact@example.com)'
        })

    def get_page_content(self, title):
        """Lấy nội dung trang Wikipedia"""
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'extracts|pageprops|categories|links',
            'exintro': True,
            'explaintext': True,
            'redirects': True
        }

        try:
            response = self.session.get(self.base_url, params=params)
            data = response.json()

            page_data = {}
            for page_id, page in data['query']['pages'].items():
                if 'extract' in page:
                    page_data = {
                        'title': page.get('title'),
                        'extract': page.get('extract'),
                        'categories': [cat['title'] for cat in page.get('categories', [])],
                        'links': [link['title'] for link in page.get('links', [])],
                        'pageprops': page.get('pageprops', {})
                    }
            return page_data
        except Exception as e:
            print(f"Lỗi khi lấy trang {title}: {e}")
            return None

    def get_infobox_data(self, title):
        """Trích xuất dữ liệu từ infobox"""
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'revisions',
            'rvprop': 'content',
            'rvslots': 'main'
        }

        try:
            response = self.session.get(self.base_url, params=params)
            data = response.json()

            for page_id, page in data['query']['pages'].items():
                if 'revisions' in page:
                    content = page['revisions'][0]['slots']['main']['*']
                    return self.parse_infobox(content)
            return {}
        except Exception as e:
            print(f"Lỗi khi lấy infobox {title}: {e}")
            return {}

    def parse_infobox(self, content):
        """Parse infobox từ wikitext"""
        infobox_data = {}

        # Tìm infobox
        infobox_match = re.search(r'\{\{Infobox[^}]*\}\}', content, re.DOTALL | re.IGNORECASE)
        if infobox_match:
            infobox_text = infobox_match.group()

            # Trích xuất các field
            field_pattern = r'\|\s*([^=]+)\s*=\s*([^|]*)'
            matches = re.findall(field_pattern, infobox_text)

            for key, value in matches:
                key = key.strip()
                value = value.strip()
                if value:
                    infobox_data[key] = value

        return infobox_data

    def get_category_pages(self, category, limit=100):
        """Lấy danh sách trang trong category"""
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'categorymembers',
            'cmtitle': f'Thể loại:{category}',
            'cmlimit': limit
        }

        try:
            response = self.session.get(self.base_url, params=params)
            data = response.json()

            pages = []
            for page in data['query']['categorymembers']:
                pages.append(page['title'])
            return pages
        except Exception as e:
            print(f"Lỗi khi lấy category {category}: {e}")
            return []


# Sử dụng
def collect_wikipedia_data():
    crawler = VietnameseWikipediaCrawler()

    # Lấy dữ liệu từ một số category quan trọng
    categories = [
        'Nhân vật lịch sử Việt Nam',
        'Thành phố Việt Nam',
        'Trường đại học Việt Nam',
        'Công ty Việt Nam'
    ]

    all_data = []
    for category in categories:
        print(f"Đang xử lý category: {category}")
        pages = crawler.get_category_pages(category, limit=50)

        for page_title in pages:
            print(f"Đang xử lý: {page_title}")
            page_data = crawler.get_page_content(page_title)
            infobox_data = crawler.get_infobox_data(page_title)

            if page_data:
                page_data['infobox'] = infobox_data
                page_data['category'] = category
                all_data.append(page_data)

            time.sleep(0.5)  # Tránh spam server

    # Lưu dữ liệu
    with open('vietnamese_wikipedia_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"Đã thu thập {len(all_data)} trang Wikipedia")
    return all_data

if __name__ == "__main__":
    collect_wikipedia_data()