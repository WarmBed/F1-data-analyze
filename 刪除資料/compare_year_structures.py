"""比較 JSON 中各年份的數據結構"""
import json
from pathlib import Path

# 載入最新的 JSON
json_file = Path("json/season_calendar_2020-2025_20251006T181255Z.json")
with open(json_file, 'r', encoding='utf-8') as f:
    payload = json.load(f)

print("=" * 80)
print("🔍 深度比較各年份數據結構")
print("=" * 80)

data_container = payload.get('data')
print(f"\n1️⃣ payload['data'] 類型: {type(data_container)}")
print(f"   可用年份: {list(data_container.keys())}")

print("\n" + "=" * 80)
print("2️⃣ 逐年結構分析")
print("=" * 80)

for year in ['2020', '2021', '2022', '2023', '2024', '2025']:
    print(f"\n📅 {year} 年:")
    
    if year not in data_container:
        print(f"   ❌ {year} 不在 data_container 中")
        continue
    
    year_data = data_container[year]
    print(f"   類型: {type(year_data)}")
    
    if isinstance(year_data, dict):
        print(f"   Keys: {list(year_data.keys())}")
        
        # 檢查是否有雙層嵌套
        if 'data' in year_data:
            inner_data = year_data['data']
            print(f"   ⚠️  發現雙層嵌套! year_data['data'] 類型: {type(inner_data)}")
            if isinstance(inner_data, list):
                print(f"      事件數量: {len(inner_data)}")
                if inner_data:
                    print(f"      第一個事件 keys: {list(inner_data[0].keys())[:5]}...")
                    print(f"      is_completed: {inner_data[0].get('is_completed')}")
        
        # 檢查 metadata
        if 'metadata' in year_data:
            meta = year_data['metadata']
            print(f"   Metadata:")
            print(f"      total_rounds: {meta.get('total_rounds')}")
            print(f"      completed_rounds: {meta.get('completed_rounds')}")
            
    elif isinstance(year_data, list):
        print(f"   ✅ 直接是列表 (正確結構)")
        print(f"   事件數量: {len(year_data)}")
        if year_data:
            print(f"   第一個事件 keys: {list(year_data[0].keys())[:5]}...")

print("\n" + "=" * 80)
print("3️⃣ 模擬 SeasonCalendarProvider._transform_payload() 的處理")
print("=" * 80)

year = 2024
year_str = str(year)

print(f"\n🎯 查詢年份: {year}")
print(f"\n步驟 1: data_container = payload.get('data')")
data_container = payload.get('data')
print(f"   結果: {type(data_container)}, keys = {list(data_container.keys())}")

print(f"\n步驟 2: 檢查 '{year_str}' in data_container")
has_year = year_str in data_container
print(f"   結果: {has_year}")

if has_year:
    print(f"\n步驟 3: year_data = data_container['{year_str}']")
    year_data = data_container[year_str]
    print(f"   結果類型: {type(year_data)}")
    print(f"   結果 keys: {list(year_data.keys()) if isinstance(year_data, dict) else 'NOT DICT'}")
    
    # 這裡是問題所在!
    print(f"\n步驟 4: SeasonCalendarProvider 期待什麼?")
    print(f"   期待: year_data 是 list[event]")
    print(f"   實際: year_data 是 dict 且包含 'data' 鍵")
    
    if isinstance(year_data, dict) and 'data' in year_data:
        print(f"\n   ❌ 結構不匹配!")
        print(f"   應該訪問: data_container['{year_str}']['data']")
        print(f"   實際訪問: data_container['{year_str}']")
        
        correct_data = year_data['data']
        print(f"\n   正確數據: {type(correct_data)}, 長度 = {len(correct_data) if isinstance(correct_data, list) else 'N/A'}")

print("\n" + "=" * 80)
print("4️⃣ 測試 2025 年 (GUI 能正常讀取)")
print("=" * 80)

year_2025 = data_container.get('2025')
print(f"\n2025 年數據類型: {type(year_2025)}")
if isinstance(year_2025, dict):
    print(f"2025 年 keys: {list(year_2025.keys())}")
    if 'data' in year_2025:
        print(f"2025['data'] 類型: {type(year_2025['data'])}")
        print(f"2025['data'] 長度: {len(year_2025['data']) if isinstance(year_2025['data'], list) else 'N/A'}")
