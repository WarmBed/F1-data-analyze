"""檢查 2025 賽季 SC 記錄"""
import pickle
from pathlib import Path
import pandas as pd

# 搜尋所有 2025 Race 的 track_status
cache_path = Path('cache/2025')
for race_dir in cache_path.iterdir():
    if not race_dir.is_dir():
        continue
    
    race_name = race_dir.name
    for session_dir in race_dir.iterdir():
        if 'Race' in session_dir.name:
            ts_file = session_dir / 'track_status_data.ff1pkl'
            if ts_file.exists():
                with open(ts_file, 'rb') as f:
                    data = pickle.load(f)
                track_data = data.get('data', {})
                if 'Status' in track_data:
                    df = pd.DataFrame(track_data)
                    # 檢查是否有 SC (Status 4) 或 VSC (Status 6)
                    sc_vsc = df[df['Status'].isin(['4', '5', '6'])]
                    if len(sc_vsc) > 0:
                        print(f'\n{race_name} - SC/VSC records:')
                        print(sc_vsc[['Time', 'Status', 'Message']].to_string())
                    else:
                        print(f'{race_name}: No SC/VSC')
