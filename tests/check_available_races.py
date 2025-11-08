"""
檢查可用的比賽數據並選擇最新的一場
"""
import json
import os
from datetime import datetime

json_dir = 'json/predictionJSON'
files = [f for f in os.listdir(json_dir) if f.startswith('fp_q_data_')]

# 按檔案修改時間排序
files_with_time = []
for f in files:
    path = os.path.join(json_dir, f)
    mtime = os.path.getmtime(path)
    
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        # 新格式：metadata 中包含 year 和 race
        if 'metadata' in data:
            year = data['metadata'].get('year')
            race = data['metadata'].get('race')
        else:
            # 舊格式：直接在根級別
            year = data.get('year')
            race = data.get('race')
    
    files_with_time.append({
        'filename': f,
        'mtime': mtime,
        'year': year,
        'race': race
    })

# 排序並顯示最新的 10 場
files_with_time.sort(key=lambda x: x['mtime'], reverse=True)

print("最新的 10 場比賽數據:")
print("-" * 70)
for i, f in enumerate(files_with_time[:10], 1):
    mtime_str = datetime.fromtimestamp(f['mtime']).strftime('%Y-%m-%d %H:%M')
    year = f['year'] if f['year'] else 'N/A'
    race = f['race'] if f['race'] else 'N/A'
    print(f"{i}. {year} {race:<20} (修改時間: {mtime_str})")

# 檢查是否有 2024 或 2025 的數據
recent_races = [f for f in files_with_time if f['year'] in [2024, 2025]]
if recent_races:
    print(f"\n找到 {len(recent_races)} 場 2024-2025 賽季的比賽")
    print("使用最新的一場進行示範預測")
    latest = recent_races[0]
    print(f"\n選擇: {latest['year']} {latest['race']}")
    
    # 保存選擇的檔案名
    with open('latest_race_for_demo.txt', 'w') as f:
        f.write(latest['filename'])
