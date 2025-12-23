"""測試 Drupal Views AJAX 端點"""
import requests

# Drupal Views 可能的端點
urls_to_test = [
    "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071?_format=json",
    "https://www.fia.com/views/ajax",
    "https://www.fia.com/decision_documents_list",
]

headers = {'User-Agent': 'Mozilla/5.0'}

for url in urls_to_test:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"\n{'='*70}")
        print(f"URL: {url}")
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type')}")
        
        if r.status_code == 200:
            content = r.text[:300]
            print(f"Content (first 300 chars):\n{content}")
    except Exception as e:
        print(f"Error: {e}")
