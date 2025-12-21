"""驗證 2025 Australia R 生成的 safety_periods"""
import json
from glob import glob
import os

# 找到最新的 2025 Australia JSON
pattern = "json/all_incidents_summary_2025_Australia*.json"
files = glob(pattern)

if not files:
    print(f"❌ 找不到檔案: {pattern}")
    exit(1)

latest = max(files, key=os.path.getmtime)
print(f"📂 讀取: {latest}\n")

with open(latest, 'r', encoding='utf-8') as f:
    data = json.load(f)

periods = data.get('data', {}).get('safety_periods', [])

print("=" * 80)
print(f"Safety Periods 驗證結果 - 2025 Australia R")
print("=" * 80)
print(f"\n✅ 找到 {len(periods)} 個 Safety Period(s)\n")

if len(periods) == 0:
    print("⚠️  警告: safety_periods 陣列是空的！")
else:
    for i, period in enumerate(periods, 1):
        print(f"【Period {i}】")
        print(f"  Type:       {period.get('type')}")
        print(f"  Start Lap:  {period.get('start_lap')}")
        print(f"  End Lap:    {period.get('end_lap')}")
        print(f"  Reason:     {period.get('reason')}")
        print(f"  Sector:     {period.get('sector')}")
        
        duration = period.get('end_lap', 0) - period.get('start_lap', 0)
        print(f"  Duration:   {duration} laps")
        print()

print("=" * 80)
print("期望結果對比:")
print("=" * 80)
print("  Expected: 3 個 SC Periods")
print("    • SC Period 1: Lap 1-7   (6 laps)")
print("    • SC Period 2: Lap 34-41 (7 laps)")
print("    • SC Period 3: Lap 47-51 (4 laps)")
print()
print(f"  Actual:   {len(periods)} 個 SC Period(s)")

if len(periods) == 3:
    print("\n  ✅ 數量匹配！")
    
    expected = [(1, 7), (34, 41), (47, 51)]
    all_match = True
    
    for i, (period, (exp_start, exp_end)) in enumerate(zip(periods, expected), 1):
        actual_start = period.get('start_lap')
        actual_end = period.get('end_lap')
        
        if actual_start == exp_start and actual_end == exp_end:
            print(f"  ✅ Period {i}: Lap {actual_start}-{actual_end} 正確")
        else:
            print(f"  ❌ Period {i}: 期望 Lap {exp_start}-{exp_end}, 實際 Lap {actual_start}-{actual_end}")
            all_match = False
    
    if all_match:
        print("\n🎉 所有 Safety Periods 完全正確！")
else:
    print(f"\n  ❌ 數量不匹配（期望 3 個，實際 {len(periods)} 個）")
