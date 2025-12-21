import json

# 載入 JSON 數據
data = json.load(open('json/historical_flags_Japan_2022-2025_20251109_172653.json', 'r', encoding='utf-8'))

print("=" * 60)
print("檢查車手事件數據結構")
print("=" * 60)

# 統計每個彎道的車手事件
driver_events_stats = {}
all_messages_with_drivers = []

for turn_key, corner_data in data['data']['corner_analysis'].items():
    # turn_key 格式為 "T1", "T2" 等
    turn_num = int(turn_key.replace('T', ''))
    events_by_year = {}
    
    for year, year_data in corner_data['yearly_breakdown'].items():
        messages = year_data.get('messages', [])
        # 只計算有車手資訊的訊息
        driver_messages = [m for m in messages if m.get('drivers') and len(m['drivers']) > 0]
        events_by_year[year] = len(driver_messages)
        
        # 收集所有有車手的訊息
        for msg in driver_messages:
            all_messages_with_drivers.append({
                'turn': turn_num,
                'year': year,
                'message': msg
            })
    
    total_events = sum(events_by_year.values())
    if total_events > 0:
        driver_events_stats[turn_key] = {
            'turn_number': turn_num,
            'by_year': events_by_year,
            'total': total_events
        }

print(f"\n總共找到 {len(all_messages_with_drivers)} 條有車手資訊的訊息")
print(f"涉及 {len(driver_events_stats)} 個彎道\n")

# 顯示結果
print(f"\n找到 {len(driver_events_stats)} 個彎道有車手事件:\n")
for turn_key in sorted(driver_events_stats.keys(), key=lambda x: driver_events_stats[x]['turn_number']):
    stats = driver_events_stats[turn_key]
    print(f"Turn {stats['turn_number']}:")
    print(f"  2022: {stats['by_year'].get('2022', 0)}")
    print(f"  2023: {stats['by_year'].get('2023', 0)}")
    print(f"  2024: {stats['by_year'].get('2024', 0)}")
    print(f"  2025: {stats['by_year'].get('2025', 0)}")
    print(f"  總計: {stats['total']}\n")

# 檢查一個有車手事件的範例
if all_messages_with_drivers:
    print("=" * 60)
    print(f"車手事件範例 (前 5 條):")
    print("=" * 60)
    
    for i, item in enumerate(all_messages_with_drivers[:5]):
        msg = item['message']
        print(f"\n{i+1}. Turn {item['turn']}, {item['year']} 年:")
        print(f"   訊息: {msg['message']}")
        print(f"   旗幟類型: {msg['flag_type']}")
        print(f"   車手:")
        for driver in msg['drivers']:
            print(f"     - 車號 {driver['car_number']}: {driver['driver_code']}")
else:
    print("\n⚠️  未找到任何有車手資訊的訊息！")
    print("嘗試搜尋關鍵字...")
    
    # 搜尋包含車手相關關鍵字的訊息
    keywords = ['SPUN', 'INVOLVING CAR', 'CAR ', 'CRASHED', 'OFF TRACK']
    keyword_messages = []
    
    for turn_key, corner_data in data['data']['corner_analysis'].items():
        turn_num = int(turn_key.replace('T', ''))
        for year, year_data in corner_data['yearly_breakdown'].items():
            messages = year_data.get('messages', [])
            for msg in messages:
                message_text = msg.get('message', '').upper()
                if any(kw in message_text for kw in keywords):
                    keyword_messages.append({
                        'turn': turn_num,
                        'year': year,
                        'message': msg
                    })
    
    print(f"\n找到 {len(keyword_messages)} 條包含關鍵字的訊息:")
    for i, item in enumerate(keyword_messages[:5]):
        msg = item['message']
        print(f"\n{i+1}. Turn {item['turn']}, {item['year']} 年:")
        print(f"   訊息: {msg['message']}")
        print(f"   旗幟類型: {msg.get('flag_type', 'N/A')}")
        print(f"   drivers 欄位: {msg.get('drivers', [])}")
