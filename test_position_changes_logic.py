import json

# 模擬 _load_position_changes_data() 的邏輯
with open('json/historical_flags_Abu_Dhabi_2022-2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

yearly_summary = data['data']['yearly_summary']
years = ['2022', '2023', '2024', '2025']
position_changes = {}

print('=== 模擬 _load_position_changes_data() ===\n')
print(f'yearly_summary 類型: {type(yearly_summary)}')
print(f'包含的鍵: {list(yearly_summary.keys())}\n')

# 標準模式：從 yearly_summary 讀取所有年份
for year in years:
    print(f'🔍 檢查年份: {year}')
    print(f'   - {year} in yearly_summary: {year in yearly_summary}')
    
    if year in yearly_summary:
        year_data = yearly_summary[year]
        print(f'   - {year} 存在於 yearly_summary')
        print(f'   - year_data 類型: {type(year_data)}')
        print(f'   - isinstance(year_data, dict): {isinstance(year_data, dict)}')
        
        if isinstance(year_data, dict):
            print(f'   - year_data 鍵值: {list(year_data.keys())}')
            print(f'   - "position_changes" in year_data: {"position_changes" in year_data}')
            
            if 'position_changes' in year_data:
                changes = year_data['position_changes']
                print(f'   - position_changes 值: {changes} (類型: {type(changes)})')
                position_changes[year] = changes
                print(f'   ✅ {year}: {changes} 次名次變更')
            else:
                position_changes[year] = 0
                print(f'   ⚠️  {year}: yearly_summary 缺少 position_changes 欄位')
        else:
            position_changes[year] = 0
            print(f'   ⚠️  {year}: year_data 不是 dict')
    else:
        position_changes[year] = 0
        print(f'   ⚠️  {year}: yearly_summary 中找不到該年份數據')
    print()

print(f'\n📊 最終結果: {position_changes}')
