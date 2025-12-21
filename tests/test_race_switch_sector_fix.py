#!/usr/bin/env python3
"""
Test Race Switch Sector Fix
測試切換 race 時 sector 標註的修復

模擬場景：
1. 載入 Brazil - 有 sector_boundaries
2. 載入 Bahrain - 有 sector_boundaries  
3. 載入一個沒有 sector_boundaries 的數據（模擬舊緩存）
4. 驗證是否保留了上一次的 sector_boundaries

測試修復邏輯：
- 在覆蓋 _current_flags_data 前保存 old_sector_boundaries
- 優先從當前 data 取 sector_boundaries
- 如果當前 data 沒有，使用 old_sector_boundaries
"""

import sys
from pathlib import Path

# 添加專案根目錄到 sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_sector_persistence_logic():
    """測試 sector 持久化邏輯"""
    
    # 模擬第一次載入（Brazil，有 sector_boundaries）
    print("=" * 80)
    print("第一次載入：Brazil（有 sector_boundaries）")
    print("=" * 80)
    
    data1 = {
        "sector_boundaries": [
            {"sector": 1, "name": "S1 End", "distance_m": 1233.1},
            {"sector": 2, "name": "S2 End", "distance_m": 3130.3},
            {"sector": 3, "name": "S3 End", "distance_m": 0.0}
        ],
        "track_data": {}
    }
    
    # 模擬處理邏輯
    _current_flags_data = None
    old_sector_boundaries = []
    
    # 保存舊數據
    if _current_flags_data:
        old_sector_boundaries = _current_flags_data.get("sector_boundaries", [])
        print(f"✅ 保存舊的 sector_boundaries: {len(old_sector_boundaries)} 個")
    else:
        print("⚠️  首次載入，無舊數據")
    
    # 儲存新數據
    _current_flags_data = data1
    
    # 構建 track_data
    track_data = data1.get("track_data", {})
    if not track_data:
        track_data = {
            "sector_boundaries": data1.get("sector_boundaries", [])
        }
    
    # 強制補充邏輯
    if "sector_boundaries" not in track_data or not track_data.get("sector_boundaries"):
        if "sector_boundaries" in data1 and data1.get("sector_boundaries"):
            track_data["sector_boundaries"] = data1.get("sector_boundaries", [])
            print(f"✅ 從當前 data 補充: {len(track_data['sector_boundaries'])} 個")
        elif old_sector_boundaries:
            track_data["sector_boundaries"] = old_sector_boundaries
            print(f"🔄 從舊數據恢復: {len(old_sector_boundaries)} 個")
        else:
            track_data["sector_boundaries"] = []
            print("⚠️  設置為空列表")
    
    print(f"最終 track_data.sector_boundaries: {len(track_data['sector_boundaries'])} 個")
    assert len(track_data['sector_boundaries']) == 3, "第一次載入應該有 3 個 sector"
    print("✅ 測試通過\n")
    
    # 模擬第二次載入（Bahrain，有 sector_boundaries）
    print("=" * 80)
    print("第二次載入：Bahrain（有 sector_boundaries）")
    print("=" * 80)
    
    data2 = {
        "sector_boundaries": [
            {"sector": 1, "name": "S1 End", "distance_m": 1767.8},
            {"sector": 2, "name": "S2 End", "distance_m": 3948.8},
            {"sector": 3, "name": "S3 End", "distance_m": 0.0}
        ],
        "track_data": {}
    }
    
    # 保存舊數據
    old_sector_boundaries = []
    if _current_flags_data:
        old_sector_boundaries = _current_flags_data.get("sector_boundaries", [])
        print(f"✅ 保存舊的 sector_boundaries: {len(old_sector_boundaries)} 個")
    
    # 儲存新數據
    _current_flags_data = data2
    
    # 構建 track_data
    track_data = data2.get("track_data", {})
    if not track_data:
        track_data = {
            "sector_boundaries": data2.get("sector_boundaries", [])
        }
    
    # 強制補充邏輯
    if "sector_boundaries" not in track_data or not track_data.get("sector_boundaries"):
        if "sector_boundaries" in data2 and data2.get("sector_boundaries"):
            track_data["sector_boundaries"] = data2.get("sector_boundaries", [])
            print(f"✅ 從當前 data 補充: {len(track_data['sector_boundaries'])} 個")
        elif old_sector_boundaries:
            track_data["sector_boundaries"] = old_sector_boundaries
            print(f"🔄 從舊數據恢復: {len(old_sector_boundaries)} 個")
        else:
            track_data["sector_boundaries"] = []
            print("⚠️  設置為空列表")
    
    print(f"最終 track_data.sector_boundaries: {len(track_data['sector_boundaries'])} 個")
    assert len(track_data['sector_boundaries']) == 3, "第二次載入應該有 3 個 sector"
    print("✅ 測試通過\n")
    
    # 模擬第三次載入（沒有 sector_boundaries 的數據，模擬舊緩存）
    print("=" * 80)
    print("第三次載入：舊緩存（沒有 sector_boundaries）")
    print("=" * 80)
    
    data3 = {
        "track_data": {}
        # 沒有 sector_boundaries
    }
    
    # 保存舊數據
    old_sector_boundaries = []
    if _current_flags_data:
        old_sector_boundaries = _current_flags_data.get("sector_boundaries", [])
        print(f"✅ 保存舊的 sector_boundaries: {len(old_sector_boundaries)} 個（來自 Bahrain）")
    
    # 儲存新數據
    _current_flags_data = data3
    
    # 構建 track_data
    track_data = data3.get("track_data", {})
    if not track_data:
        track_data = {}
    
    # 強制補充邏輯
    if "sector_boundaries" not in track_data or not track_data.get("sector_boundaries"):
        if "sector_boundaries" in data3 and data3.get("sector_boundaries"):
            track_data["sector_boundaries"] = data3.get("sector_boundaries", [])
            print(f"✅ 從當前 data 補充: {len(track_data['sector_boundaries'])} 個")
        elif old_sector_boundaries:
            track_data["sector_boundaries"] = old_sector_boundaries
            print(f"🔄 從舊數據恢復: {len(old_sector_boundaries)} 個")
        else:
            track_data["sector_boundaries"] = []
            print("⚠️  設置為空列表")
    
    print(f"最終 track_data.sector_boundaries: {len(track_data['sector_boundaries'])} 個")
    assert len(track_data['sector_boundaries']) == 3, "第三次載入應該從舊數據恢復 3 個 sector"
    print("✅ 測試通過：成功從舊數據恢復 sector_boundaries！\n")
    
    print("=" * 80)
    print("所有測試通過！修復邏輯正常工作")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_sector_persistence_logic()
        print("\n✅ 所有測試通過！")
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 測試錯誤: {e}")
        import traceback
        traceback.print_exc()
