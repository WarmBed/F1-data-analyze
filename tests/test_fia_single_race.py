"""測試單一FIA分站頁面抓取"""
import requests
from bs4 import BeautifulSoup
import re

# 正確的 2025 日本站 URL
url = "https://www.fia.com/event/japanese-grand-prix"
print(f"訪問: {url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=30)
print(f"HTTP 狀態: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')

# 檢查頁面標題
title = soup.find('h1')
print(f"頁面標題: {title.get_text().strip() if title else 'Not found'}\n")

# 尋找 PDF 連結
pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
print(f"找到 {len(pdf_links)} 個 PDF 連結\n")

if pdf_links:
    print("前10個 PDF:")
    for i, link in enumerate(pdf_links[:10], 1):
        href = link.get('href')
        text = link.get_text().strip()
        print(f"  {i}. {text[:80]}")
        print(f"     → {href[:100]}")
else:
    print("⚠️  沒有找到任何 PDF 連結!")
    print("\n檢查是否有文件列表容器:")
    
    # 尋找可能的文件容器
    containers = soup.find_all(['div', 'section'], class_=re.compile(r'document|decision|file', re.I))
    print(f"   找到 {len(containers)} 個可能的容器")
    
    # 檢查所有連結
    all_links = soup.find_all('a', href=True)
    doc_links = [a for a in all_links if 'document' in a.get('href', '').lower()]
    print(f"   找到 {len(doc_links)} 個包含 'document' 的連結")
    
    if doc_links:
        print("   前5個文件相關連結:")
        for i, link in enumerate(doc_links[:5], 1):
            print(f"     {i}. {link.get('href')}")

# 保存 HTML
with open('fia_japan_page.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("\n✓ HTML 已保存到 fia_japan_page.html")
