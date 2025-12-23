"""檢查 2025 賽道數據對應關係"""
import json
from pathlib import Path

json_dir = Path('json/predictionJSON')
files = sorted(json_dir.glob('fp_q_data_2025_*.json'))

print(f"找到 {len(files)} 個 2025 數據文件\n")

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
        metadata = data.get('metadata', {})
        
        # 提取編號
        parts = f.name.split('_')
        if len(parts) >= 4:
            num = parts[3].split('.')[0]  # 去掉 .json
            race_info = metadata.get('race', metadata.get('round', '?'))
            print(f"{num:3s}: {race_info}")
