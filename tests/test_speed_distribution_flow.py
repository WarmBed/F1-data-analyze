"""
測試速度分布數據流 - 逐行驗證
"""
import json
import sys

print("=" * 80)
print("🔍 速度分布數據流測試")
print("=" * 80)

# 步驟 1: 讀取 JSON 文件（模擬 API 返回）
print("\n步驟 1: 讀取 JSON 文件")
print("-" * 80)
with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    full_json = json.load(f)

data = full_json.get('data', {})
print(f"✅ JSON 讀取成功")
print(f"   data 層鍵: {list(data.keys())}")
print(f"   speed_distribution 存在: {'speed_distribution' in data}")

# 步驟 2: 模擬 GUI 的 _on_data_loaded 邏輯
print("\n步驟 2: 模擬 historical_track_map_mdi.py 的 _on_data_loaded")
print("-" * 80)

# 提取賽道數據
track_data = data.get("track_data", {})
print(f"track_data = data.get('track_data', {{}})  → {type(track_data)} (空={not track_data})")

# 如果 track_data 為空，從 data 構建
if not track_data:
    print(f"✅ 進入構建分支（track_data 為空）")
    track_data = {
        "detailed_position_records": data.get("detailed_position_records", []),
        "track_bounds": data.get("track_bounds", {}),
        "official_corners": data.get("official_corners", {}),
        "sector_boundaries": data.get("sector_boundaries", []),
        "speed_distribution": data.get("speed_distribution"),  # 關鍵行
    }
    print(f"   構建後的 track_data 鍵: {list(track_data.keys())}")
    print(f"   speed_distribution 值: {track_data.get('speed_distribution') is not None}")
else:
    print(f"❌ 未進入構建分支（track_data 不為空）")
    print(f"   現有 track_data 鍵: {list(track_data.keys())}")

# 確保 speed_distribution 存在（補充邏輯）
print("\n步驟 3: 補充 speed_distribution 邏輯")
print("-" * 80)
if "speed_distribution" not in track_data or not track_data.get("speed_distribution"):
    print(f"⚠️  track_data 中缺少 speed_distribution，嘗試補充...")
    if "speed_distribution" in data and data.get("speed_distribution"):
        track_data["speed_distribution"] = data.get("speed_distribution")
        print(f"✅ 從 data 補充 speed_distribution 成功")
    else:
        print(f"❌ data 中也沒有 speed_distribution")
else:
    print(f"✅ track_data 中已有 speed_distribution")

print(f"\n最終 track_data['speed_distribution'] 存在: {'speed_distribution' in track_data}")
if 'speed_distribution' in track_data and track_data['speed_distribution']:
    sd = track_data['speed_distribution']
    print(f"   Low: {sd.get('low_speed_percentage', 0):.1f}%")
    print(f"   Mid: {sd.get('mid_speed_percentage', 0):.1f}%")
    print(f"   High: {sd.get('high_speed_percentage', 0):.1f}%")

# 步驟 4: 模擬 TrackMapWidget 的 load_track_data
print("\n步驟 4: 模擬 track_map_widget.py 的 load_track_data")
print("-" * 80)

speed_dist = track_data.get("speed_distribution")
print(f"speed_dist = track_data.get('speed_distribution')  → {speed_dist is not None}")

if speed_dist:
    print(f"✅ 會執行: self.speed_distribution_data = speed_dist")
    print(f"   Low={speed_dist.get('low_speed_percentage', 0):.1f}%, Mid={speed_dist.get('mid_speed_percentage', 0):.1f}%, High={speed_dist.get('high_speed_percentage', 0):.1f}%")
else:
    print(f"❌ 會執行: self.speed_distribution_data = None")
    print(f"   日誌: [TRACK_MAP] ⚠️  未找到速度分布數據")

# 步驟 5: 模擬 paintEvent 檢查
print("\n步驟 5: 模擬 paintEvent 中的圓餅圖繪製條件")
print("-" * 80)

show_speed_distribution = True  # checkbox 預設勾選
speed_distribution_data = speed_dist

print(f"show_speed_distribution = {show_speed_distribution}")
print(f"speed_distribution_data = {speed_distribution_data is not None}")

if show_speed_distribution and speed_distribution_data:
    print(f"✅ 會繪製圓餅圖（含 6 個調試外框）")
else:
    print(f"❌ 不會繪製圓餅圖")
    if not show_speed_distribution:
        print(f"   原因: show_speed_distribution = False（未啟用）")
    if not speed_distribution_data:
        print(f"   原因: 無 speed_distribution 數據")

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)
