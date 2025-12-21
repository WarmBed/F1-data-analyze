#!/usr/bin/env python3
"""
測試 Weather Timeline 賽事選擇邏輯

驗證 Weather Timeline 是否正確選擇「下一場未開賽」的賽事
"""

from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

def test_weather_race_selection():
    """測試 Weather Timeline 賽事選擇邏輯"""
    
    print("=" * 60)
    print("Weather Timeline 賽事選擇邏輯測試")
    print("=" * 60)
    
    # 初始化 SeasonCalendarProvider
    provider = SeasonCalendarProvider()
    
    # 測試年份
    test_year = 2025
    
    print(f"\n📅 測試年份: {test_year}")
    
    try:
        # 獲取賽季日曆
        events = provider.get_completed_events(test_year)
        print(f"✅ 成功獲取 {len(events)} 場賽事")
        
        # 分離已完賽和未開賽的賽事
        completed_events = [event for event in events if event.is_completed]
        upcoming_events = [event for event in events if not event.is_completed]
        
        print(f"\n📊 賽事統計:")
        print(f"  - 已完賽: {len(completed_events)} 場")
        print(f"  - 未開賽: {len(upcoming_events)} 場")
        
        # 顯示最新已完賽的賽事
        if completed_events:
            latest_completed = completed_events[-1]
            print(f"\n🏁 最新已完賽:")
            print(f"  - 賽事: {latest_completed.display_label}")
            print(f"  - race_key: {latest_completed.race_key}")
            print(f"  - 日期: {latest_completed.race_date}")
        
        # 顯示下一場未開賽的賽事
        if upcoming_events:
            next_upcoming = upcoming_events[0]
            print(f"\n🌦️ 下一場未開賽 (Weather Timeline 將使用):")
            print(f"  - 賽事: {next_upcoming.display_label}")
            print(f"  - race_key: {next_upcoming.race_key}")
            print(f"  - 日期: {next_upcoming.race_date}")
            
            # 模擬 GUI 的邏輯
            race_base = next_upcoming.race_key
            if "Grand Prix" not in race_base:
                weather_race = f"{race_base} Grand Prix"
            else:
                weather_race = race_base
            
            print(f"  - API 參數: {weather_race}")
            
        else:
            print(f"\n⚠️ 沒有未開賽的賽事")
            if completed_events:
                print(f"   → 回退使用最新已完賽: {completed_events[-1].race_key}")
        
        # 顯示所有未開賽的賽事列表
        if upcoming_events:
            print(f"\n📋 所有未開賽賽事:")
            for i, event in enumerate(upcoming_events, 1):
                print(f"  {i}. {event.display_label} ({event.race_date})")
        
        print("\n" + "=" * 60)
        print("✅ 測試完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_weather_race_selection()
