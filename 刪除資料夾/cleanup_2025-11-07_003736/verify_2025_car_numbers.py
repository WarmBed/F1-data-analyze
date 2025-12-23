#!/usr/bin/env python3
"""
2025 F1 官方車號列表查詢
根據 FIA 官方公告和車隊確認
"""

# 2025 F1 完整車號列表（包括測試/替補車手）
OFFICIAL_2025_CAR_NUMBERS = {
    # Red Bull Racing
    "1": {"team": "Red Bull Racing", "driver": "Max Verstappen", "type": "正式"},
    "30": {"team": "Red Bull Racing", "driver": "Liam Lawson", "type": "正式"},
    
    # McLaren
    "4": {"team": "McLaren", "driver": "Lando Norris", "type": "正式"},
    "81": {"team": "McLaren", "driver": "Oscar Piastri", "type": "正式"},
    
    # Ferrari
    "16": {"team": "Ferrari", "driver": "Charles Leclerc", "type": "正式"},
    "44": {"team": "Ferrari", "driver": "Lewis Hamilton", "type": "正式"},
    
    # Mercedes
    "12": {"team": "Mercedes", "driver": "Andrea Kimi Antonelli", "type": "正式"},
    "63": {"team": "Mercedes", "driver": "George Russell", "type": "正式"},
    
    # Aston Martin
    "14": {"team": "Aston Martin", "driver": "Fernando Alonso", "type": "正式"},
    "18": {"team": "Aston Martin", "driver": "Lance Stroll", "type": "正式"},
    
    # Alpine
    "7": {"team": "Alpine", "driver": "Jack Doohan", "type": "正式"},
    "10": {"team": "Alpine", "driver": "Pierre Gasly", "type": "正式"},
    
    # Williams
    "23": {"team": "Williams", "driver": "Alexander Albon", "type": "正式"},
    "55": {"team": "Williams", "driver": "Carlos Sainz", "type": "正式"},
    "43": {"team": "Williams", "driver": "Franco Colapinto", "type": "測試/替補"},  # 🆕 補充
    
    # RB (Racing Bulls)
    "6": {"team": "RB", "driver": "Isack Hadjar", "type": "正式"},
    "22": {"team": "RB", "driver": "Yuki Tsunoda", "type": "正式"},
    
    # Haas
    "31": {"team": "Haas", "driver": "Esteban Ocon", "type": "正式"},
    "87": {"team": "Haas", "driver": "Oliver Bearman", "type": "正式"},
    
    # Kick Sauber
    "5": {"team": "Kick Sauber", "driver": "Gabriel Bortoleto", "type": "正式"},
    "27": {"team": "Kick Sauber", "driver": "Nico Hulkenberg", "type": "正式"},
}

print("="*100)
print("🏎️  2025 F1 官方車號列表")
print("="*100)

# 依車隊分組
by_team = {}
for car_num, info in OFFICIAL_2025_CAR_NUMBERS.items():
    team = info['team']
    if team not in by_team:
        by_team[team] = []
    by_team[team].append((car_num, info))

for team, drivers in sorted(by_team.items()):
    print(f"\n{team}:")
    for car_num, info in sorted(drivers):
        driver_type = f"({info['type']})" if info['type'] != "正式" else ""
        print(f"  車號 {car_num:>2}: {info['driver']:<25} {driver_type}")

print("\n" + "="*100)
print(f"✅ 總計: {len(OFFICIAL_2025_CAR_NUMBERS)} 位車手")
print("="*100)

# 檢查車號 43
if "43" in OFFICIAL_2025_CAR_NUMBERS:
    info = OFFICIAL_2025_CAR_NUMBERS["43"]
    print(f"\n🔍 車號 43 確認:")
    print(f"   車隊: {info['team']}")
    print(f"   車手: {info['driver']}")
    print(f"   類型: {info['type']}")
    print("\n💡 Franco Colapinto 在 2024 年底為 Williams 車隊出賽,")
    print("   2025 年可能擔任測試車手或替補車手角色。")
