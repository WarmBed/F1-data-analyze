import json

# 載入舊檔案 (2022-2024)
with open('json/historical_flags_Las_Vegas_2022-2024.json', 'r', encoding='utf-8') as f:
    old_full = json.load(f)
    old_data = old_full['data']

# 載入新檔案 (2023-2024, 應該使用 2024 年賽道佈局)
with open('json/historical_flags_Las_Vegas_2023-2024.json', 'r', encoding='utf-8') as f:
    new_full = json.load(f)
    new_data = new_full['data']

old_rec = old_data['detailed_position_records'][0]
new_rec = new_data['detailed_position_records'][0]

print("=== Position Records Comparison ===")
print(f"OLD (2022-2024 生成時間: {old_full['timestamp']})")
print(f"  First point: X={old_rec['position_x']:.2f}, Y={old_rec['position_y']:.2f}")
print(f"  Total points: {len(old_data['detailed_position_records'])}")

print(f"\nNEW (2023-2024 生成時間: {new_full['timestamp']})")
print(f"  First point: X={new_rec['position_x']:.2f}, Y={new_rec['position_y']:.2f}")
print(f"  Total points: {len(new_data['detailed_position_records'])}")

print(f"\nSAME DATA: {old_rec['position_x'] == new_rec['position_x'] and old_rec['position_y'] == new_rec['position_y']}")

# 比較所有點的前10個
print(f"\nFirst 5 points comparison:")
for i in range(min(5, len(old_data['detailed_position_records']), len(new_data['detailed_position_records']))):
    old_p = old_data['detailed_position_records'][i]
    new_p = new_data['detailed_position_records'][i]
    match = "✅" if (old_p['position_x'] == new_p['position_x'] and old_p['position_y'] == new_p['position_y']) else "❌"
    print(f"  Point {i+1}: {match}  OLD({old_p['position_x']:.1f},{old_p['position_y']:.1f}) vs NEW({new_p['position_x']:.1f},{new_p['position_y']:.1f})")
