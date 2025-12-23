"""比較 F48 和 F121 JSON 結構"""
import json

# 讀取 F48 JSON
with open('json/all_drivers_straight_line_speed_2025_Abu Dhabi_R.json', 'r', encoding='utf-8') as f:
    f48 = json.load(f)

# 讀取 F121 JSON
with open('json/fp2_straight_line_all_laps_analysis_2025_Abu Dhabi_R.json', 'r', encoding='utf-8') as f:
    f121 = json.load(f)

print("=" * 80)
print("F48 vs F121 JSON 結構比較")
print("=" * 80)
print()

print("【頂層欄位比較】")
print(f"  F48 欄位: {list(f48.keys())}")
print(f"  F121 欄位: {list(f121.keys())}")
print()

print("【車手數據結構】")

# F48 結構
print("------- F48 (單圈最佳) -------")
if 'results' in f48:
    f48_results = f48.get('results', {})
    f48_drivers = f48_results.get('all_drivers', [])
    if f48_drivers:
        sample = f48_drivers[0]
        print(f"  車手數: {len(f48_drivers)}")
        print(f"  範例車手: {sample.get('driver', 'N/A')}")
        print(f"  欄位:")
        for key, value in sample.items():
            if isinstance(value, dict):
                print(f"    • {key}: dict")
            elif isinstance(value, list):
                print(f"    • {key}: list[{len(value)}]")
            else:
                print(f"    • {key}: {value}")
print()

# F121 結構
print("------- F121 (全圈數統計) -------")
f121_drivers = f121.get('drivers', [])
if f121_drivers:
    sample = f121_drivers[0]
    print(f"  車手數: {len(f121_drivers)}")
    print(f"  範例車手: {sample.get('driver', 'N/A')}")
    print(f"  欄位:")
    for key, value in sample.items():
        if isinstance(value, dict):
            print(f"    • {key}: dict with {list(value.keys())}")
        elif isinstance(value, list):
            print(f"    • {key}: list[{len(value)}]")
        else:
            print(f"    • {key}: {value}")
print()

print("【關鍵差異】")
print("  F48:")
print("    - max_speed_kmh: 單一最高速度值 (最快圈)")
print("    - segment_accel_time_seconds: 單一加速時間 (賽道段)")
print("    - time_to_max_speed_seconds: 單一推算時間 (線性)")
print("    - 數據來源: 硬編碼起點 + 油門辨識終點")
print()
print("  F121:")
print("    - speed_stats: 完整統計分佈 (median/mean/std_dev/...)")
print("    - acceleration_100_300_stats: 加速時間統計")
print("    - time_to_max_speed_stats: 推算時間統計")
print("    - absolute_max_speed_kmh: 所有圈的絕對最高速度")
print("    - absolute_max_speed_lap: 達到最高速的圈數")
print("    - speeds_raw: 原始速度陣列")
print("    - 數據來源: 官方 API car_data (100→300 固定範圍)")
print()

print("【GUI 適配需求】")
print("  1. 新建 all_drivers_max_speed_analysis 資料夾")
print("  2. 創建專屬 DataLoader (呼叫 F121)")
print("  3. 創建 TableWidget (顯示 F121 統計數據)")
print("  4. 創建 MDI 視窗整合")
print("  5. 註冊模組到工廠")
print("=" * 80)
