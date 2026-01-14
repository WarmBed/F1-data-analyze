# -*- coding: utf-8 -*-
"""
檢查 Team Radio 數據中的車手數量
"""
import json
from pathlib import Path
from collections import Counter

# 讀取 Abu Dhabi 正賽數據
data_file = Path(r"c:\Users\mike2\OneDrive\Code\F1-data-analyze\team_radio_data\2025\TeamRadio_2025_Abu_Dhabi_R_parsed.json")

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"📊 Abu Dhabi 2025 Race - Team Radio 分析")
print(f"=" * 50)
print(f"總記錄數: {len(data)}")

# 統計每個車手的記錄數
driver_counts = Counter(r['racing_number'] for r in data)
print(f"唯一車手數: {len(driver_counts)}")
print(f"\n各車手記錄數:")

for driver_num in sorted(driver_counts.keys(), key=int):
    count = driver_counts[driver_num]
    print(f"  車手 {driver_num:>2}: {count} 條記錄")

# 2025 年車手名單 (20 位)
all_drivers_2025 = {
    '1': 'VER', '4': 'NOR', '5': 'GAS', '6': 'HAD', 
    '10': 'LAW', '11': 'PER', '14': 'ALO', '18': 'STR',
    '22': 'TSU', '23': 'ALB', '27': 'HUL', '30': 'DOO',
    '31': 'OCO', '38': 'BOR', '44': 'HAM', '55': 'SAI',
    '63': 'RUS', '81': 'PIA', '87': 'BEA', '16': 'LEC'
}

missing_drivers = set(all_drivers_2025.keys()) - set(driver_counts.keys())
print(f"\n⚠️ 缺少 Team Radio 的車手 ({len(missing_drivers)} 位):")
for d in sorted(missing_drivers, key=int):
    print(f"  車手 {d:>2} ({all_drivers_2025.get(d, '?')})")
