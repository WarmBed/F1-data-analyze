"""檢查實際數據欄位"""
import json
from pathlib import Path

f = list(Path('json/predictionJSON').glob('fp_q_data_2025_7_*.json'))[0]
with open(f, 'r', encoding='utf-8') as file:
    data = json.load(file)

drivers = data['drivers']
print(f"drivers 類型: {type(drivers)}")
print(f"長度: {len(drivers)}")

if isinstance(drivers, list):
    first_driver = drivers[0]
    print(f"\n第一個車手類型: {type(first_driver)}")
    
    if isinstance(first_driver, dict):
        print(f"\n欄位 ({len(first_driver.keys())} 個):")
        for i, key in enumerate(sorted(first_driver.keys()), 1):
            value = first_driver[key]
            print(f"  {i:2d}. {key:40s}: {type(value).__name__:10s} = {str(value)[:50]}")
