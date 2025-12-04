"""
直接從 F1 官方 API 下載卡達站即時 CarData.z 數據
"""
import requests
import base64
import zlib
import json
from datetime import datetime

def decompress_zlib_base64(data: str) -> dict:
    """解壓縮 base64 + zlib 編碼的數據"""
    try:
        decoded = base64.b64decode(data)
        decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
        return json.loads(decompressed.decode('utf-8'))
    except Exception as e:
        print(f"解壓縮失敗: {e}")
        return None

def get_session_path():
    """獲取當前 session 路徑"""
    # 先從 Index.json 獲取當前 session
    index_url = "https://livetiming.formula1.com/static/Index.json"
    try:
        resp = requests.get(index_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"當前賽事: {data}")
            return data.get('Path', '')
    except Exception as e:
        print(f"獲取 Index 失敗: {e}")
    
    # 備用: 直接使用卡達站路徑
    return "2025/2025-11-30_Qatar_Grand_Prix/2025-11-30_Race/"

def main():
    print("=" * 70)
    print("直接下載卡達站 CarData.z 即時數據")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 獲取 session 路徑
    session_path = get_session_path()
    print(f"\nSession Path: {session_path}")
    
    # 下載 CarData.z.jsonStream
    cardata_url = f"https://livetiming.formula1.com/static/{session_path}CarData.z.jsonStream"
    print(f"\n下載 URL: {cardata_url}")
    
    try:
        resp = requests.get(cardata_url, timeout=30, stream=True)
        print(f"HTTP 狀態: {resp.status_code}")
        
        if resp.status_code == 200:
            # jsonStream 格式: 每行是 JSON 記錄
            content = resp.text
            lines = content.strip().split('\n')
            print(f"總行數: {len(lines)}")
            
            # 解析最後幾筆數據 (最新的)
            print("\n" + "=" * 70)
            print("最新 10 筆 CarData.z 數據:")
            print("=" * 70)
            
            for i, line in enumerate(lines[-10:]):
                try:
                    # 每行格式可能是: 時間戳 + JSON 或直接是壓縮數據
                    # 嘗試解析
                    if line.startswith('{'):
                        # 純 JSON
                        record = json.loads(line)
                    else:
                        # 時間戳 + 壓縮數據
                        parts = line.split('\r\n', 1) if '\r\n' in line else [line]
                        if len(parts) == 1:
                            # 12位時間戳 + 數據
                            timestamp = line[:12]
                            data_part = line[12:]
                            if data_part.startswith('{'):
                                record = {'timestamp': timestamp, 'data': json.loads(data_part)}
                            else:
                                # base64 + zlib 壓縮
                                decompressed = decompress_zlib_base64(data_part)
                                record = {'timestamp': timestamp, 'data': decompressed}
                        else:
                            record = {'raw': line[:200]}
                    
                    print(f"\n--- 記錄 {len(lines) - 10 + i + 1} ---")
                    if isinstance(record, dict):
                        # 格式化輸出
                        if 'data' in record and record['data']:
                            data = record['data']
                            if 'Entries' in data:
                                for entry in data['Entries'][:1]:
                                    print(f"  Utc: {entry.get('Utc', 'N/A')}")
                                    cars = entry.get('Cars', {})
                                    for driver_no, car_data in list(cars.items())[:3]:
                                        channels = car_data.get('Channels', {})
                                        print(f"    車手 #{driver_no}:")
                                        print(f"      RPM: {channels.get('0', '-')}")
                                        print(f"      Speed: {channels.get('2', '-')}")
                                        print(f"      Gear: {channels.get('3', '-')}")
                                        print(f"      Throttle: {channels.get('4', '-')}")
                                        print(f"      Brake: {channels.get('5', '-')}")
                                        print(f"      DRS: {channels.get('45', '-')}")
                            else:
                                print(f"  {json.dumps(record, indent=2, ensure_ascii=False)[:500]}")
                        else:
                            print(f"  {json.dumps(record, indent=2, ensure_ascii=False)[:500]}")
                    else:
                        print(f"  {str(record)[:500]}")
                        
                except Exception as e:
                    print(f"  解析失敗: {e}")
                    print(f"  原始數據: {line[:200]}...")
            
            # 顯示原始格式範例
            print("\n" + "=" * 70)
            print("原始行格式範例 (前3行):")
            print("=" * 70)
            for i, line in enumerate(lines[:3]):
                print(f"\n行 {i+1} (長度 {len(line)}):")
                print(f"  前 100 字元: {line[:100]}")
                
        else:
            print(f"下載失敗: {resp.status_code}")
            print(resp.text[:500])
            
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
