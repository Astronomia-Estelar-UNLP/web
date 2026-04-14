import os
import glob
import re

def get_mapping(directory):
    path = os.path.join(directory, "*")
    mapping = {}
    for f in glob.glob(path):
        fname = os.path.basename(f)
        m = re.match(r'^(\d+)_+', fname)
        if m:
            item_id = m.group(1)
            # If we already have a mapping for this ID, prefer a version that isn't the generic "licensed_for" page
            if item_id in mapping:
                if "licensed_for" in mapping[item_id] and "licensed_for" not in fname:
                    mapping[item_id] = fname
            else:
                mapping[item_id] = fname
    return mapping

pages_dir = "/Users/juanpablo/2026/Estelar/website/pbworks-export/pages"
files_dir = "/Users/juanpablo/2026/Estelar/website/pbworks-export/files"
output_dir = "/Users/juanpablo/2026/Estelar/website"

page_map = get_mapping(pages_dir)
file_map = get_mapping(files_dir)

# PBworks links regex
re_pb = re.compile(r'(?:https?://astronomiaestelarlp\.pbworks\.com)?/w/(page|file(?:/fetch)?)/(\d+)(?:/[^"\'>\s]*)?', re.IGNORECASE)

stats = {
    'files_scanned': 0,
    'links_scanned': 0,
    'links_rewritten': 0,
    'unresolved': set()
}

html_files = glob.glob(os.path.join(output_dir, "*.html"))

for html_file in html_files:
    stats['files_scanned'] += 1
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    modified_flag = [False]

    def replacer(match):
        stats['links_scanned'] += 1
        item_id = match.group(2)
        
        # Check both maps since sometimes files are stored in the 'pages' export
        if item_id in file_map:
            modified_flag[0] = True
            stats['links_rewritten'] += 1
            return f"pbworks-export/files/{file_map[item_id]}"
        elif item_id in page_map:
            modified_flag[0] = True
            stats['links_rewritten'] += 1
            return f"pbworks-export/pages/{page_map[item_id]}"
        else:
            stats['unresolved'].add(item_id)
            return match.group(0)

    new_content = re_pb.sub(replacer, content)

    if modified_flag[0]:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

print("--- Execution Summary ---")
print(f"Files scanned: {stats['files_scanned']}")
print(f"Links scanned: {stats['links_scanned']}")
print(f"Links rewritten: {stats['links_rewritten']}")
print(f"Unresolved count: {len(stats['unresolved'])}")
if stats['unresolved']:
    unresolved_list = sorted(list(stats['unresolved']))
    print(f"Unresolved IDs: {', '.join(unresolved_list)}")
