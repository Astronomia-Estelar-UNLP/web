import os
import re
import glob
import json
import requests
import shutil

# Configuration
COOKIE = "pbj=6e2b810c82969e9a69b699db350d001776187189; _ga=GA1.1.283252718.1776187191; __qca=P0-1774021834-1776187190896; hm3=1; pi3=03b9d97c2b48ed45e8e88fccc924a3cc5a652a5c; ds3=de-IM29nSUNEw; last=astronomiaestelarlp; _ga_54LYVM2Y0K=GS2.1.s1776187190$o1$g1$t1776187233$j17$l0$h0"
HEADERS = {
    "Cookie": COOKIE,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://astronomiaestelarlp.pbworks.com/"
}
EXPORT_DIR = "/Users/juanpablo/2026/Estelar/website/pbworks-export"
PAGES_DIR = os.path.join(EXPORT_DIR, "pages")
FILES_DIR = os.path.join(EXPORT_DIR, "files")
OMIT_IDS = {'113897152'}

os.makedirs(PAGES_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

def get_referenced_ids():
    page_ids = set()
    file_ids = set()
    # Match /w/page/ID or /w/file/ID or /w/file/fetch/ID
    re_page = re.compile(r'/w/page/(\d+)')
    re_file = re.compile(r'/w/file/(?:fetch/)?(\d+)')
    
    html_files = glob.glob("/Users/juanpablo/2026/Estelar/website/*.html")
    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            page_ids.update(re_page.findall(content))
            file_ids.update(re_file.findall(content))
    return page_ids - OMIT_IDS, file_ids - OMIT_IDS

def get_local_ids(directory):
    ids = set()
    if not os.path.exists(directory):
        return ids
    for f in os.listdir(directory):
        m = re.match(r'^(\d+)[_]+', f)
        if m:
            ids.add(m.group(1))
    return ids

def download_page(page_id):
    url = f"https://astronomiaestelarlp.pbworks.com/w/page/{page_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        # Check for success and not a login page
        if resp.status_code == 200 and "login" not in resp.url.lower():
            if "Please log in" in resp.text:
                return False, "Login required content"
            dest = os.path.join(PAGES_DIR, f"{page_id}__from_site.html")
            with open(dest, 'w', encoding='utf-8') as f:
                f.write(resp.text)
            return True, None
        return False, f"Status {resp.status_code} or Login Redirect"
    except Exception as e:
        return False, str(e)

def download_file(file_id):
    urls = [
        f"https://astronomiaestelarlp.pbworks.com/w/file/fetch/{file_id}",
        f"https://astronomiaestelarlp.pbworks.com/w/file/{file_id}"
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, stream=True, timeout=15)
            if resp.status_code == 200:
                ct = resp.headers.get('Content-Type', '').lower()
                # If it's an HTML page but we expect a file, it's likely a redirect/error
                if "text/html" in ct and ("login" in resp.url.lower() or "login" in resp.text[:1000].lower()):
                    continue
                
                ext = "bin"
                disp = resp.headers.get('Content-Disposition', '')
                ext_match = re.search(r'\.([a-zA-Z0-9]+)"?$', disp)
                if ext_match:
                    ext = ext_match.group(1)
                
                dest = os.path.join(FILES_DIR, f"{file_id}_from_site.{ext}")
                with open(dest, 'wb') as f:
                    shutil.copyfileobj(resp.raw, f)
                return True, None
        except Exception as e:
            pass
    return False, "Failed all URL attempts"

def main():
    ref_pages, ref_files = get_referenced_ids()
    loc_pages = get_local_ids(PAGES_DIR)
    loc_files = get_local_ids(FILES_DIR)
    
    missing_pages = ref_pages - loc_pages
    missing_files = ref_files - loc_files
    
    print(f"Referenced Pages: {len(ref_pages)}, Local: {len(loc_pages)}, Missing: {len(missing_pages)}")
    print(f"Referenced Files: {len(ref_files)}, Local: {len(loc_files)}, Missing: {len(missing_files)}")
    
    report = {"pages": {"success": 0, "fail": 0, "failures": []}, "files": {"success": 0, "fail": 0, "failures": []}}
    
    for pid in sorted(list(missing_pages)):
        print(f"Downloading page {pid}...")
        success, err = download_page(pid)
        if success:
            report["pages"]["success"] += 1
        else:
            report["pages"]["fail"] += 1
            report["pages"]["failures"].append({"id": pid, "error": err})
            
    for fid in sorted(list(missing_files)):
        print(f"Downloading file {fid}...")
        success, err = download_file(fid)
        if success:
            report["files"]["success"] += 1
        else:
            report["files"]["fail"] += 1
            report["files"]["failures"].append({"id": fid, "error": err})
            
    with open(os.path.join(EXPORT_DIR, "download_missing_report.json"), 'w') as f:
        json.dump(report, f, indent=2)
    
    print("Download finished.")

if __name__ == "__main__":
    main()
