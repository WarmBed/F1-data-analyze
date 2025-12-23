"""檢查最新的 season_calendar JSON 結構"""
import json
from pathlib import Path

# 找到最新的文件
json_dir = Path("json")
candidates = sorted(
    json_dir.glob("season_calendar_2020-2025_*.json"),
    key=lambda p: p.stat().st_mtime,
    reverse=True
)

if not candidates:
    print("❌ 找不到 season_calendar JSON 文件")
    exit(1)

latest = candidates[0]
print(f"📄 檢查文件: {latest.name}")
print(f"⏰ 生成時間: {latest.stat().st_mtime}")
print("=" * 80)

with open(latest, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n1️⃣ 頂層結構:")
print(f"   Keys: {list(data.keys())}")
print(f"   Success: {data.get('success')}")
print(f"   Message: {data.get('message')}")

print("\n2️⃣ data 字段:")
data_field = data.get('data')
print(f"   Type: {type(data_field)}")
if isinstance(data_field, dict):
    print(f"   Keys: {list(data_field.keys())}")
    
    # 檢查 2024 年數據
    if '2024' in data_field:
        year_2024 = data_field['2024']
        print(f"\n3️⃣ 2024 年數據:")
        print(f"   Type: {type(year_2024)}")
        if isinstance(year_2024, dict):
            print(f"   Keys: {list(year_2024.keys())}")
            
            # 檢查是否有 data 或 events
            if 'data' in year_2024:
                events = year_2024['data']
                print(f"\n   year_2024['data']:")
                print(f"      Type: {type(events)}")
                if isinstance(events, list):
                    print(f"      長度: {len(events)}")
                    if events:
                        print(f"      第一個事件: {list(events[0].keys())}")
                        print(f"      is_completed: {events[0].get('is_completed')}")
            
            if 'metadata' in year_2024:
                meta = year_2024['metadata']
                print(f"\n   year_2024['metadata']:")
                print(f"      total_rounds: {meta.get('total_rounds')}")
                print(f"      completed_rounds: {meta.get('completed_rounds')}")

print("\n" + "=" * 80)
print("🎯 結論:")
print("=" * 80)

# 判斷結構是否正確
if isinstance(data_field, dict) and '2024' in data_field:
    year_2024 = data_field['2024']
    if isinstance(year_2024, dict) and 'data' in year_2024:
        events = year_2024['data']
        if isinstance(events, list) and len(events) > 0:
            print("✅ JSON 結構正確: data['2024']['data'] 包含賽事列表")
            print(f"   2024 年共有 {len(events)} 場賽事")
        else:
            print("❌ JSON 結構異常: data['2024']['data'] 不是有效的列表")
    else:
        print("❌ JSON 結構異常: data['2024'] 沒有 'data' 字段")
else:
    print("❌ JSON 結構異常: data 不是字典或沒有 '2024' 鍵")
