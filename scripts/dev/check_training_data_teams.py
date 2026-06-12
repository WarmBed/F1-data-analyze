"""檢查訓練數據中的車隊名稱分佈"""

import json
from collections import Counter
from pathlib import Path

# 載入訓練數據
training_file = Path("training_data/fp2_q_training_data_2022_2025.json")

print(f"讀取訓練數據: {training_file}")
with open(training_file, 'r', encoding='utf-8') as f:
    training_data = json.load(f)

print(f"總數據筆數: {len(training_data)}")

# 統計車隊分佈
team_counter = Counter()
team_year_dist = {}

for record in training_data:
    team = record.get('team', 'Unknown')
    year = record.get('year', 'Unknown')
    
    team_counter[team] += 1
    
    if team not in team_year_dist:
        team_year_dist[team] = Counter()
    team_year_dist[team][year] += 1

print("\n=== 車隊數據分佈 (總計) ===")
print(f"{'車隊':<30} {'總樣本數':<10} {'年份分佈'}")
print("-" * 80)

for team, count in sorted(team_counter.items(), key=lambda x: x[1], reverse=True):
    year_dist = team_year_dist[team]
    year_str = ", ".join([f"{year}: {cnt}" for year, cnt in sorted(year_dist.items())])
    print(f"{team:<30} {count:<10} {year_str}")

# 重點檢查新舊車隊名稱對應
print("\n=== 車隊更名檢查 ===")

rename_map = {
    "Alfa Romeo": "Kick Sauber",  # 2024 更名
    "AlphaTauri": "Racing Bulls",  # 2024 更名
    "Aston Martin": "Aston Martin",  # 無更名
}

print("\n檢查是否有舊名稱存在:")
for old_name, new_name in rename_map.items():
    old_count = team_counter.get(old_name, 0)
    new_count = team_counter.get(new_name, 0)
    
    if old_count > 0:
        print(f"  ⚠️  發現舊名稱: {old_name} ({old_count} 筆)")
        print(f"     新名稱: {new_name} ({new_count} 筆)")
        print(f"     📊 如果合併: {old_count + new_count} 筆")

# 檢查 Quali Sim 標記
print("\n=== Quali Sim 數據分佈 ===")

team_quali_sim = {}
for record in training_data:
    team = record.get('team', 'Unknown')
    is_quali_sim = record.get('is_quali_sim', False)
    
    if team not in team_quali_sim:
        team_quali_sim[team] = {'total': 0, 'quali_sim': 0}
    
    team_quali_sim[team]['total'] += 1
    if is_quali_sim:
        team_quali_sim[team]['quali_sim'] += 1

print(f"{'車隊':<30} {'總樣本':<10} {'Quali Sim':<12} {'比例'}")
print("-" * 80)

for team in sorted(team_quali_sim.keys()):
    stats = team_quali_sim[team]
    total = stats['total']
    qs = stats['quali_sim']
    ratio = (qs / total * 100) if total > 0 else 0
    print(f"{team:<30} {total:<10} {qs:<12} {ratio:>5.1f}%")

print("\n=== 問題分析 ===")
print("🔍 Kick Sauber 和 Racing Bulls 樣本數少的可能原因:")
print("   1. 這是 2024 年才更名的車隊")
print("   2. 訓練數據中 2022-2023 年使用舊名稱 (Alfa Romeo, AlphaTauri)")
print("   3. learn_team_fuel_habits.py 沒有處理車隊更名映射")
print("\n💡 解決方案:")
print("   需要在 learn_team_fuel_habits.py 中添加車隊名稱標準化邏輯")
print("   將 Alfa Romeo → Kick Sauber")
print("   將 AlphaTauri → Racing Bulls")
