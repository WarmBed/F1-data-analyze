"""
比較 FastF1 與 Live F1 的數據更新頻率
"""
import sys
import fastf1

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')
from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource

def analyze_livef1_frequency():
    """分析 Live F1 數據更新頻率"""
    print("=" * 70)
    print("Live F1 數據更新頻率分析")
    print("=" * 70)
    
    data_source = LiveF1DataSource(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    print("\n載入資料...")
    data_source.load_all_data()
    
    position_data = data_source.get_position_data()
    timing_data = data_source.get_timing_data()
    cardata = data_source.get_cardata()
    
    # 計算時間間隔
    def calc_intervals(data, name):
        if len(data) < 2:
            return
        
        intervals = []
        for i in range(1, min(1000, len(data))):  # 只分析前1000筆
            t1 = data[i-1]['timestamp']
            t2 = data[i]['timestamp']
            
            # 轉換為秒數
            t1_sec = time_to_seconds(t1)
            t2_sec = time_to_seconds(t2)
            
            interval = t2_sec - t1_sec
            if interval > 0:
                intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            
            print(f"\n{name}:")
            print(f"  總記錄數: {len(data)}")
            print(f"  平均間隔: {avg_interval:.3f} 秒 ({1/avg_interval:.1f} Hz)")
            print(f"  最小間隔: {min_interval:.3f} 秒")
            print(f"  最大間隔: {max_interval:.3f} 秒")
    
    calc_intervals(position_data, "Position 資料")
    calc_intervals(timing_data, "Timing 資料")
    calc_intervals(cardata, "CarData 資料")

def analyze_fastf1_frequency():
    """分析 FastF1 數據更新頻率"""
    print("\n" + "=" * 70)
    print("FastF1 數據更新頻率分析")
    print("=" * 70)
    
    try:
        # 使用 2024 年的資料（因為 2025 可能還沒有）
        session = fastf1.get_session(2024, 'Japan', 'R')
        print("\n載入 FastF1 資料...")
        session.load(telemetry=True)
        
        # 取得某位車手的遙測資料
        driver = session.laps.pick_driver('VER')
        if len(driver) > 0:
            telemetry = driver.pick_lap(1).get_telemetry()
            
            if len(telemetry) > 1:
                # 計算時間間隔
                time_diffs = telemetry['Time'].diff().dt.total_seconds()
                valid_diffs = time_diffs[time_diffs > 0]
                
                if len(valid_diffs) > 0:
                    avg_interval = valid_diffs.mean()
                    min_interval = valid_diffs.min()
                    max_interval = valid_diffs.max()
                    
                    print(f"\nFastF1 遙測資料 (VER Lap 1):")
                    print(f"  總資料點數: {len(telemetry)}")
                    print(f"  平均間隔: {avg_interval:.3f} 秒 ({1/avg_interval:.1f} Hz)")
                    print(f"  最小間隔: {min_interval:.3f} 秒")
                    print(f"  最大間隔: {max_interval:.3f} 秒")
        
        # 車手位置資料
        position_data = session.laps.pick_driver('VER').get_pos_data()
        if position_data is not None and len(position_data) > 1:
            time_diffs = position_data['Time'].diff().dt.total_seconds()
            valid_diffs = time_diffs[time_diffs > 0]
            
            if len(valid_diffs) > 0:
                avg_interval = valid_diffs.mean()
                print(f"\nFastF1 位置資料 (VER):")
                print(f"  總資料點數: {len(position_data)}")
                print(f"  平均間隔: {avg_interval:.3f} 秒 ({1/avg_interval:.1f} Hz)")
                
    except Exception as e:
        print(f"\n無法載入 FastF1 資料: {e}")

def time_to_seconds(time_str):
    """轉換時間戳為秒數"""
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0.0

def main():
    print("F1 數據更新頻率比較分析\n")
    
    analyze_livef1_frequency()
    analyze_fastf1_frequency()
    
    print("\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
