#!/usr/bin/env python3
"""檢查 FastF1 對 United States 2025 R 返回的實際事件名稱"""

import fastf1

# 啟用緩存
fastf1.Cache.enable_cache('cache')

print("=" * 80)
print("🔍 檢查 FastF1Session 事件名稱")
print("=" * 80)

try:
    print("\n📡 載入 2025 United States R 會話...")
    session = fastf1.get_session(2025, "United States", "R")
    session.load()
    
    print("\n✅ 會話載入成功！")
    print(f"\n📍 事件資訊:")
    print(f"  EventName: {session.event['EventName']}")
    print(f"  EventFormat: {session.event.get('EventFormat', 'N/A')}")
    print(f"  Location: {session.event.get('Location', 'N/A')}")
    print(f"  Country: {session.event.get('Country', 'N/A')}")
    print(f"  OfficialEventName: {session.event.get('OfficialEventName', 'N/A')}")
    
    print(f"\n📊 會話資訊:")
    print(f"  Session: {session.session_info.get('Type', 'N/A')}")
    print(f"  Date: {session.session_info.get('StartDate', 'N/A')}")
    
    # 檢查進站數據
    laps = session.laps
    if hasattr(laps, 'pick_driver'):
        first_driver = laps['Driver'].iloc[0] if len(laps) > 0 else None
        if first_driver:
            driver_laps = laps.pick_driver(first_driver)
            print(f"\n🏎️  首位車手: {first_driver}")
            print(f"  圈數: {len(driver_laps)}")
    
except Exception as e:
    print(f"\n❌ 失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
