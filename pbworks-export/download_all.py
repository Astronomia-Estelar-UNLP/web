import json
import os
import subprocess
import re
from pathlib import Path
import sys

# Paths
base_dir = Path("/Users/juanpablo/2026/Estelar/website/pbworks-export")
pages_dir = base_dir / "pages"
files_dir = base_dir / "files"
pages_list_file = base_dir / "pages_list.json"
files_list_file = base_dir / "files_list.json"
report_file = base_dir / "download_report.json"

for d in [pages_dir, files_dir]:
    d.mkdir(parents=True, exist_ok=True)

# Headers
cookie = "pbj=6e2b810c82969e9a69b699db350d001776187189; pi3=03b9d97c2b48ed45e8e88fccc924a3cc5a652a5c; ds3=de-IM29nSUNEw; last=astronomiaestelarlp"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
referer = "http://astronomiaestelarlp.pbworks.com/"

# PBworks occasionally returns an HTML page instead of the binary for specific legacy files.
# Keep these explicitly omitted so reruns remain deterministic.
omitted_file_urls = {
    "http://astronomiaestelarlp.pbworks.com/w/file/fetch/113897152/t2png.gif": "Server returns HTML/redirect instead of GIF"
}

# Load or initialize report
if report_file.exists():
    try:
        with open(report_file, 'r') as f:
            report = json.load(f)
    except:
        report = {"pages_total": 0, "pages_ok": 0, "pages_failed": 0, "files_total": 0, "files_ok": 0, "files_failed": 0, "failed_items": []}
else:
    report = {
        "pages_total": 0,
        "pages_ok": 0,
        "pages_failed": 0,
        "files_total": 0,
        "files_ok": 0,
        "files_failed": 0,
        "files_omitted": 0,
        "failed_items": [],
        "omitted_items": []
    }

def save_report():
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

def ensure_report_shape():
    report.setdefault("files_omitted", 0)
    report.setdefault("failed_items", [])
    report.setdefault("omitted_items", [])

ensure_report_shape()
report["failed_items"] = []

def safe_filename(s):
    return re.sub(r'[^\w\-_\.]', '_', s)

def is_html_login(path):
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024).lower()
            return b"<!doctype html" in chunk or b"<html" in chunk or b"login" in chunk
    except:
        return False

def download_item(url, dest, is_file=False):
    try:
        # Check if already exists and is valid
        if dest.exists() and dest.stat().st_size > 0:
            if not is_file:
                return True, "already_exists"
            if not is_html_login(dest):
                return True, "already_exists"
            # If it's a file but looks like HTML, re-download

        cmd = [
            'curl', '-L', '--fail', '-s',
            '--max-time', '60',
            '-H', f'Cookie: {cookie}',
            '-H', f'User-Agent: {user_agent}',
            '-H', f'Referer: {referer}',
            '-w', '%{content_type}',
            '-o', str(dest),
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        content_type = result.stdout.strip()
        
        if result.returncode != 0:
            return False, f"Curl error {result.returncode}: {result.stderr}"
        
        if is_file and "text/html" in content_type:
            return False, f"Expected file but got text/html (login page?)"
            
        return True, content_type
    except Exception as e:
        return False, str(e)

# 1. Download Pages
if pages_list_file.exists():
    with open(pages_list_file, 'r') as f:
        pages = json.load(f)
        report["pages_total"] = len(pages)
        report["pages_ok"] = 0
        report["pages_failed"] = 0
        for i, page in enumerate(pages):
            url = page.get('url')
            if not url: continue
            
            match = re.search(r'/page/(\d+)/(.+)', url)
            page_id = match.group(1) if match else "unknown"
            slug = match.group(2) if match else "page"
            dest_html = pages_dir / f"{page_id}__{safe_filename(slug)}.html"
            
            success, info = download_item(url, dest_html)
            if success:
                if info != "already_exists":
                    try:
                        with open(dest_html, 'r', encoding='utf-8', errors='ignore') as hf:
                            html_content = hf.read()
                        
                        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                        title = title_match.group(1).strip() if title_match else ""
                        
                        content_patterns = [
                            r'<div[^>]+id=["\']page-content["\'][^>]*>(.*?)</div>\s*<!-- content-end -->',
                            r'<div[^>]+class=["\'][^"\']*wiki-content[^"\']*["\'][^>]*>(.*?)</div>',
                            r'<div[^>]+class=["\']page-content["\'][^>]*>(.*?)</div>'
                        ]
                        
                        extracted = None
                        for pattern in content_patterns:
                            m = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                            if m:
                                extracted = m.group(1)
                                break
                        
                        if not extracted:
                            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.IGNORECASE | re.DOTALL)
                            extracted = body_match.group(1) if body_match else html_content

                        final_content = f"<!-- Title: {title} -->\n{extracted}"
                        with open(dest_html, 'w', encoding='utf-8') as hf:
                            hf.write(final_content)
                    except Exception as e:
                        report["pages_failed"] += 1
                        report["failed_items"].append({"url": url, "error": f"Process error: {str(e)}"})
                        continue
                
                report["pages_ok"] += 1
            else:
                report["pages_failed"] += 1
                report["failed_items"].append({"url": url, "error": info})
            
            if (i + 1) % 20 == 0:
                print(f"Progress Pages: {i+1}/{len(pages)}", flush=True)
                save_report()

# 2. Download Files
if files_list_file.exists():
    with open(files_list_file, 'r') as f:
        files = json.load(f)
        report["files_total"] = len(files)
        report["files_ok"] = 0
        report["files_failed"] = 0
        report["files_omitted"] = 0
        report["omitted_items"] = []
        for i, item in enumerate(files):
            url = item.get('url')
            if not url: continue
            
            fetch_url = url.replace('/w/file/', '/w/file/fetch/')

            if fetch_url in omitted_file_urls:
                report["files_omitted"] += 1
                report["omitted_items"].append({
                    "url": fetch_url,
                    "reason": omitted_file_urls[fetch_url]
                })
                continue
            
            match = re.search(r'/file/(?:fetch/)?(\d+)/(.+)', url)
            file_id = match.group(1) if match else "unknown"
            orig_name = match.group(2) if match else "file"
            dest_file = files_dir / f"{file_id}_{safe_filename(orig_name)}"
            
            success, info = download_item(fetch_url, dest_file, is_file=True)
            if success:
                report["files_ok"] += 1
            else:
                report["files_failed"] += 1
                report["failed_items"].append({"url": fetch_url, "error": info})
            
            if (i + 1) % 20 == 0:
                print(f"Progress Files: {i+1}/{len(files)}", flush=True)
                save_report()

# Final Save Report
save_report()

print(f"\nSummary:")
print(f"Pages: Total {report['pages_total']}, OK {report['pages_ok']}, Failed {report['pages_failed']}")
print(f"Files: Total {report['files_total']}, OK {report['files_ok']}, Omitted {report['files_omitted']}, Failed {report['files_failed']}")
