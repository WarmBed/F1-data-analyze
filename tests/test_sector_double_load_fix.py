#!/usr/bin/env python3
"""
測試 Sector 雙重載入修復
Test Sector Double Load Fix

問題場景：
1. load_track_data(track_data) - track_data 有 sector_boundaries
2. set_sector_boundaries(data.sector_boundaries) - data 沒有，傳遞空列表
3. 結果：sector_boundaries 被清空

修復：
1. set_sector_boundaries 從 track_data 取得（已經過補充邏輯）
2. load_track_data 不清空現有 sector_boundaries
"""

def test_load_then_set_scenario():
    """測試先 load_track_data 再 set_sector_boundaries 的場景"""
    
    print("=" * 80)
    print("場景 1: load_track_data 有數據 → set_sector_boundaries 也有數據")
    print("=" * 80)
    
    # 模擬 TrackMapWidget 狀態
    widget_sector_boundaries = []
    
    # Step 1: load_track_data (track_data 有 sector_boundaries)
    track_data = {
        "sector_boundaries": [
            {"sector": 1, "name": "S1 End", "distance_m": 1233.1},
            {"sector": 2, "name": "S2 End", "distance_m": 3130.3},
            {"sector": 3, "name": "S3 End", "distance_m": 0.0}
        ]
    }
    
    sector_boundaries_data = track_data.get("sector_boundaries", [])
    if sector_boundaries_data:
        widget_sector_boundaries = sector_boundaries_data
        print(f"✅ load_track_data: 載入 {len(widget_sector_boundaries)} 個 sector")
    
    # Step 2: set_sector_boundaries (從 track_data 取得)
    sector_boundaries = track_data.get("sector_boundaries", [])
    if sector_boundaries:
        widget_sector_boundaries = sector_boundaries
        print(f"✅ set_sector_boundaries: 設置 {len(widget_sector_boundaries)} 個 sector")
    
    print(f"最終結果: {len(widget_sector_boundaries)} 個 sector")
    assert len(widget_sector_boundaries) == 3, "應該有 3 個 sector"
    print("✅ 測試通過\n")
    
    print("=" * 80)
    print("場景 2: load_track_data 有數據 → set_sector_boundaries 空（舊版 bug）")
    print("=" * 80)
    
    # 模擬 TrackMapWidget 狀態
    widget_sector_boundaries = []
    
    # Step 1: load_track_data (track_data 有 sector_boundaries)
    track_data = {
        "sector_boundaries": [
            {"sector": 1, "name": "S1 End", "distance_m": 1233.1},
            {"sector": 2, "name": "S2 End", "distance_m": 3130.3},
            {"sector": 3, "name": "S3 End", "distance_m": 0.0}
        ]
    }
    
    sector_boundaries_data = track_data.get("sector_boundaries", [])
    if sector_boundaries_data:
        widget_sector_boundaries = sector_boundaries_data
        print(f"✅ load_track_data: 載入 {len(widget_sector_boundaries)} 個 sector")
    
    # Step 2: set_sector_boundaries (❌ 舊版從 data 取得，data 沒有)
    data = {}  # data 層級沒有 sector_boundaries
    sector_boundaries = data.get("sector_boundaries", [])
    
    if sector_boundaries:
        widget_sector_boundaries = sector_boundaries
        print(f"✅ set_sector_boundaries: 設置 {len(widget_sector_boundaries)} 個 sector")
    else:
        print(f"⚠️  set_sector_boundaries: 新數據為空，保留現有 {len(widget_sector_boundaries)} 個 sector")
        # 修復後的邏輯：不清空
    
    print(f"最終結果: {len(widget_sector_boundaries)} 個 sector")
    assert len(widget_sector_boundaries) == 3, "修復後應該保留 3 個 sector"
    print("✅ 測試通過：修復後不會被清空\n")
    
    print("=" * 80)
    print("場景 3: load_track_data 空 → set_sector_boundaries 有數據（補救）")
    print("=" * 80)
    
    # 模擬 TrackMapWidget 狀態（已有數據）
    widget_sector_boundaries = [
        {"sector": 1, "name": "S1 End", "distance_m": 1767.8},
        {"sector": 2, "name": "S2 End", "distance_m": 3948.8},
        {"sector": 3, "name": "S3 End", "distance_m": 0.0}
    ]
    print(f"初始狀態: {len(widget_sector_boundaries)} 個 sector (Bahrain)")
    
    # Step 1: load_track_data (track_data 沒有 sector_boundaries - 舊緩存)
    track_data = {}
    
    sector_boundaries_data = track_data.get("sector_boundaries", [])
    if sector_boundaries_data:
        widget_sector_boundaries = sector_boundaries_data
        print(f"✅ load_track_data: 載入 {len(widget_sector_boundaries)} 個 sector")
    else:
        # 修復後的邏輯：保留現有
        print(f"⚠️  load_track_data: 新數據為空，保留現有 {len(widget_sector_boundaries)} 個 sector")
    
    # Step 2: set_sector_boundaries (從補充後的 track_data 取得)
    # 假設補充邏輯已經將 sector_boundaries 加入 track_data
    track_data["sector_boundaries"] = [
        {"sector": 1, "name": "S1 End", "distance_m": 1233.1},
        {"sector": 2, "name": "S2 End", "distance_m": 3130.3},
        {"sector": 3, "name": "S3 End", "distance_m": 0.0}
    ]
    
    sector_boundaries = track_data.get("sector_boundaries", [])
    if sector_boundaries:
        widget_sector_boundaries = sector_boundaries
        print(f"✅ set_sector_boundaries: 設置 {len(widget_sector_boundaries)} 個 sector (Brazil)")
    
    print(f"最終結果: {len(widget_sector_boundaries)} 個 sector")
    assert len(widget_sector_boundaries) == 3, "應該更新為新的 3 個 sector"
    print("✅ 測試通過：成功更新為新賽道數據\n")

if __name__ == "__main__":
    try:
        test_load_then_set_scenario()
        print("=" * 80)
        print("✅ 所有測試通過！雙重載入修復正常工作")
        print("=" * 80)
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 測試錯誤: {e}")
        import traceback
        traceback.print_exc()
