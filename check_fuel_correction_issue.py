"""檢查 FP2→Q 預測中的燃油校正異常問題"""

import json
import fastf1
from pathlib import Path

# 啟用緩存
fastf1.Cache.enable_cache('f1_analysis_cache')

# 載入 2025 Abu Dhabi Race 數據
print("載入 2025 Abu Dhabi Race 數據...")
session = fastf1.get_session(2025, 'Abu Dhabi', 'R')
session.load()

# 建立車手→車隊映射
driver_team_map = {}
for _, row in session.results.iterrows():
    driver = row['Abbreviation']
    team = row['TeamName']
    driver_team_map[driver] = team

print("\n=== 2025 Abu Dhabi 車手車隊映射 ===")
for driver in sorted(driver_team_map.keys()):
    print(f"{driver:4} -> {driver_team_map[driver]}")

# 載入燃油校正數據
fuel_habits_file = Path("training_data/team_fuel_habits.json")
with open(fuel_habits_file, 'r', encoding='utf-8') as f:
    fuel_data = json.load(f)

team_fuel_habits = fuel_data.get('team_habits', {})

# 重點車手：VER, HUL, BOR, HAD
target_drivers = ['VER', 'HUL', 'BOR', 'HAD']

print("\n=== 燃油校正數據對比 ===")
print(f"{'車手':<6} {'車隊':<25} {'燃油校正(秒)':<15} {'樣本數':<10} {'Quali Sim數'}")
print("-" * 80)

for driver in target_drivers:
    if driver in driver_team_map:
        team = driver_team_map[driver]
        
        # 尋找對應的燃油習慣（需要處理車隊名稱差異）
        fuel_correction = None
        sample_count = None
        quali_sim_count = None
        matched_team = None
        
        # 嘗試精確匹配
        if team in team_fuel_habits:
            matched_team = team
        else:
            # 嘗試模糊匹配（處理 Haas F1 Team, Kick Sauber 等）
            for habit_team in team_fuel_habits.keys():
                if team.lower() in habit_team.lower() or habit_team.lower() in team.lower():
                    matched_team = habit_team
                    break
        
        if matched_team:
            fuel_correction = team_fuel_habits[matched_team].get('fuel_correction_seconds')
            sample_count = team_fuel_habits[matched_team].get('sample_count')
            quali_sim_count = team_fuel_habits[matched_team].get('quali_sim_count')
        
        print(f"{driver:<6} {team:<25} {fuel_correction if fuel_correction else 'N/A':<15} {sample_count if sample_count else 'N/A':<10} {quali_sim_count if quali_sim_count else 'N/A'}")
    else:
        print(f"{driver:<6} {'未找到車隊資訊':<25}")

# 顯示所有車隊的燃油校正排序
print("\n=== 所有車隊燃油校正數值排序 ===")
print(f"{'車隊':<25} {'燃油校正(秒)':<15} {'Quali Sim數':<12} {'估計燃油(kg)'}")
print("-" * 80)

# 按燃油校正數值排序
sorted_teams = sorted(
    team_fuel_habits.items(),
    key=lambda x: x[1].get('fuel_correction_seconds', 0),
    reverse=True
)

for team, data in sorted_teams:
    if data.get('has_quali_sim_data'):
        fuel_corr = data.get('fuel_correction_seconds')
        qs_count = data.get('quali_sim_count')
        fuel_kg = data.get('estimated_fp2_fuel_kg')
        print(f"{team:<25} {fuel_corr:<15.3f} {qs_count:<12} {fuel_kg:.1f}")

print("\n=== 分析結論 ===")
print("📊 燃油校正邏輯: final_predicted_time = FP2_time + model_improvement + fuel_correction")
print("⚠️  問題排查:")
print("   1. fuel_correction 應該是正值（FP2 Quali Sim 比實際 Q 快，需要加回）")
print("   2. 排序應該按 predicted_time 升序（時間越快排名越前）")
print("   3. 如果 HUL/BOR/HAD 排名異常高，可能是:")
print("      - 他們的 FP2 時間原本就很快（不太可能）")
print("      - 燃油校正數值異常低（使預測時間過快）")
print("      - 模型預測的 improvement 異常（負值過大）")
