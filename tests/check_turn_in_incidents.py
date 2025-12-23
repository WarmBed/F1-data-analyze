import json

# 讀取 JSON 檔案
with open('json/all_incidents_summary_2022_Japanese_Grand_Prix_RACE.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 搜索包含 TURN 的事件
turn_incidents = [inc for inc in data['data']['all_incidents'] if 'TURN' in inc['message'].upper()]

print(f"✅ 找到 {len(turn_incidents)} 個包含 TURN 的事件\n")
print("=" * 70)

for inc in turn_incidents[:10]:
    print(f"\n事件 {inc['sequence_number']}:")
    print(f"  Lap: {inc['lap']}")
    print(f"  Message: {inc['message']}")
    print(f"  Sector: {inc['sector']}")
    print(f"  Category: {inc['category']}")
    print("-" * 70)
