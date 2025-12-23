#!/usr/bin/env python3
"""檢查 Function 100 JSON 中 corners 的格式"""

import json
from pathlib import Path

# 查找 JSON 檔案
json_dir = Path('json')
json_files = list(json_dir.glob('historical_track_flags_*_2024_Japan_R_*.json'))

if not json_files:
    print("找不到 JSON 檔案")
    exit(1)

print(f"找到 {len(json_files)} 個檔案")
print(f"使用檔案: {json_files[0].name}\n")

# 讀取檔案
with open(json_files[0], 'r', encoding='utf-8') as f:
    data = json.load(f)

# 檢查雙重嵌套
if "function_id" in data and "data" in data:
    print("⚠️  檢測到雙重嵌套，提取內層 data")
    data = data["data"]

print(f"JSON 頂層鍵: {list(data.keys())}\n")

# 檢查 chart_data
chart_data = data.get('chart_data', {})
print(f"chart_data 鍵: {list(chart_data.keys())}\n")

# 檢查 corners
corners = chart_data.get('corners', [])
print(f"corners 類型: {type(corners)}")
print(f"corners 長度: {len(corners) if isinstance(corners, list) else 'N/A'}")

if isinstance(corners, dict):
    print(f"corners 是字典，鍵: {list(corners.keys())}")
    print(f"\n範例內容 (前 3 個鍵):")
    for i, (key, value) in enumerate(list(corners.items())[:3]):
        print(f"  {key}: {value}")
elif isinstance(corners, list):
    print(f"\n範例內容 (前 3 個元素):")
    for i, corner in enumerate(corners[:3]):
        print(f"  [{i}]: {corner} (類型: {type(corner)})")
else:
    print(f"corners 類型未知: {type(corners)}")

# 檢查 official_corners
if 'official_corners' in chart_data:
    official_corners = chart_data['official_corners']
    print(f"\n\nofficial_corners 存在！")
    print(f"  類型: {type(official_corners)}")
    print(f"  鍵: {list(official_corners.keys()) if isinstance(official_corners, dict) else 'N/A'}")
    
    if 'corners' in official_corners:
        corners_list = official_corners['corners']
        print(f"\n  official_corners['corners']:")
        print(f"    類型: {type(corners_list)}")
        print(f"    長度: {len(corners_list) if isinstance(corners_list, list) else 'N/A'}")
        
        if isinstance(corners_list, list) and corners_list:
            print(f"\n    範例 (前 3 個):")
            for i, corner in enumerate(corners_list[:3]):
                print(f"      [{i}]: {corner}")
