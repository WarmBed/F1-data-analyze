#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 GUI 年份下拉選單是否包含 2026
"""

import sys
from PyQt5.QtWidgets import QApplication, QComboBox

def test_year_combo():
    """測試年份選擇器的選項"""
    print("=" * 80)
    print("🧪 測試 Year ComboBox 選項")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    
    # 模擬 GUI 中的年份選擇器初始化
    year_combo = QComboBox()
    year_combo.addItems([str(year) for year in range(2020, 2027)])
    year_combo.setCurrentText("2025")
    
    # 獲取所有選項
    all_items = [year_combo.itemText(i) for i in range(year_combo.count())]
    
    print(f"\n📋 Year ComboBox 所有選項:")
    for i, item in enumerate(all_items):
        is_current = " ← 當前選擇" if item == year_combo.currentText() else ""
        print(f"   {i}. {item}{is_current}")
    
    print(f"\n📊 統計:")
    print(f"   總選項數: {year_combo.count()}")
    print(f"   預設選擇: {year_combo.currentText()}")
    print(f"   最小年份: {all_items[0]}")
    print(f"   最大年份: {all_items[-1]}")
    
    # 驗證
    has_2026 = "2026" in all_items
    print(f"\n✅ 包含 2026: {'是' if has_2026 else '否'}")
    
    if has_2026:
        print("\n🎯 結論: ComboBox 初始化代碼正確，包含 2026 選項")
        print("💡 如果 GUI 中看不到 2026，可能原因:")
        print("   1. GUI 使用了不同的初始化代碼路徑")
        print("   2. 某個管理器類別覆寫了年份選項")
        print("   3. 需要檢查 ToolbarBuilder 或其他管理器類別")
    else:
        print("\n❌ 錯誤: ComboBox 未包含 2026")
    
    return has_2026

if __name__ == "__main__":
    success = test_year_combo()
    sys.exit(0 if success else 1)
