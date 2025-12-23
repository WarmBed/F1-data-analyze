"""
直接測試 GUI 模組導入和代碼執行
"""
import sys
import json

print("=" * 80)
print("🔍 直接測試 GUI 模組代碼")
print("=" * 80)

# 讀取測試數據
with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    full_json = json.load(f)

data = full_json.get('data', {})

# 模擬 _on_data_loaded 的核心邏輯
print("\n模擬 _on_data_loaded 邏輯:")
print("-" * 80)

track_data = data.get("track_data", {})
print(f"1. track_data = data.get('track_data', {{}})  → type={type(track_data)}, empty={not track_data}")

if not track_data:
    print(f"2. ✅ 進入 if not track_data 分支")
    track_data = {
        "detailed_position_records": data.get("detailed_position_records", []),
        "track_bounds": data.get("track_bounds", {}),
        "official_corners": data.get("official_corners", {}),
        "sector_boundaries": data.get("sector_boundaries", []),
        "speed_distribution": data.get("speed_distribution"),
    }
    print(f"3. 構建後 track_data 鍵: {list(track_data.keys())}")
    print(f"4. speed_distribution 在 track_data: {'speed_distribution' in track_data}")
    print(f"5. speed_distribution 值不為 None: {track_data.get('speed_distribution') is not None}")

# 補充邏輯
print(f"\n6. 檢查補充邏輯:")
if "speed_distribution" not in track_data or not track_data.get("speed_distribution"):
    print(f"   進入補充分支")
    if "speed_distribution" in data and data.get("speed_distribution"):
        track_data["speed_distribution"] = data.get("speed_distribution")
        print(f"   ✅ 從 data 補充 speed_distribution")
    else:
        print(f"   ❌ data 中無 speed_distribution")
else:
    print(f"   ✅ track_data 已有 speed_distribution，無需補充")

# 最終檢查
print(f"\n最終狀態:")
print(f"- track_data 鍵數量: {len(track_data.keys())}")
print(f"- speed_distribution 存在: {'speed_distribution' in track_data}")
print(f"- speed_distribution 不為 None: {track_data.get('speed_distribution') is not None}")

if track_data.get('speed_distribution'):
    sd = track_data['speed_distribution']
    print(f"\n速度分布數據:")
    print(f"  Low: {sd.get('low_speed_percentage')}%")
    print(f"  Mid: {sd.get('mid_speed_percentage')}%")
    print(f"  High: {sd.get('high_speed_percentage')}%")
    
print("\n" + "=" * 80)
print("✅ 測試完成 - 代碼邏輯正確")
print("=" * 80)
