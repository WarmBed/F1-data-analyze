import json
import os
from datetime import datetime

# 等待新的 JSON 生成
json_file = 'json/all_drivers_cornering_analysis_2025_Mexico_R.json'

print("=" * 80)
print("插值法修復驗證工具")
print("=" * 80)
print(f"\n檢查檔案: {json_file}")

# 檢查檔案是否存在
if not os.path.exists(json_file):
    print("[ERROR] 檔案不存在，請等待 Function 47 執行完成")
    exit(1)

# 讀取檔案時間
file_time = datetime.fromtimestamp(os.path.getmtime(json_file))
print(f"檔案修改時間: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 檢查是否是最近生成的（5分鐘內）
time_diff = datetime.now() - file_time
if time_diff.total_seconds() > 300:
    print(f"[WARNING] 檔案可能不是最新的（{time_diff.total_seconds():.0f} 秒前）")
    print("[INFO] 請等待 Function 47 執行完成")
else:
    print(f"[OK] 檔案是最新的（{time_diff.total_seconds():.0f} 秒前生成）")

# 讀取 JSON 檔案
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

drivers = data['fastest_lap_analysis']['drivers']

print(f"\n總車手數: {len(drivers)}")
print("\n" + "=" * 80)
print("T13 (low-speed corner) 數據完整性檢查")
print("=" * 80)

# 統計數據完整性
complete_count = 0
null_entry_drivers = []
null_apex_drivers = []
null_exit_drivers = []

for d in drivers:
    driver_code = d['driver']
    t13_data = d['corners']['low_speed_corner_13']
    entry = t13_data['entry_50m_speed']
    apex = t13_data['apex_speed']
    exit = t13_data['exit_50m_speed']
    
    if all([entry, apex, exit]):
        complete_count += 1
    else:
        if entry is None:
            null_entry_drivers.append(driver_code)
        if apex is None:
            null_apex_drivers.append(driver_code)
        if exit is None:
            null_exit_drivers.append(driver_code)

print(f"\n📊 統計摘要:")
print(f"  ✅ 完整數據車手: {complete_count} / {len(drivers)}")
print(f"  ⚠️  Entry 缺失: {len(null_entry_drivers)} 位 {null_entry_drivers if null_entry_drivers else ''}")
print(f"  ⚠️  Apex 缺失: {len(null_apex_drivers)} 位 {null_apex_drivers if null_apex_drivers else ''}")
print(f"  ⚠️  Exit 缺失: {len(null_exit_drivers)} 位 {null_exit_drivers if null_exit_drivers else ''}")

# 對比舊結果
old_complete = 18
old_null_entry = 1  # PIA
old_null_exit = 1   # ANT

print(f"\n📈 改進對比:")
print(f"  完整數據: {old_complete} → {complete_count} ({'+' if complete_count > old_complete else ''}{complete_count - old_complete})")
print(f"  Entry 缺失: {old_null_entry} → {len(null_entry_drivers)} ({'-' if len(null_entry_drivers) < old_null_entry else ''}{len(null_entry_drivers) - old_null_entry})")
print(f"  Exit 缺失: {old_null_exit} → {len(null_exit_drivers)} ({'-' if len(null_exit_drivers) < old_null_exit else ''}{len(null_exit_drivers) - old_null_exit})")

if complete_count == len(drivers):
    print("\n✅ 太棒了！所有車手的 T13 數據都完整了！")
    print("🎉 插值法成功修復了所有缺失數據！")
elif complete_count > old_complete:
    print(f"\n✅ 很好！數據完整性提升了 {complete_count - old_complete} 位車手")
    print("📈 插值法成功改善了數據品質！")
else:
    print(f"\n⚠️  數據完整性沒有改善")
    print("🔍 可能需要進一步調整插值邏輯")

# 詳細顯示仍有問題的車手
if complete_count < len(drivers):
    print(f"\n⚠️  仍有 {len(drivers) - complete_count} 位車手數據不完整:")
    for d in drivers:
        driver_code = d['driver']
        t13_data = d['corners']['low_speed_corner_13']
        entry = t13_data['entry_50m_speed']
        apex = t13_data['apex_speed']
        exit = t13_data['exit_50m_speed']
        
        if not all([entry, apex, exit]):
            entry_str = f'{entry:6.1f}' if entry is not None else '  NULL'
            apex_str = f'{apex:6.1f}' if apex is not None else '  NULL'
            exit_str = f'{exit:6.1f}' if exit is not None else '  NULL'
            print(f"  • {driver_code}: Entry: {entry_str} | Apex: {apex_str} | Exit: {exit_str}")

print("\n" + "=" * 80)
