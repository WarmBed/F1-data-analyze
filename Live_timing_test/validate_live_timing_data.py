"""
F1 Live Timing 資料驗證腳本
檢查項目：
1. 賽事時間範圍
2. 車速分布
3. 圈數計算
4. 與前車距離
5. 一圈約2分鐘的驗證
6. trackmap 車手位置分布
"""
import sys
import os
import json
import base64
import zlib
import requests
from typing import List, Dict, Any
from datetime import timedelta

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

class LiveF1DataValidator:
    """Live F1 資料驗證器"""
    
    def __init__(self, year: int, meeting: str, session: str):
        self.year = str(year)
        self.meeting = meeting
        self.session = session
        self.base_url = "https://livetiming.formula1.com/static"
        
        self.position_data: List[Dict] = []
        self.timing_data: List[Dict] = []
        self.cardata: List[Dict] = []
        
    def load_data(self):
        """下載並載入所有資料"""
        print("=" * 70)
        print("[驗證器] 下載 Live Timing 資料...")
        print("=" * 70)
        
        # 載入 Position 資料
        print("\n[1/3] 載入 Position 資料...")
        self.position_data = self._load_stream("Position.z.jsonStream", compressed=True)
        print(f"  -> Position 記錄: {len(self.position_data)}")
        
        # 載入 Timing 資料  
        print("\n[2/3] 載入 Timing 資料...")
        self.timing_data = self._load_stream("TimingData.jsonStream", compressed=False)
        print(f"  -> Timing 記錄: {len(self.timing_data)}")
        
        # 載入 CarData
        print("\n[3/3] 載入 CarData 資料...")
        self.cardata = self._load_stream("CarData.z.jsonStream", compressed=True)
        print(f"  -> CarData 記錄: {len(self.cardata)}")
        
        print("\n[SUCCESS] 資料載入完成！\n")
        
    def validate_race_time(self):
        """驗證1: 賽事時間範圍"""
        print("=" * 70)
        print("[驗證 1] 賽事時間範圍")
        print("=" * 70)
        
        if not self.position_data:
            print("  [ERROR] Position 資料為空")
            return
            
        timestamps = [rec['timestamp'] for rec in self.position_data]
        first_time = timestamps[0]
        last_time = timestamps[-1]
        
        first_sec = self._time_to_seconds(first_time)
        last_sec = self._time_to_seconds(last_time)
        duration_sec = last_sec - first_sec
        
        print(f"  開始時間: {first_time} ({first_sec:.2f}s)")
        print(f"  結束時間: {last_time} ({last_sec:.2f}s)")
        print(f"  總時長: {duration_sec:.2f}s ({duration_sec/60:.2f} 分鐘)")
        print(f"  資料點數: {len(timestamps)}")
        print(f"  平均間隔: {duration_sec/max(1, len(timestamps)-1):.3f}s")
        print()
        
    def validate_speed_data(self):
        """驗證2: 車速分布"""
        print("=" * 70)
        print("[驗證 2] 車速資料分析")
        print("=" * 70)
        
        if not self.cardata:
            print("  [ERROR] CarData 資料為空")
            return
            
        all_speeds = []
        driver_speeds = {}
        
        for record in self.cardata:
            data = record.get('data', {})
            entries = data.get('Entries', [])
            
            for entry in entries:
                cars = entry.get('Cars', {})
                for driver_num, car_data in cars.items():
                    channels = car_data.get('Channels', {})
                    speed = channels.get('2')  # Channel 2 = Speed
                    
                    if speed is not None and 0 < speed < 400:  # 過濾異常值
                        all_speeds.append(speed)
                        if driver_num not in driver_speeds:
                            driver_speeds[driver_num] = []
                        driver_speeds[driver_num].append(speed)
        
        if all_speeds:
            print(f"  有效速度資料點: {len(all_speeds)}")
            print(f"  最小速度: {min(all_speeds):.0f} km/h")
            print(f"  最大速度: {max(all_speeds):.0f} km/h")
            print(f"  平均速度: {sum(all_speeds)/len(all_speeds):.0f} km/h")
            
            # 分車手統計
            print(f"\n  各車手速度統計 (前5名):")
            sorted_drivers = sorted(driver_speeds.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            for driver_num, speeds in sorted_drivers:
                if speeds:
                    print(f"    車手 #{driver_num}: 資料點={len(speeds)}, "
                          f"最高={max(speeds):.0f} km/h, "
                          f"平均={sum(speeds)/len(speeds):.0f} km/h")
        else:
            print("  [WARNING] 無有效速度資料")
        print()
        
    def validate_lap_data(self):
        """驗證3: 圈數計算與單圈時間"""
        print("=" * 70)
        print("[驗證 3] 圈數與單圈時間分析")
        print("=" * 70)
        
        if not self.timing_data:
            print("  [ERROR] Timing 資料為空")
            return
            
        # 分析圈數變化
        driver_laps = {}  # driver_num -> {lap_num -> timestamp}
        lap_times = {}    # driver_num -> [lap_time_seconds]
        
        for record in self.timing_data:
            timestamp = record.get('timestamp')
            data = record.get('data', {})
            lines = data.get('Lines', {})
            
            for driver_num, driver_data in lines.items():
                lap_num = driver_data.get('NumberOfLaps')
                last_lap = driver_data.get('LastLapTime', {})
                
                if lap_num is not None:
                    if driver_num not in driver_laps:
                        driver_laps[driver_num] = {}
                    driver_laps[driver_num][lap_num] = timestamp
                    
                # 記錄單圈時間
                if isinstance(last_lap, dict):
                    lap_time_str = last_lap.get('Value')
                    if lap_time_str:
                        lap_time_sec = self._laptime_to_seconds(lap_time_str)
                        if lap_time_sec and 60 < lap_time_sec < 300:  # 1-5分鐘之間
                            if driver_num not in lap_times:
                                lap_times[driver_num] = []
                            lap_times[driver_num].append(lap_time_sec)
        
        # 統計結果
        print(f"  追蹤到的車手數: {len(driver_laps)}")
        
        # 選擇資料最完整的車手
        best_driver = None
        max_laps = 0
        for driver_num, laps in driver_laps.items():
            if len(laps) > max_laps:
                max_laps = len(laps)
                best_driver = driver_num
        
        if best_driver:
            print(f"\n  最多圈數車手: #{best_driver} ({max_laps} 圈)")
            laps = driver_laps[best_driver]
            
            # 檢查前幾圈的時間
            print(f"\n  前5圈時間戳:")
            for lap_num in sorted(laps.keys())[:5]:
                print(f"    第 {lap_num} 圈: {laps[lap_num]}")
        
        # 單圈時間統計
        if lap_times:
            all_lap_times = []
            for times in lap_times.values():
                all_lap_times.extend(times)
            
            if all_lap_times:
                avg_lap = sum(all_lap_times) / len(all_lap_times)
                min_lap = min(all_lap_times)
                max_lap = max(all_lap_times)
                
                print(f"\n  單圈時間統計:")
                print(f"    總單圈記錄: {len(all_lap_times)}")
                print(f"    平均單圈: {self._seconds_to_laptime(avg_lap)}")
                print(f"    最快單圈: {self._seconds_to_laptime(min_lap)}")
                print(f"    最慢單圈: {self._seconds_to_laptime(max_lap)}")
                print(f"\n  [驗證] 一圈約 {avg_lap/60:.2f} 分鐘 {'[✓ 符合預期]' if 1.5 < avg_lap/60 < 2.5 else '[!]注意]'}")
        
        print()
        
    def validate_gap_data(self):
        """驗證4: 與前車距離計算"""
        print("=" * 70)
        print("[驗證 4] 車手間隔分析")
        print("=" * 70)
        
        if not self.timing_data:
            print("  [ERROR] Timing 資料為空")
            return
            
        # 找一個有完整資料的時間點
        sample_record = None
        for record in self.timing_data:
            data = record.get('data', {})
            lines = data.get('Lines', {})
            if len(lines) >= 10:  # 至少10位車手的資料
                sample_record = record
                break
        
        if not sample_record:
            print("  [WARNING] 找不到完整的資料點")
            return
            
        timestamp = sample_record['timestamp']
        data = sample_record['data']
        lines = data.get('Lines', {})
        
        print(f"  分析時間點: {timestamp}")
        print(f"  車手數: {len(lines)}\n")
        
        # 按排名排序
        sorted_drivers = sorted(
            lines.items(),
            key=lambda x: int(x[1].get('Position') or 999)
        )
        
        print(f"  排名情況:")
        for driver_num, driver_data in sorted_drivers[:10]:  # 前10名
            position = driver_data.get('Position')
            gap_leader = driver_data.get('GapToLeader')
            interval = driver_data.get('IntervalToPositionAhead')
            lap = driver_data.get('NumberOfLaps')
            
            # 格式化間隔
            gap_str = self._format_gap(gap_leader) if gap_leader else "—"
            interval_str = self._format_gap(interval) if interval else "—"
            
            print(f"    P{position}: 車手 #{driver_num:2s} | "
                  f"圈數={lap or '?'} | "
                  f"與領先差距={gap_str:>10s} | "
                  f"與前車={interval_str:>10s}")
        
        print()
        
    def validate_track_positions(self):
        """驗證5: 賽道位置分布（檢查車手在 trackmap 上的分布）"""
        print("=" * 70)
        print("[驗證 5] 賽道位置分布分析")
        print("=" * 70)
        
        if not self.position_data:
            print("  [ERROR] Position 資料為空")
            return
            
        # 取樣幾個時間點來檢查
        sample_indices = [0, len(self.position_data)//4, len(self.position_data)//2, 
                         3*len(self.position_data)//4, len(self.position_data)-1]
        
        print(f"  檢查 {len(sample_indices)} 個時間點的車手位置分布:\n")
        
        for idx in sample_indices:
            if idx >= len(self.position_data):
                continue
                
            record = self.position_data[idx]
            timestamp = record['timestamp']
            data = record.get('data', {})
            
            position_list = data.get('Position')
            if not position_list or not isinstance(position_list, list):
                continue
                
            position_entry = position_list[0]
            entries = position_entry.get('Entries', {})
            
            # 統計車手位置
            positions = []
            for driver_num, driver_pos in entries.items():
                x = driver_pos.get('X')
                y = driver_pos.get('Y')
                status = driver_pos.get('Status')
                if x is not None and y is not None:
                    positions.append((driver_num, x, y, status))
            
            if positions:
                print(f"  時間 {timestamp} (進度 {idx/len(self.position_data)*100:.1f}%):")
                print(f"    車手數: {len(positions)}")
                
                # X, Y 範圍
                x_coords = [p[1] for p in positions]
                y_coords = [p[2] for p in positions]
                print(f"    X 範圍: {min(x_coords):.0f} ~ {max(x_coords):.0f}")
                print(f"    Y 範圍: {min(y_coords):.0f} ~ {max(y_coords):.0f}")
                
                # 計算車手之間的平均距離
                if len(positions) >= 2:
                    import math
                    distances = []
                    for i in range(len(positions)-1):
                        x1, y1 = positions[i][1], positions[i][2]
                        x2, y2 = positions[i+1][1], positions[i+1][2]
                        dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                        distances.append(dist)
                    
                    if distances:
                        avg_dist = sum(distances) / len(distances)
                        print(f"    車手平均間距: {avg_dist:.1f} (單位)")
                        print(f"    [驗證] 車手位置{'分散' if avg_dist > 50 else '密集'}")
                
                print()
        
    # ========== 輔助方法 ==========
    
    def _load_stream(self, filename: str, compressed: bool) -> List[Dict]:
        """載入 jsonStream 檔案"""
        url = f"{self.base_url}/{self.year}/{self.meeting}/{self.session}/{filename}"
        
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            text = response.content.decode('utf-8-sig')
        except Exception as e:
            print(f"  [ERROR] 下載失敗: {e}")
            return []
        
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
    
    def _time_to_seconds(self, time_str: str) -> float:
        """轉換時間戳為秒數"""
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except:
            return 0.0
    
    def _laptime_to_seconds(self, laptime_str: str) -> float:
        """轉換單圈時間為秒數 (格式: 1:23.456)"""
        try:
            parts = laptime_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            return float(laptime_str)
        except:
            return 0.0
    
    def _seconds_to_laptime(self, seconds: float) -> str:
        """秒數轉換為單圈時間格式"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def _format_gap(self, gap_value) -> str:
        """格式化差距顯示"""
        if gap_value is None:
            return "N/A"
        
        if isinstance(gap_value, dict):
            value = gap_value.get('Value', '')
            return str(value)
        
        return str(gap_value)

def main():
    print("=" * 70)
    print("F1 Live Timing 資料驗證工具")
    print("賽事: 2025 Japan GP Race")
    print("=" * 70)
    print()
    
    validator = LiveF1DataValidator(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    # 載入資料
    validator.load_data()
    
    # 執行各項驗證
    validator.validate_race_time()
    validator.validate_speed_data()
    validator.validate_lap_data()
    validator.validate_gap_data()
    validator.validate_track_positions()
    
    print("=" * 70)
    print("[完成] 所有驗證項目已完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
