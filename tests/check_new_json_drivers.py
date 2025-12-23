import json

# 載入最新的 JSON
data = json.load(open('json/historical_flags_Japan_2022-2025_20251110_005919.json', 'r', encoding='utf-8'))

print("=" * 60)
print("檢查新生成 JSON 的車手資訊")
print("=" * 60)

# 檢查 T11 2023（之前發現有很多車手事件）
t11_2023 = data['data']['corner_analysis']['T11']['yearly_breakdown']['2023']
msgs_with_drivers = [m for m in t11_2023.get('messages', []) if m.get('drivers')]

print(f"\nT11 2023 有 {len(msgs_with_drivers)} 條包含車手的訊息:\n")

for i, msg in enumerate(msgs_with_drivers[:5], 1):
    print(f"{i}. {msg['message']}")
    print(f"   車手: {msg['drivers']}")
    print(f"   原因: {msg['reason']}")
    print()

# 統計所有彎道的車手事件
total_driver_events = 0
turns_with_drivers = []

for turn_key, corner_data in data['data']['corner_analysis'].items():
    turn_events = 0
    for year, year_data in corner_data['yearly_breakdown'].items():
        messages = year_data.get('messages', [])
        driver_msgs = [m for m in messages if m.get('drivers')]
        turn_events += len(driver_msgs)
    
    if turn_events > 0:
        turn_num = int(turn_key.replace('T', ''))
        turns_with_drivers.append((turn_num, turn_events))
        total_driver_events += turn_events

print("=" * 60)
print(f"總計: {total_driver_events} 條車手事件，分布在 {len(turns_with_drivers)} 個彎道")
print("=" * 60)

if turns_with_drivers:
    print("\n各彎道車手事件統計:")
    for turn_num, count in sorted(turns_with_drivers):
        print(f"  Turn {turn_num}: {count} 次")
