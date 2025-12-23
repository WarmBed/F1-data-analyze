import sys
import json

sys.path.insert(0, '.')

from modules.gui.race_analysis.track_map.historical_track_map_data_loader import HistoricalTrackMapDataLoader

# 讀取 JSON 檔案
with open('json/historical_flags_Abu_Dhabi_2022-2025.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# 提取 API data
api_data = raw_data.get('data', {})

# 創建 loader 並處理數據
loader = HistoricalTrackMapDataLoader()
processed = loader.process_loaded_data(api_data)

# 檢查處理後的 yearly_summary
yearly = processed.get('yearly_summary', {})
print('=== 處理後的 yearly_summary ===')
print(f'包含的年份: {sorted(yearly.keys())}')

print('\n=== 各年份數據 ===')
for year in sorted(yearly.keys()):
    year_data = yearly[year]
    print(f'\n{year}:')
    print(f'  yellow_flags: {year_data.get("yellow_flags")}')
    print(f'  green_flags: {year_data.get("green_flags")}')
    print(f'  total_laps: {year_data.get("total_laps")}')
    print(f'  position_changes: {year_data.get("position_changes")}')
