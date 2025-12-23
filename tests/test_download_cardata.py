"""
測試重新下載 Abu Dhabi Race 並檢查 CarData
"""
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from modules.gui.live_timing.core.f1_api_downloader import F1APIDownloader
from core.logger import get_logger

logger = get_logger("test_download_cardata", component="gui")

def progress_callback(percent, message):
    print(f"[{percent:3d}%] {message}")

downloader = F1APIDownloader()

print("=" * 60)
print("Testing F1 API Download with CarData Check")
print("=" * 60)

year = 2025
race = "Abu Dhabi"
session = "R"

print(f"\nTarget: {year} {race} {session}")
print("\nStep 1: Check existing PKL...")
print("-" * 60)

cache_path = downloader.get_cache_path(year, race, session)
print(f"Cache path: {cache_path}")
print(f"Cache exists: {cache_path.exists()}")

if not cache_path.exists():
    print("\n❌ PKL does not exist! Please run download first.")
    sys.exit(1)

import pickle
with open(cache_path, 'rb') as f:
    data = pickle.load(f)

print("\nPKL loaded successfully")
snapshots = data.get('snapshots', [])
print(f"Total snapshots: {len(snapshots)}")

print("\n" + "=" * 60)
print("Snapshot Structure Check:")
print("=" * 60)

if not snapshots:
    print("❌ No snapshots in PKL!")
    sys.exit(1)

first_snapshot = snapshots[0]
print(f"First snapshot keys: {list(first_snapshot.keys())}")

drivers = first_snapshot.get('drivers', {})
print(f"Drivers count: {len(drivers)}")

if drivers:
    first_driver_num = list(drivers.keys())[0]
    first_driver = drivers[first_driver_num]
    print(f"\nFirst driver ({first_driver_num}) keys:")
    for key in sorted(first_driver.keys()):
        print(f"  - {key}")

print("\n" + "=" * 60)
print("Telemetry Fields Check:")
print("=" * 60)

telemetry_fields = ['speed', 'rpm', 'gear', 'throttle', 'brake', 'drs']
for field in telemetry_fields:
    has_field = field in first_driver
    status = "✅" if has_field else "❌"
    value = first_driver.get(field, "N/A") if has_field else "Not found"
    print(f"{status} {field:10s}: {value}")
print(f"CarData records: {len(cardata)}")

if cardata:
    print("\nFirst CarData record:")
    first_record = cardata[0]
    print(f"  Keys: {list(first_record.keys())}")
    
    data = first_record.get('data', {})
    if isinstance(data, dict):
        print(f"  Data keys: {list(data.keys())}")
        
        entries = data.get('Entries', [])
        if entries:
            print(f"  Entries count: {len(entries)}")
            first_entry = entries[0]
            print(f"  First entry keys: {list(first_entry.keys())}")
            
            cars = first_entry.get('Cars', {})
            if cars:
                print(f"  Cars count: {len(cars)}")
                first_car_num = list(cars.keys())[0]
                first_car = cars[first_car_num]
                print(f"  First car ({first_car_num}) keys: {list(first_car.keys())}")
                
                channels = first_car.get('Channels', {})
                if channels:
                    print(f"  Channels count: {len(channels)}")
                    print(f"  Channel keys: {list(channels.keys())[:10]}")
                    
                    # 檢查遙測欄位
                    print("\n  Telemetry Fields Check:")
                    telemetry_map = {
                        '0': 'RPM',
                        '2': 'Speed',
                        '3': 'nGear',
                        '4': 'Throttle',
                        '5': 'Brake',
                        '45': 'DRS'
                    }
                    for channel_id, field_name in telemetry_map.items():
                        value = channels.get(channel_id) or channels.get(int(channel_id))
                        status = "✅" if value is not None else "❌"
                        print(f"    {status} Channel {channel_id:3s} ({field_name:8s}): {value}")
else:
    print("❌ No CarData found!")

print("\n" + "=" * 60)
print("Conclusion:")
print("=" * 60)
if cardata and len(cardata) > 0:
    print("✅ CarData is present in raw download")
    print("   → Problem might be in processing or PKL storage")
else:
    print("❌ CarData is NOT in raw download")
    print("   → Check if CarData.z.jsonStream was downloaded")
