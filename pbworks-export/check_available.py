import os
import glob
import re

def get_all_ids(subdir):
    path = f"/Users/juanpablo/2026/Estelar/website/pbworks-export/{subdir}/*"
    ids = set()
    for f in glob.glob(path):
        m = re.match(r'^(\d+)_+', os.path.basename(f))
        if m:
            ids.add(m.group(1))
    return ids

page_ids = get_all_ids("pages")
file_ids = get_all_ids("files")

print(f"Total Page IDs in export: {len(page_ids)}")
print(f"Total File IDs in export: {len(file_ids)}")

# Check some specific IDs from the manual list earlier
missing_ids = ["106869723", "115643956", "140794935"]
for mid in missing_ids:
    print(f"ID {mid} in pages? {mid in page_ids} | in files? {mid in file_ids}")

# Look for filename similarities
for mid in missing_ids:
    found = glob.glob(f"/Users/juanpablo/2026/Estelar/website/pbworks-export/*/*{mid}*")
    print(f"Search for '{mid}': {found}")
