#!/usr/bin/env python3
"""檢查 Historical Flags JSON 中的 official_corners 數據"""

import json
from pathlib import Path

# 檢查 Brazil JSON
json_file = Path("json/historical_flags_Brazil_2022-2025.json")
if json_file.exists():
    print(f"[INFO] 讀取 {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        wrapper = json.load(f)
    
    print(f"\n頂層鍵: {list(wrapper.keys())}")
    
    # ✅ 修復：數據在 wrapper['data'] 下
    data = wrapper.get('data', {})
    print(f"\ndata 鍵: {list(data.keys())}")
    
    official_corners = data.get('official_corners', {})
    print(f"\n=== official_corners 檢查 ===")
    print(f"available: {official_corners.get('available')}")
    print(f"count: {official_corners.get('count')}")
    
    corners = official_corners.get('corners', [])
    print(f"corners 陣列長度: {len(corners)}")
    
    if corners:
        print(f"\n第 1 個彎道:")
        print(f"  {corners[0]}")
        print(f"\n最後 1 個彎道:")
        print(f"  {corners[-1]}")
    else:
        print("\n❌ corners 陣列為空！")
else:
    print(f"❌ 找不到 {json_file}")

# 檢查 Las Vegas JSON
json_file_lv = Path("json/historical_flags_Las_Vegas_2024-2024.json")
if json_file_lv.exists():
    print(f"\n\n[INFO] 讀取 {json_file_lv}")
    with open(json_file_lv, 'r', encoding='utf-8') as f:
        wrapper_lv = json.load(f)
    
    data_lv = wrapper_lv.get('data', {})
    official_corners_lv = data_lv.get('official_corners', {})
    
    print(f"\n=== Las Vegas official_corners 檢查 ===")
    print(f"available: {official_corners_lv.get('available')}")
    print(f"count: {official_corners_lv.get('count')}")
    
    corners_lv = official_corners_lv.get('corners', [])
    print(f"corners 陣列長度: {len(corners_lv)}")
    
    if corners_lv:
        print(f"\n第 1 個彎道:")
        print(f"  {corners_lv[0]}")
    else:
        print("\n❌ corners 陣列為空！")
