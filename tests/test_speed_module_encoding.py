#!/usr/bin/env python3
"""
測試全車手直線速度分析模組初始化
Test All Drivers Straight Line Speed Module Initialization
"""

import sys
from PyQt5.QtWidgets import QApplication

def test_module_import():
    """測試模組導入"""
    print("=" * 60)
    print("測試 1: 模組導入")
    print("=" * 60)
    
    try:
        from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget import (
            AllDriversStraightLineSpeedTableWidget
        )
        print("✅ AllDriversStraightLineSpeedTableWidget 導入成功")
        return True, AllDriversStraightLineSpeedTableWidget
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_widget_creation(WidgetClass):
    """測試 Widget 創建"""
    print("\n" + "=" * 60)
    print("測試 2: Widget 創建")
    print("=" * 60)
    
    try:
        app = QApplication(sys.argv)
        widget = WidgetClass(parent=None)
        print(f"✅ Widget 創建成功: {widget}")
        print(f"   類型: {type(widget)}")
        print(f"   info_label 存在: {hasattr(widget, 'info_label')}")
        
        if hasattr(widget, 'info_label'):
            print(f"   info_label 文字: {widget.info_label.text()}")
        
        return True
    except Exception as e:
        print(f"❌ Widget 創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試流程"""
    print("\n" + "=" * 60)
    print("全車手直線速度分析模組 - 編碼修復驗證")
    print("=" * 60 + "\n")
    
    # 測試 1: 模組導入
    success1, WidgetClass = test_module_import()
    if not success1:
        print("\n❌ 測試失敗於模組導入階段")
        return False
    
    # 測試 2: Widget 創建
    success2 = test_widget_creation(WidgetClass)
    if not success2:
        print("\n❌ 測試失敗於 Widget 創建階段")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 所有測試通過！編碼問題已修復")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
