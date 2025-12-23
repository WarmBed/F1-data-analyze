"""檢查 F48/F54/F34 在衝刺賽週末的數據生成情況"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
import json

# 衝刺賽週末列表（沒有 FP3）
sprint_weekends = {
    2020: ["Emilia Romagna"],
    2021: ["Great Britain", "Italy", "Brazil"],
    2022: ["Emilia Romagna", "Austria", "Brazil"],
    2023: ["Azerbaijan", "Austria", "Belgium", "Qatar", "United States", "Brazil"],
    2024: ["China", "Miami", "Austria", "United States", "Brazil", "Qatar"],
}

# 功能 ID 和文件模式
functions = {
    48: "all_drivers_straight_line_speed",
    54: "driver_throttle_ratio",
    34: "brake_performance",
}

json_dir = Path("json")

print("=" * 80)
print("衝刺賽週末數據檢查 (F48/F54/F34)")
print("=" * 80)

for func_id, pattern in functions.items():
    print(f"\n{'='*80}")
    print(f"功能 {func_id}: {pattern}")
    print(f"{'='*80}")
    
    fp3_count = 0
    fp1_count = 0
    missing = []
    
    for year, races in sprint_weekends.items():
        for race in races:
            # 檢查 FP3 檔案
            fp3_files = list(json_dir.glob(f"{pattern}_{year}_{race}_FP3.json"))
            # 檢查 FP1 檔案（替代方案）
            fp1_files = list(json_dir.glob(f"{pattern}_{year}_{race}_FP1.json"))
            
            if fp3_files:
                fp3_count += 1
                print(f"  ✅ {year} {race:20s} - 有 FP3 (錯誤！衝刺週末沒有 FP3)")
            elif fp1_files:
                fp1_count += 1
                print(f"  ✅ {year} {race:20s} - 有 FP1 (正確替代)")
            else:
                missing.append((year, race))
                print(f"  ❌ {year} {race:20s} - 缺失")
    
    total_sprints = sum(len(races) for races in sprint_weekends.values())
    print(f"\n統計：")
    print(f"  - 衝刺賽總數: {total_sprints}")
    print(f"  - FP3 檔案: {fp3_count} (應為 0)")
    print(f"  - FP1 檔案: {fp1_count}")
    print(f"  - 缺失: {len(missing)}")
    
    if missing:
        print(f"\n缺失的衝刺賽週末：")
        for year, race in missing:
            print(f"    {year} {race}")

print("\n" + "=" * 80)
print("結論")
print("=" * 80)
print("如果功能顯示「有 FP3」，表示在衝刺週末錯誤生成了 FP3 數據")
print("這些功能需要應用衝刺賽週末自動切換邏輯（FP3 → FP1）")
