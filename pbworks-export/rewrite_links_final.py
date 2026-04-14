import os
import re
import glob

base_dir = "/Users/juanpablo/2026/Estelar/website"
export_dir = os.path.join(base_dir, "pbworks-export")
pages_dir = os.path.join(export_dir, "pages")
files_dir = os.path.join(export_dir, "files")

def build_map(directory, pattern):
    id_map = {}
    files = glob.glob(os.path.join(directory, pattern))
    for fpath in files:
        fname = os.path.basename(fpath)
        match = re.search(r'^(\d+)[_]+', fname)
        if match:
            fid = match.group(1)
            if fid not in id_map:
                id_map[fid] = fname
            else:
                # Shortest basename then lexicographic
                current = id_map[fid]
                if len(fname) < len(current) or (len(fname) == len(current) and fname < current):
                    id_map[fid] = fname
    return id_map

page_id_map = build_map(pages_dir, "*.html")
file_id_map = build_map(files_dir, "*")

stats = {"scanned": 0, "rewritten": 0}
unresolved = []

# Patterns for PBworks links
# Page links: /w/page/ID/...
# File links: /w/file/ID/... or /w/file/fetch/ID/...
re_pb = re.compile(r'(https?://astronomiaestelarlp\.pbworks\.com)?/w/(page|file(?:/fetch)?)/(\d+)(?:/[^"\'>]*)?')

html_files = glob.glob(os.path.join(base_dir, "*.html"))

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    def replacement(match):
        stats["scanned"] += 1
        link_type = match.group(2)
        fid = match.group(3)
        
        if "page" in link_type:
            if fid in page_id_map:
                stats["rewritten"] += 1
                return f"pbworks-export/pages/{page_id_map[fid]}"
        else:
            if fid in file_id_map:
                stats["rewritten"] += 1
                return f"pbworks-export/files/{file_id_map[fid]}"
        
        unresolved.append((fid, os.path.basename(html_file), match.group(0)))
        return match.group(0)

    new_content = re_pb.sub(replacement, content)
    
    if new_content != content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

print(f"Total links scanned: {stats['scanned']}")
print(f"Links rewritten: {stats['rewritten']}")

if unresolved:
    print("\nUnresolved external PBworks links (first 50):")
    for fid, fname, full_match in unresolved[:50]:
        print(f"ID: {fid} | File: {fname} | Link: {full_match}")
