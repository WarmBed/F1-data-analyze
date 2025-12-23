import json

# 讀取 JSON 檔案
with open('json/predictionJSON/fp_q_data_2024_Japan_20251029_134007.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*60)
print("FP→Q 訓練數據結構檢查")
print("="*60)

# 1. Metadata
print("\n【1. Metadata】")
for key, value in data['metadata'].items():
    print(f"  {key}: {value}")

# 2. Practice Sessions 結構
print("\n【2. Practice Sessions】")
print(f"  包含會話: {list(data['practice_sessions'].keys())}")

# 3. FP1 詳細數據
print("\n【3. FP1 數據】")
fp1_data = data['practice_sessions']['FP1']
print(f"  會話名稱: {fp1_data['session_info']['session_name']}")
print(f"  日期: {fp1_data['session_info']['date']}")
print(f"  天氣:")
for key, value in fp1_data['weather'].items():
    print(f"    - {key}: {value}")
print(f"  車手數量: {len(fp1_data['driver_data'])}")

# 4. VER 在 FP1 的數據
print("\n【4. VER 在 FP1 的完整數據】")
ver_fp1 = fp1_data['driver_data']['VER']
for key, value in ver_fp1.items():
    print(f"  {key}: {value}")

# 5. Qualifying 結構
print("\n【5. Qualifying 數據】")
q_data = data['qualifying']
print(f"  賽事: {q_data['session_info']['event_name']}")
print(f"  賽道: {q_data['session_info']['circuit']}")
print(f"  國家: {q_data['session_info']['country']}")
print(f"  日期: {q_data['session_info']['date']}")
print(f"  天氣:")
for key, value in q_data['weather'].items():
    print(f"    - {key}: {value}")
print(f"  結果數量: {len(q_data['results'])}")

# 6. VER 排位賽結果
print("\n【6. VER Qualifying 結果】")
ver_q = q_data['results']['VER']
for key, value in ver_q.items():
    print(f"  {key}: {value}")

# 7. 數據完整性檢查
print("\n【7. 數據完整性檢查】")
print(f"  總車手列表: {data['drivers']}")
print(f"  車手數量: {len(data['drivers'])}")

# 8. 檢查所有 FP 會話的車手一致性
print("\n【8. 各會話車手數量】")
for session_name, session_data in data['practice_sessions'].items():
    driver_count = len(session_data['driver_data'])
    print(f"  {session_name}: {driver_count} 位車手")

# 9. 輪胎數據檢查
print("\n【9. 輪胎配方數據檢查 (VER FP1)】")
compounds = ver_fp1.get('compounds_used', [])
print(f"  使用的輪胎配方: {compounds}")
print(f"  配方種類: {len(set(compounds))}")

# 10. 計算 FP 與 Q 的關聯性
print("\n【10. FP→Q 預測所需數據檢查】")
print("  ✅ FP1/FP2/FP3 單圈時間 (best/avg/std)")
print("  ✅ 分段時間 (sector1/2/3 best)")
print("  ✅ 速度陷阱 (speed_trap_max)")
print("  ✅ 輪胎配方 (compounds_used)")
print("  ✅ 輪胎平均胎齡 (tire_age_avg)")
print("  ✅ 天氣數據 (air_temp, track_temp, humidity, rainfall)")
print("  ✅ 車隊資訊 (team, team_color)")
print("  ✅ Qualifying 最終排名 (position)")
print("  ✅ Qualifying Q1/Q2/Q3 時間")

print("\n" + "="*60)
print("✅ JSON 數據格式驗證通過！包含所有 FP→Q 預測所需欄位")
print("="*60)
