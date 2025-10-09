import json

# 載入 JSON 檔案
with open('json/season_calendar_2020-2025_20251006T162216Z.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)

print("=" * 60)
print("第一層結構分析")
print("=" * 60)
print(f"Top-level keys: {list(payload.keys())}")
print(f"\nTop-level 'data' type: {type(payload.get('data'))}")

if 'data' in payload:
    first_data = payload['data']
    print(f"\n第二層 (payload['data']) keys: {list(first_data.keys())}")
    
    if 'data' in first_data:
        second_data = first_data['data']
        print(f"\n第三層 (payload['data']['data']) type: {type(second_data)}")
        print(f"第三層 keys (前10個): {list(second_data.keys())[:10]}")
        
        # 檢查是否有年份鍵
        year_keys = [k for k in second_data.keys() if str(k).isdigit() and len(str(k)) == 4]
        print(f"\n✅ 找到年份鍵: {year_keys}")
        
        if '2024' in second_data:
            print(f"\n2024 資料類型: {type(second_data['2024'])}")
            if isinstance(second_data['2024'], list):
                print(f"2024 事件數量: {len(second_data['2024'])}")
    else:
        print("\n⚠️  payload['data'] 中沒有 'data' 鍵")
        # 檢查是否直接就是年份
        year_keys = [k for k in first_data.keys() if str(k).isdigit() and len(str(k)) == 4]
        if year_keys:
            print(f"✅ payload['data'] 直接包含年份: {year_keys}")
