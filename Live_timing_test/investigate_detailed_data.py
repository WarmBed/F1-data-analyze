"""
調查 Live F1 API 詳細資料結構

目標：
1. RaceControlMessages - 比賽控制訊息
2. TeamRadio - 車隊無線電 (是否有內容?)
3. TrackStatus - 賽道狀態 (是否有彎道編號?)
4. TimingStats - I1, I2, I3 扇區時間
5. PitLaneTimeCollection - 維修站時間
6. LapCount - 圈數進度
"""

import json
import requests
import base64
import zlib


def main():
    base_url = 'https://livetiming.formula1.com/static/2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race'

    # =====================================================================
    print("=" * 80)
    print("[1] RaceControlMessages - 比賽控制訊息")
    print("=" * 80)
    
    url = f'{base_url}/RaceControlMessages.jsonStream'
    response = requests.get(url, timeout=30)
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
    
    all_messages = []
    for line in lines:
        timestamp = line[:12]
        payload = line[12:]
        try:
            data = json.loads(payload)
            messages = data.get('Messages', [])
            for msg in messages:
                msg['_timestamp'] = timestamp
                all_messages.append(msg)
        except:
            pass
    
    print(f"總共 {len(all_messages)} 則訊息")
    print("\n範例訊息:")
    for msg in all_messages[:20]:
        lap = msg.get('Lap', '?')
        cat = msg.get('Category', '?')
        flag = msg.get('Flag', '')
        scope = msg.get('Scope', '')
        message = msg.get('Message', '')[:60]
        print(f"  L{lap:2} | {cat:10} | {flag:8} | {scope:8} | {message}")

    # =====================================================================
    print("\n" + "=" * 80)
    print("[2] TeamRadio - 車隊無線電")
    print("=" * 80)
    
    url = f'{base_url}/TeamRadio.jsonStream'
    response = requests.get(url, timeout=30)
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
    
    all_radios = []
    for line in lines:
        timestamp = line[:12]
        payload = line[12:]
        try:
            data = json.loads(payload)
            captures = data.get('Captures', [])
            for cap in captures:
                cap['_timestamp'] = timestamp
                all_radios.append(cap)
        except:
            pass
    
    print(f"總共 {len(all_radios)} 則無線電")
    print("\n範例無線電:")
    for radio in all_radios[:10]:
        driver = radio.get('RacingNumber', '?')
        utc = radio.get('Utc', '?')
        path = radio.get('Path', '?')
        print(f"  車手 {driver:2} | {utc} | {path}")
    
    print("\n結論: 無線電只有 MP3 檔案路徑，沒有文字內容")

    # =====================================================================
    print("\n" + "=" * 80)
    print("[3] TrackStatus - 賽道狀態 (彎道編號?)")
    print("=" * 80)
    
    url = f'{base_url}/TrackStatus.jsonStream'
    response = requests.get(url, timeout=30)
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
    
    print(f"總共 {len(lines)} 筆狀態更新")
    print("\n所有狀態:")
    for line in lines:
        timestamp = line[:12]
        payload = line[12:]
        try:
            data = json.loads(payload)
            print(f"  {timestamp} | Status={data.get('Status')} | Message={data.get('Message')}")
        except:
            pass
    
    print("\n結論: TrackStatus 只有全場狀態，沒有彎道編號")

    # =====================================================================
    print("\n" + "=" * 80)
    print("[4] TimingStats - 扇區時間 (I1, I2, I3)")
    print("=" * 80)
    
    url = f'{base_url}/TimingStats.jsonStream'
    response = requests.get(url, timeout=30)
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
    
    # 找一筆有扇區資料的記錄
    sample_data = None
    for line in lines[-100:]:  # 看後面的資料
        payload = line[12:]
        try:
            data = json.loads(payload)
            if 'Lines' in data:
                for driver, driver_data in data['Lines'].items():
                    if 'BestSectors' in driver_data or 'BestSpeeds' in driver_data:
                        sample_data = driver_data
                        print(f"\n車手 {driver} 的統計資料:")
                        print(json.dumps(driver_data, indent=2, ensure_ascii=False))
                        break
                if sample_data:
                    break
        except:
            pass
    
    if not sample_data:
        print("沒有找到扇區資料")

    # =====================================================================
    print("\n" + "=" * 80)
    print("[5] PitLaneTimeCollection - 維修站時間")
    print("=" * 80)
    
    url = f'{base_url}/PitLaneTimeCollection.jsonStream'
    response = requests.get(url, timeout=30)
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
    
    print(f"總共 {len(lines)} 筆維修站時間記錄")
    print("\n所有記錄:")
    for line in lines:
        timestamp = line[:12]
        payload = line[12:]
        try:
            data = json.loads(payload)
            pit_times = data.get('PitTimes', {})
            for driver, pit_info in pit_times.items():
                duration = pit_info.get('Duration', '?')
                lap = pit_info.get('Lap', '?')
                print(f"  {timestamp} | 車手 {driver:2} | 圈數 {lap} | 耗時 {duration}s")
        except:
            pass

    # =====================================================================
    print("\n" + "=" * 80)
    print("[6] LapCount - 圈數進度")
    print("=" * 80)
    
    url = f'{base_url}/LapCount.jsonStream'
    response = requests.get(url, timeout=30)
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
    
    print(f"總共 {len(lines)} 筆圈數記錄")
    print("\n範例 (前5筆和後5筆):")
    for line in lines[:5]:
        timestamp = line[:12]
        payload = line[12:]
        try:
            data = json.loads(payload)
            print(f"  {timestamp} | {data}")
        except:
            pass
    print("  ...")
    for line in lines[-5:]:
        timestamp = line[:12]
        payload = line[12:]
        try:
            data = json.loads(payload)
            print(f"  {timestamp} | {data}")
        except:
            pass

    # =====================================================================
    print("\n" + "=" * 80)
    print("[7] CarData.z - 車輛遙測 (Speed, RPM, Gear, Throttle, Brake, DRS)")
    print("=" * 80)
    
    url = f'{base_url}/CarData.z.jsonStream'
    response = requests.get(url, timeout=30)
    content = response.content.decode('utf-8-sig')
    lines = [l for l in content.splitlines() if l.strip() and len(l) > 12]
    
    print(f"總共 {len(lines)} 筆遙測記錄")
    
    # 解壓縮一筆資料看結構
    for line in lines[100:105]:
        timestamp = line[:12]
        payload = line[12:]
        try:
            decoded = base64.b64decode(payload)
            inflated = zlib.decompress(decoded, wbits=-15)
            data = json.loads(inflated.decode('utf-8'))
            print(f"\n{timestamp} 的資料結構:")
            
            entries = data.get('Entries', [])
            if entries:
                for entry in entries[:2]:
                    print(f"  Utc: {entry.get('Utc', '?')}")
                    cars = entry.get('Cars', {})
                    for driver, car_data in list(cars.items())[:3]:
                        channels = car_data.get('Channels', {})
                        print(f"    車手 {driver}: RPM={channels.get('0')}, Speed={channels.get('2')}, Gear={channels.get('3')}, Throttle={channels.get('4')}, Brake={channels.get('5')}, DRS={channels.get('45')}")
            break
        except Exception as e:
            print(f"  解壓失敗: {e}")


if __name__ == '__main__':
    main()
