"""檢查 Live Timing 原始緩存中 VER 的 snapshot 分佈"""
import pickle
from pathlib import Path
from collections import defaultdict

print("Loading position_data.ff1pkl...", flush=True)

pkl_path = Path("cache/2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/position_data.ff1pkl")

with pkl_path.open("rb") as f:
    pos_data = pickle.load(f)

data = pos_data.get('data', {})
print(f"All driver numbers: {sorted(data.keys(), key=lambda x: int(x) if x.isdigit() else 999)}", flush=True)

# Check VER (driver #1)
ver_data = data.get('1')
if ver_data is not None:
    print(f"\n=== VER (driver #1) ===", flush=True)
    print(f"Type: {type(ver_data)}", flush=True)
    
    if hasattr(ver_data, 'columns'):
        print(f"Columns: {ver_data.columns.tolist()}", flush=True)
        print(f"Shape: {ver_data.shape}", flush=True)
        print(f"\nFirst 5 rows:", flush=True)
        print(ver_data.head(), flush=True)
        print(f"\nLast 5 rows:", flush=True)
        print(ver_data.tail(), flush=True)
        
        # Check time range
        if 'Time' in ver_data.columns:
            print(f"\nTime range: {ver_data['Time'].min()} to {ver_data['Time'].max()}", flush=True)
    elif hasattr(ver_data, 'keys'):
        print(f"Keys: {list(ver_data.keys())[:10]}", flush=True)
    else:
        print(f"Sample: {str(ver_data)[:500]}", flush=True)
else:
    print("VER (driver #1) not found in position_data!", flush=True)

