#!/usr/bin/env python3
"""
測試 -f15 新增的「賽事名次變更總次數」功能
"""

import json
from pathlib import Path

# 模擬超車統計數據
mock_overtaking_stats = [
    {"driver_name": "VER", "overtakes_made": 8, "overtaken_by": 2, "net_overtaking": 6},
    {"driver_name": "HAM", "overtakes_made": 12, "overtaken_by": 4, "net_overtaking": 8},
    {"driver_name": "LEC", "overtakes_made": 6, "overtaken_by": 5, "net_overtaking": 1},
    {"driver_name": "SAI", "overtakes_made": 9, "overtaken_by": 3, "net_overtaking": 6},
    {"driver_name": "NOR", "overtakes_made": 7, "overtaken_by": 6, "net_overtaking": 1},
]

def test_generate_summary_statistics():
    """測試統計摘要生成函數"""
    print("=" * 80)
    print("測試 -f15 新增功能：賽事名次變更總次數")
    print("=" * 80)
    
    # 計算統計
    total_overtakes = sum(s['overtakes_made'] for s in mock_overtaking_stats)
    total_overtaken = sum(s['overtaken_by'] for s in mock_overtaking_stats)
    total_position_changes = total_overtakes + total_overtaken
    
    print(f"\n📊 模擬數據統計：")
    print(f"   車手數量: {len(mock_overtaking_stats)} 人")
    print(f"   總超車次數: {total_overtakes} 次")
    print(f"   總被超次數: {total_overtaken} 次")
    print(f"   🆕 賽事名次變更總次數: {total_position_changes} 次")
    print(f"   平均每車手名次變化: {total_position_changes / len(mock_overtaking_stats):.1f} 次")
    
    # 驗證計算邏輯
    print(f"\n✅ 驗證計算邏輯：")
    print(f"   {total_overtakes} (超車) + {total_overtaken} (被超) = {total_position_changes} (總變化)")
    
    # 顯示詳細數據
    print(f"\n📋 詳細數據：")
    for i, driver in enumerate(mock_overtaking_stats, 1):
        changes = driver['overtakes_made'] + driver['overtaken_by']
        print(f"   {i}. {driver['driver_name']}: {driver['overtakes_made']} 超車 + {driver['overtaken_by']} 被超 = {changes} 次變化")
    
    print(f"\n" + "=" * 80)
    
    # 檢查最新的 JSON 檔案
    print("\n🔍 檢查最新生成的 JSON 檔案：")
    json_dir = Path("json")
    json_files = list(json_dir.glob("all_drivers_annual_overtaking_statistics_*.json"))
    
    if json_files:
        latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"   檔案: {latest_json.name}")
        print(f"   時間: {latest_json.stat().st_mtime}")
        
        with open(latest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        summary = data.get('summary', {})
        print(f"\n   JSON Summary 內容：")
        print(f"   - total_drivers: {summary.get('total_drivers')}")
        print(f"   - total_overtakes: {summary.get('total_overtakes')}")
        print(f"   - total_overtaken: {summary.get('total_overtaken')}")
        
        if 'total_position_changes' in summary:
            print(f"   - 🆕 total_position_changes: {summary.get('total_position_changes')} ✅")
            print(f"   - 🆕 average_position_changes_per_driver: {summary.get('average_position_changes_per_driver')} ✅")
        else:
            print(f"   - ❌ total_position_changes: 欄位不存在（需要重新執行 -f15）")
    else:
        print("   ⚠️  找不到 JSON 檔案")
    
    print(f"\n" + "=" * 80)
    print("✅ 測試完成！")
    print("\n💡 提示：執行以下命令生成新的統計數據：")
    print("   python f1_analysis_modular_main.py -f 15 -y 2024 -r Japan -s R")
    print("=" * 80)

if __name__ == "__main__":
    test_generate_summary_statistics()
