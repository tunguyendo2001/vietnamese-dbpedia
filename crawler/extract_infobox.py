import mwparserfromhell
import json
import os
from tqdm import tqdm

def extract_infobox(wikitext):
    code = mwparserfromhell.parse(wikitext)
    infoboxes = []
    for template in code.filter_templates():
        name = str(template.name.strip())
        if name.lower().startswith("thông tin") or name.lower().startswith("infobox"):
            data = {}
            for param in template.params:
                name = str(param.name.strip())
                value = str(param.value.strip())
                if value:
                    data[name] = value
            infoboxes.append({
                "template": str(template.name.strip()),
                "data": data
            })
    return infoboxes

def main():
    raw_dir = "data/raw"
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    
    files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    print(f"Extracting infoboxes from {len(files)} files...")
    
    for filename in tqdm(files):
        with open(os.path.join(raw_dir, filename), 'r', encoding='utf-8') as f:
            article = json.load(f)
        
        infoboxes = extract_infobox(article['content'])
        
        result = {
            "title": article['title'],
            "en_title": article.get('en_title'),
            "infoboxes": infoboxes
        }
        
        with open(os.path.join(processed_dir, filename), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
