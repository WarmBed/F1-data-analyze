#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 RaceFans 文章結構
"""

import requests
from bs4 import BeautifulSoup

# 測試 URL - 已知包含升級資訊的文章
test_urls = [
    "https://www.racefans.net/2025/05/30/all-teams-except-mclaren-bring-car-updates-for-first-round-under-new-front-wing-rules/",
    "https://www.racefans.net/2025/10/24/verstappen-to-benefit-from-four-part-red-bull-car-upgrade-at-mexican-gp/",
    "https://www.racefans.net/2025/04/18/ferrari-mclaren-and-red-bull-bring-upgrades-again-for-saudi-arabian-grand-prix/"
]

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

for url in test_urls:
    print("\n" + "=" * 80)
    print(f"🔍 檢查文章: {url}")
    print("=" * 80)
    
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 檢查標題
        title = soup.find('h1')
        print(f"\n📰 標題: {title.get_text(strip=True) if title else 'NOT FOUND'}")
        
        # 檢查表格
        tables = soup.find_all('table')
        print(f"\n📊 找到 {len(tables)} 個表格")
        
        for i, table in enumerate(tables, 1):
            print(f"\n  表格 {i}:")
            print(f"  Class: {table.get('class', 'None')}")
            
            # 表頭
            headers = table.find_all('th')
            if headers:
                print(f"  表頭: {[h.get_text(strip=True) for h in headers]}")
            
            # 前 3 行數據
            rows = table.find_all('tr')
            print(f"  總行數: {len(rows)}")
            
            for j, row in enumerate(rows[:3], 1):
                cells = row.find_all(['td', 'th'])
                cell_texts = [c.get_text(strip=True) for c in cells]
                print(f"    行 {j}: {cell_texts}")
        
        # 檢查列表結構
        lists = soup.find_all(['ul', 'ol'])
        print(f"\n📋 找到 {len(lists)} 個列表")
        
        for i, lst in enumerate(lists[:3], 1):
            items = lst.find_all('li')
            print(f"\n  列表 {i} ({len(items)} 項):")
            for j, item in enumerate(items[:3], 1):
                text = item.get_text(strip=True)
                if 'red bull' in text.lower() or 'verstappen' in text.lower():
                    print(f"    🎯 行 {j}: {text[:100]}")
                else:
                    print(f"    行 {j}: {text[:100]}")
        
        # 檢查文章內容結構
        article = soup.find('article') or soup.find('div', class_=lambda x: x and 'content' in str(x).lower())
        
        if article:
            print(f"\n📄 文章內容:")
            
            # 尋找強調的車隊名稱
            strong_tags = article.find_all('strong')[:10]
            print(f"  強調文本 ({len(strong_tags)}):")
            for tag in strong_tags:
                text = tag.get_text(strip=True)
                if text:
                    print(f"    - {text}")
            
            # 尋找段落中的升級資訊
            paragraphs = article.find_all('p')[:5]
            print(f"\n  前 5 段:")
            for i, p in enumerate(paragraphs, 1):
                text = p.get_text(strip=True)
                if 'upgrade' in text.lower() or 'update' in text.lower():
                    print(f"    段 {i}: {text[:150]}...")
        
        # 保存完整 HTML 供分析
        output_file = f"article_{i}_structure.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        print(f"\n💾 完整 HTML 已保存至: {output_file}")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

print("\n" + "=" * 80)
print("✅ 檢查完成")
print("=" * 80)
