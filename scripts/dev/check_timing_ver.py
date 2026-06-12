"""檢查 timing_app_data 中 VER 的圈數分佈"""
import pickle
from pathlib import Path

timing_path = Path("cache/2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/timing_app_data.ff1pkl")

with timing_path.open("rb") as f:
    timing_data = pickle.load(f)

data = timing_data.get("data", timing_data)

print(f"Total rows: {len(data)}", flush=True)
print(f"Unique drivers: {sorted(data['Driver'].unique())}", flush=True)

# 檢查 VER
ver_data = data[data['Driver'] == '1']
print(f"\n=== VER (Driver='1') ===", flush=True)
print(f"Total rows: {len(ver_data)}", flush=True)
print(f"Lap numbers: {sorted(ver_data['LapNumber'].unique())}", flush=True)

if len(ver_data) > 0:
    print(f"\nFirst 5 rows:", flush=True)
    print(ver_data.head().to_string(), flush=True)
    print(f"\nLast 5 rows:", flush=True)
    print(ver_data.tail().to_string(), flush=True)

# 比較其他車手
print(f"\n=== All drivers lap counts ===", flush=True)
for driver in sorted(data['Driver'].unique(), key=lambda x: int(x) if x.isdigit() else 999):
    d = data[data['Driver'] == driver]
    laps = sorted(d['LapNumber'].dropna().unique())
    if laps:
        print(f"Driver #{driver}: {len(laps)} laps (Lap {min(laps)}-{max(laps)})", flush=True)
