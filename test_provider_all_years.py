"""測試 SeasonCalendarProvider 的實際行為"""
import sys
sys.path.insert(0, ".")

from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

print("=" * 80)
print("[TEST] SeasonCalendarProvider.get_completed_events()")
print("=" * 80)

provider = SeasonCalendarProvider()

# 測試各個年份
test_years = [2020, 2021, 2022, 2023, 2024, 2025]

for year in test_years:
    print(f"\n[{year}] Testing year {year}:")
    print("-" * 80)
    
    try:
        events = provider.get_completed_events(year)
        print(f"   [OK] Success")
        print(f"   Events: {len(events)}")
        
        if events:
            first_event = events[0]
            print(f"   First event:")
            print(f"      - event_name: {first_event.event_name}")
            print(f"      - round: {first_event.round}")
            print(f"      - is_completed: {first_event.is_completed}")
            
            # Count completed
            completed = sum(1 for e in events if e.is_completed)
            print(f"   Completed: {completed}/{len(events)}")
        else:
            print(f"   [WARN] Empty list")
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("[SUMMARY]")
print("=" * 80)
print("\n如果所有年份都返回 0 事件,則說明 _transform_payload() 有 bug")
print("如果只有部分年份返回 0 事件,則說明 JSON 數據或年份匹配有問題")
