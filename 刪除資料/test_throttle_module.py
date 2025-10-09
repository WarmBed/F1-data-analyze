#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試油門折線圖模組
"""

import sys
from PyQt5.QtWidgets import QApplication

def test_module_import():
    """測試模組導入"""
    print("=" * 60)
    print("測試 1: 導入模組")
    print("=" * 60)
    
    try:
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule
        print("✅ 模組導入成功")
        return True
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_creation():
    """測試模組創建"""
    print("\n" + "=" * 60)
    print("測試 2: 創建模組實例")
    print("=" * 60)
    
    try:
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule
        
        # 創建模組實例
        module = ThrottleLineChartModule(
            year=2025,
            race="Japan",
            session="R"
        )
        
        print(f"✅ 模組實例創建成功")
        print(f"   - 模組名稱: {module.module_name}")
        print(f"   - 顯示名稱: {module.display_name}")
        print(f"   - 版本: {module.version}")
        print(f"   - 視窗標題: {module.get_window_title()}")
        print(f"   - 預設大小: {module.get_default_size()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模組創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_widget_creation():
    """測試 Widget 創建"""
    print("\n" + "=" * 60)
    print("測試 3: 創建 Widget")
    print("=" * 60)
    
    try:
        # 需要 QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import ThrottleLineChartModule
        
        module = ThrottleLineChartModule(
            year=2025,
            race="Japan",
            session="R"
        )
        
        widget = module.get_widget()
        
        if widget:
            print(f"✅ Widget 創建成功")
            print(f"   - Widget 類型: {type(widget).__name__}")
            print(f"   - Widget 大小: {widget.size()}")
            return True
        else:
            print(f"❌ Widget 創建失敗: get_widget() 返回 None")
            return False
        
    except Exception as e:
        print(f"❌ Widget 創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("\n🧪 油門折線圖模組完整測試")
    print("=" * 60)
    
    results = []
    
    # 測試 1: 導入
    results.append(("導入模組", test_module_import()))
    
    # 測試 2: 創建實例
    results.append(("創建實例", test_module_creation()))
    
    # 測試 3: 創建 Widget
    results.append(("創建 Widget", test_widget_creation()))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！模組可以正常使用")
        return 0
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤訊息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
