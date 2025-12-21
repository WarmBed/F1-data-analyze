"""
快速驗證腳本 - 確認 objgraph 是否能看到 GUI 物件

在 F1T GUI 的 Python Debug Console 中執行此腳本
"""

import objgraph
import gc

print("\n=== 快速驗證測試 ===\n")

# 測試 1: 檢查是否能看到 PyQt5 物件
print("測試 1: 檢查 PyQt5 物件")
qwidget_count = objgraph.count('QWidget')
qmainwindow_count = objgraph.count('QMainWindow')
print(f"  QWidget: {qwidget_count} 個")
print(f"  QMainWindow: {qmainwindow_count} 個")

if qwidget_count == 0:
    print("  ❌ 無法看到 QWidget，objgraph 可能未連接到 GUI 進程")
else:
    print(f"  ✅ 可以看到 {qwidget_count} 個 QWidget")

# 測試 2: 顯示最常見的類型
print("\n測試 2: 最常見的類型（TOP 15）")
most_common = objgraph.most_common_types(limit=15)
for type_name, count in most_common:
    print(f"  {type_name}: {count} 個")

# 測試 3: 搜索 F1T 相關類型
print("\n測試 3: 搜索 F1T 相關類型")
all_types = objgraph.most_common_types(limit=200)

found_f1t_types = []
for type_name, count in all_types:
    if any(keyword in type_name for keyword in ['Speed', 'Analysis', 'Telemetry', 'F1', 'Lap', 'Chart', 'Data', 'Manager', 'Loader', 'MDI']):
        found_f1t_types.append((type_name, count))

if found_f1t_types:
    print(f"  找到 {len(found_f1t_types)} 個 F1T 相關類型:")
    for type_name, count in found_f1t_types[:20]:
        print(f"    {type_name}: {count} 個")
else:
    print("  ❌ 未找到 F1T 相關類型")

# 測試 4: GC 測試
print("\n測試 4: GC 回收測試")
collected = gc.collect()
print(f"  GC 回收了 {collected} 個物件")

print("\n=== 驗證完成 ===")
