"""
檢查時間戳範圍
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

print("載入資料...")
data_source.load_all_data()

position_data = data_source.get_position_data()
timing_data = data_source.get_timing_data()
cardata = data_source.get_cardata()

print("\n時間範圍:")
print(f"Position: {position_data[0]['timestamp']} ~ {position_data[-1]['timestamp']}")
print(f"Timing:   {timing_data[0]['timestamp']} ~ {timing_data[-1]['timestamp']}")
print(f"CarData:  {cardata[0]['timestamp']} ~ {cardata[-1]['timestamp']}")

# 檢查前10筆 Timing 資料
print("\n前10筆 Timing 資料:")
for i, rec in enumerate(timing_data[:10]):
    ts = rec['timestamp']
    data = rec['data']
    lines = data.get('Lines', {})
    if lines:
        driver_1 = lines.get('1', {})
        lap = driver_1.get('NumberOfLaps')
        print(f"  [{i}] {ts}: 圈數={lap}")
