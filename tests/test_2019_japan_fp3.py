"""深入檢查 2019 Japan FP3 數據加載問題"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fastf1
import traceback

print("=" * 80)
print("檢查 2019 Japan FP3 數據加載")
print("=" * 80)

try:
    # 步驟 1: 獲取 session
    print("\n[步驟 1] 獲取 session 對象...")
    session = fastf1.get_session(2019, 'Japan', 'FP3')
    print(f"✅ Session: {session}")
    
    # 步驟 2: 檢查 session 屬性
    print("\n[步驟 2] 檢查 session 基本資訊...")
    print(f"  - Event: {session.event}")
    print(f"  - Name: {session.name}")
    print(f"  - Date: {session.date}")
    
    # 步驟 3: 嘗試加載數據
    print("\n[步驟 3] 嘗試加載 session 數據...")
    session.load()
    print(f"✅ 數據加載成功")
    
    # 步驟 4: 檢查天氣數據
    print("\n[步驟 4] 檢查天氣數據...")
    weather_data = session.weather_data
    print(f"  - 天氣數據行數: {len(weather_data)}")
    print(f"  - 欄位: {list(weather_data.columns)}")
    
    if len(weather_data) > 0:
        print(f"  - 第一筆: {weather_data.iloc[0].to_dict()}")
    
    # 步驟 5: 檢查 laps 數據
    print("\n[步驟 5] 檢查 laps 數據...")
    laps = session.laps
    print(f"  - 總圈數: {len(laps)}")
    
    if len(laps) > 0:
        print(f"  - 車手列表: {laps['Driver'].unique().tolist()}")
    
    print("\n" + "=" * 80)
    print("✅ 所有檢查通過，數據正常")
    print("=" * 80)
    
except Exception as e:
    print("\n" + "=" * 80)
    print("❌ 發生錯誤")
    print("=" * 80)
    print(f"錯誤類型: {type(e).__name__}")
    print(f"錯誤訊息: {e}")
    print("\n完整 Traceback:")
    traceback.print_exc()
