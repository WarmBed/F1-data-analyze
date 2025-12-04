"""
快速驗證修復後的資料對齊邏輯
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
    print("驗證修復後的資料對齊邏輯")
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
    processor.process_and_align_data(downsample_factor=50)  # 降採樣50x加速測試
    
    # 獲取快照
    snapshots = processor.get_aligned_snapshots()
    
    if not snapshots:
        print("\n[ERROR] 沒有生成快照！")
        return
    
    print(f"\n生成 {len(snapshots)} 個快照")
    
    # 檢查幾個時間點的資料
    test_indices = [len(snapshots)//4, len(snapshots)//2, 3*len(snapshots)//4]
    
    print("\n" + "=" * 70)
    print("檢查資料品質（3個時間點）")
    print("=" * 70)
    
    for idx in test_indices:
        if idx >= len(snapshots):
            continue
            
        snapshot = snapshots[idx]
        race_time = snapshot.get('race_time')
        drivers = snapshot.get('drivers', {})
        
        print(f"\n時間: {race_time} (進度 {idx/len(snapshots)*100:.1f}%)")
        print(f"車手數: {len(drivers)}")
        
        # 統計有效資料
        counts = {
            'lap': 0,
            'speed': 0,
            'position': 0,
            'gap_to_leader': 0
        }
        
        for driver_num, driver_data in drivers.items():
            if driver_data.get('lap') is not None:
                counts['lap'] += 1
            if driver_data.get('speed') is not None:
                counts['speed'] += 1
            if driver_data.get('position') is not None:
                counts['position'] += 1
            if driver_data.get('gap_to_leader') is not None:
                counts['gap_to_leader'] += 1
        
        print(f"  有圈數: {counts['lap']}/{len(drivers)} ({counts['lap']/max(1,len(drivers))*100:.0f}%)")
        print(f"  有速度: {counts['speed']}/{len(drivers)} ({counts['speed']/max(1,len(drivers))*100:.0f}%)")
        print(f"  有排名: {counts['position']}/{len(drivers)} ({counts['position']/max(1,len(drivers))*100:.0f}%)")
        print(f"  有差距: {counts['gap_to_leader']}/{len(drivers)} ({counts['gap_to_leader']/max(1,len(drivers))*100:.0f}%)")
        
        # 顯示前3位車手的資料
        print(f"\n  前3位車手資料:")
        sorted_drivers = sorted(
            drivers.items(),
            key=lambda x: x[1].get('position') if x[1].get('position') is not None else 999
        )
        
        for driver_num, driver_data in sorted_drivers[:3]:
            lap = driver_data.get('lap', 'N/A')
            speed = driver_data.get('speed')
            speed_str = f"{speed:.0f} km/h" if speed is not None else "N/A"
            pos = driver_data.get('position', 'N/A')
            gap = driver_data.get('gap_to_leader_display', 'N/A')
            
            print(f"    P{pos}: 車手 #{driver_num:2s} | 圈數={lap} | 速度={speed_str:>10s} | 差距={gap}")
    
    print("\n" + "=" * 70)
    print("[完成] 驗證完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
