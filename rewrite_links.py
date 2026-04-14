import os
import re
import glob

# Config
root_dir = "/Users/juanpablo/2026/Estelar/website"
export_dir = os.path.join(root_dir, "pbworks-export")
pages_dir = os.path.join(export_dir, "pages")
files_dir = os.path.join(export_dir, "files")

# 1. Build mapping
def build_mapping(directory, pattern):
    mapping = {}
    files = glob.glob(os.path.join(directory, pattern))
    for fpath in files:
        fname = os.path.basename(fpath)
        match = re.match(r'^(\d+)', fname)
        if match:
            id_str = match.group(1)
            if id_str not in mapping:
                mapping[id_str] = fname
            else:
                current = mapping[id_str]
                if len(fname) < len(current):
                    mapping[id_str] = fname
                elif len(fname) == len(current) and fname < current:
                    mapping[id_str] = fname
    return mapping

pages_map = build_mapping(pages_dir, "*__*.html")
files_map = build_mapping(files_dir, "*_*")

print(f"Mapped {len(pages_map)} pages and {len(files_map)} files.")

# 2. Identify HTML files in root
html_files = [f for f in os.listdir(root_dir) if f.endswith(".html") and os.path.isfile(os.path.join(root_dir, f))]
print(f"Found {len(html_files)} HTML files in root.")

# 3. Rewrite Links
# Match with optional trailing slash and anything after it
pb_page_regex = re.compile(r'(https?://astronomiaestelarlp\.pbworks\.com)?/w/page/(\d+)(?:/[^"\'>\s]*)?', re.I)
pb_file_regex = re.compile(r'(https?://astronomiaestelarlp\.pbworks\.com)?/w/file/(?:fetch/)?(\d+)(?:/[^"\'>\s]*)?', re.I)

total_links_rewritten = 0
files_changed_count = 0
unresolved_links = []

for html_file in html_files:
    fpath = os.path.join(root_dir, html_file)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    current_rewritten_count = [0]

    def page_sub(match):
        id_str = match.group(2)
        if id_str in pages_map:
            current_rewritten_count[0] += 1
            return f"pbworks-export/pages/{pages_map[id_str]}"
        unresolved_links.append(match.group(0))
        return match.group(0)

    def file_sub(match):
        id_str = match.group(2)
        if id_str in files_map:
            current_rewritten_count[0] += 1
            return f"pbworks-export/files/{files_map[id_str]}"
        unresolved_links.append(match.group(0))
        return match.group(0)

    content = pb_page_regex.sub(page_sub, content)
    content = pb_file_regex.sub(file_sub, content)

    if content != original_content:
        files_changed_count += 1
        total_links_rewritten += current_rewritten_count[0]
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {html_file}: {current_rewritten_count[0]} links.")

# 4. Report Summary
print("\n--- Summary ---")
print(f"Files changed: {files_changed_count}")
print(f"Links rewritten total: {total_links_rewritten}")
print(f"Unresolved PBworks links found: {len(unresolved_links)}")
if unresolved_links:
    print("Unique unresolved links (up to 20):")
    for link in sorted(list(set(unresolved_links)))[:20]:
        print(f"  {link}")
