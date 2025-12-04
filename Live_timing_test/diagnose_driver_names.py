"""
診斷車手名稱問題
"""
import sys
sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource, LivePositionDataProcessor

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

print("載入資料...")
data_source.load_all_data()

# 檢查 DriverList 是否成功載入
driver_info = data_source.load_driver_list()

print(f"\n車手資訊載入: {len(driver_info)} 位車手")
print("\n前5位車手:")
for i, (num, info) in enumerate(list(driver_info.items())[:5]):
    print(f"  #{num}: {info}")

# 處理資料
processor = LivePositionDataProcessor(data_source)
processor.process_and_align_data(downsample_factor=1)

snapshots = processor.get_aligned_snapshots()

if snapshots:
    # 檢查第一個快照
    first = snapshots[len(snapshots)//2]
    print(f"\n快照時間: {first['race_time']}")
    print("\n前3位車手的資料:")
    
    sorted_drivers = sorted(
        first['drivers'].items(),
        key=lambda x: x[1].get('position', 999)
    )
    
    for num, data in sorted_drivers[:3]:
        print(f"\n車手 #{num}:")
        print(f"  driver_tla: {data.get('driver_tla', 'MISSING!')}")
        print(f"  driver_name: {data.get('driver_name', 'MISSING!')}")
        print(f"  team_name: {data.get('team_name', 'MISSING!')}")
        print(f"  team_color: {data.get('team_color', 'MISSING!')}")
