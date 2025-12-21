"""驗證 Brazil 2022-2025 JSON 是否包含所有年份的 position_changes"""
import json

data = json.load(open('json/historical_flags_Brazil_2022-2025.json', encoding='utf-8'))
yearly = data.get('data', {}).get('yearly_summary', {})

print('=== yearly_summary 所有年份的 position_changes ===')
for year in ['2022', '2023', '2024', '2025']:
    if year in yearly:
        changes = yearly[year].get('position_changes', 'KEY_NOT_FOUND')
        print(f'{year}: {changes} 次名次變更')
    else:
        print(f'{year}: 年份不存在')
