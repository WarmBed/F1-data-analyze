import json
from pathlib import Path
from datetime import datetime, timezone

# 讀取 Season Calendar
files = sorted(Path('json').glob('season_calendar_multi_year*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
data = json.loads(files[0].read_text(encoding='utf-8'))

events_2025 = data['data']['2025']

print(f"2025 總賽事數: {len(events_2025)}")

completed = [e for e in events_2025 if e.get('is_completed')]
print(f"已完成賽事: {len(completed)}")

if completed:
    latest = completed[-1]
    print(f"\n最後一場已完成賽事:")
    print(f"  - 名稱: {latest['event_name']}")
    print(f"  - Round: {latest['round']}")
    print(f"  - is_completed: {latest['is_completed']}")
    print(f"  - race_date_utc: {latest['race_date_utc']}")
    
    race_date = datetime.fromisoformat(latest['race_date_utc'].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    hours_since = (now - race_date).total_seconds() / 3600
    print(f"  - 賽後經過: {hours_since:.1f} 小時")
else:
    print("\n❌ 沒有已完成的賽事！")
    print("\n檢查 Las Vegas:")
    vegas = [e for e in events_2025 if e.get('location') == 'Las Vegas']
    if vegas:
        v = vegas[0]
        print(f"  - 名稱: {v['event_name']}")
        print(f"  - is_completed: {v['is_completed']}")  # <<< 這裡是問題！
        print(f"  - race_date_utc: {v['race_date_utc']}")
