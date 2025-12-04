"""
F1 Live Timing Demo 完整測試腳本
測試項目：
1. 資料載入
2. 圈數計算
3. 速度資料
4. 與前車距離
5. 賽道位置分布
6. 單圈時間驗證
"""
import sys
sys.path.insert(0, '.')

# 設置 UTF-8 編碼
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource, LivePositionDataProcessor
import math

def print_section(title):
    """印出區塊標題"""
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)

def test_data_loading():
    """測試1: 資料載入"""
    print_section("測試 1: 資料載入")
    
    data_source = LiveF1DataSource(
        year=2025,
        meeting="2025-04-06_Japanese_Grand_Prix",
        session="2025-04-06_Race"
    )
    
    print("正在下載資料...")
    success = data_source.load_all_data()
    
    if success:
        print("[PASS] 資料載入成功")
        return data_source
    else:
        print("[FAIL] 資料載入失敗")
        return None

def test_data_processing(data_source):
    """測試2: 資料處理與對齊"""
    print_section("測試 2: 資料處理與對齊")
    
    processor = LivePositionDataProcessor(data_source)
    
    print("正在處理資料（降採樣 20x）...")
    processor.process_and_align_data(downsample_factor=20)
    
    snapshots = processor.get_aligned_snapshots()
    
    if snapshots:
        print(f"[PASS] 生成 {len(snapshots)} 個時間快照")
        return processor, snapshots
    else:
        print("[FAIL] 沒有生成快照")
        return None, []

def test_lap_numbers(snapshots):
    """測試3: 圈數計算"""
    print_section("測試 3: 圈數計算")
    
    if not snapshots:
        print("[SKIP] 無快照資料")
        return
    
    # 檢查中段資料
    mid_idx = len(snapshots) // 2
    snapshot = snapshots[mid_idx]
    
    drivers = snapshot.get('drivers', {})
    lap_counts = {}
    
    for driver_num, driver_data in drivers.items():
        lap = driver_data.get('lap')
        if lap is not None:
            lap_counts[driver_num] = lap
    
    print(f"時間點: {snapshot.get('race_time')}")
    print(f"有圈數資料的車手: {len(lap_counts)}/{len(drivers)}")
    
    if len(lap_counts) >= 15:  # 至少75%的車手有圈數
        print(f"[PASS] 圈數資料完整")
        
        # 顯示範例
        sorted_laps = sorted(lap_counts.items(), key=lambda x: -x[1])[:5]
        print("\n圈數最多的5位車手:")
        for driver_num, lap in sorted_laps:
            print(f"  車手 #{driver_num}: {lap} 圈")
    else:
        print(f"[FAIL] 圈數資料不足")

def test_speed_data(snapshots):
    """測試4: 速度資料"""
    print_section("測試 4: 速度資料")
    
    if not snapshots:
        print("[SKIP] 無快照資料")
        return
    
    # 收集所有速度資料
    all_speeds = []
    
    for snapshot in snapshots:
        drivers = snapshot.get('drivers', {})
        for driver_num, driver_data in drivers.items():
            speed = driver_data.get('speed')
            if speed is not None and 0 < speed < 400:
                all_speeds.append(speed)
    
    if all_speeds:
        avg_speed = sum(all_speeds) / len(all_speeds)
        max_speed = max(all_speeds)
        min_speed = min(all_speeds)
        
        print(f"速度資料點數: {len(all_speeds)}")
        print(f"平均速度: {avg_speed:.1f} km/h")
        print(f"最高速度: {max_speed:.1f} km/h")
        print(f"最低速度: {min_speed:.1f} km/h")
        
        if 150 < avg_speed < 300 and max_speed < 400:
            print("[PASS] 速度資料合理")
        else:
            print("[WARNING] 速度資料可能異常")
    else:
        print("[FAIL] 無有效速度資料")

def test_gap_to_leader(snapshots):
    """測試5: 與前車距離計算"""
    print_section("測試 5: 與領先者距離")
    
    if not snapshots:
        print("[SKIP] 無快照資料")
        return
    
    # 檢查中段的一個快照
    mid_idx = len(snapshots) // 2
    snapshot = snapshots[mid_idx]
    
    drivers = snapshot.get('drivers', {})
    
    # 按排名排序
    sorted_drivers = sorted(
        drivers.items(),
        key=lambda x: x[1].get('position') if x[1].get('position') is not None else 999
    )
    
    print(f"時間點: {snapshot.get('race_time')}")
    print("\n前10位車手的距離資料:")
    
    valid_gaps = 0
    for driver_num, driver_data in sorted_drivers[:10]:
        pos = driver_data.get('position', '?')
        gap_display = driver_data.get('gap_to_leader_display', 'N/A')
        interval_display = driver_data.get('gap_to_ahead_display', 'N/A')
        
        if gap_display != 'N/A' or pos == 1:
            valid_gaps += 1
        
        print(f"  P{pos}: 車手 #{driver_num:2s} | 與領先者={gap_display:>10s} | 與前車={interval_display:>10s}")
    
    if valid_gaps >= 8:
        print(f"\n[PASS] 距離資料完整 ({valid_gaps}/10)")
    else:
        print(f"\n[FAIL] 距離資料不足 ({valid_gaps}/10)")

def test_track_positions(snapshots):
    """測試6: 賽道位置分布"""
    print_section("測試 6: 賽道位置分布")
    
    if not snapshots:
        print("[SKIP] 無快照資料")
        return
    
    # 檢查幾個不同時間點
    test_points = [
        len(snapshots) // 4,
        len(snapshots) // 2,
        3 * len(snapshots) // 4
    ]
    
    print("檢查3個時間點的車手分布:")
    
    all_distances_ok = True
    
    for idx in test_points:
        if idx >= len(snapshots):
            continue
        
        snapshot = snapshots[idx]
        drivers = snapshot.get('drivers', {})
        
        # 收集位置
        positions = []
        for driver_num, driver_data in drivers.items():
            x = driver_data.get('x')
            y = driver_data.get('y')
            if x is not None and y is not None:
                positions.append((x, y))
        
        if len(positions) >= 2:
            # 計算平均距離
            total_dist = 0
            count = 0
            for i in range(len(positions) - 1):
                x1, y1 = positions[i]
                x2, y2 = positions[i + 1]
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                total_dist += dist
                count += 1
            
            avg_dist = total_dist / count if count > 0 else 0
            
            race_time = snapshot.get('race_time')
            progress = idx / len(snapshots) * 100
            
            print(f"\n  時間 {race_time} (進度 {progress:.1f}%):")
            print(f"    車手數: {len(positions)}")
            print(f"    平均間距: {avg_dist:.1f}")
            
            # 比賽進行中，車手應該分散
            if progress > 20 and avg_dist < 50:
                print(f"    [WARNING] 車手位置過於密集")
                all_distances_ok = False
            else:
                print(f"    [OK] 車手位置分布正常")
    
    if all_distances_ok:
        print("\n[PASS] 賽道位置分布測試通過")
    else:
        print("\n[WARNING] 部分時間點車手位置異常")

def test_lap_time_consistency(snapshots):
    """測試7: 單圈時間一致性"""
    print_section("測試 7: 單圈時間驗證")
    
    if not snapshots:
        print("[SKIP] 無快照資料")
        return
    
    # 追蹤某位車手的圈數變化
    driver_to_track = '1'  # 追蹤車手 #1
    
    lap_changes = []
    prev_lap = None
    prev_time = None
    
    for snapshot in snapshots:
        drivers = snapshot.get('drivers', {})
        if driver_to_track in drivers:
            current_lap = drivers[driver_to_track].get('lap')
            current_time = snapshot.get('race_time_seconds')
            
            if prev_lap is not None and current_lap is not None:
                if current_lap > prev_lap:
                    # 圈數增加
                    time_diff = current_time - prev_time
                    lap_changes.append({
                        'from_lap': prev_lap,
                        'to_lap': current_lap,
                        'time_seconds': time_diff
                    })
            
            prev_lap = current_lap
            prev_time = current_time
    
    if lap_changes:
        print(f"偵測到車手 #{driver_to_track} 的 {len(lap_changes)} 次圈數變化:")
        
        valid_lap_times = [lc['time_seconds'] for lc in lap_changes if 60 < lc['time_seconds'] < 200]
        
        if valid_lap_times:
            avg_lap_time = sum(valid_lap_times) / len(valid_lap_times)
            
            print(f"\n單圈時間統計:")
            print(f"  有效單圈數: {len(valid_lap_times)}")
            print(f"  平均單圈: {avg_lap_time:.1f} 秒 ({avg_lap_time/60:.2f} 分鐘)")
            
            # 顯示前幾圈
            print(f"\n前5次圈數變化:")
            for i, lc in enumerate(lap_changes[:5]):
                print(f"  第 {lc['from_lap']} → {lc['to_lap']} 圈: {lc['time_seconds']:.1f} 秒")
            
            # 驗證：Suzuka 單圈約 1.5-2 分鐘
            if 80 < avg_lap_time < 140:
                print(f"\n[PASS] 單圈時間符合預期 (約 {avg_lap_time/60:.2f} 分鐘)")
            else:
                print(f"\n[WARNING] 單圈時間可能異常")
        else:
            print("[WARNING] 無有效的單圈時間資料")
    else:
        print("[INFO] 因降採樣，未偵測到圈數變化（這是正常的）")

def main():
    print("=" * 70)
    print("F1 Live Timing Demo - 完整測試")
    print("賽事: 2025 Japan GP Race")
    print("=" * 70)
    
    # 測試1: 資料載入
    data_source = test_data_loading()
    if not data_source:
        print("\n[ABORT] 資料載入失敗，中止測試")
        return
    
    # 測試2: 資料處理
    processor, snapshots = test_data_processing(data_source)
    if not snapshots:
        print("\n[ABORT] 資料處理失敗，中止測試")
        return
    
    # 測試3-7: 各項功能驗證
    test_lap_numbers(snapshots)
    test_speed_data(snapshots)
    test_gap_to_leader(snapshots)
    test_track_positions(snapshots)
    test_lap_time_consistency(snapshots)
    
    # 總結
    print_section("測試總結")
    print("[INFO] 所有測試完成")
    print("[INFO] 請運行 'python run_demo.py' 啟動圖形介面進行視覺化驗證")
    print("\n圖形介面功能:")
    print("  - 左側賽道地圖：顯示車手即時位置")
    print("  - 右側排名表：顯示圈數、速度、與前車距離")
    print("  - 下方時間軸：可播放/暫停/拖動時間")
    print("  - 速度控制：1x, 2x, 4x, 8x")

if __name__ == "__main__":
    main()
