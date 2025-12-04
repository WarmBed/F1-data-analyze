"""
診斷資料對齊問題
檢查為什麼 GUI 顯示 N/A
"""
import sys
import json
import base64
import zlib
import requests

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def load_stream(year, meeting, session, filename, compressed):
    """載入 jsonStream 檔案"""
    url = f"https://livetiming.formula1.com/static/{year}/{meeting}/{session}/{filename}"
    
    print(f"下載: {filename}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    text = response.content.decode('utf-8-sig')
    
    lines = [line for line in text.splitlines() if line.strip()]
    records = []
    
    for line in lines:
        if len(line) <= 12:
            continue
            
        timestamp = line[:12]
        payload_text = line[12:]
        
        try:
            if compressed:
                decoded = base64.b64decode(payload_text)
                inflated = zlib.decompress(decoded, wbits=-15)
                payload = json.loads(inflated.decode('utf-8'))
            else:
                payload = json.loads(payload_text)
            
            # 處理 SignalR 封裝
            if isinstance(payload, dict) and 'A' in payload:
                for entry in payload['A']:
                    if isinstance(entry, dict):
                        records.append({'timestamp': timestamp, 'data': entry})
            else:
                records.append({'timestamp': timestamp, 'data': payload})
                
        except Exception:
            continue
    
    print(f"  -> 載入 {len(records)} 筆記錄")
    return records

def main():
    print("=" * 70)
    print("診斷資料對齊問題")
    print("=" * 70)
    
    year = "2025"
    meeting = "2025-04-06_Japanese_Grand_Prix"
    session = "2025-04-06_Race"
    
    # 載入資料
    print("\n載入資料...")
    position_data = load_stream(year, meeting, session, "Position.z.jsonStream", True)
    timing_data = load_stream(year, meeting, session, "TimingData.jsonStream", False)
    cardata = load_stream(year, meeting, session, "CarData.z.jsonStream", True)
    
    # 分析特定時間點（圖片顯示的時間 00:27:21.556）
    target_time = "00:27:21.556"
    print(f"\n分析目標時間: {target_time}")
    print("=" * 70)
    
    # 1. 檢查 Position 資料
    print("\n[1] Position 資料:")
    position_record = None
    for rec in position_data:
        if rec['timestamp'] == target_time or abs(time_to_sec(rec['timestamp']) - time_to_sec(target_time)) < 1:
            position_record = rec
            break
    
    if position_record:
        print(f"  時間戳: {position_record['timestamp']}")
        data = position_record['data']
        position_list = data.get('Position', [])
        if position_list:
            entries = position_list[0].get('Entries', {})
            print(f"  車手數: {len(entries)}")
            # 檢查第一位車手
            if entries:
                first_driver = list(entries.keys())[0]
                driver_data = entries[first_driver]
                print(f"  範例車手 #{first_driver}:")
                print(f"    X: {driver_data.get('X')}")
                print(f"    Y: {driver_data.get('Y')}")
                print(f"    Status: {driver_data.get('Status')}")
    else:
        print("  [!] 找不到對應的 Position 記錄")
    
    # 2. 檢查 Timing 資料
    print("\n[2] Timing 資料:")
    timing_record = None
    for rec in timing_data:
        if abs(time_to_sec(rec['timestamp']) - time_to_sec(target_time)) < 1:
            timing_record = rec
            break
    
    if timing_record:
        print(f"  時間戳: {timing_record['timestamp']}")
        data = timing_record['data']
        lines = data.get('Lines', {})
        print(f"  車手數: {len(lines)}")
        # 檢查第一位車手
        if lines:
            first_driver = list(lines.keys())[0]
            driver_data = lines[first_driver]
            print(f"  範例車手 #{first_driver}:")
            print(f"    圈數: {driver_data.get('NumberOfLaps')}")
            print(f"    排名: {driver_data.get('Position')}")
            print(f"    與領先差距: {driver_data.get('GapToLeader')}")
            print(f"    與前車: {driver_data.get('IntervalToPositionAhead')}")
    else:
        print("  [!] 找不到對應的 Timing 記錄")
    
    # 3. 檢查 CarData
    print("\n[3] CarData 資料:")
    cardata_record = None
    for rec in cardata:
        if abs(time_to_sec(rec['timestamp']) - time_to_sec(target_time)) < 1:
            cardata_record = rec
            break
    
    if cardata_record:
        print(f"  時間戳: {cardata_record['timestamp']}")
        data = cardata_record['data']
        entries = data.get('Entries', [])
        print(f"  Entries 數量: {len(entries)}")
        if entries:
            cars = entries[0].get('Cars', {})
            print(f"  車手數: {len(cars)}")
            if cars:
                first_driver = list(cars.keys())[0]
                car_data = cars[first_driver]
                channels = car_data.get('Channels', {})
                print(f"  範例車手 #{first_driver}:")
                print(f"    Channels: {channels}")
                print(f"    速度 (Channel 2): {channels.get('2')}")
    else:
        print("  [!] 找不到對應的 CarData 記錄")
    
    # 4. 檢查時間戳分布
    print("\n[4] 時間戳分布分析:")
    print(f"  Position 時間範圍: {position_data[0]['timestamp']} ~ {position_data[-1]['timestamp']}")
    print(f"  Timing 時間範圍: {timing_data[0]['timestamp']} ~ {timing_data[-1]['timestamp']}")
    print(f"  CarData 時間範圍: {cardata[0]['timestamp']} ~ {cardata[-1]['timestamp']}")
    
    # 檢查前10筆 Timing 資料的結構
    print("\n[5] 前10筆 Timing 資料結構:")
    for i, rec in enumerate(timing_data[:10]):
        data = rec['data']
        lines = data.get('Lines', {})
        if lines:
            first_driver = list(lines.keys())[0]
            driver_data = lines[first_driver]
            lap = driver_data.get('NumberOfLaps')
            pos = driver_data.get('Position')
            print(f"  [{i}] {rec['timestamp']}: 車手數={len(lines)}, 範例車手 #{first_driver} 圈數={lap}, 排名={pos}")

def time_to_sec(time_str):
    """轉換時間戳為秒數"""
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0.0

if __name__ == "__main__":
    main()
