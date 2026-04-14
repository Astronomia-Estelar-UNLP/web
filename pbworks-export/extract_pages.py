import os
import json
import re
from html.parser import HTMLParser

class PBWorksParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_content = False
        self.content_html = []
        self.page_title = ""
        self.capture_title = False
        self.div_level = 0
        self.content_level = -1

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'title' and not self.page_title:
            self.capture_title = True
            
        # Updated targeting for PBworks content
        is_content_start = (attrs_dict.get('id') == 'main-content' or 
                           'page-content' in str(attrs_dict.get('class', '')) or
                           'wiki' in str(attrs_dict.get('class', '')))
        
        if is_content_start:
            if not self.in_content:
                self.in_content = True
                self.content_level = self.div_level
        
        # Track depth for multiple container types (td, div, etc)
        self.div_level += 1
            
        if self.in_content:
            attr_str = " ".join([f'{k}="{v}"' for k, v in attrs])
            self.content_html.append(f"<{tag}{' ' + attr_str if attr_str else ''}>")

    def handle_endtag(self, tag):
        if self.in_content:
            self.content_html.append(f"</{tag}>")
            
        self.div_level -= 1
        if self.in_content and self.div_level == self.content_level:
            self.in_content = False
        
        if tag == 'title':
            self.capture_title = False

    def handle_data(self, data):
        if self.capture_title:
            text = data.strip().split(' / ')[0]
            if text and not self.page_title:
                self.page_title = text
        if self.in_content:
            self.content_html.append(data)

def get_text_preview(html_str, limit=200):
    text = re.sub('<[^<]+?>', '', html_str).strip()
    text = re.sub('\s+', ' ', text)
    return text[:limit] + "..." if len(text) > limit else text

pages_dir = "/Users/juanpablo/2026/Estelar/website/pbworks-export/pages"
clean_dir = os.path.join(pages_dir, "clean")
os.makedirs(clean_dir, exist_ok=True)

index_data = []
files = [f for f in os.listdir(pages_dir) if f.endswith('.html')]

print(f"Processing {len(files)} files...")

for filename in files:
    path = os.path.join(pages_dir, filename)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()
    
    parser = PBWorksParser()
    parser.feed(html_content)
    
    clean_html = "".join(parser.content_html)
    
    # Save clean version
    with open(os.path.join(clean_dir, filename), 'w', encoding='utf-8') as f:
        f.write(f"<h1>{parser.page_title}</h1>\n")
        f.write(clean_html)
        
    index_data.append({
        "filename": filename,
        "title": parser.page_title,
        "content_preview": get_text_preview(clean_html)
    })

with open(os.path.join(pages_dir, "index.json"), 'w', encoding='utf-8') as f:
    json.dump(index_data, f, indent=2)

print(f"Extraction complete. Processed {len(index_data)} pages.")
