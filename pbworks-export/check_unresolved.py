import os
import re
import json
import glob

EXPORT_DIR = "/Users/juanpablo/2026/Estelar/website/pbworks-export"
PAGES_DIR = os.path.join(EXPORT_DIR, "pages")
FILES_DIR = os.path.join(EXPORT_DIR, "files")
REPORT_FILE = os.path.join(EXPORT_DIR, "rewrite_after_missing_report.json")

def get_all_ids(directory):
    ids = {}
    if os.path.exists(directory):
        for f in os.listdir(directory):
            m = re.match(r'^(\d+)_+', f)
            if m:
                ids[m.group(1)] = f
    return ids

page_ids = get_all_ids(PAGES_DIR)
file_ids = get_all_ids(FILES_DIR)

if not os.path.exists(REPORT_FILE):
    print(f"Error: {REPORT_FILE} not found.")
    exit(1)

with open(REPORT_FILE, 'r') as f:
    report = json.load(f)

unresolved_ids = report.get('unresolved_ids', [])
print(f"Total Unresolved IDs from report: {len(unresolved_ids)}")

found_locally = []
still_missing = []

for fid in unresolved_ids:
    if fid in page_ids:
        found_locally.append((fid, 'page', page_ids[fid]))
    elif fid in file_ids:
        found_locally.append((fid, 'file', file_ids[fid]))
    else:
        still_missing.append(fid)

print(f"\nFound locally but not rewritten: {len(found_locally)}")
for fid, type_, name in found_locally:
    print(f"  ID: {fid} | Type: {type_} | File: {name}")

print(f"\nStill missing (not in local export): {len(still_missing)}")
if still_missing:
    print("  IDs:", ", ".join(still_missing))

