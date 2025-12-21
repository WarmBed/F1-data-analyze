"""
檢查 PKL 檔案中是否包含 CarData（遙測數據）
"""
import pickle
from pathlib import Path

pkl_path = Path("data/live_timing_cache/2025/2025_Abu_Dhabi_Race.pkl")

print(f"Reading: {pkl_path}")
print(f"Size: {pkl_path.stat().st_size / 1024 / 1024:.2f} MB\n")

with open(pkl_path, 'rb') as f:
    data = pickle.load(f)

print("=" * 60)
print("PKL Top-Level Keys:")
print("=" * 60)
for key in data.keys():
    print(f"  - {key}")

print("\n" + "=" * 60)
print("Snapshots Analysis:")
print("=" * 60)
snapshots = data.get('snapshots', [])
print(f"Total snapshots: {len(snapshots)}")

if snapshots:
    print(f"\nFirst snapshot keys:")
    for key in snapshots[0].keys():
        print(f"  - {key}")
    
    # 檢查是否有 CarData
    print("\n" + "=" * 60)
    print("Checking for CarData in snapshots:")
    print("=" * 60)
    
    has_cardata = False
    cardata_count = 0
    
    for i, snapshot in enumerate(snapshots[:100]):  # 檢查前 100 個
        if 'CarData.z' in snapshot:
            has_cardata = True
            cardata_count += 1
            if cardata_count == 1:  # 顯示第一個 CarData 範例
                print(f"\n✅ Found CarData.z in snapshot {i}")
                cardata = snapshot['CarData.z']
                print(f"CarData type: {type(cardata)}")
                if isinstance(cardata, dict):
                    print(f"CarData keys: {list(cardata.keys())}")
                    
                    # 檢查 Entries
                    if 'Entries' in cardata:
                        entries = cardata['Entries']
                        print(f"\nEntries count: {len(entries)}")
                        if entries:
                            first_entry = list(entries.values())[0]
                            print(f"First entry keys: {list(first_entry.keys())}")
                            
                            # 檢查 Cars
                            if 'Cars' in first_entry:
                                cars = first_entry['Cars']
                                print(f"\nCars count: {len(cars)}")
                                if cars:
                                    first_car = list(cars.values())[0]
                                    print(f"First car keys: {list(first_car.keys())}")
                                    
                                    # 檢查遙測欄位
                                    print("\n" + "=" * 60)
                                    print("Telemetry Fields Check:")
                                    print("=" * 60)
                                    telemetry_fields = ['Speed', 'RPM', 'nGear', 'Throttle', 'Brake', 'DRS']
                                    for field in telemetry_fields:
                                        exists = field in first_car
                                        status = "✅" if exists else "❌"
                                        value = first_car.get(field, "N/A") if exists else "Not found"
                                        print(f"{status} {field:10s}: {value}")
    
    if has_cardata:
        print(f"\n✅ Total CarData entries in first 100 snapshots: {cardata_count}")
    else:
        print("\n❌ No CarData.z found in snapshots!")
        print("\nAvailable snapshot keys:")
        if snapshots:
            for key in snapshots[0].keys():
                print(f"  - {key}")

print("\n" + "=" * 60)
print("Conclusion:")
print("=" * 60)
if has_cardata:
    print("✅ PKL contains CarData with telemetry")
else:
    print("❌ PKL does NOT contain CarData!")
    print("   → Need to re-download with CarData included")
