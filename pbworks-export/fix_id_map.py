import os
import glob
import re

def get_all_ids(directory):
    path = os.path.join(directory, "*")
    ids = set()
    for f in glob.glob(path):
        fname = os.path.basename(f)
        m = re.match(r'^(\d+)_+', fname)
        if m:
            ids.add(m.group(1))
    return ids

pages_dir = "/Users/juanpablo/2026/Estelar/website/pbworks-export/pages"
files_dir = "/Users/juanpablo/2026/Estelar/website/pbworks-export/files"

page_ids = get_all_ids(pages_dir)
file_ids = get_all_ids(files_dir)

print(f"Total Page IDs in export: {len(page_ids)}")
print(f"Total File IDs in export: {len(file_ids)}")

re_pb = re.compile(r'(https?://astronomiaestelarlp\.pbworks\.com)?/w/(page|file(?:/fetch)?)/(\d+)(?:/[^"\'>]*)?')

html_files = glob.glob("/Users/juanpablo/2026/Estelar/website/*.html")
found_links = 0
matchable_links = 0

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = re_pb.findall(content)
    for match in matches:
        found_links += 1
        link_type = match[1].lower()
        fid = match[2]
        if "page" in link_type:
            if fid in page_ids:
                matchable_links += 1
        else:
            if fid in file_ids:
                matchable_links += 1

print(f"Found {found_links} PBworks links in HTML files.")
print(f"Matchable links based on local export: {matchable_links}")
