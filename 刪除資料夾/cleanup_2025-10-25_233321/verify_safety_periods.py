"""驗證生成的 safety_periods 資料結構"""
import json
import os
from glob import glob

# 找到最新的 2021 Bahrain JSON 檔案
pattern = "json/all_incidents_summary_2021_Bahrain*.json"
files = glob(pattern)

if not files:
    print(f"❌ 找不到檔案: {pattern}")
    exit(1)

# 按修改時間排序，取最新的
latest_file = max(files, key=os.path.getmtime)
print(f"📂 讀取檔案: {latest_file}\n")

with open(latest_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# safety_periods 在 data 物件內部
root_data = data.get('data', {})

# 檢查 safety_periods 欄位
if 'safety_periods' not in root_data:
    print("❌ 錯誤：data 物件中沒有 'safety_periods' 欄位！")
    print(f"data 物件的欄位: {list(root_data.keys())}")
    exit(1)

safety_periods = root_data['safety_periods']
print(f"✅ 找到 safety_periods 欄位")
print(f"📊 共有 {len(safety_periods)} 個 Safety Period(s)\n")

if len(safety_periods) == 0:
    print("⚠️  警告：safety_periods 陣列是空的！")
else:
    print("=" * 80)
    print("Safety Periods 詳細內容:")
    print("=" * 80)
    
    for i, period in enumerate(safety_periods, 1):
        print(f"\n【Period {i}】")
        print(f"  Type:       {period.get('type')}")
        print(f"  Start Lap:  {period.get('start_lap')}")
        print(f"  End Lap:    {period.get('end_lap')}")
        print(f"  Reason:     {period.get('reason')}")
        print(f"  Sector:     {period.get('sector')}")
        
        # 驗證必要欄位
        required_fields = ['type', 'start_lap', 'end_lap', 'reason']
        missing = [f for f in required_fields if f not in period]
        
        if missing:
            print(f"  ⚠️  缺少欄位: {missing}")
        else:
            print(f"  ✅ 所有必要欄位完整")

print("\n" + "=" * 80)
print("驗證結果總結:")
print("=" * 80)

# 結構驗證
all_valid = True
for period in safety_periods:
    if not all(k in period for k in ['type', 'start_lap', 'end_lap', 'reason']):
        all_valid = False
        break

if all_valid and len(safety_periods) > 0:
    print("✅ 所有 Safety Periods 結構正確")
    print(f"✅ 符合 GUI 期望的格式: {{type, start_lap, end_lap, reason}}")
else:
    print("❌ 資料結構驗證失敗")

print(f"\n總計: {len(safety_periods)} 個有效的 Safety Period(s)")
