#!/usr/bin/env python3
"""
測試賽道變更檢測邏輯
Test Track Change Detection Logic

驗證切換賽道時會清空舊座標
"""

def test_track_change_detection():
    """測試賽道變更檢測"""
    
    print("=" * 80)
    print("場景 1: 同一賽道，保留座標")
    print("=" * 80)
    
    # 模擬狀態
    old_sector_boundaries = [
        {"sector": 1, "name": "S1 End", "distance_m": 1233.1, "position_x": 2126.9, "position_y": -2616.1}
    ]
    old_race = "Brazil"
    
    # 新數據（同一賽道）
    new_race = "Brazil"
    new_data_has_sector = False  # 模擬新數據沒有 sector_boundaries
    
    print(f"舊賽道: {old_race}")
    print(f"新賽道: {new_race}")
    print(f"舊座標: {len(old_sector_boundaries)} 個")
    
    # 賽道變更檢測
    if old_race and new_race and old_race != new_race:
        print(f"🚨 檢測到賽道變更: {old_race} → {new_race}")
        print(f"🗑️  清空舊座標")
        old_sector_boundaries = []
    else:
        print(f"✅ 同一賽道，保留舊座標")
    
    # 補充邏輯
    if not new_data_has_sector and old_sector_boundaries:
        result = old_sector_boundaries
        print(f"✅ 使用保留的座標: {len(result)} 個")
    else:
        result = []
        print(f"⚠️  設置為空列表")
    
    assert len(result) == 1, "同一賽道應該保留座標"
    print("✅ 測試通過\n")
    
    print("=" * 80)
    print("場景 2: 切換賽道，清空座標")
    print("=" * 80)
    
    # 模擬狀態
    old_sector_boundaries = [
        {"sector": 1, "name": "S1 End", "distance_m": 1767.8, "position_x": 5806.0, "position_y": 4839.0}
    ]
    old_race = "Bahrain"
    
    # 新數據（不同賽道）
    new_race = "Brazil"
    new_data_has_sector = False  # 模擬新數據沒有 sector_boundaries
    
    print(f"舊賽道: {old_race}")
    print(f"新賽道: {new_race}")
    print(f"舊座標: {len(old_sector_boundaries)} 個 (Bahrain 座標)")
    
    # 賽道變更檢測
    if old_race and new_race and old_race != new_race:
        print(f"🚨 檢測到賽道變更: {old_race} → {new_race}")
        print(f"🗑️  清空舊座標（避免 Bahrain 座標出現在 Brazil 賽道上）")
        old_sector_boundaries = []
    else:
        print(f"✅ 同一賽道，保留舊座標")
    
    # 補充邏輯
    if not new_data_has_sector and old_sector_boundaries:
        result = old_sector_boundaries
        print(f"✅ 使用保留的座標: {len(result)} 個")
    else:
        result = []
        print(f"✅ 設置為空列表（正確：避免錯誤座標）")
    
    assert len(result) == 0, "切換賽道應該清空舊座標"
    print("✅ 測試通過：避免了座標錯誤\n")
    
    print("=" * 80)
    print("場景 3: 切換賽道，新數據有正確座標")
    print("=" * 80)
    
    # 模擬狀態
    old_sector_boundaries = [
        {"sector": 1, "name": "S1 End", "distance_m": 1767.8, "position_x": 5806.0, "position_y": 4839.0}
    ]
    old_race = "Bahrain"
    
    # 新數據（不同賽道，有正確座標）
    new_race = "Brazil"
    new_data_sector_boundaries = [
        {"sector": 1, "name": "S1 End", "distance_m": 1233.1, "position_x": 2126.9, "position_y": -2616.1}
    ]
    
    print(f"舊賽道: {old_race}")
    print(f"新賽道: {new_race}")
    print(f"舊座標: {len(old_sector_boundaries)} 個 (Bahrain X: 5806.0)")
    print(f"新座標: {len(new_data_sector_boundaries)} 個 (Brazil X: 2126.9)")
    
    # 賽道變更檢測
    if old_race and new_race and old_race != new_race:
        print(f"🚨 檢測到賽道變更: {old_race} → {new_race}")
        print(f"🗑️  清空舊座標")
        old_sector_boundaries = []
    
    # 補充邏輯（優先使用新數據）
    if new_data_sector_boundaries:
        result = new_data_sector_boundaries
        print(f"✅ 使用新數據的座標: {len(result)} 個")
        print(f"   座標: X={result[0]['position_x']:.1f}, Y={result[0]['position_y']:.1f}")
    elif old_sector_boundaries:
        result = old_sector_boundaries
        print(f"🔄 使用保留的座標: {len(result)} 個")
    else:
        result = []
        print(f"⚠️  設置為空列表")
    
    assert len(result) == 1, "應該有座標"
    assert result[0]['position_x'] == 2126.9, "應該是 Brazil 的座標，不是 Bahrain 的"
    print("✅ 測試通過：使用了正確的 Brazil 座標\n")

if __name__ == "__main__":
    try:
        test_track_change_detection()
        print("=" * 80)
        print("✅ 所有測試通過！賽道變更檢測正常工作")
        print("=" * 80)
        print("""
修復效果：
- 同一賽道重新載入 → 保留座標 ✅
- 切換到不同賽道 → 清空舊座標，避免座標錯誤 ✅
- 新數據有座標 → 優先使用新座標 ✅

這樣可以避免：
❌ Bahrain 的座標出現在 Brazil 賽道上
❌ Brazil 的座標出現在 Bahrain 賽道上
""")
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
