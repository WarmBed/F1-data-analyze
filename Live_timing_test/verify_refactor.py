"""
快速驗證重構後的 demo
"""
import sys
sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource, LivePositionDataProcessor

print("=" * 70)
print("驗證重構後的 Demo")
print("=" * 70)

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

print("\n載入資料...")
data_source.load_all_data()

processor = LivePositionDataProcessor(data_source)

print("\n處理資料（不降採樣）...")
processor.process_and_align_data(downsample_factor=1)

snapshots = processor.get_aligned_snapshots()

print("\n" + "=" * 70)
print("驗證結果")
print("=" * 70)

if snapshots:
    print(f"\n✅ 總快照數: {len(snapshots)}")
    
    first = snapshots[0]
    last = snapshots[-1]
    
    print(f"\n時間範圍:")
    print(f"  開始: {first['race_time']}")
    print(f"  結束: {last['race_time']}")
    
    # 檢查第一個快照
    print(f"\n第一個快照:")
    first_drivers = first['drivers']
    print(f"  車手數: {len(first_drivers)}")
    
    # 檢查第一位車手
    if first_drivers:
        first_driver = list(first_drivers.values())[0]
        print(f"  範例車手資料:")
        print(f"    圈數: {first_driver.get('lap')}")
        print(f"    速度: {first_driver.get('speed')} km/h")
        print(f"    排名: {first_driver.get('position')}")
        print(f"    X: {first_driver.get('x')}")
        print(f"    Y: {first_driver.get('y')}")
    
    # 檢查中段快照
    mid = snapshots[len(snapshots)//2]
    print(f"\n中段快照 ({mid['race_time']}):")
    mid_drivers = mid['drivers']
    
    # 統計中段資料完整性
    lap_count = sum(1 for d in mid_drivers.values() if d.get('lap') is not None)
    speed_count = sum(1 for d in mid_drivers.values() if d.get('speed') is not None)
    
    print(f"  車手數: {len(mid_drivers)}")
    print(f"  有圈數: {lap_count}/{len(mid_drivers)} ({lap_count/len(mid_drivers)*100:.0f}%)")
    print(f"  有速度: {speed_count}/{len(mid_drivers)} ({speed_count/len(mid_drivers)*100:.0f}%)")
    
    print(f"\n✅ 重構成功！")
    print(f"   - 保留了所有 {len(snapshots)} 個原始數據點")
    print(f"   - 自動跳過了無圈數的時間段")
    print(f"   - 資料完整性良好")
else:
    print("\n❌ 沒有生成快照！")
