#!/usr/bin/env python3
"""
Debug Race Switch Sector Loss
調試切換 race 時 sector 標註消失的問題

測試流程：
1. 載入 Brazil 2024 - 檢查 sector_boundaries
2. 切換到 Bahrain 2024 - 檢查 sector_boundaries
3. 切換回 Brazil 2024 - 檢查 sector_boundaries

分析點：
- _on_data_loaded() 調用次數
- track_data 中 sector_boundaries 的存在
- TrackMapWidget.sector_boundaries 的狀態
- 持久化邏輯是否正常工作
"""

import json
from pathlib import Path

def check_json_sector_boundaries(json_path: Path) -> None:
    """檢查 JSON 檔案中的 sector_boundaries"""
    print(f"\n{'='*80}")
    print(f"檢查檔案: {json_path.name}")
    print(f"{'='*80}")
    
    if not json_path.exists():
        print(f"❌ 檔案不存在")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查頂層結構
    top_keys = list(data.keys())
    print(f"✅ 頂層鍵: {top_keys}")
    
    # 檢查 data 層級
    if 'data' in data:
        data_level = data['data']
        data_keys = list(data_level.keys())
        print(f"✅ data 層級鍵: {data_keys}")
        
        # 檢查 sector_boundaries
        if 'sector_boundaries' in data_level:
            sector_boundaries = data_level['sector_boundaries']
            print(f"\n✅ sector_boundaries 存在")
            print(f"   數量: {len(sector_boundaries)}")
            for sb in sector_boundaries:
                print(f"   - {sb.get('name')}: {sb.get('distance_m'):.1f}m at ({sb.get('position_x'):.1f}, {sb.get('position_y'):.1f})")
        else:
            print(f"\n❌ sector_boundaries 不存在於 data 層級")
        
        # 檢查 track_data
        if 'track_data' in data_level:
            track_data = data_level['track_data']
            track_keys = list(track_data.keys())
            print(f"\n✅ track_data 存在")
            print(f"   鍵: {track_keys}")
            
            if 'sector_boundaries' in track_data:
                print(f"   ✅ sector_boundaries 在 track_data 中")
                print(f"      數量: {len(track_data['sector_boundaries'])}")
            else:
                print(f"   ❌ sector_boundaries 不在 track_data 中")
        else:
            print(f"\n❌ track_data 不存在")
    else:
        print(f"❌ data 層級不存在")

def analyze_data_flow_issue():
    """分析數據流問題"""
    print("\n" + "="*80)
    print("數據流分析")
    print("="*80)
    
    print("""
問題描述：
用戶報告切換 race 時 sector 標註消失

可能原因：
1. 切換 race 時重新調用 _on_data_loaded()
2. 新的數據沒有包含 sector_boundaries
3. 持久化邏輯 (_current_flags_data) 被新數據覆蓋
4. TrackMapWidget.load_track_data() 清空了 sector_boundaries

關鍵代碼位置：
1. historical_track_map_mdi.py:_on_data_loaded() (Line 887)
   - 保存數據: self._current_flags_data = data
   - 持久化邏輯 (Line 901-915)

2. track_map_widget.py:load_track_data() (Line 239-255)
   - 載入 sector_boundaries

調試策略：
A. 檢查 JSON 檔案是否都有 sector_boundaries
B. 追蹤 _on_data_loaded() 的調用次數
C. 檢查 track_data 的構建邏輯
D. 驗證持久化邏輯的觸發條件

可能的問題：
❗ 持久化邏輯只在 "sector_boundaries" not in track_data 時觸發
❗ 如果新數據的 track_data 為空，但持久化邏輯只檢查 track_data 中的 sector_boundaries
❗ 這會導致新數據覆蓋舊的 _current_flags_data，但不恢復 sector_boundaries

修復方案：
✅ 方案 A: 在切換 race 時保留上一次的 sector_boundaries（不推薦，數據不一致）
✅ 方案 B: 確保 API 返回的數據總是包含 sector_boundaries
✅ 方案 C: 改進持久化邏輯，在 _on_data_loaded() 開始就檢查並保存 sector_boundaries
✅ 方案 D: 在 TrackMapWidget.load_track_data() 中不清空 sector_boundaries，除非新數據明確提供
""")

def main():
    """主程式"""
    json_dir = Path("json")
    
    # 檢查 Brazil JSON
    brazil_json = json_dir / "historical_flags_Brazil_2022-2025.json"
    check_json_sector_boundaries(brazil_json)
    
    # 檢查 Bahrain JSON
    bahrain_json = json_dir / "historical_flags_Bahrain_2022-2025.json"
    check_json_sector_boundaries(bahrain_json)
    
    # 分析數據流問題
    analyze_data_flow_issue()
    
    print("\n" + "="*80)
    print("建議測試步驟")
    print("="*80)
    print("""
1. 啟動 GUI: python f1t_gui_main.py
2. 打開 Historical Track Map
3. 選擇 Brazil 2024 → 確認有 S1/S2/S3 標註
4. 切換到 Bahrain 2024 → 檢查是否有標註
5. 切換回 Brazil 2024 → 檢查標註是否消失

同時觀察 Console 輸出：
- [HISTORICAL_TRACK_MAP_MDI] _on_data_loaded 觸發
- [DEBUG] sector_boundaries 數量
- [TRACK_MAP] 成功載入 X 個 Sector 邊界

預期問題：
❌ 切換到新 race 時，_on_data_loaded() 被調用
❌ 新數據的 track_data 可能為空或沒有 sector_boundaries
❌ 持久化邏輯可能沒有觸發（條件不滿足）
❌ TrackMapWidget 被設置為空的 sector_boundaries
""")

if __name__ == "__main__":
    main()
