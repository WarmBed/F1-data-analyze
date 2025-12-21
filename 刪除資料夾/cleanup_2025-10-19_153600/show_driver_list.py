"""從 F98 team_colors JSON 提取車手名單"""
import json
import os
from glob import glob

# 找最新的 team_colors JSON
json_files = glob("json/team_colors_2025_*.json")
if not json_files:
    print("❌ 找不到 team_colors JSON 檔案")
    print("請執行: python f1_analysis_modular_main.py -f 98 -y 2025")
    exit(1)

latest_file = max(json_files, key=os.path.getmtime)
print(f"📂 讀取: {latest_file}\n")

with open(latest_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data.get('data', {}).get('drivers', {})

print("=" * 60)
print(f"2025 賽季車手名單（共 {len(drivers)} 位）")
print("=" * 60)

# 按車隊分組
teams = {}
for code, info in drivers.items():
    team = info.get('team_name', 'Unknown')
    if team not in teams:
        teams[team] = []
    teams[team].append({
        'code': code,
        'name': info.get('full_name', ''),
        'color': info.get('hex', '')
    })

# 顯示每個車隊的車手
for team in sorted(teams.keys()):
    print(f"\n🏎️  {team}")
    for driver in sorted(teams[team], key=lambda x: x['name']):
        print(f"   {driver['code']:3s} - {driver['name']:25s} ({driver['color']})")

print("\n" + "=" * 60)
print("車手代碼列表（用於 CLI 命令）:")
print("=" * 60)
driver_codes = sorted(drivers.keys())
print(", ".join(driver_codes))

print("\n" + "=" * 60)
print("使用範例:")
print("=" * 60)
print("# 比較兩位車手的遙測數據")
print(f"python f1_analysis_modular_main.py -f 13 -y 2025 -r Singapore -s R -d {driver_codes[0]} -d2 {driver_codes[1]}")
