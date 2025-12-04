"""測試 TrackStatus 資料流"""
import json
from pathlib import Path

# 1. 直接讀取原始資料
print("=== 1. 原始 JSON 資料 ===")
json_path = Path("json/LiveF1/2025/Qatar_Race/TrackStatus.json")
with open(json_path, 'r') as f:
    raw_data = json.load(f)
print(f"Records: {len(raw_data.get('records', []))}")
for rec in raw_data.get('records', []):
    print(f"  {rec['timestamp']} -> Status {rec['data']['Status']}")

# 2. 使用 LocalDataSource
print("\n=== 2. LocalLiveF1DataSource.get_track_status() ===")
from modules.gui.live_timing.core.local_source import LocalLiveF1DataSource
ds = LocalLiveF1DataSource("2025", "Qatar")
ds.load_all_data()
track_status = ds.get_track_status()
print(f"TrackStatus records: {len(track_status)}")
for rec in track_status[:5]:
    print(f"  {rec}")

# 3. 使用 Processor
print("\n=== 3. Processor.get_track_status_at_time() ===")
from modules.gui.live_timing.core.position_processor import LivePositionDataProcessor
processor = LivePositionDataProcessor(ds)

test_times = ['01:05:00.000', '01:08:00.000', '01:09:00.000', '01:12:00.000', '01:17:00.000']
for t in test_times:
    status = processor.get_track_status_at_time(t)
    print(f"  {t} -> Status {status}")
