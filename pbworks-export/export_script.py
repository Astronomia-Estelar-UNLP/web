import json
import os
import csv
import subprocess
import re

input_file = "/Users/juanpablo/Library/Application Support/Code - Insiders/User/workspaceStorage/d7235d049295a65bc38f7691b792e9a5/GitHub.copilot-chat/chat-session-resources/0eca7646-e98b-4666-91b7-ff4a99a03cc5/call_lCL8INwOCYmTbeEUkMoECC4u__vscode-1776185879237/content.txt"
export_dir = "/Users/juanpablo/2026/Estelar/website/pbworks-export"
# Updated cookies
cookie = "pbj=6e2b810c82969e9a69b699db350d001776187189; _ga=GA1.1.283252718.1776187191; __qca=P0-1774021834-1776187190896; hm3=1; pi3=03b9d97c2b48ed45e8e88fccc924a3cc5a652a5c; ds3=de-IM29nSUNEw; last=astronomiaestelarlp; _ga_54LYVM2Y0K=GS2.1.1776187190.1.1.1776187233.17.0.0"

def safe_filename(s):
    return re.sub(r'[^\w\-_\.]', '_', s)

with open(input_file, 'r') as f:
    content = f.read()
    if content.startswith("Result: "):
        content = content[len("Result: "):]
    data = json.loads(content)

items_list = data.get('items', [])
manifest = []
pages = []
files = []
base_domain = "https://astronomiaestelarlp.pbworks.com"

for item in items_list:
    item_type_raw = item.get('type', '').lower()
    if item_type_raw == 'folder': continue
    name = item.get('name', 'unnamed')
    href = item.get('href', '')
    match = re.search(r'/(\d+)/', href)
    item_id = match.group(1) if match else "unknown"
    url = f"{base_domain}{href}" if href.startswith('/') else href
    item_type = 'page' if item_type_raw == 'page' else 'file'
    manifest_item = {'id': item_id, 'name': name, 'url': url, 'type': item_type}
    manifest.append(manifest_item)
    if item_type == 'page': pages.append(manifest_item)
    else: files.append(manifest_item)

def download(url, dest):
    try:
        # Use simple curl with cookies
        cmd = ['curl', '-L', '--fail', '-H', f'Cookie: {cookie}', '-o', dest, url]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    except: return False

os.makedirs(os.path.join(export_dir, 'pages'), exist_ok=True)
os.makedirs(os.path.join(export_dir, 'files'), exist_ok=True)

print(f"Re-downloading {len(pages)} pages...")
for item in pages:
    slug = safe_filename(item['name'])
    dest = os.path.join(export_dir, 'pages', f"{item['id']}__{slug}.html")
    # Only download first 5 to check
    if pages.index(item) < 5:
        download(item['url'], dest)
        print(f"Downloaded {item['name']}")
