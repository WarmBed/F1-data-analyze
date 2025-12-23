#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專門檢查有表格的 Mexican GP 文章
"""

import requests
from bs4 import BeautifulSoup

# 這篇文章包含升級表格
url = "https://www.racefans.net/2025/10/24/verstappen-to-benefit-from-four-part-red-bull-car-upgrade-at-mexican-gp/"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print(f"🔍 檢查文章: {url}")
print("=" * 80)

try:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 查找表格
    tables = soup.find_all('table')
    print(f"\n📊 找到 {len(tables)} 個表格\n")
    
    for i, table in enumerate(tables, 1):
        print(f"{'='*80}")
        print(f"表格 {i}:")
        print(f"Class: {table.get('class', 'None')}")
        print(f"{'='*80}\n")
        
        # 提取所有行
        rows = table.find_all('tr')
        print(f"總行數: {len(rows)}\n")
        
        for row_num, row in enumerate(rows, 1):
            cells = row.find_all(['td', 'th'])
            cell_texts = [c.get_text(strip=True) for c in cells]
            
            print(f"行 {row_num}: {cell_texts}")
        
        print(f"\n{'='*80}\n")
    
    # 保存完整表格 HTML
    output_file = "mexican_gp_tables.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        for table in tables:
            f.write(table.prettify())
            f.write("\n\n" + "="*80 + "\n\n")
    
    print(f"💾 表格 HTML 已保存至: {output_file}")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
