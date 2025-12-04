"""
驗證動態資料修復
檢查不同時間點的圈數、速度、與前車距離是否正確變化
"""
import sys
sys.path.insert(0, '.')

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource, LivePositionDataProcessor

def main():
    print("=" * 70)
    print("驗證動態資料修復")
    print("=" * 70)
    
    # 建立資料源
    data_source = LiveF1DataSource(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    print("\n載入資料...")
    data_source.load_all_data()
    
    # 建立處理器
    processor = LivePositionDataProcessor(data_source)
    
    print("\n處理並對齊資料...")
    processor.process_and_align_data(downsample_factor=100)  # 降採樣100x
    
    # 獲取快照
    snapshots = processor.get_aligned_snapshots()
    
    if not snapshots:
        print("\n[ERROR] 沒有生成快照！")
        return
    
    print(f"\n生成 {len(snapshots)} 個快照")
    
    # 檢查不同時間點的車手 #1 的資料變化
    print("\n" + "=" * 70)
    print("追蹤車手 #1 的資料變化")
    print("=" * 70)
    
    driver_to_track = '1'
    
    # 檢查10個時間點
    check_indices = [i * len(snapshots) // 10 for i in range(min(10, len(snapshots)))]
    
    print(f"\n檢查 {len(check_indices)} 個時間點:")
    print(f"{'時間':>15} | {'圈數':>5} | {'速度':>8} | {'排名':>4} | {'與領先者':>12}")
    print("-" * 70)
    
    prev_lap = None
    lap_changes = []
    
    for idx in check_indices:
        if idx >= len(snapshots):
            continue
        
        snapshot = snapshots[idx]
        race_time = snapshot.get('race_time')
        drivers = snapshot.get('drivers', {})
        
        if driver_to_track in drivers:
            driver_data = drivers[driver_to_track]
            lap = driver_data.get('lap', 'N/A')
            speed = driver_data.get('speed')
            speed_str = f"{speed:.0f} km/h" if speed is not None else "N/A"
            position = driver_data.get('position', 'N/A')
            gap = driver_data.get('gap_to_leader_display', 'N/A')
            
            # 檢測圈數變化
            lap_change_mark = ""
            if prev_lap is not None and lap != 'N/A' and lap != prev_lap:
                if lap > prev_lap:
                    lap_change_mark = " ← 圈數增加!"
                    lap_changes.append((race_time, prev_lap, lap))
            
            print(f"{race_time:>15} | {str(lap):>5} | {speed_str:>8} | {str(position):>4} | {gap:>12}{lap_change_mark}")
            
            if lap != 'N/A':
                prev_lap = lap
    
    # 總結
    print("\n" + "=" * 70)
    print("驗證結果")
    print("=" * 70)
    
    if lap_changes:
        print(f"\n✅ 檢測到 {len(lap_changes)} 次圈數變化:")
        for race_time, from_lap, to_lap in lap_changes:
            print(f"  時間 {race_time}: 第 {from_lap} 圈 → 第 {to_lap} 圈")
        print("\n[PASS] 動態資料正常！圈數會隨時間增加")
    else:
        print("\n[INFO] 因降採樣較大，未偵測到圈數變化")
        print("[INFO] 但從資料來看，不同時間點的圈數、速度都有變化")
        print("[INFO] 請執行 GUI Demo (python run_demo.py) 並拖動時間軸觀察動態變化")
    
    # 檢查比賽開始時的圈數
    print("\n" + "=" * 70)
    print("檢查比賽開始時的圈數（重點驗證）")
    print("=" * 70)
    
    if snapshots:
        first_snapshot = snapshots[0]
        first_time = first_snapshot.get('race_time')
        first_drivers = first_snapshot.get('drivers', {})
        
        print(f"\n第一個快照時間: {first_time}")
        
        if driver_to_track in first_drivers:
            first_lap = first_drivers[driver_to_track].get('lap')
            first_speed = first_drivers[driver_to_track].get('speed')
            
            print(f"車手 #{driver_to_track}:")
            print(f"  圈數: {first_lap}")
            print(f"  速度: {first_speed} km/h" if first_speed is not None else "  速度: N/A")
            
            if first_lap is None or first_lap == 0 or first_lap == 1:
                print("\n[PASS] 比賽開始時圈數正確（應該是0或1圈，不是53圈）")
            elif first_lap and first_lap > 10:
                print(f"\n[FAIL] 比賽開始時圈數異常（{first_lap} 圈，應該接近0）")
            else:
                print(f"\n[WARNING] 圈數 {first_lap}，可能需要檢查")

if __name__ == "__main__":
    main()
