import json

data = json.load(open('training_data/team_fuel_habits.json', encoding='utf-8'))
teams = data['team_habits']

print('車隊數:', len(teams))
print()
print('車隊燃油校正值 (僅 Quali Sim):')
print('-'*60)

for t, v in sorted(teams.items(), key=lambda x: x[1]['fuel_correction_seconds']):
    print(f"{t:<20} {v['fuel_correction_seconds']}s  ({v['quali_sim_count']} QS樣本)")
