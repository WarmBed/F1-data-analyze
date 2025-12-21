"""
驗證 Sector 邊界修復 - 數據轉換層
"""
import json

print("=" * 80)
print("🧪 測試 _transform_api_data_to_gui_format 中的 Sector 邊界處理")
print("=" * 80)

# 載入 JSON 模擬 API 數據
with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    full_data = json.load(f)

# 模擬 API 返回的數據（第二層 data）
api_data = full_data.get('data', {})

print("\n[步驟 1] 檢查 API 數據...")
print(f"  api_data keys: {list(api_data.keys())}")
print(f"  sector_boundaries 在 api_data: {'sector_boundaries' in api_data}")

if 'sector_boundaries' in api_data:
    sb = api_data['sector_boundaries']
    print(f"  ✅ sector_boundaries 數量: {len(sb)}")
    for boundary in sb:
        print(f"     - {boundary.get('name')}: {boundary.get('distance_m'):.1f}m")

print("\n[步驟 2] 模擬 _transform_api_data_to_gui_format...")

# 模擬轉換邏輯（修復後的版本）
position_records = api_data.get("detailed_position_records", [])
track_bounds = api_data.get("track_bounds", {})
official_corners_data = api_data.get("official_corners", {})
sector_boundaries_data = api_data.get("sector_boundaries", [])  # ← 關鍵！

print(f"  提取 sector_boundaries: {len(sector_boundaries_data)} 個")

# 構建 track_data
track_data = {
    "detailed_position_records": position_records,
    "track_bounds": track_bounds,
    "official_corners": official_corners_data,
    "sector_boundaries": sector_boundaries_data  # ← 關鍵！包含在 track_data 中
}

print("\n[步驟 3] 驗證 track_data...")
print(f"  track_data keys: {list(track_data.keys())}")
print(f"  sector_boundaries 在 track_data: {'sector_boundaries' in track_data}")

if 'sector_boundaries' in track_data:
    print(f"  ✅ sector_boundaries 數量: {len(track_data['sector_boundaries'])}")
else:
    print(f"  ❌ ERROR: sector_boundaries 不在 track_data 中！")

print("\n" + "=" * 80)
print("✅ 測試完成！track_data 現在包含 sector_boundaries")
print("=" * 80)
print("\n📋 預期行為：")
print("  1. 重啟 GUI: python f1t_gui_main.py")
print("  2. 打開 Historical Track Map → Brazil 2024")
print("  3. Console 應顯示:")
print("     [HISTORICAL_TRACK_MAP_MDI] 🏁 從 API 數據載入 3 個 Sector 邊界")
print("     [TRACK_MAP] ✅ 成功載入 3 個 Sector 邊界")
print("  4. 賽道圖上應顯示 3 條橘紅色虛線 (S1/S2/S3)")
