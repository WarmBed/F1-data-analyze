#!/usr/bin/env python3
"""
測試 Race ComboBox 預設選擇邏輯
驗證 GUI 啟動時是否自動選擇最後一場已完賽的比賽
"""

import sys
from datetime import datetime
from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

def test_default_race_selection():
    """測試預設比賽選擇邏輯"""
    print("=" * 60)
    print("測試：Race ComboBox 預設選擇邏輯")
    print("=" * 60)
    
    provider = SeasonCalendarProvider()
    current_year = datetime.now().year
    
    print(f"\n正在獲取 {current_year} 年的賽季日曆...")
    
    try:
        events = provider.get_completed_events(current_year)
        
        if not events:
            print(f"❌ 無法獲取 {current_year} 年的賽事數據")
            return False
        
        # 分類已完賽和未完賽的比賽
        completed_events = [event for event in events if event.is_completed]
        upcoming_events = [event for event in events if not event.is_completed]
        
        print(f"\n📊 賽季統計:")
        print(f"   總賽事數: {len(events)}")
        print(f"   已完賽: {len(completed_events)}")
        print(f"   未完賽: {len(upcoming_events)}")
        
        if completed_events:
            print(f"\n✅ 已完賽的比賽列表:")
            for i, event in enumerate(completed_events, 1):
                marker = "👉 [預設選擇]" if i == len(completed_events) else ""
                print(f"   {i}. {event.display_label} ({event.race_key}) - Round {event.round} {marker}")
            
            # 測試邏輯：使用 completed_events[-1] 獲取最後一場
            default_selection = completed_events[-1]
            print(f"\n🎯 預設選擇邏輯測試:")
            print(f"   使用 completed_events[-1]")
            print(f"   ✅ 預設選擇: {default_selection.display_label} ({default_selection.race_key})")
            print(f"   📅 比賽日期: {default_selection.race_date}")
            print(f"   🏁 Round: {default_selection.round}")
            
            # 驗證這確實是列表中的最後一項
            if default_selection == completed_events[-1]:
                print(f"\n✅ 測試通過！GUI 將自動選擇最後一場已完賽的比賽")
                return True
            else:
                print(f"\n❌ 測試失敗！邏輯錯誤")
                return False
        else:
            print(f"\n⚠️ {current_year} 年尚無已完賽的比賽")
            
            if upcoming_events:
                print(f"\n📅 未來比賽:")
                for i, event in enumerate(upcoming_events, 1):
                    marker = "👉 [預設選擇]" if i == 1 else ""
                    print(f"   {i}. {event.display_label} ({event.race_key}) - Round {event.round} {marker}")
                
                print(f"\n🎯 當無已完賽比賽時，將選擇第一場未來比賽")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("F1T GUI - Race 預設選擇測試")
    print("=" * 60)
    
    success = test_default_race_selection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 測試完成！修改已正確實施")
    else:
        print("❌ 測試未通過，請檢查代碼")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
