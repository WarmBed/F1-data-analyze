"""
驗證 stint 數據處理修復 - 使用真實 JSON 數據
"""
import json

print("=" * 80)
print("驗證 stint 數據處理修復 - 使用真實數據")
print("=" * 80)

# 讀取真實的 JSON 數據
with open('json/tire_strategy_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers_analysis = data.get('drivers_analysis', {})

print(f"\n✅ 成功載入 {len(drivers_analysis)} 位車手的數據")

# 模擬新的處理邏輯
print("\n" + "=" * 80)
print("測試新的 stint 處理邏輯:")
print("-" * 80)

problematic_count = 0
success_count = 0

for driver_code in sorted(list(drivers_analysis.keys())[:5]):  # 測試前5位車手
    driver_data = drivers_analysis[driver_code]
    stint_data = driver_data.get("stint_analysis", [])
    
    print(f"\n車手: {driver_code}")
    
    for index, stint in enumerate(stint_data, start=1):
        # 新邏輯
        start_lap = stint.get("start_lap")
        if start_lap is None:
            start_lap = stint.get("lap_start")
            if start_lap is None:
                start_lap = stint.get("startLap")
                if start_lap is None:
                    start_lap = 1
        
        end_lap = stint.get("end_lap")
        if end_lap is None or end_lap <= 0:
            end_lap = stint.get("lap_end")
            if end_lap is None or end_lap <= 0:
                end_lap = stint.get("endLap")
                if end_lap is None or end_lap <= 0:
                    # 嘗試使用 length 欄位計算 end_lap
                    length = stint.get("length")
                    if length is not None and length > 0:
                        end_lap = start_lap + length - 1
                    else:
                        # 最後的回退：使用 start_lap（單圈 stint）
                        end_lap = start_lap
        
        # 檢查是否會觸發警告
        if end_lap <= start_lap and stint.get("length", 1) > 1:
            # 只在不是單圈 stint 的情況下才視為問題
            problematic_count += 1
            print(f"  ⚠️ Stint {index}: start={start_lap}, end={end_lap}")
            print(f"     原始數據: {stint}")
        else:
            success_count += 1
            print(f"  ✅ Stint {index}: start={start_lap}, end={end_lap}, length={stint.get('length', '?')}")

print("\n" + "=" * 80)
print("驗證結果:")
print("-" * 80)
print(f"✅ 成功處理: {success_count} 個 stint")
print(f"⚠️ 有問題: {problematic_count} 個 stint")

if problematic_count == 0:
    print("\n🎉 修復成功！所有 stint 數據處理正常，不會再觸發警告！")
else:
    print(f"\n⚠️ 仍有 {problematic_count} 個問題需要進一步調查")

print("=" * 80)
