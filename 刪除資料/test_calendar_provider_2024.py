"""測試 SeasonCalendarProvider 的 2024 年數據載入"""
import sys
sys.path.insert(0, '.')

from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

provider = SeasonCalendarProvider()

# 測試 2024 年
print("=" * 60)
print("測試 2024 年數據載入")
print("=" * 60)

try:
    events_2024 = provider.get_completed_events(2024)
    print(f"\n✅ 成功載入 2024 年數據")
    print(f"📊 總賽事數: {len(events_2024)}")
    
    completed = [e for e in events_2024 if e.is_completed]
    upcoming = [e for e in events_2024 if not e.is_completed]
    
    print(f"📊 已完成賽事: {len(completed)}")
    print(f"📊 未來賽事: {len(upcoming)}")
    
    if completed:
        print(f"\n✅ 前 5 場已完成賽事:")
        for e in completed[:5]:
            print(f"   - {e.display_label}")
    else:
        print(f"\n❌ 未找到任何已完成賽事！")
        
    if events_2024:
        print(f"\n🔍 所有賽事列表:")
        for e in events_2024:
            status = "✅" if e.is_completed else "⏳"
            print(f"   {status} {e.race_key:20s} | {e.display_label}")
            
except Exception as e:
    print(f"\n❌ 載入失敗: {e}")
    import traceback
    traceback.print_exc()
