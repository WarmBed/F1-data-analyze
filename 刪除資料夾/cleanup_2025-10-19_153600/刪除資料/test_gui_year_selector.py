"""測試 GUI 年份選擇邏輯 - 模擬實際 GUI 行為"""
import sys
sys.path.insert(0, ".")

from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

print("=" * 80)
print("[SIMULATION] GUI Race Selector Behavior")
print("=" * 80)

provider = SeasonCalendarProvider()

# 模擬 GUI 中的年份列表
years = list(range(2020, 2026))  # [2020, 2021, 2022, 2023, 2024, 2025]

print(f"\n[YEAR_COMBO] Available years: {years}")
print("\n" + "=" * 80)

results = {}

for year in years:
    print(f"\n[{year}] Loading events...")
    
    try:
        # 模擬 _get_calendar_events_for_year(year)
        events = provider.get_completed_events(year)
        
        # 模擬 GUI 中的過濾邏輯
        completed = [e for e in events if e.is_completed]
        upcoming = [e for e in events if not e.is_completed]
        
        results[year] = {
            "total": len(events),
            "completed": len(completed),
            "upcoming": len(upcoming),
            "has_events": len(events) > 0
        }
        
        # 模擬 race_combo 顯示
        if len(events) == 0:
            display_text = f"{year} [無已完成賽事]"
        else:
            display_text = f"{year} ({len(completed)} 已完成, {len(upcoming)} 未來)"
        
        print(f"   Events: {len(events)} total")
        print(f"   Completed: {len(completed)}")
        print(f"   Upcoming: {len(upcoming)}")
        print(f"   Display: \"{display_text}\"")
        
    except Exception as e:
        print(f"   [ERROR] {e}")
        results[year] = {"total": 0, "completed": 0, "upcoming": 0, "has_events": False}

print("\n" + "=" * 80)
print("[SUMMARY]")
print("=" * 80)

for year, stats in results.items():
    status = "✓" if stats["has_events"] else "✗"
    print(f"  {year}: {status} {stats['total']} events ({stats['completed']} completed, {stats['upcoming']} upcoming)")

# 判斷問題
years_with_events = [y for y, s in results.items() if s["has_events"]]
years_without_events = [y for y, s in results.items() if not s["has_events"]]

print("\n" + "=" * 80)
print("[DIAGNOSIS]")
print("=" * 80)

if len(years_without_events) == 0:
    print("✅ 所有年份都能正確載入事件!")
    print("   問題可能在於 GUI 顯示邏輯或快取")
elif len(years_with_events) == 0:
    print("❌ 所有年份都無法載入事件!")
    print("   SeasonCalendarProvider 存在嚴重問題")
else:
    print(f"⚠️  部分年份無法載入:")
    print(f"   成功: {years_with_events}")
    print(f"   失敗: {years_without_events}")
    
    # 檢查是否只有 2025 能載入
    if years_with_events == [2025]:
        print("\n   → 只有 2025 能載入,這符合用戶報告的問題!")
        print("   → 但測試顯示所有年份都應該能載入...")
        print("   → 可能是 GUI 快取或初始化順序問題")
