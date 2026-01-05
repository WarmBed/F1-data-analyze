"""檢查 historical_flags JSON 檔案的 source 狀態"""
import json
import os

json_dir = "json"
files = [f for f in os.listdir(json_dir) if f.startswith('historical_flags_') and f.endswith('.json')]
print(f"總 historical_flags JSON 檔案數: {len(files)}")

source_counts = {}

for f in files:
    filepath = os.path.join(json_dir, f)
    with open(filepath, 'r', encoding='utf-8') as fp:
        data = json.load(fp)
    
    # 檢查各年份的 source
    pos_by_year = data.get('position_changes_by_year', {})
    for year in ['2022', '2023', '2024', '2025']:
        src = pos_by_year.get(year, {}).get('source', 'N/A')
        key = f"{year}:{src}"
        source_counts[key] = source_counts.get(key, 0) + 1

print("\n各年份 source 統計:")
for key in sorted(source_counts.keys()):
    print(f"  {key}: {source_counts[key]} 個檔案")
