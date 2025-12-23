#!/usr/bin/env python3
"""快速測試數據轉換"""
import json
import sys
from pathlib import Path

# 讀取 JSON
json_file = Path("json/historical_flags_Japan_2022-2025.json")
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 60)
print("JSON 數據結構測試")
print("=" * 60)

api_data = data["data"]
print(f"✅ JSON 載入成功")
print(f"   api_data 類型: {type(api_data)}")
print(f"   api_data 鍵: {list(api_data.keys())}")

# 測試轉換邏輯（不使用 MDI 類別）
position_records = api_data.get("detailed_position_records", [])
track_bounds = api_data.get("track_bounds", {})
metadata = api_data.get("metadata", {})

print(f"\n提取數據:")
print(f"   位置點: {len(position_records)}")
print(f"   track_bounds: {track_bounds}")
print(f"   metadata keys: {list(metadata.keys())}")

# 構建 track_data
track_data = {
    "detailed_position_records": position_records,
    "track_bounds": track_bounds,
    "official_corners": {
        "available": False,
        "corners": []
    }
}
print(f"\n✅ track_data 構建成功")

# 構建 chart_data
chart_data = {
    "track_outline": position_records,
    "corners": []
}

# 提取彎道編號
corner_analysis = api_data.get("corner_analysis", {})
if corner_analysis:
    corner_numbers = sorted([int(k.replace('T', '')) for k in corner_analysis.keys()])
    chart_data["corners"] = corner_numbers
    print(f"✅ 提取到 {len(corner_numbers)} 個彎道")

# 組合 GUI 數據
gui_data = {
    "track_data": track_data,
    "chart_data": chart_data,
    "yearly_summary": api_data.get("yearly_summary", {}),
    "corner_analysis": api_data.get("corner_analysis", {}),
    "trends": api_data.get("trends", {}),
    "elevation_profile": api_data.get("elevation_profile"),
    "metadata": metadata
}

print(f"\n✅ GUI 數據組合成功")
print(f"   GUI 數據鍵: {list(gui_data.keys())}")
print(f"   GUI 數據類型: {type(gui_data)}")

# 驗證 elevation_profile 訪問（這是原錯誤發生點）
print(f"\n測試 elevation_profile 訪問:")
if gui_data.get("elevation_profile"):
    elev = gui_data["elevation_profile"]
    if isinstance(elev, dict) and elev.get("available"):
        print(f"   ✅ 高程範圍: {elev['min_elevation']:.1f}m ~ {elev['max_elevation']:.1f}m")
    else:
        print(f"   ⚠️  elevation_profile 存在但不可用: {elev}")
else:
    print(f"   ⚠️  elevation_profile 不存在")

print(f"\n🎉 數據轉換測試完成！沒有發生 'NoneType' object has no attribute 'get' 錯誤")
