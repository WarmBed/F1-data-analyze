#!/usr/bin/env python3
"""
修正重置按鈕 Unicode 字符的腳本
"""

import re

# 讀取檔案
with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修正損壞的 Unicode 字符 (可能顯示為 � 或其他)
# 使用正則表達式找到並替換
pattern = r'QPushButton\("[^"]*顯示所有資料"\)'
replacement = 'QPushButton("🔄 顯示所有資料")'

# 計算替換次數
matches = re.findall(pattern, content)
print(f"找到 {len(matches)} 個重置按鈕定義:")
for i, match in enumerate(matches, 1):
    print(f"  {i}. {match}")

# 執行替換
content = re.sub(pattern, replacement, content)

# 寫回檔案
with open('f1t_gui_main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ 已修正 {len(matches)} 個重置按鈕的 Unicode 字符")
