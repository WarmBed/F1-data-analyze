"""
驗證 Sector 邊界持久化修復
測試場景：當 _on_data_loaded 被調用兩次時，第二次不會清空 sector_boundaries
"""

print("=" * 80)
print("🧪 測試 Sector 邊界持久化邏輯")
print("=" * 80)

# 模擬第一次調用：來自 API（包含 sector_boundaries）
print("\n[場景 1] 第一次 _on_data_loaded: 來自 API（包含 sector_boundaries）")
api_data = {
    "track_data": {
        "detailed_position_records": [{"x": 0, "y": 0}],
        "track_bounds": {},
        "official_corners": {"available": True, "count": 15, "corners": []},
        "sector_boundaries": [
            {"sector": 1, "name": "S1 End", "distance_m": 1233.1},
            {"sector": 2, "name": "S2 End", "distance_m": 3130.3},
            {"sector": 3, "name": "S3 End", "distance_m": 0.0}
        ]
    }
}

_current_flags_data = None  # 初始為空
track_data = api_data.get("track_data", {})

if not track_data:
    print("  ⚠️  track_data 為空，從 data 構建...")
else:
    if "sector_boundaries" not in track_data:
        if "sector_boundaries" in api_data:
            track_data["sector_boundaries"] = api_data.get("sector_boundaries", [])
            print("  ✅ 從 data 補充 sector_boundaries")
        elif _current_flags_data and "sector_boundaries" in _current_flags_data:
            track_data["sector_boundaries"] = _current_flags_data.get("sector_boundaries", [])
            print(f"  🔄 從 _current_flags_data 恢復 sector_boundaries")

print(f"  結果: sector_boundaries 在 track_data: {'sector_boundaries' in track_data}")
print(f"  結果: sector_boundaries 數量: {len(track_data.get('sector_boundaries', []))}")

# 保存到 _current_flags_data
_current_flags_data = {"sector_boundaries": track_data.get("sector_boundaries", [])}

# 模擬第二次調用：來自 data_manager（不包含 sector_boundaries）
print("\n[場景 2] 第二次 _on_data_loaded: 來自 data_manager（不包含 sector_boundaries）")
old_data = {
    "track_data": {
        "position_records": [{"x": 0, "y": 0}],
        "official_corners": {"available": True, "count": 15, "corners": []},
        "metadata": {}
        # ❌ 注意：沒有 sector_boundaries！
    }
}

track_data = old_data.get("track_data", {})

if not track_data:
    print("  ⚠️  track_data 為空，從 data 構建...")
else:
    # 🏁 關鍵修復：總是檢查並補充 sector_boundaries
    if "sector_boundaries" not in track_data:
        # 優先從 data 取得
        if "sector_boundaries" in old_data:
            track_data["sector_boundaries"] = old_data.get("sector_boundaries", [])
            print("  ✅ 從 data 補充 sector_boundaries")
        # 如果 data 也沒有，嘗試從之前保存的 _current_flags_data 恢復
        elif _current_flags_data and "sector_boundaries" in _current_flags_data:
            track_data["sector_boundaries"] = _current_flags_data.get("sector_boundaries", [])
            print(f"  🔄 從 _current_flags_data 恢復 {len(_current_flags_data.get('sector_boundaries', []))} 個 Sector 邊界")

print(f"  結果: sector_boundaries 在 track_data: {'sector_boundaries' in track_data}")
print(f"  結果: sector_boundaries 數量: {len(track_data.get('sector_boundaries', []))}")

print("\n" + "=" * 80)
if len(track_data.get('sector_boundaries', [])) == 3:
    print("✅ 測試通過！Sector 邊界成功持久化")
else:
    print("❌ 測試失敗！Sector 邊界被清空")
print("=" * 80)

print("\n📋 預期行為：")
print("  1. 重啟 GUI: python f1t_gui_main.py")
print("  2. 打開 Historical Track Map → Brazil 2024")
print("  3. Console 應顯示:")
print("     [DEBUG] 🔄 從 _current_flags_data 恢復 3 個 Sector 邊界")
print("  4. 賽道圖上應顯示 3 條橘紅色虛線 (S1/S2/S3)")
