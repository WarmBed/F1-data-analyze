"""
檢查 DriverList 和 PIT 相關資料
"""
import sys
sys.path.insert(0, '.')

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from Live_timing_test.demo_histroy_live_position_tracking import LiveF1DataSource

data_source = LiveF1DataSource(
    year=2025,
    meeting="2025-04-06_Japanese_Grand_Prix",
    session="2025-04-06_Race"
)

print("=" * 70)
print("檢查 DriverList 和 PIT 資料")
print("=" * 70)

# 1. 檢查 DriverList
print("\n[1] 載入 DriverList.jsonStream...")
try:
    driver_list = data_source._load_stream("DriverList.jsonStream", compressed=False)
    if driver_list:
        print(f"成功載入 {len(driver_list)} 筆記錄")
        
        # 檢查第一筆資料結構
        if driver_list:
            first_record = driver_list[0]
            print(f"\n第一筆資料:")
            print(f"  時間戳: {first_record.get('timestamp')}")
            
            data = first_record.get('data', {})
            if isinstance(data, dict):
                # 顯示所有車手
                for driver_num, driver_info in list(data.items())[:3]:
                    print(f"\n  車手 #{driver_num}:")
                    for key, value in driver_info.items():
                        print(f"    {key}: {value}")
    else:
        print("❌ DriverList 載入失敗")
except Exception as e:
    print(f"❌ 錯誤: {e}")

# 2. 檢查 TimingData 中是否有 PIT 資訊
print("\n" + "=" * 70)
print("[2] 檢查 TimingData 中的 PIT 資訊...")
print("=" * 70)

data_source.load_all_data()
timing_data = data_source.get_timing_data()

print(f"\n總 Timing 記錄: {len(timing_data)}")

# 搜尋包含 PIT 相關欄位的記錄
pit_related_fields = ['InPit', 'PitOut', 'PitTime', 'Pits', 'NumberOfPitStops']
found_pit_data = False

for i, record in enumerate(timing_data):
    data = record.get('data', {})
    lines = data.get('Lines', {})
    
    for driver_num, driver_data in lines.items():
        for field in pit_related_fields:
            if field in driver_data:
                if not found_pit_data:
                    print(f"\n✅ 找到 PIT 相關資料!")
                    found_pit_data = True
                
                timestamp = record.get('timestamp')
                value = driver_data.get(field)
                print(f"  [{i}] {timestamp} - 車手 #{driver_num}: {field} = {value}")
                
                # 只顯示前10個
                if i > 100:
                    break
        
        if i > 100 and found_pit_data:
            break
    
    if i > 100 and found_pit_data:
        break

if not found_pit_data:
    print("\n❌ 未找到 PIT 相關資料")
    print("\n可能的原因:")
    print("  1. Live F1 API 不提供 PIT 資訊")
    print("  2. PIT 資訊在其他 Stream 中（例如 TrackStatus.jsonStream）")
    print("  3. 需要檢查其他欄位名稱")

# 3. 列出可用的所有 Stream
print("\n" + "=" * 70)
print("[3] 可用的 Stream 檔案")
print("=" * 70)

common_streams = [
    "Position.z.jsonStream",
    "CarData.z.jsonStream", 
    "TimingData.jsonStream",
    "DriverList.jsonStream",
    "TrackStatus.jsonStream",
    "SessionInfo.jsonStream",
    "TimingStats.jsonStream",
    "LapCount.jsonStream"
]

print("\n嘗試載入各種 Stream:")
for stream_name in common_streams:
    try:
        compressed = stream_name.endswith('.z.jsonStream')
        data = data_source._load_stream(stream_name, compressed=compressed)
        if data:
            print(f"  ✅ {stream_name}: {len(data)} 筆記錄")
        else:
            print(f"  ❌ {stream_name}: 載入失敗")
    except Exception as e:
        print(f"  ❌ {stream_name}: {e}")
