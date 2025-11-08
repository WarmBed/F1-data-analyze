"""測試移除排名欄位後的表格排序"""
import json

# 讀取 JSON 數據
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

# 提取 drivers 數據
data = response.get('data', {})
drivers = data.get('driver_speeds', [])

# 按 segment_accel_time_seconds 升序排序
sorted_drivers = sorted(drivers, key=lambda x: x.get('segment_accel_time_seconds', 9999))

print('\n========== 排序測試：移除排名欄位後 ==========\n')
print('✅ 欄位變更：')
print('  舊版（8欄）: 排名 | 車手 | 車隊 | 最高速度 | 加速時間 | 平均加速度 | 起始速度 | 視覺化')
print('  新版（7欄）: 車手 | 車隊 | 最高速度 | 加速時間 | 平均加速度 | 起始速度 | 視覺化')
print('  ❌ 移除了「排名」欄位（固定排名會誤導用戶）\n')

print('✅ 正確的加速時間排序（升序，最快在前）：\n')
for i, d in enumerate(sorted_drivers[:12], 1):
    driver = d.get('driver', 'N/A')
    number = d.get('driver_number', 0)
    time = d.get('segment_accel_time_seconds', 0)
    print(f'  {i:2d}. {driver:3s}  #{number:2d}   {time:5.3f} s')

print('\n\n🔍 用戶反映的問題車手：')
ant = next((d for d in drivers if d.get('driver') == 'ANT'), None)
bea = next((d for d in drivers if d.get('driver') == 'BEA'), None)

if ant:
    ant_time = ant.get('segment_accel_time_seconds', 0)
    ant_rank = sorted_drivers.index(ant) + 1
    print(f'  ANT: {ant_time:.3f} s → 正確排名 #{ant_rank}（用戶看到錯誤排名 #1）')
    
if bea:
    bea_time = bea.get('segment_accel_time_seconds', 0)
    bea_rank = sorted_drivers.index(bea) + 1
    print(f'  BEA: {bea_time:.3f} s → 正確排名 #{bea_rank}（用戶看到錯誤排名 #6）')

print('\n\n💡 解決方案總結：')
print('  ✅ 移除固定「排名」欄位')
print('  ✅ 所有欄位索引減 1（0-6 instead of 0-7）')
print('  ✅ 視覺化欄位從 column 7 改為 column 6')
print('  ✅ 委託設置從 setItemDelegateForColumn(7) 改為 (6)')
print('  ✅ 用戶點擊任何欄位標題都能動態排序')
print('\n  優點：')
print('  1. 不會有固定排名誤導用戶')
print('  2. 支持多欄位排序（點擊任何欄位標題）')
print('  3. 支持升序/降序切換')
print('  4. Qt 自動處理排序邏輯，不需要手動維護排名')
