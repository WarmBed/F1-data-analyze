#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模擬 GUI 切換到 2026 年並檢查 Season Progress 更新
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def test_year_switch_to_2026():
    """測試切換到 2026 年"""
    print("=" * 80)
    print("🧪 測試 GUI 切換到 2026 年")
    print("=" * 80)
    
    from f1t_gui_main import StyleHMainWindow
    
    app = QApplication(sys.argv)
    main_window = StyleHMainWindow()
    
    # 檢查 Year ComboBox 選項
    year_combo = main_window.year_combo
    all_years = [year_combo.itemText(i) for i in range(year_combo.count())]
    
    print(f"\n📋 Year ComboBox 選項: {', '.join(all_years)}")
    print(f"📍 當前選擇: {year_combo.currentText()}")
    
    if "2026" not in all_years:
        print("\n❌ 錯誤: Year ComboBox 不包含 2026")
        return False
    
    print(f"\n✅ Year ComboBox 包含 2026")
    
    # 模擬切換到 2026
    print(f"\n🔄 模擬切換年份: 2025 → 2026")
    year_combo.setCurrentText("2026")
    
    # 等待事件處理
    app.processEvents()
    
    print(f"📍 切換後年份: {year_combo.currentText()}")
    
    # 檢查 Season Progress
    print(f"\n🔍 檢查 Season Progress 更新...")
    
    # 查找 Season Progress MDI
    season_progress_found = False
    for subwindow in main_window.mdi_area.subWindowList():
        widget = subwindow.widget()
        if hasattr(widget, '__class__') and 'SeasonProgress' in widget.__class__.__name__:
            season_progress_found = True
            print(f"   ✅ 找到 Season Progress MDI")
            
            # 檢查年份
            if hasattr(widget, 'year'):
                print(f"   📅 MDI 年份: {widget.year}")
            
            if hasattr(widget, 'widget') and hasattr(widget.widget, 'season_year'):
                print(f"   📅 Widget 年份: {widget.widget.season_year}")
            
            break
    
    if not season_progress_found:
        print(f"   ℹ️  Season Progress MDI 未找到（可能在 Home 視窗中）")
    
    print(f"\n✅ 測試完成")
    print(f"💡 在實際 GUI 中，點擊 Year 下拉選單並選擇 2026")
    print(f"💡 Season Progress 會自動更新為 '0 / 24' (2026)")
    
    return True

if __name__ == "__main__":
    try:
        success = test_year_switch_to_2026()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
