"""
自訂 F1 Live Timing 資料提取器 (參考 LiveF1 邏輯)
目標: 提取 HAM Lap 10 的速度資料

學習目標:
1. 下載並解碼多個資料源
2. 整合 CarData + TimingData
3. 時間戳對齊
4. 圈數過濾
"""
import requests
import json
import base64
import zlib
from datetime import datetime, timedelta
from typing import List, Dict, Any

# ========== 解碼器 (參考 LiveF1) ==========

def decode_f1_packet(raw_b64_string: str) -> Dict:
    """
    解碼 F1 壓縮封包
    參考: LiveF1 的解碼邏輯
    """
    try:
        decoded_bytes = base64.b64decode(raw_b64_string)
        decompressed_bytes = zlib.decompress(decoded_bytes, wbits=-15)
        return json.loads(decompressed_bytes.decode('utf-8'))
    except Exception as e:
        return None


def parse_timestamp(ts_str: str) -> timedelta:
    """
    解析時間戳字串 'HH:MM:SS.mmm' -> timedelta
    """
    parts = ts_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


# ========== 資料下載器 (參考 LiveF1 Adapter) ==========

class F1DataDownloader:
    """F1 靜態資料下載器"""
    
    def __init__(self, year: int, meeting: str, session: str):
        self.base_url = "https://livetiming.formula1.com/static"
        self.year = year
        self.meeting = meeting
        self.session = session
        
    def _build_url(self, filename: str) -> str:
        """構建完整 URL"""
        return f"{self.base_url}/{self.year}/{self.meeting}/{self.session}/{filename}"
    
    def download_file(self, filename: str) -> bytes:
        """下載檔案"""
        url = self._build_url(filename)
        print(f"[Download] {filename}")
        print(f"  URL: {url}")
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        size_mb = len(response.content) / 1024 / 1024
        print(f"  Size: {size_mb:.2f} MB")
        return response.content
    
    def parse_jsonstream(self, content: bytes) -> List[Dict]:
        """
        解析 .jsonStream 格式
        參考: LiveF1 的 livetimingF1_getdata
        """
        text = content.decode('utf-8-sig')
        lines = text.split('\r\n')
        lines = [line for line in lines if line.strip()]
        
        records = []
        for line in lines:
            if len(line) < 12:
                continue
            
            timestamp = line[:12]
            data_str = line[12:]
            
            # 對於 .z 檔案,需要解碼
            if '.z.' in str(content[:100]):  # 簡單判斷
                decoded = decode_f1_packet(data_str)
            else:
                try:
                    decoded = json.loads(data_str)
                except:
                    continue
            
            if decoded:
                records.append({
                    'timestamp': timestamp,
                    'data': decoded
                })
        
        return records
    
    def parse_json(self, content: bytes) -> Dict:
        """解析一般 JSON"""
        text = content.decode('utf-8-sig')
        return json.loads(text)


# ========== 圈數提取器 (核心邏輯) ==========

class LapDataExtractor:
    """
    圈數資料提取器
    整合 CarData + TimingData
    """
    
    def __init__(self, downloader: F1DataDownloader):
        self.downloader = downloader
        self.car_data_records = []
        self.timing_data_records = []
        
    def load_data(self):
        """下載並解析必要資料"""
        print("\n" + "="*70)
        print("Step 1: Loading CarData.z (遙測資料)")
        print("="*70)
        
        car_content = self.downloader.download_file("CarData.z.jsonStream")
        self.car_data_records = self.downloader.parse_jsonstream(car_content)
        print(f"[OK] Loaded {len(self.car_data_records)} CarData records")
        
        print("\n" + "="*70)
        print("Step 2: Loading TimingData (圈數資訊)")
        print("="*70)
        
        timing_content = self.downloader.download_file("TimingData.jsonStream")
        self.timing_data_records = self.downloader.parse_jsonstream(timing_content)
        print(f"[OK] Loaded {len(self.timing_data_records)} TimingData records")
    
    def get_lap_times(self, driver_number: str) -> List[Dict]:
        """
        從 TimingData 提取指定車手的圈時資訊
        """
        lap_times = []
        
        for record in self.timing_data_records:
            data = record['data']
            
            # TimingData 結構: {'Lines': {'44': {...}}}
            if 'Lines' in data and driver_number in data['Lines']:
                driver_data = data['Lines'][driver_number]
                
                # 取得圈數
                lap_num = driver_data.get('NumberOfLaps')
                last_lap_time = driver_data.get('LastLapTime', {}).get('Value')
                
                if lap_num:
                    lap_times.append({
                        'timestamp': record['timestamp'],
                        'lap_number': int(lap_num),
                        'last_lap_time': last_lap_time
                    })
        
        return lap_times
    
    def extract_lap_speed(self, driver_number: str, lap_number: int) -> List[Dict]:
        """
        提取指定車手、指定圈數的速度資料
        
        核心邏輯:
        1. 從 TimingData 找到該圈的開始/結束時間
        2. 從 CarData 過濾該時間範圍內的資料
        """
        print("\n" + "="*70)
        print(f"Step 3: Extracting Driver {driver_number} Lap {lap_number}")
        print("="*70)
        
        # 1. 找到圈時資訊
        lap_times = self.get_lap_times(driver_number)
        print(f"[OK] Found {len(lap_times)} lap timing records for driver {driver_number}")
        
        # 找到 Lap N 和 Lap N+1 的時間戳
        lap_start = None
        lap_end = None
        
        for i, lap_info in enumerate(lap_times):
            if lap_info['lap_number'] == lap_number:
                lap_start = parse_timestamp(lap_info['timestamp'])
                print(f"  Lap {lap_number} starts at: {lap_info['timestamp']}")
                
                # 找下一圈的開始 = 這一圈的結束
                if i + 1 < len(lap_times):
                    lap_end = parse_timestamp(lap_times[i + 1]['timestamp'])
                    print(f"  Lap {lap_number} ends at: {lap_times[i + 1]['timestamp']}")
                break
        
        if not lap_start:
            print(f"[ERROR] Cannot find Lap {lap_number} start time")
            return []
        
        # 2. 從 CarData 過濾該時間範圍
        print(f"\n[Processing] Filtering CarData in time range...")
        print(f"  Range: {lap_start} to {lap_end if lap_end else 'end of race'}")
        speed_data = []
        in_range_count = 0
        found_driver_count = 0
        all_speeds = []
        
        for record in self.car_data_records:
            record_time = parse_timestamp(record['timestamp'])
            
            # 檢查是否在圈數範圍內
            in_range = record_time >= lap_start
            if lap_end:
                in_range = in_range and record_time < lap_end
            
            if in_range:
                in_range_count += 1
                # 提取該車手的速度
                data = record['data']
                if 'Entries' in data:
                    for entry in data['Entries']:
                        cars = entry.get('Cars', {})
                        if driver_number in cars:
                            found_driver_count += 1
                            channels = cars[driver_number].get('Channels', {})
                            speed = channels.get('0')  # Channel 0 = Speed
                            
                            if speed is not None:
                                all_speeds.append(speed)
                                # 放寬過濾 - 只過濾明顯異常值
                                if speed > 0:  # 接受所有正數速度
                                    speed_data.append({
                                        'timestamp': record['timestamp'],
                                        'time_offset': (record_time - lap_start).total_seconds(),
                                        'speed': speed
                                    })
        
        print(f"  Records in time range: {in_range_count}")
        print(f"  Driver found in: {found_driver_count} records")
        if all_speeds:
            print(f"  Speed range (raw): {min(all_speeds)} - {max(all_speeds)} km/h")
        print(f"[OK] Extracted {len(speed_data)} speed readings (including all positive values)")
        return speed_data


# ========== 主程式 ==========

def main():
    print("="*70)
    print("F1 Live Timing - Custom Lap Speed Extractor")
    print("Target: HAM (44) Lap 10 @ 2025 Japan")
    print("="*70)
    
    # 初始化下載器
    downloader = F1DataDownloader(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    # 初始化提取器
    extractor = LapDataExtractor(downloader)
    
    # 載入資料
    extractor.load_data()
    
    # 提取 HAM Lap 10
    ham_lap10_speeds = extractor.extract_lap_speed(
        driver_number='44',
        lap_number=10
    )
    
    # 顯示結果
    print("\n" + "="*70)
    print("Results: HAM Lap 10 Speed Data")
    print("="*70)
    
    if ham_lap10_speeds:
        print(f"\nTotal data points: {len(ham_lap10_speeds)}")
        print(f"Speed range: {min(s['speed'] for s in ham_lap10_speeds):.0f} - {max(s['speed'] for s in ham_lap10_speeds):.0f} km/h")
        
        print(f"\nFirst 10 readings:")
        for i, data in enumerate(ham_lap10_speeds[:10]):
            print(f"  {i+1:2d}. T+{data['time_offset']:6.2f}s | Speed: {data['speed']:3.0f} km/h | {data['timestamp']}")
        
        print(f"\n... ({len(ham_lap10_speeds) - 20} more) ...")
        
        print(f"\nLast 10 readings:")
        for i, data in enumerate(ham_lap10_speeds[-10:]):
            idx = len(ham_lap10_speeds) - 10 + i
            print(f"  {idx+1:2d}. T+{data['time_offset']:6.2f}s | Speed: {data['speed']:3.0f} km/h | {data['timestamp']}")
        
        # 與 fastf1 比較
        print(f"\n" + "="*70)
        print("Comparison with fastf1")
        print("="*70)
        print(f"  Custom extractor: {len(ham_lap10_speeds)} data points")
        print(f"  fastf1:           714 data points (from previous test)")
        print(f"  Difference:       {abs(len(ham_lap10_speeds) - 714)} points")
        
        if abs(len(ham_lap10_speeds) - 714) < 50:
            print(f"\n  [SUCCESS] Results are very close!")
        else:
            print(f"\n  [NOTE] Difference may be due to:")
            print(f"    - Different filtering criteria")
            print(f"    - Timing boundary differences")
            print(f"    - fastf1 interpolation")
    else:
        print("[ERROR] No data extracted!")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
