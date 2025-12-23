import json
from pathlib import Path

# 找到 Brazil JSON
json_files = list(Path('json').glob('historical_flags_Brazil*.json'))
if json_files:
    json_file = json_files[0]
    print(f"檢查檔案: {json_file}")
    
    data = json.load(open(json_file, encoding='utf-8'))
    yearly_summary = data.get('data', {}).get('yearly_summary', {})
    
    print("\n=== 所有年份的 position_changes ===")
    for year in ['2022', '2023', '2024', '2025']:
        if year in yearly_summary:
            year_data = yearly_summary[year]
            if isinstance(year_data, dict):
                pos_changes = year_data.get('position_changes', 'NO FIELD')
                print(f"{year}: {pos_changes}")
            else:
                print(f"{year}: 數據格式錯誤 (type={type(year_data)})")
        else:
            print(f"{year}: 不存在")
else:
    print("找不到 Brazil JSON 檔案")
