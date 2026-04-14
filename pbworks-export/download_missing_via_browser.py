#!/usr/bin/env python3
"""
Download missing PBworks items (pages and files) using Playwright.
Uses authenticated browser session to bypass httpOnly cookie limitations.
"""

import asyncio
import json
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright

EXPORT_DIR = "/Users/juanpablo/2026/Estelar/website/pbworks-export"
PAGES_DIR = os.path.join(EXPORT_DIR, "pages")
FILES_DIR = os.path.join(EXPORT_DIR, "files")

# Create directories if they don't exist
os.makedirs(PAGES_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

# Missing page IDs from download_missing_report.json
MISSING_PAGES = [
    "127810650", "145603782", "130425858", "109721302", "145603764",
    "134844459", "145603839", "109782670", "145603806", "106869723",
    "109783576", "134894835", "145603716", "142483752", "142478469",
    "127329902", "139102686", "109367761", "109708060", "109716019",
    "134514273", "130640262", "145603800", "109900978", "109716113",
    "134514201", "130650382", "109717099", "145603765", "109709161"
]

# Missing file IDs
MISSING_FILES = [
    "108649141", "108649132", "107272074", "107228610", "149560386",
    "107228625", "107228631", "108005755", "107272073", "149560370",
    "107272088", "107228629"
]

BASE_URL = "https://astronomiaestelarlp.pbworks.com"

def safe_filename(s):
    """Convert string to safe filename."""
    return re.sub(r'[^\w\-_\.]', '_', s)

async def download_page(page, item_id):
    """Download a PBworks page and save as HTML."""
    url = f"{BASE_URL}/w/page/{item_id}"
    
    try:
        response = await page.goto(url, wait_until="networkidle")
        
        if not response or response.status >= 400:
            return {"id": item_id, "type": "page", "status": "failed", "error": f"HTTP {response.status if response else 'no response'}"}
        
        # Extract page title
        title = await page.title()
        
        # Save HTML content
        content = await page.content()
        filename = f"{item_id}__{safe_filename(title)}.html"
        dest_path = os.path.join(PAGES_DIR, filename)
        
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "id": item_id,
            "type": "page",
            "status": "success",
            "filename": filename,
            "title": title
        }
    except Exception as e:
        return {
            "id": item_id,
            "type": "page",
            "status": "failed",
            "error": str(e)
        }

async def download_file(page, item_id):
    """Download a PBworks file."""
    url = f"{BASE_URL}/w/file/{item_id}"
    
    try:
        response = await page.goto(url, wait_until="networkidle")
        
        if not response or response.status >= 400:
            return {"id": item_id, "type": "file", "status": "failed", "error": f"HTTP {response.status if response else 'no response'}"}
        
        # Try to get filename from page content or URL
        title = await page.title()
        
        # Extract filename from title or generate one
        # Title is typically "filename - astronmiaestelarlp..."
        match = re.search(r'^([^-]+)\s*-', title)
        filename = safe_filename(match.group(1).strip()) if match else safe_filename(title)
        
        # Get the actual file download link
        download_link = await page.evaluate("""
            () => {
                const link = document.querySelector('a[href*="/file/"]');
                return link ? link.href : null;
            }
        """)
        
        if not download_link:
            # Try to extract from current URL or use file download endpoint
            download_link = f"{BASE_URL}/w/file/fetch/{item_id}"
        
        # Download file via separate request
        file_response = await page.goto(download_link, wait_until="networkidle")
        
        if file_response and file_response.status == 200:
            body = await page.content()
            dest_path = os.path.join(FILES_DIR, f"{item_id}_{filename}")
            
            with open(dest_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(body)
            
            return {
                "id": item_id,
                "type": "file",
                "status": "success",
                "filename": f"{item_id}_{filename}"
            }
        else:
            return {
                "id": item_id,
                "type": "file",
                "status": "failed",
                "error": f"Download link returned {file_response.status if file_response else 'no response'}"
            }
    except Exception as e:
        return {
            "id": item_id,
            "type": "file",
            "status": "failed",
            "error": str(e)
        }

async def main():
    """Main download function."""
    results = {
        "pages": {"success": 0, "failed": 0, "items": []},
        "files": {"success": 0, "failed": 0, "items": []}
    }
    
    async with async_playwright() as p:
        # Connect to existing browser or launch new one
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        print("=" * 60)
        print("DOWNLOADING MISSING PBWORKS ITEMS VIA BROWSER")
        print("=" * 60)
        
        # Download pages
        print(f"\nDownloading {len(MISSING_PAGES)} pages...")
        for i, page_id in enumerate(MISSING_PAGES, 1):
            result = await download_page(page, page_id)
            results["pages"]["items"].append(result)
            if result["status"] == "success":
                results["pages"]["success"] += 1
                print(f"✓ Page {i}/{len(MISSING_PAGES)}: {page_id}")
            else:
                results["pages"]["failed"] += 1
                print(f"✗ Page {i}/{len(MISSING_PAGES)}: {page_id} - {result.get('error', 'Unknown error')}")
        
        # Download files
        print(f"\nDownloading {len(MISSING_FILES)} files...")
        for i, file_id in enumerate(MISSING_FILES, 1):
            result = await download_file(page, file_id)
            results["files"]["items"].append(result)
            if result["status"] == "success":
                results["files"]["success"] += 1
                print(f"✓ File {i}/{len(MISSING_FILES)}: {file_id}")
            else:
                results["files"]["failed"] += 1
                print(f"✗ File {i}/{len(MISSING_FILES)}: {file_id} - {result.get('error', 'Unknown error')}")
        
        await context.close()
        await browser.close()
    
    # Save results
    report_path = os.path.join(EXPORT_DIR, "download_missing_via_browser_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Pages: {results['pages']['success']} success, {results['pages']['failed']} failed")
    print(f"Files: {results['files']['success']} success, {results['files']['failed']} failed")
    print(f"Total: {results['pages']['success'] + results['files']['success']} success, " +
          f"{results['pages']['failed'] + results['files']['failed']} failed")
    print(f"\nReport saved to: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
