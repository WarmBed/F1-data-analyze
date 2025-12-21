import json

# 載入新檔案 (2022-2024, 應該使用 2024 年賽道佈局)
with open('json/historical_flags_Brazil_2022-2024.json', 'r', encoding='utf-8') as f:
    new_full = json.load(f)
    new_data = new_full['data']

# 載入舊檔案 (2022-2025, 使用第一個可用年份)
with open('json/historical_flags_Brazil_2022-2025.json', 'r', encoding='utf-8') as f:
    old_full = json.load(f)
    old_data = old_full['data']

print("=== Brazil Track Map Year Check ===")
print(f"\nNEW (2022-2024) - 生成時間: {new_full['timestamp']}")
print(f"  總位置點: {len(new_data['detailed_position_records'])}")
if len(new_data['detailed_position_records']) > 0:
    rec = new_data['detailed_position_records'][0]
    print(f"  第一點: X={rec['position_x']:.2f}, Y={rec['position_y']:.2f}")

print(f"\nOLD (2022-2025) - 生成時間: {old_full['timestamp']}")
print(f"  總位置點: {len(old_data['detailed_position_records'])}")
if len(old_data['detailed_position_records']) > 0:
    rec = old_data['detailed_position_records'][0]
    print(f"  第一點: X={rec['position_x']:.2f}, Y={rec['position_y']:.2f}")

# 比較前5個點
print(f"\n前5個點比較:")
for i in range(min(5, len(new_data['detailed_position_records']), len(old_data['detailed_position_records']))):
    new_p = new_data['detailed_position_records'][i]
    old_p = old_data['detailed_position_records'][i]
    match = "✅ SAME" if (new_p['position_x'] == old_p['position_x'] and new_p['position_y'] == old_p['position_y']) else "❌ DIFFERENT"
    print(f"  點 {i+1}: {match}")
    
# 結論
all_same = all(
    new_data['detailed_position_records'][i]['position_x'] == old_data['detailed_position_records'][i]['position_x'] and
    new_data['detailed_position_records'][i]['position_y'] == old_data['detailed_position_records'][i]['position_y']
    for i in range(min(len(new_data['detailed_position_records']), len(old_data['detailed_position_records'])))
)

if all_same:
    print(f"\n✅ 結論: 新舊檔案使用相同的賽道佈局（都是 2024 年）")
else:
    print(f"\n⚠️  結論: 新舊檔案使用不同的賽道佈局")
