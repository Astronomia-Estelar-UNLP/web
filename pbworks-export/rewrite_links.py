import os
import re
import glob
import json

EXPORT_DIR = "/Users/juanpablo/2026/Estelar/website/pbworks-export"
PAGES_DIR = os.path.join(EXPORT_DIR, "pages")
FILES_DIR = os.path.join(EXPORT_DIR, "files")

def build_id_map(directory):
    id_map = {}
    if not os.path.exists(directory):
        return id_map
    for filename in os.listdir(directory):
        m = re.match(r"^(\d+)[_]+", filename)
        if m:
            fid = m.group(1)
            if fid not in id_map:
                id_map[fid] = filename
            else:
                current = id_map[fid]
                if len(filename) < len(current):
                    id_map[fid] = filename
                elif len(filename) == len(current) and filename < current:
                    id_map[fid] = filename
    return id_map

page_map = build_id_map(PAGES_DIR)
file_map = build_id_map(FILES_DIR)

print(f"DEBUG: Found {len(page_map)} pages and {len(file_map)} files in map.")

re_pb = re.compile(r"((?:https?://astronomiaestelarlp\.pbworks\.com)?/w/(page|file(?:/fetch)?)/(\d+)(?:/[^\"'>\s]*)?)")

html_files = glob.glob("/Users/juanpablo/2026/Estelar/website/*.html")
report = {
    "links_scanned": 0,
    "links_rewritten": 0,
    "unresolved_ids": [],
    "modified_files": []
}

unresolved_set = set()

for html_path in html_files:
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Use a dictionary to track modifications within the nested function
    state = {"modified": False}
    
    def replace_func(match):
        report["links_scanned"] += 1
        full_url = match.group(1)
        ltype = match.group(2).lower()
        fid = match.group(3)
        
        target = None
        if "page" in ltype:
            if fid in page_map:
                target = f"pbworks-export/pages/{page_map[fid]}"
        else:
            if fid in file_map:
                target = f"pbworks-export/files/{file_map[fid]}"
        
        if target:
            report["links_rewritten"] += 1
            state["modified"] = True
            return target
        else:
            if fid != "113897152":
                unresolved_set.add(fid)
            return full_url

    new_content = re_pb.sub(replace_func, content)
    
    if state["modified"]:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        report["modified_files"].append(os.path.basename(html_path))

report["unresolved_count"] = len(unresolved_set)
report["unresolved_ids"] = list(unresolved_set)

with open(os.path.join(EXPORT_DIR, "rewrite_after_missing_report.json"), "w") as f:
    json.dump(report, f, indent=2)

print("--- Final Pass Summary ---")
print(f"Links scanned: {report['links_scanned']}")
print(f"Links rewritten: {report['links_rewritten']}")
print(f"Unresolved PBworks IDs: {report['unresolved_count']}")
print(f"Modified HTML files: {len(report['modified_files'])}")
print(f"Unresolved IDs Example: {report['unresolved_ids'][:10]}")
