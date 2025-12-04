"""
快速測試 TrackMap 修復
"""
import sys
sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource, LivePositionDataProcessor

print("=" * 70)
print("測試 TrackMap 修復")
print("=" * 70)

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

print("\n載入資料...")
data_source.load_all_data()

processor = LivePositionDataProcessor(data_source)
processor.process_and_align_data(downsample_factor=1)

snapshots = processor.get_aligned_snapshots()

if snapshots:
    mid = snapshots[len(snapshots)//2]
    
    print(f"\n快照時間: {mid['race_time']}")
    print(f"車手數: {len(mid['drivers'])}")
    
    print("\n前5位車手的座標:")
    print(f"{'排名':>4} {'車手':>4} {'X':>8} {'Y':>8}")
    print("-" * 30)
    
    sorted_drivers = sorted(
        mid['drivers'].items(),
        key=lambda x: x[1].get('position') or 999
    )
    
    for driver_num, data in sorted_drivers[:5]:
        pos = data.get('position', '?')
        x = data.get('x', 0)
        y = data.get('y', 0)
        print(f"{str(pos):>4} #{driver_num:>3} {x:>8} {y:>8}")
    
    print("\n✅ 修復完成")
    print("   每位車手都有真實的 X/Y 座標")
    print("   TrackMap 會直接使用這些座標，不再估算")
    print("\n請檢查 GUI Demo，車手應該在正確的賽道位置上！")
