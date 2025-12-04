"""
找出有效資料的時間範圍
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
    
    return records

def main():
    print("尋找有效資料時間範圍")
    print("=" * 70)
    
    year = "2025"
    meeting = "2025-04-06_Japanese_Grand_Prix"
    session = "2025-04-06_Race"
    
    print("\n載入 Timing 資料...")
    timing_data = load_stream(year, meeting, session, "TimingData.jsonStream", False)
    print(f"總記錄: {len(timing_data)}")
    
    print("\n載入 CarData...")
    cardata = load_stream(year, meeting, session, "CarData.z.jsonStream", True)
    print(f"總記錄: {len(cardata)}")
    
    # 找出第一筆有圈數資料的記錄
    print("\n" + "=" * 70)
    print("尋找第一筆有效的 Timing 資料 (有圈數)...")
    print("=" * 70)
    
    for i, rec in enumerate(timing_data):
        data = rec['data']
        lines = data.get('Lines', {})
        
        for driver_num, driver_data in lines.items():
            lap = driver_data.get('NumberOfLaps')
            if lap is not None and lap > 0:
                print(f"\n[找到!] 記錄 #{i}")
                print(f"  時間戳: {rec['timestamp']}")
                print(f"  車手數: {len(lines)}")
                print(f"  車手 #{driver_num}: 圈數={lap}")
                print(f"\n完整資料:")
                for dn, dd in list(lines.items())[:5]:
                    print(f"  車手 #{dn}: 圈數={dd.get('NumberOfLaps')}, 排名={dd.get('Position')}")
                break
        else:
            continue
        break
    
    # 找出第一筆有速度資料的記錄
    print("\n" + "=" * 70)
    print("尋找第一筆有效的 CarData (速度 > 0)...")
    print("=" * 70)
    
    for i, rec in enumerate(cardata):
        data = rec['data']
        entries = data.get('Entries', [])
        
        found = False
        for entry in entries:
            cars = entry.get('Cars', {})
            for driver_num, car_data in cars.items():
                channels = car_data.get('Channels', {})
                speed = channels.get('2')
                if speed and speed > 0:
                    print(f"\n[找到!] 記錄 #{i}")
                    print(f"  時間戳: {rec['timestamp']}")
                    print(f"  車手數: {len(cars)}")
                    print(f"  車手 #{driver_num}: 速度={speed} km/h")
                    print(f"\n速度資料樣本:")
                    for dn, cd in list(cars.items())[:5]:
                        ch = cd.get('Channels', {})
                        print(f"  車手 #{dn}: 速度={ch.get('2')} km/h")
                    found = True
                    break
            if found:
                break
        if found:
            break
    
    # 檢查中段資料（約1小時處）
    print("\n" + "=" * 70)
    print("檢查中段資料 (約1小時處)...")
    print("=" * 70)
    
    mid_index = len(timing_data) // 2
    rec = timing_data[mid_index]
    print(f"\n記錄 #{mid_index}")
    print(f"  時間戳: {rec['timestamp']}")
    data = rec['data']
    lines = data.get('Lines', {})
    print(f"  車手數: {len(lines)}")
    
    if lines:
        for dn, dd in list(lines.items())[:5]:
            print(f"  車手 #{dn}: 圈數={dd.get('NumberOfLaps')}, 排名={dd.get('Position')}, "
                  f"與前車={dd.get('IntervalToPositionAhead')}")

if __name__ == "__main__":
    main()
