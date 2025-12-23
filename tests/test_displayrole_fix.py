"""
最終驗證：Qt.DisplayRole 修正後的排序測試
"""

import json
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
import sys

print("\n" + "=" * 100)
print(" 最終驗證：Qt.DisplayRole 修正後的排序測試")
print("=" * 100)

# 讀取真實 JSON 數據
with open('json/all_drivers_straight_line_speed_2025_Singapore_R.json', 'r', encoding='utf-8') as f:
    response = json.load(f)

data = response.get('data', {})
drivers = data.get('driver_speeds', [])

# 創建 Qt 應用程式
app = QApplication(sys.argv)

# ============================================================
# 修正後的實現：同時設置 DisplayRole 和 UserRole
# ============================================================
print(f"\n【修正後的實現】同時設置 Qt.DisplayRole（排序）和 Qt.UserRole（數據）")
print("-" * 100)

table = QTableWidget(len(drivers), 7)
table.setHorizontalHeaderLabels(["車手", "車隊", "最高速度", "加速時間", "平均加速度", "起始速度", "視覺化"])
table.setSortingEnabled(False)

for row, driver_data in enumerate(drivers):
    driver = driver_data.get("driver", "")
    team = driver_data.get("team", "")
    max_speed = driver_data.get("max_speed_kmh", 0)
    segment_accel_time = driver_data.get("segment_accel_time_seconds", None)
    
    has_segment_data = segment_accel_time is not None
    segment_accel_time = float(segment_accel_time) if segment_accel_time is not None else 0.0
    
    # 0. 車手
    driver_item = QTableWidgetItem(driver)
    table.setItem(row, 0, driver_item)
    
    # 1. 車隊
    team_item = QTableWidgetItem(team)
    table.setItem(row, 1, team_item)
    
    # 2. 最高速度
    speed_item = QTableWidgetItem(f"{max_speed:.1f} km/h")
    speed_item.setData(Qt.DisplayRole, max_speed)  # ✅ 修正：設置數字
    speed_item.setData(Qt.UserRole, max_speed)
    table.setItem(row, 2, speed_item)
    
    # 3. 加速時間 ⭐ 關鍵修正
    if has_segment_data:
        seg_time_item = QTableWidgetItem(f"{segment_accel_time:.3f} s")
        seg_time_item.setData(Qt.DisplayRole, segment_accel_time)  # ✅ 修正：設置數字
        seg_time_item.setData(Qt.UserRole, segment_accel_time)
    else:
        seg_time_item = QTableWidgetItem("N/A")
        seg_time_item.setData(Qt.DisplayRole, 9999)
        seg_time_item.setData(Qt.UserRole, 9999)
    table.setItem(row, 3, seg_time_item)

print(f"  資料填充完成，共 {len(drivers)} 位車手")

# 啟用排序
table.setSortingEnabled(True)
table.sortItems(3, Qt.AscendingOrder)

print(f"\n  ✅ 按「加速時間」升序排序後（前 15 位）:")
print(f"  {'排名':^6} {'車手':^6} {'加速時間':^15} {'DisplayRole':^15} {'UserRole':^15}")
print(f"  {'-' * 6} {'-' * 6} {'-' * 15} {'-' * 15} {'-' * 15}")

for visual_row in range(min(15, table.rowCount())):
    driver = table.item(visual_row, 0).text()
    time_text = table.item(visual_row, 3).text()
    time_display = table.item(visual_row, 3).data(Qt.DisplayRole)
    time_user = table.item(visual_row, 3).data(Qt.UserRole)
    print(f"  {visual_row + 1:^6d} {driver:^6s} {time_text:^15s} {time_display:^15.3f} {time_user:^15.3f}")

# 檢查關鍵車手
print(f"\n【關鍵車手位置檢查】")
print("-" * 100)

key_drivers = {"STR": None, "ANT": None, "BEA": None}
for row in range(table.rowCount()):
    driver = table.item(row, 0).text()
    if driver in key_drivers:
        key_drivers[driver] = row

for driver, row in key_drivers.items():
    if row is not None:
        time = table.item(row, 3).data(Qt.DisplayRole)
        print(f"  {driver}: 位於第 {row + 1:2d} 位 (加速時間: {time:.3f}s)")

print("\n" + "=" * 100)
print(" 驗證結論")
print("=" * 100)

# 檢查排序是否正確
is_sorted = True
prev_time = 0
for row in range(table.rowCount()):
    current_time = table.item(row, 3).data(Qt.DisplayRole)
    if current_time < prev_time:
        is_sorted = False
        break
    prev_time = current_time

if is_sorted:
    print(f"\n  ✅ 排序完全正確！加速時間從小到大排列")
    print(f"  ✅ STR (最快) 應該在第 1 位")
    print(f"  ✅ ANT (較慢) 應該在後面")
    print(f"  ✅ BEA (中等) 應該在中間位置")
else:
    print(f"\n  ❌ 排序仍然有問題")

print(f"\n  💡 關鍵修正：")
print(f"     setData(Qt.DisplayRole, float_value)  # ✅ 必須設置數字，而非字串")
print(f"     setData(Qt.UserRole, float_value)      # ✅ 保留數值供其他功能使用")
print("\n" + "=" * 100 + "\n")

sys.exit(0)
