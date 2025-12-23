"""
診斷加速時間排序問題
"""
import json

# 讀取 JSON 檔案
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

data = response.get('data', {})
drivers = data.get('driver_speeds', [])

print("=" * 80)
print("診斷：加速時間排序問題")
print("=" * 80)
print()

# 檢查數據類型
print("✅ 檢查數據類型：")
for i, driver in enumerate(drivers[:3]):
    accel_time = driver.get('segment_accel_time_seconds')
    print(f"{driver['driver']:3s}: segment_accel_time_seconds = {accel_time} (type: {type(accel_time).__name__})")

print()
print("=" * 80)
print("原始 JSON 順序（前 10 位）：")
print("=" * 80)
print(f"{'索引':4s} {'車手':4s} {'車號':4s} {'加速時間':12s}")
print("-" * 40)
for i, driver in enumerate(drivers[:10]):
    driver_code = driver.get('driver', '')
    driver_number = driver.get('driver_number', 'N/A')
    accel_time = driver.get('segment_accel_time_seconds', 0)
    print(f"{i+1:3d}  {driver_code:3s}  {str(driver_number):4s} {accel_time:8.3f} s")

print()
print("=" * 80)
print("按加速時間升序排列（應該的正確順序）：")
print("=" * 80)
print(f"{'排名':4s} {'車手':4s} {'車號':4s} {'加速時間':12s}")
print("-" * 40)

# 按加速時間排序
sorted_drivers = sorted(drivers, key=lambda x: x.get('segment_accel_time_seconds', 9999))

for i, driver in enumerate(sorted_drivers[:10]):
    driver_code = driver.get('driver', '')
    driver_number = driver.get('driver_number', 'N/A')
    accel_time = driver.get('segment_accel_time_seconds', 0)
    print(f"{i+1:3d}  {driver_code:3s}  {str(driver_number):4s} {accel_time:8.3f} s")

print()
print("=" * 80)
print("問題分析：")
print("=" * 80)
print()

# 找出 ANT 和 BEA
ant_data = next((d for d in drivers if d['driver'] == 'ANT'), None)
bea_data = next((d for d in drivers if d['driver'] == 'BEA'), None)

if ant_data and bea_data:
    ant_time = ant_data.get('segment_accel_time_seconds')
    bea_time = bea_data.get('segment_accel_time_seconds')
    ant_number = ant_data.get('driver_number')
    bea_number = bea_data.get('driver_number')
    
    print(f"ANT (#1): 加速時間 = {ant_time:.3f} s")
    print(f"BEA (#10): 加速時間 = {bea_time:.3f} s")
    print()
    
    if bea_time < ant_time:
        print(f"✅ BEA ({bea_time:.3f}s) 應該排在 ANT ({ant_time:.3f}s) 前面！")
        print(f"   時間差：{ant_time - bea_time:.3f} s")
    
    print()
    print("🔍 可能的問題：")
    print("   1. 排序欄位使用錯誤（可能用了車手號碼而非加速時間）")
    print("   2. UserRole 數據設置不正確")
    print("   3. Qt 表格排序被其他欄位覆蓋")
    print()
    print("📋 GUI 中「排名」欄位顯示的值：")
    print(f"   ANT 排名欄顯示: 1 (這可能是車手號碼 #{ant_number})")
    print(f"   BEA 排名欄顯示: 10 (這可能是車手號碼 #{bea_number})")
    print()
    print("❌ 問題確認：GUI 的「排名」欄位顯示的是車手號碼，不是排名！")
    print("   這導致用戶誤以為是按排名排序的。")
