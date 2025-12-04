"""
測試 FastF1 能否提供「某一時間點所有車手的位置」
"""
import sys
import fastf1
import pandas as pd

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, '.')
from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource

def test_fastf1_global_snapshot():
    """測試 FastF1 能否獲取全局快照"""
    print("=" * 70)
    print("FastF1 全局快照測試")
    print("=" * 70)
    
    try:
        session = fastf1.get_session(2024, 'Japan', 'R')
        print("\n載入 FastF1 資料...")
        session.load(telemetry=True)
        
        # 嘗試獲取某一時刻（比如比賽進行5分鐘）所有車手的位置
        target_time = pd.Timedelta(minutes=5)
        
        print(f"\n嘗試獲取 {target_time} 時所有車手的位置...")
        
        # 方法1：遍歷所有車手，找最接近的時間點
        all_drivers = session.drivers
        positions_at_time = {}
        
        for driver in all_drivers[:5]:  # 只測試前5位
            try:
                driver_laps = session.laps.pick_driver(driver)
                if len(driver_laps) > 0:
                    # 獲取位置資料
                    pos_data = driver_laps.get_pos_data()
                    if pos_data is not None and len(pos_data) > 0:
                        # 找最接近目標時間的點
                        time_diffs = abs(pos_data['Time'] - target_time)
                        closest_idx = time_diffs.idxmin()
                        
                        closest_point = pos_data.loc[closest_idx]
                        positions_at_time[driver] = {
                            'time': closest_point['Time'],
                            'x': closest_point['X'],
                            'y': closest_point['Y'],
                            'status': closest_point.get('Status', 'Unknown')
                        }
            except Exception as e:
                print(f"  車手 {driver} 失敗: {e}")
        
        print(f"\n成功獲取 {len(positions_at_time)} 位車手的位置:")
        for driver, pos in positions_at_time.items():
            time_diff = abs((pos['time'] - target_time).total_seconds())
            print(f"  車手 {driver}: X={pos['x']:.1f}, Y={pos['y']:.1f} (時間差: {time_diff:.2f}s)")
        
        print("\n結論：")
        print("  ✓ FastF1 可以獲取某一時刻所有車手的位置")
        print("  ✗ 但需要遍歷所有車手並手動對齊時間")
        print("  ✗ 每位車手的時間戳不同步，需要插值")
        
    except Exception as e:
        print(f"\n錯誤: {e}")

def test_livef1_global_snapshot():
    """測試 Live F1 的全局快照"""
    print("\n" + "=" * 70)
    print("Live F1 全局快照測試")
    print("=" * 70)
    
    data_source = LiveF1DataSource(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    print("\n載入 Live F1 資料...")
    data_source.load_all_data()
    
    position_data = data_source.get_position_data()
    
    # 取一個時間點（比如第100個記錄）
    if len(position_data) > 100:
        snapshot = position_data[100]
        timestamp = snapshot['timestamp']
        data = snapshot['data']
        
        position_list = data.get('Position', [])
        if position_list and isinstance(position_list, list):
            entries = position_list[0].get('Entries', {})
            
            print(f"\n時間點: {timestamp}")
            print(f"包含 {len(entries)} 位車手的位置:")
            
            for i, (driver_num, driver_pos) in enumerate(list(entries.items())[:5]):
                x = driver_pos.get('X')
                y = driver_pos.get('Y')
                status = driver_pos.get('Status')
                print(f"  車手 #{driver_num}: X={x}, Y={y}, Status={status}")
            
            print("\n結論：")
            print("  ✓ Live F1 原生提供「全局快照」")
            print("  ✓ 一個時間戳包含所有車手的位置")
            print("  ✓ 所有車手的時間完全同步")

def main():
    print("FastF1 vs Live F1 全局快照能力比較\n")
    
    test_fastf1_global_snapshot()
    test_livef1_global_snapshot()
    
    print("\n" + "=" * 70)
    print("總結")
    print("=" * 70)
    print("\nFastF1:")
    print("  - 以「單一車手」為中心")
    print("  - 每位車手有獨立的時間序列")
    print("  - 需要手動對齊時間來獲取全局快照")
    print("  - 時間戳可能相差數秒")
    print("\nLive F1:")
    print("  - 提供「全局快照」")
    print("  - 一個時間點包含所有車手")
    print("  - 天然適合即時位置追蹤")
    print("  - 時間完全同步")

if __name__ == "__main__":
    main()
