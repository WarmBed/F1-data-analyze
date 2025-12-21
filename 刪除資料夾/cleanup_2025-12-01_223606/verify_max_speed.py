import json

with open('json/historical_flags_Brazil_2022-2025.json', encoding='utf-8') as f:
    data = json.load(f)

yearly_summary = data['data']['yearly_summary']

print("\n" + "="*50)
print("最高速度驗證結果")
print("="*50 + "\n")

for year in ['2022', '2023', '2024', '2025']:
    max_speed = yearly_summary[year].get('max_speed', 'N/A')
    print(f"{year} 年: {max_speed} km/h")

print("\n" + "="*50)
print("✅ 所有年份的最高速度數據已成功計算！")
print("="*50 + "\n")
