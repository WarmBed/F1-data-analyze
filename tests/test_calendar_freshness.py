"""
測試 GUI Season Calendar Provider 的智能加速刷新機制
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

def test_calendar_freshness():
    print("=" * 70)
    print("🧪 測試 Season Calendar 智能加速刷新機制")
    print("=" * 70)
    
    provider = SeasonCalendarProvider()
    
    # 測試 2025 年賽事
    print("\n📅 獲取 2025 年賽事（會自動判斷刷新模式）...")
    try:
        events = provider.get_completed_events(2025)
        
        print(f"\n✅ 成功載入 {len(events)} 個賽事")
        
        # 找到 United States 賽事
        us_events = [e for e in events if "United States" in e.race_key or "United States" in e.display_label]
        
        if us_events:
            us = us_events[0]
            print(f"\n🇺🇸 United States Grand Prix:")
            print(f"  race_key: {us.race_key}")
            print(f"  display_label: {us.display_label}")
            print(f"  race_date: {us.race_date}")
            print(f"  is_completed: {us.is_completed}")
            print(f"  round: {us.round}")
            
            # 檢查狀態是否正確
            now = datetime.now(timezone.utc)
            print(f"\n🕐 當前時間: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            if us.race_date:
                race_date_str = us.race_date + " 19:00:00"  # 假設正賽時間
                print(f"🏁 正賽時間: {race_date_str} UTC")
                
                if us.is_completed:
                    print("  ✅ 狀態正確：已完賽")
                else:
                    print("  ❌ 狀態錯誤：應該已完賽但顯示為 Upcoming")
                    print("  💡 建議：執行 python f1_analysis_modular_main.py -f 99 --force")
        else:
            print("\n⚠️  未找到 United States 賽事")
        
        # 顯示所有賽事狀態
        print(f"\n📊 2025 年賽事狀態統計:")
        completed = [e for e in events if e.is_completed]
        upcoming = [e for e in events if not e.is_completed]
        
        print(f"  已完賽: {len(completed)} 場")
        print(f"  未開賽: {len(upcoming)} 場")
        
        if completed:
            print(f"\n✅ 最近完賽:")
            for event in completed[-3:]:
                print(f"  - {event.race_key} ({event.race_date})")
        
        if upcoming:
            print(f"\n⏳ 即將開賽:")
            now = datetime.now(timezone.utc)
            for event in upcoming[:5]:
                race_date = datetime.strptime(event.race_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) if event.race_date else None
                days_until = (race_date - now).days if race_date else None
                
                if days_until is not None:
                    if -1 <= days_until <= 2:
                        status = f"🚨 臨近！({days_until} 天{'後' if days_until >= 0 else '前'})"
                    elif days_until < -1:
                        status = f"⚠️  已過 ({abs(days_until)} 天前)"
                    else:
                        status = f"({days_until} 天後)"
                else:
                    status = ""
                
                print(f"  - {event.race_key} ({event.race_date}) {status}")
        
        # 測試刷新間隔判斷
        print(f"\n🔄 刷新策略測試:")
        from modules.gui.shared.season_calendar_provider import (
            CALENDAR_REFRESH_HOURS_NORMAL,
            CALENDAR_REFRESH_HOURS_RACE_APPROACHING,
            RACE_APPROACHING_THRESHOLD_DAYS
        )
        print(f"  正常模式: {CALENDAR_REFRESH_HOURS_NORMAL} 小時（{CALENDAR_REFRESH_HOURS_NORMAL/24:.1f} 天）")
        print(f"  加速模式: {CALENDAR_REFRESH_HOURS_RACE_APPROACHING} 小時")
        print(f"  觸發閾值: 賽前 {RACE_APPROACHING_THRESHOLD_DAYS} 天")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ 測試完成")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_calendar_freshness()
    sys.exit(0 if success else 1)
