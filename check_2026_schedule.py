"""檢查 FastF1 2026 年賽程數據"""
import fastf1

# 檢查 2026 年是否有賽事數據
print("檢查 2026 年賽程...")
try:
    schedule_2026 = fastf1.get_event_schedule(2026)
    print(f"✅ 2026 年賽程: {len(schedule_2026)} 場賽事")
    print("\n前 10 場賽事:")
    print(schedule_2026[['EventName', 'EventDate']].head(10))
except Exception as e:
    print(f"❌ 2026 年無賽程數據: {e}")

print("\n" + "="*60)

# 檢查 2025 年最後一場賽事
print("\n檢查 2025 年賽程...")
try:
    schedule_2025 = fastf1.get_event_schedule(2025)
    last_race = schedule_2025.iloc[-1]
    print(f"✅ 2025 年最後一場: {last_race['EventName']} ({last_race['EventDate']})")
    print(f"   共 {len(schedule_2025)} 場賽事")
except Exception as e:
    print(f"❌ 2025 年賽程錯誤: {e}")
