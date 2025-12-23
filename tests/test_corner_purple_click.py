"""
測試彎道性能散點圖的紫色點點擊功能

驗證：
1. 紫色過濾點可以正確懸停顯示提示
2. 紫色過濾點可以右鍵點擊顯示選單
3. 索引映射正確（點擊 ANT 顯示 ANT，不會選到其他車手）
"""
import sys
import json
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_index_mapping():
    """測試索引映射邏輯"""
    import numpy as np
    
    # 模擬數據
    total_drivers = 5
    x_data = [100, 110, 120, 130, 140]  # 5 個點
    is_filtered = [False, True, False, True, False]  # 索引 1 和 3 是過濾點
    
    # 建立映射
    filtered_mask = np.array(is_filtered)
    normal_mask = ~filtered_mask
    global_indices = np.arange(len(x_data))
    
    # 正常點映射
    normal_map = global_indices[normal_mask]  # [0, 2, 4]
    # 過濾點映射
    filtered_map = global_indices[filtered_mask]  # [1, 3]
    
    print("=== 索引映射測試 ===")
    print(f"全局索引: {list(global_indices)}")
    print(f"過濾遮罩: {is_filtered}")
    print(f"正常點映射: {list(normal_map)} (全局索引 0,2,4 → scatter 相對索引 0,1,2)")
    print(f"過濾點映射: {list(filtered_map)} (全局索引 1,3 → scatter 相對索引 0,1)")
    print()
    
    # 測試反向查找
    print("=== 反向查找測試 ===")
    # 如果點擊過濾點的第 0 個（scatter 相對索引 0）
    clicked_relative = 0
    clicked_global = filtered_map[clicked_relative]
    print(f"點擊過濾點 scatter[0] → 全局索引 {clicked_global} (應該是 1)")
    
    # 如果點擊過濾點的第 1 個（scatter 相對索引 1）
    clicked_relative = 1
    clicked_global = filtered_map[clicked_relative]
    print(f"點擊過濾點 scatter[1] → 全局索引 {clicked_global} (應該是 3)")
    print()

def test_abu_dhabi_data():
    """測試 Abu Dhabi 實際數據"""
    json_path = Path("json/F120_corner_all_laps_analysis_2025_Abu_Dhabi_R.json")
    
    if not json_path.exists():
        print(f"❌ 找不到測試數據: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    drivers_data = data['mode_a_unified']['drivers']
    
    print("=== Abu Dhabi Low Speed Corner 6 過濾狀態 ===")
    for i, driver in enumerate(drivers_data):
        corner = driver['corners'].get('low_speed_corner_6')
        if corner and (corner.get('entry_filtered') or corner.get('exit_filtered')):
            print(f"索引 {i}: {driver['driver']} - Entry:{corner.get('entry_outliers_count', 0)}, Exit:{corner.get('exit_outliers_count', 0)}")
    
    print()
    print("預期結果：ANT 應該顯示為過濾點（紫色）")
    print("點擊測試：右鍵點擊 ANT 的紫色點應該顯示 'ANT'，不應該是其他車手")

if __name__ == "__main__":
    test_index_mapping()
    print("\n" + "="*60 + "\n")
    test_abu_dhabi_data()
    
    print("\n" + "="*60)
    print("✅ 測試完成")
    print("\n請在 GUI 中驗證：")
    print("1. 打開 Low Speed Corner 模組")
    print("2. 懸停在 ANT 的紫色點上，應該顯示 'ANT (Estimated)'")
    print("3. 右鍵點擊 ANT 的紫色點，應該顯示 'Hide ANT' 選項")
    print("4. 不應該選到其他車手")
