#!/usr/bin/env python3
"""檢查 JSON 中 description 欄位的格式"""
import json
import os

# 找到一個 JSON 檔案
json_dir = "json"
json_path = os.path.join(json_dir, "fia_parts_analysis_v2_2025.json")

if os.path.exists(json_path):
    print(f"✅ 檢查檔案: {os.path.basename(json_path)}\n")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changes = data.get('parts_changes', [])
    print(f"總記錄數: {len(changes)}\n")
    
    # 收集所有不同的 description
    descriptions = set()
    for record in changes[:20]:  # 檢查前 20 筆
        desc = record.get("類型說明", "")
        if desc:
            descriptions.add(desc)
    
    print("📋 前 20 筆中的 Description 樣本:")
    for i, desc in enumerate(sorted(descriptions), 1):
        print(f"{i}. {desc}")
else:
    print("❌ 找不到 JSON 檔案")
