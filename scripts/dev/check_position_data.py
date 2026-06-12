import pickle
from pathlib import Path
from collections import defaultdict

# Load position data
pkl_path = Path("cache/2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/position_data.ff1pkl")

with pkl_path.open("rb") as f:
    pos_data = pickle.load(f)

print(f"Type: {type(pos_data)}")
print(f"Length: {len(pos_data) if hasattr(pos_data, '__len__') else 'N/A'}")

# Check structure
if hasattr(pos_data, 'keys'):
    print(f"Keys: {list(pos_data.keys())[:10]}...")
elif hasattr(pos_data, 'columns'):
    print(f"Columns: {pos_data.columns.tolist()}")
    print(f"Shape: {pos_data.shape}")
    
    # Check VER data
    if 'Driver' in pos_data.columns:
        ver = pos_data[pos_data['Driver'] == 'VER']
        print(f"\nVER rows: {len(ver)}")
    
    # Look at first few rows
    print(f"\nFirst 5 rows:\n{pos_data.head()}")
