"""檢查最新的 Brazil JSON 是否包含 position_changes"""
import json
from pathlib import Path

# 查找最新的 Brazil JSON
json_dir = Path('json')
files = sorted(
    json_dir.glob('historical_flags_analysis*Brazil*2025*'),
    key=lambda x: x.stat().st_mtime,
    reverse=True
)

if not files:
    print("找不到 Brazil 2025 的 JSON 檔案")
    exit(1)

latest = files[0]
print(f"最新檔案: {latest.name}")
print(f"修改時間: {latest.stat().st_mtime}")

# 讀取數據
with open(latest, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取 yearly_summary
yearly_summary = data.get('data', {}).get('yearly_summary', {})

print("\n=== yearly_summary 所有年份 ===")
for year in ['2022', '2023', '2024', '2025']:
    if year in yearly_summary:
        year_data = yearly_summary[year]
        position_changes = year_data.get('position_changes', 'KEY_NOT_FOUND')
        print(f"{year}: position_changes = {position_changes}")
    else:
        print(f"{year}: 年份不存在")

print("\n=== 2025 完整數據 ===")
if '2025' in yearly_summary:
    print(json.dumps(yearly_summary['2025'], indent=2, ensure_ascii=False))
else:
    print("2025 年份不存在！")
