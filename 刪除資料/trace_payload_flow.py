"""追蹤 payload 在整個流程中的結構變化"""
import json
from pathlib import Path

# 模擬 _load_latest_json() 的行為
json_file = Path("json/season_calendar_2020-2025_20251006T162216Z.json")
payload = json.loads(json_file.read_text(encoding="utf-8"))

print("=" * 70)
print("步驟 1: _load_latest_json() 返回的 payload")
print("=" * 70)
print(f"payload keys: {list(payload.keys())}")
print(f"payload['data'] type: {type(payload.get('data'))}")

if 'data' in payload:
    data_container = payload['data']
    print(f"\npayload['data'] keys: {list(data_container.keys())[:20]}")
    
    # 檢查是否有年份
    year_keys = [k for k in data_container.keys() if str(k).isdigit() and len(str(k)) == 4]
    print(f"\n✅ 年份鍵: {year_keys}")
    
    # 檢查 2024
    if '2024' in data_container:
        print(f"\n✅ payload['data']['2024'] 存在")
        print(f"   類型: {type(data_container['2024'])}")
        if isinstance(data_container['2024'], list):
            print(f"   長度: {len(data_container['2024'])}")
            if data_container['2024']:
                print(f"   第一個事件鍵: {list(data_container['2024'][0].keys())}")

print("\n" + "=" * 70)
print("步驟 2: 模擬 _transform_payload() 的處理")
print("=" * 70)

year = 2024
year_str = str(year)

# 這是 _transform_payload() 的邏輯
data_container = payload.get("data")
print(f"\ndata_container = payload.get('data')")
print(f"data_container type: {type(data_container)}")
print(f"data_container keys: {list(data_container.keys())[:20]}")

# 檢查年份
has_year = year_str in data_container
print(f"\n'{year_str}' in data_container: {has_year}")

if has_year:
    print(f"\n✅ 找到 {year} 年數據!")
    year_data = data_container[year_str]
    print(f"   類型: {type(year_data)}")
    if isinstance(year_data, list):
        print(f"   事件數量: {len(year_data)}")
else:
    print(f"\n❌ 未找到 {year} 年數據")
    print(f"   可用鍵: {list(data_container.keys())}")
