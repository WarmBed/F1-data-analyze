#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速驗證 GUI 年份選擇器
"""

import sys
from PyQt5.QtWidgets import QApplication
from f1t_gui_main import StyleHMainWindow

def check_year_combo():
    """檢查主視窗的年份選擇器"""
    print("=" * 80)
    print("🔍 檢查 GUI 主視窗年份選擇器")
    print("=" * 80)
    
    app = QApplication(sys.argv)
    
    # 創建主視窗實例
    print("\n⏳ 正在創建主視窗...")
    main_window = StyleHMainWindow()
    
    # 檢查 year_combo
    year_combo = main_window.year_combo
    all_years = [year_combo.itemText(i) for i in range(year_combo.count())]
    
    print(f"\n📋 Year ComboBox 選項:")
    for i, year in enumerate(all_years):
        current_marker = " ✓ 當前選擇" if year == year_combo.currentText() else ""
        print(f"   {i+1}. {year}{current_marker}")
    
    print(f"\n📊 統計:")
    print(f"   總數: {year_combo.count()}")
    print(f"   範圍: {all_years[0]} - {all_years[-1]}")
    print(f"   預設: {year_combo.currentText()}")
    
    has_2026 = "2026" in all_years
    print(f"\n{'✅' if has_2026 else '❌'} 包含 2026: {has_2026}")
    
    if has_2026:
        print("\n🎉 成功！GUI 年份選擇器已包含 2026")
        print("💡 請在 GUI 中點擊 Year 下拉選單查看所有選項")
    else:
        print("\n❌ 錯誤：GUI 年份選擇器不包含 2026")
        print("💡 請檢查是否有其他代碼路徑覆寫了年份選項")
    
    # 不顯示視窗，直接退出
    return has_2026

if __name__ == "__main__":
    try:
        success = check_year_combo()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
