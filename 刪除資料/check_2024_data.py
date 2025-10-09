import json
from pathlib import Path

# 找最新的 JSON
json_files = list(Path('json').glob('season_calendar_*.json'))
if not json_files:
    print("找不到 JSON 檔案")
    exit(1)

latest = max(json_files, key=lambda p: p.stat().st_mtime)
print(f"檢查檔案: {latest.name}\n")

data = json.load(open(latest, 'r', encoding='utf-8'))

# 檢查 2024 年
events_2024 = data['data']['2024']['data']
print(f"📊 2024 年總賽事數: {len(events_2024)}")
print(f"📊 2024 已完成賽事 (metadata): {data['data']['2024']['metadata']['completed_rounds']}")

# 統計 is_completed 欄位
completed_count = sum(1 for e in events_2024 if e.get('is_completed') == True)
not_completed_count = sum(1 for e in events_2024 if e.get('is_completed') == False)
none_count = sum(1 for e in events_2024 if e.get('is_completed') is None)

print(f"\n🔍 is_completed 欄位統計:")
print(f"   is_completed = True:  {completed_count}")
print(f"   is_completed = False: {not_completed_count}")
print(f"   is_completed = None:  {none_count}")

# 顯示前 5 場賽事
print(f"\n📋 前 5 場賽事詳細:")
for i, event in enumerate(events_2024[:5], 1):
    name = event.get('event_name')
    is_comp = event.get('is_completed')
    date = event.get('race_date_local', 'N/A')
    print(f"   {i}. {name:30s} | is_completed={is_comp!s:5s} | {date}")

print(f"\n📋 最後 5 場賽事詳細:")
for i, event in enumerate(events_2024[-5:], len(events_2024)-4):
    name = event.get('event_name')
    is_comp = event.get('is_completed')
    date = event.get('race_date_local', 'N/A')
    print(f"   {i}. {name:30s} | is_completed={is_comp!s:5s} | {date}")
