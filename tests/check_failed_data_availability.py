"""檢查失敗的 3 個 session 的數據可用性"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fastf1

failed_sessions = [
    (2019, "Japan", "FP3"),
    (2020, "Styria", "FP3"),
    (2021, "Russia", "FP3"),
]

print("=" * 80)
print("檢查失敗 Session 的數據可用性")
print("=" * 80)

for year, race, session_type in failed_sessions:
    print(f"\n{year} {race} {session_type}:")
    try:
        session = fastf1.get_session(year, race, session_type)
        print(f"  ✅ Session 物件創建成功")
        
        try:
            session.load()
            print(f"  ✅ 數據加載成功")
            
            # 檢查關鍵數據
            weather_rows = len(session.weather_data) if hasattr(session, 'weather_data') else 0
            laps_rows = len(session.laps) if hasattr(session, 'laps') else 0
            
            print(f"  ✅ 天氣數據: {weather_rows} 行")
            print(f"  ✅ Laps 數據: {laps_rows} 行")
            
            if weather_rows == 0:
                print(f"  ⚠️  天氣數據為空")
            if laps_rows == 0:
                print(f"  ⚠️  Laps 數據為空")
                
        except Exception as load_error:
            print(f"  ❌ 數據加載失敗: {load_error}")
            
    except Exception as session_error:
        print(f"  ❌ Session 創建失敗: {session_error}")

print("\n" + "=" * 80)
print("結論")
print("=" * 80)
print("這些 session 可能因為以下原因失敗：")
print("  1. 比賽取消（如 2019 Japan 颱風）")
print("  2. API 數據缺失")
print("  3. Session 不存在")
print("\n建議：在批次執行器中標記這些為「不可用」而非「失敗」")
