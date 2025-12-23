#!/usr/bin/env python3
"""快速測試車手列表載入修復"""
import sys
from PyQt5.QtWidgets import QApplication

# 導入對話框
from f1t_gui_main import LapAnalysisOptionsDialog

print("=" * 60)
print("🧪 測試車手列表載入修復")
print("=" * 60)

app = QApplication([])

# 創建對話框（不顯示）
dialog = LapAnalysisOptionsDialog()

# 檢查車手列表
print(f"\n車手1下拉選單:")
print(f"  項目數: {dialog.driver1_combo.count()}")
if dialog.driver1_combo.count() > 0:
    print(f"  前5個: {[dialog.driver1_combo.itemText(i) for i in range(min(5, dialog.driver1_combo.count()))]}")
else:
    print(f"  ❌ 空列表")

print(f"\n車手2下拉選單:")
print(f"  項目數: {dialog.driver2_combo.count()}")
if dialog.driver2_combo.count() > 0:
    print(f"  前5個: {[dialog.driver2_combo.itemText(i) for i in range(min(5, dialog.driver2_combo.count()))]}")
else:
    print(f"  ❌ 空列表")

print(f"\n" + "=" * 60)
if dialog.driver1_combo.count() > 0 and dialog.driver2_combo.count() > 1:
    print("✅ 測試通過：車手列表已正確載入")
else:
    print("❌ 測試失敗：車手列表未正確載入")
print("=" * 60)
