#!/usr/bin/env python3
"""
Download the remaining 12 unresolved IDs using Playwright.
"""

import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

EXPORT_DIR = "/Users/juanpablo/2026/Estelar/website/pbworks-export"
PAGES_DIR = os.path.join(EXPORT_DIR, "pages")
FILES_DIR = os.path.join(EXPORT_DIR, "files")

# Remaining unresolved IDs
REMAINING_IDS = [
    "152271309",  # page or file?
    "145751175",
    "108379330",
    "107632047",
    "108281494",
    "115643956",
    "109909228",
    "107347584",
    "145603863",
    "110316421",
    "145603809",
    "140794935"
]

BASE_URL = "https://astronomiaestelarlp.pbworks.com"

def safe_filename(s):
    return re.sub(r'[^\w\-_\.]', '_', s)

async def try_download_as_page(page, item_id):
    """Try to download as a page."""
    url = f"{BASE_URL}/w/page/{item_id}"
    
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=10000)
        
        if not response or response.status >= 400:
            return None
        
        title = await page.title()
        
        # Check if it's a login page
        if "login" in title.lower() or "error" in title.lower():
            return None
        
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
    except:
        return None

async def try_download_as_file(page, item_id):
    """Try to download as a file."""
    url = f"{BASE_URL}/w/file/{item_id}"
    
    try:
        response = await page.goto(url, wait_until="networkidle", timeout=10000)
        
        if not response or response.status >= 400:
            return None
        
        title = await page.title()
        
        # Check if it's a login page
        if "login" in title.lower() or "error" in title.lower():
            return None
        
        # Try to extract filename
        match = re.search(r'^([^-]+)\s*-', title)
        filename = safe_filename(match.group(1).strip()) if match else safe_filename(title)
        
        content = await page.content()
        dest_path = os.path.join(FILES_DIR, f"{item_id}_{filename}")
        
        with open(dest_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(content)
        
        return {
            "id": item_id,
            "type": "file",
            "status": "success",
            "filename": f"{item_id}_{filename}"
        }
    except:
        return None

async def download_item(page, item_id):
    """Try to download item, trying both page and file endpoints."""
    # Try as page first
    result = await try_download_as_page(page, item_id)
    if result:
        return result
    
    # Try as file
    result = await try_download_as_file(page, item_id)
    if result:
        return result
    
    # Both failed
    return {
        "id": item_id,
        "status": "failed",
        "error": "Could not download as page or file"
    }

async def main():
    results = {"success": 0, "failed": 0, "items": []}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page_obj = await context.new_page()
        
        print("=" * 60)
        print("DOWNLOADING REMAINING 12 UNRESOLVED ITEMS")
        print("=" * 60)
        
        for i, item_id in enumerate(REMAINING_IDS, 1):
            result = await download_item(page_obj, item_id)
            results["items"].append(result)
            
            if result["status"] == "success":
                results["success"] += 1
                print(f"✓ {i}/12: {item_id} ({result['type']})")
            else:
                results["failed"] += 1
                print(f"✗ {i}/12: {item_id} - {result.get('error', 'Unknown error')}")
        
        await context.close()
        await browser.close()
    
    # Save results
    report_path = os.path.join(EXPORT_DIR, "download_remaining_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"Total: {results['success']} success, {results['failed']} failed")
    print(f"Report: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
