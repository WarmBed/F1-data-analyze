"""診斷 All Drivers Speed 欄位對應問題"""
import json

# 讀取 Japan 數據
with open('json/all_drivers_straight_line_speed_2025_Japan_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

data = response['data']['data']
driver_speeds = data['driver_speeds']

print("=" * 100)
print("🔍 All Drivers Speed & Acceleration 欄位對應診斷")
print("=" * 100)

# 顯示欄位定義
print("\n📋 GUI 欄位定義（從代碼）:")
print("-" * 100)
columns = [
    "0. 車手",
    "1. 車隊",
    "2. 最高速度",
    "3. 加速時間 (speed_analysis_header_segment_accel_time)",
    "4. 平均加速度",
    "5. 起始速度",
    "6. 最高速度時間 (speed_analysis_header_max_speed_time)",
    "7. 加速性能視覺化"
]
for col in columns:
    print(f"  {col}")

print("\n" + "=" * 100)
print("📊 實際數據示例（前 3 位車手）")
print("=" * 100)

for i, driver in enumerate(driver_speeds[:3]):
    print(f"\n車手 {i+1}: {driver['driver']} ({driver['team']})")
    print("-" * 100)
    
    # 顯示所有相關時間數據
    print(f"  最高速度 (max_speed_kmh): {driver['max_speed_kmh']} km/h")
    print(f"  起始速度 (segment_start_speed_kmh): {driver.get('segment_start_speed_kmh')} km/h")
    print(f"  統一結束速度 (segment_unified_end_speed_kmh): {driver.get('segment_unified_end_speed_kmh')} km/h")
    print(f"  個人最高速度 (segment_personal_max_speed_kmh): {driver.get('segment_personal_max_speed_kmh')} km/h")
    print()
    print(f"  📌 segment_accel_time_seconds: {driver.get('segment_accel_time_seconds')} 秒")
    print(f"     → 意義: 從起始速度到【統一結束速度】的時間")
    print(f"     → 計算: {driver.get('segment_start_speed_kmh')} → {driver.get('segment_unified_end_speed_kmh')} km/h")
    print()
    print(f"  📌 max_speed_time_seconds: {driver.get('max_speed_time_seconds')} 秒")
    print(f"     → 意義: 從起始速度到【個人最高速度】的時間")
    print(f"     → 計算: {driver.get('segment_start_speed_kmh')} → {driver.get('segment_personal_max_speed_kmh')} km/h")

print("\n" + "=" * 100)
print("🎯 GUI 欄位對應現狀")
print("=" * 100)
print("欄位 3 (加速時間) → 填充數據: segment_accel_time_seconds")
print("欄位 6 (最高速度時間) → 填充數據: max_speed_time_seconds")
print()
print("✅ 這個對應是【正確的】！")
print()
print("但是根據用戶的邏輯：")
print("  - '加速時間' 應該是到達統一速度的時間 ← segment_accel_time_seconds ✅")
print("  - '最高速度時間' 應該是到達個人最高速度的時間 ← max_speed_time_seconds ✅")

print("\n" + "=" * 100)
print("⚠️  問題分析")
print("=" * 100)
print("從截圖中看到:")
print("  - 'Max Speed Time' 欄位顯示約 7.2-8.3 秒")
print("  - 'Accel Time' 欄位顯示約 5.7-6.7 秒")
print()
print("但從 JSON 數據看到:")
print("  - segment_accel_time_seconds: 約 1.0 秒（BOR = 1.04）")
print("  - max_speed_time_seconds: 約 7.4 秒（BOR = 7.367）")
print()
print("❓ 截圖中的數據與 JSON 不符！")
print()
print("可能的原因:")
print("  1. 截圖使用的是舊版 JSON（不同的計算邏輯）")
print("  2. GUI 有額外的計算邏輯修改了數值")
print("  3. 截圖中的賽事與 Japan 不同")

print("\n" + "=" * 100)
print("💡 建議行動")
print("=" * 100)
print("1. 確認截圖中的賽事（年份、賽道、Session）")
print("2. 檢查對應的 JSON 檔案數據")
print("3. 確認 GUI 是否有額外計算邏輯")
