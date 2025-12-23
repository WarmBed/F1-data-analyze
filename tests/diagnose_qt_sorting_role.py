"""診斷 Qt.UserRole vs Qt.DisplayRole 的排序差異"""
from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
import sys

app = QApplication(sys.argv)

print("\n" + "=" * 80)
print("Qt TableWidget 排序機制測試")
print("=" * 80)

# 測試數據（故意打亂順序）
test_data = [
    ("ANT", 9.959),
    ("ALB", 9.680),
    ("SAI", 9.480),
    ("RUS", 9.519),
    ("BEA", 9.760),
    ("STR", 9.160),
]

# ============================================================
# 測試 1: 使用 Qt.UserRole（我們當前的方式）
# ============================================================
print("\n【測試 1】使用 Qt.UserRole 設置排序數據")
print("-" * 80)

table1 = QTableWidget(6, 2)
table1.setHorizontalHeaderLabels(["車手", "加速時間 (UserRole)"])
table1.setSortingEnabled(False)

for row, (driver, time) in enumerate(test_data):
    # 車手
    driver_item = QTableWidgetItem(driver)
    table1.setItem(row, 0, driver_item)
    
    # 加速時間 - 使用 Qt.UserRole
    time_item = QTableWidgetItem(f"{time:.3f} s")
    time_item.setData(Qt.UserRole, time)  # ❌ 我們當前的方式
    table1.setItem(row, 1, time_item)
    
    print(f"  Row {row}: {driver} - Text: '{time_item.text()}' | UserRole: {time_item.data(Qt.UserRole)} (type: {type(time_item.data(Qt.UserRole)).__name__})")

table1.setSortingEnabled(True)
table1.sortItems(1, Qt.AscendingOrder)

print("\n  ✅ 排序後（column 1, 升序）:")
for row in range(table1.rowCount()):
    driver = table1.item(row, 0).text()
    time_text = table1.item(row, 1).text()
    time_data = table1.item(row, 1).data(Qt.UserRole)
    print(f"    {row + 1}. {driver} - {time_text} (UserRole: {time_data})")

# ============================================================
# 測試 2: 使用 Qt.DisplayRole（Ideal Lap 的方式）
# ============================================================
print("\n【測試 2】使用 Qt.DisplayRole 設置排序數據")
print("-" * 80)

table2 = QTableWidget(6, 2)
table2.setHorizontalHeaderLabels(["車手", "加速時間 (DisplayRole)"])
table2.setSortingEnabled(False)

for row, (driver, time) in enumerate(test_data):
    # 車手
    driver_item = QTableWidgetItem(driver)
    table2.setItem(row, 0, driver_item)
    
    # 加速時間 - 使用 Qt.DisplayRole
    time_item = QTableWidgetItem()
    time_item.setData(Qt.DisplayRole, time)  # ✅ Ideal Lap 的方式
    time_item.setText(f"{time:.3f} s")
    table2.setItem(row, 1, time_item)
    
    print(f"  Row {row}: {driver} - Text: '{time_item.text()}' | DisplayRole: {time_item.data(Qt.DisplayRole)} (type: {type(time_item.data(Qt.DisplayRole)).__name__})")

table2.setSortingEnabled(True)
table2.sortItems(1, Qt.AscendingOrder)

print("\n  ✅ 排序後（column 1, 升序）:")
for row in range(table2.rowCount()):
    driver = table2.item(row, 0).text()
    time_text = table2.item(row, 1).text()
    time_data = table2.item(row, 1).data(Qt.DisplayRole)
    print(f"    {row + 1}. {driver} - {time_text} (DisplayRole: {time_data})")

# ============================================================
# 測試 3: 同時使用 DisplayRole 和 UserRole
# ============================================================
print("\n【測試 3】同時使用 DisplayRole（排序）和 UserRole（存儲）")
print("-" * 80)

table3 = QTableWidget(6, 2)
table3.setHorizontalHeaderLabels(["車手", "加速時間 (Both)"])
table3.setSortingEnabled(False)

for row, (driver, time) in enumerate(test_data):
    # 車手
    driver_item = QTableWidgetItem(driver)
    table3.setItem(row, 0, driver_item)
    
    # 加速時間 - 同時設置兩個 Role
    time_item = QTableWidgetItem(f"{time:.3f} s")
    time_item.setData(Qt.DisplayRole, time)  # ✅ 用於排序
    time_item.setData(Qt.UserRole, time)     # ✅ 用於存儲原始值
    table3.setItem(row, 1, time_item)
    
    print(f"  Row {row}: {driver} - DisplayRole: {time_item.data(Qt.DisplayRole)}, UserRole: {time_item.data(Qt.UserRole)}")

table3.setSortingEnabled(True)
table3.sortItems(1, Qt.AscendingOrder)

print("\n  ✅ 排序後（column 1, 升序）:")
for row in range(table3.rowCount()):
    driver = table3.item(row, 0).text()
    time_text = table3.item(row, 1).text()
    time_display = table3.item(row, 1).data(Qt.DisplayRole)
    time_user = table3.item(row, 1).data(Qt.UserRole)
    print(f"    {row + 1}. {driver} - {time_text} (Display: {time_display}, User: {time_user})")

print("\n" + "=" * 80)
print("結論：")
print("=" * 80)
print("❌ Qt.UserRole: 不參與排序（Qt 內部不使用此 Role 排序）")
print("✅ Qt.DisplayRole: 參與排序（Qt 默認使用 DisplayRole 排序）")
print("💡 最佳實踐: 同時設置 DisplayRole（排序）和 UserRole（數據存儲）")
print("=" * 80 + "\n")

sys.exit(0)
