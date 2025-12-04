"""
調查 Live F1 輪胎資料結構

目標：
1. 分析 TimingAppData 中的 Stints 欄位
2. 分析 TimingData 中的 InPit / PitOut / NumberOfPitStops 欄位
3. 搞清楚如何正確判斷進站圈數和更換的輪胎
"""

import json
import requests


def main():
    base_url = 'https://livetiming.formula1.com/static'
    year = '2025'
    meeting = '2025-04-06_Japanese_Grand_Prix'
    session = '2025-04-06_Race'

    print("=" * 80)
    print("【調查 1】TimingAppData - Stints（輪胎策略）資料")
    print("=" * 80)
    
    url = f'{base_url}/{year}/{meeting}/{session}/TimingAppData.jsonStream'
    print(f'正在下載: {url}\n')

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip()]
    print(f'總共 {len(lines)} 行記錄\n')

    # 分析 Stints 結構
    stint_updates = {}  # driver -> list of (timestamp, stints_data)
    
    for line in lines:
        if len(line) <= 12:
            continue
        timestamp = line[:12]
        payload_text = line[12:]
        
        try:
            data = json.loads(payload_text)
        except:
            continue
        
        lines_data = data.get('Lines', {})
        if not isinstance(lines_data, dict):
            continue
        
        for driver_num, driver_data in lines_data.items():
            if not isinstance(driver_data, dict):
                continue
            
            stints = driver_data.get('Stints')
            if stints:
                if driver_num not in stint_updates:
                    stint_updates[driver_num] = []
                stint_updates[driver_num].append({
                    'ts': timestamp,
                    'stints': stints
                })

    print(f'有 Stints 更新的車手: {len(stint_updates)} 位\n')

    # 特別關注：找出何時出現第二個 stint（換胎）
    print("=" * 80)
    print("【重點】尋找第二個 Stint（換胎後的輪胎）")
    print("=" * 80)
    
    for driver_num in sorted(stint_updates.keys()):
        updates = stint_updates[driver_num]
        
        # 找出第一次出現 stint index "1" 或 列表長度 > 1 的時間點
        for update in updates:
            stints = update["stints"]
            
            # 檢查是否有第二個 stint
            has_second_stint = False
            if isinstance(stints, list) and len(stints) > 1:
                has_second_stint = True
            elif isinstance(stints, dict) and "1" in stints:
                has_second_stint = True
            
            if has_second_stint:
                print(f'車手 {driver_num}: 第二個 stint 出現於 {update["ts"]}')
                print(f'  資料: {json.dumps(stints, ensure_ascii=False)}')
                break
        else:
            # 沒找到第二個 stint，顯示最後的資料
            if updates:
                last = updates[-1]
                print(f'車手 {driver_num}: ⚠️ 沒有第二個 stint（僅一次換胎）')
                print(f'  最後資料: {json.dumps(last["stints"], ensure_ascii=False)}')
        print()

    print("\n" + "=" * 80)
    print("【調查 2】TimingData - InPit / PitOut / NumberOfPitStops")
    print("=" * 80)
    
    url2 = f'{base_url}/{year}/{meeting}/{session}/TimingData.jsonStream'
    print(f'正在下載: {url2}\n')

    response2 = requests.get(url2, timeout=60)
    response2.raise_for_status()
    content2 = response2.content.decode('utf-8-sig')
    lines2 = [l for l in content2.splitlines() if l.strip()]
    print(f'總共 {len(lines2)} 行記錄\n')

    # 分析 PIT 相關欄位
    pit_events = {}  # driver -> list of (timestamp, field, value)
    driver_laps = {}  # driver -> current lap number

    for line in lines2:
        if len(line) <= 12:
            continue
        timestamp = line[:12]
        payload_text = line[12:]
        
        try:
            data = json.loads(payload_text)
        except:
            continue
        
        lines_data = data.get('Lines', {})
        if not isinstance(lines_data, dict):
            continue
        
        for driver_num, driver_data in lines_data.items():
            if not isinstance(driver_data, dict):
                continue
            
            # 追蹤圈數
            if 'NumberOfLaps' in driver_data:
                driver_laps[driver_num] = driver_data['NumberOfLaps']
            
            current_lap = driver_laps.get(driver_num, 0)
            
            # 記錄 PIT 相關事件
            for field in ['InPit', 'PitOut', 'NumberOfPitStops']:
                if field in driver_data:
                    if driver_num not in pit_events:
                        pit_events[driver_num] = []
                    pit_events[driver_num].append({
                        'ts': timestamp,
                        'field': field,
                        'value': driver_data[field],
                        'lap': current_lap
                    })

    print(f'有 PIT 相關事件的車手: {len(pit_events)} 位\n')

    # 顯示每位車手的 PIT 事件
    for driver_num in sorted(pit_events.keys()):
        events = pit_events[driver_num]
        print(f'車手 {driver_num}: {len(events)} 次 PIT 相關事件')
        
        # 顯示重要事件（InPit=True 或 NumberOfPitStops 變化）
        important_events = []
        last_pit_count = 0
        for event in events:
            if event['field'] == 'InPit' and event['value'] == True:
                important_events.append(f"  → 進站 @ 圈數 {event['lap']} (ts: {event['ts']})")
            elif event['field'] == 'InPit' and event['value'] == False and event['lap'] > 0:
                important_events.append(f"  ← 出站 @ 圈數 {event['lap']} (ts: {event['ts']})")
            elif event['field'] == 'NumberOfPitStops':
                if event['value'] != last_pit_count:
                    important_events.append(f"  🔢 進站次數變成 {event['value']} @ 圈數 {event['lap']} (ts: {event['ts']})")
                    last_pit_count = event['value']
        
        for ie in important_events:
            print(ie)
        print()


if __name__ == '__main__':
    main()
