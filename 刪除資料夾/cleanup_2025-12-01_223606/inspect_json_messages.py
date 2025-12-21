import json

# 載入最新的 JSON
data = json.load(open('json/historical_flags_Japan_2022-2025_20251110_005919.json', 'r', encoding='utf-8'))

# 檢查 T11 2023 的所有訊息
t11_2023 = data['data']['corner_analysis']['T11']['yearly_breakdown']['2023']
all_msgs = t11_2023.get('messages', [])

print(f"T11 2023 總訊息數: {len(all_msgs)}\n")

# 顯示前 3 條訊息的完整內容
for i, msg in enumerate(all_msgs[:3], 1):
    print(f"訊息 {i}:")
    print(f"  message: {msg.get('message')}")
    print(f"  drivers: {msg.get('drivers')}")
    print(f"  reason: {msg.get('reason')}")
    print()
