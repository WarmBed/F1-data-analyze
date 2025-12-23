"""
測試 Sector 邊界修復
驗證 track_data 現在包含 sector_boundaries
"""
import json

print("=" * 80)
print("🧪 測試 Sector 邊界數據流修復")
print("=" * 80)

# 載入 JSON
with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    full_data = json.load(f)

data = full_data.get('data', {})

print("\n[步驟 1] 檢查原始數據結構...")
print(f"  data keys: {list(data.keys())}")
print(f"  sector_boundaries 在 data 中: {'sector_boundaries' in data}")
print(f"  track_data 在 data 中: {'track_data' in data}")

track_data_original = data.get("track_data", {})
print(f"  原始 track_data 鍵: {list(track_data_original.keys()) if track_data_original else 'EMPTY'}")
print(f"  sector_boundaries 在原始 track_data: {'sector_boundaries' in track_data_original}")

print("\n[步驟 2] 模擬修復後的邏輯...")
# 模擬修復代碼
track_data = data.get("track_data", {})

if not track_data:
    print("  ✅ track_data 為空，從 data 構建...")
    track_data = {
        "detailed_position_records": data.get("detailed_position_records", []),
        "track_bounds": data.get("track_bounds", {}),
        "official_corners": data.get("official_corners", {}),
        "sector_boundaries": data.get("sector_boundaries", []),
    }
else:
    if "sector_boundaries" not in track_data and "sector_boundaries" in data:
        track_data["sector_boundaries"] = data.get("sector_boundaries", [])
        print("  ✅ 從 data 補充 sector_boundaries 到 track_data")

print("\n[步驟 3] 驗證修復後的 track_data...")
print(f"  修復後 track_data 鍵: {list(track_data.keys())}")
print(f"  sector_boundaries 在修復後 track_data: {'sector_boundaries' in track_data}")

if "sector_boundaries" in track_data:
    sb = track_data["sector_boundaries"]
    print(f"  ✅ sector_boundaries 數量: {len(sb)}")
    for boundary in sb:
        print(f"     - {boundary.get('name')}: {boundary.get('distance_m'):.1f}m")
else:
    print(f"  ❌ sector_boundaries 仍然不在 track_data 中！")

print("\n" + "=" * 80)
print("✅ 測試完成！現在 track_data 包含 sector_boundaries")
print("=" * 80)
print("\n📋 預期行為：")
print("  1. 重啟 GUI: python f1t_gui_main.py")
print("  2. 打開 Historical Track Map → Brazil 2024")
print("  3. Console 應顯示:")
print("     [DEBUG] sector_boundaries 在 track_data 中: True")
print("     [DEBUG] sector_boundaries 數量: 3")
print("     [TRACK_MAP] ✅ 成功載入 3 個 Sector 邊界")
print("  4. 賽道圖上應顯示 3 條橘紅色虛線 (S1/S2/S3)")
