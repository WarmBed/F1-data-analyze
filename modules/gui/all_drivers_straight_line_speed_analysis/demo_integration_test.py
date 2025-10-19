#!/usr/bin/env python3
"""
Demo 5: 整合測試
測試所有功能的整合測試

作者: F1T Team
日期: 2025-10-14
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


def test_imports():
    """測試模組 Import"""
    print("\n[TEST 1] 測試模組 Import...")
    try:
        print("  [1.1] Import AllDriversStraightLineSpeedModule...")
        from modules.gui.all_drivers_straight_line_speed_analysis import AllDriversStraightLineSpeedModule
        print("  [1.2] Import AllDriversStraightLineSpeedMDI...")
        from modules.gui.all_drivers_straight_line_speed_analysis import AllDriversStraightLineSpeedMDI
        print("  [1.3] Import AllDriversStraightLineSpeedWidget...")
        from modules.gui.all_drivers_straight_line_speed_analysis import AllDriversStraightLineSpeedWidget
        print("✅ 所有模組 Import 成功")
        return True
    except ImportError as e:
        print(f"❌ Import 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_loader():
    """測試資料載入器"""
    print("\n[TEST 2] 測試資料載入器...")
    try:
        from modules.gui.lap_analysis.speed_analysis.straight_line_speed_loader import (
            StraightLineSpeedDataLoader
        )
        
        loader = StraightLineSpeedDataLoader()
        print("✅ 資料載入器創建成功")
        return True
    except Exception as e:
        print(f"❌ 資料載入器測試失敗: {e}")
        return False


def test_widget_creation():
    """測試 Widget 創建"""
    print("\n[TEST 3] 測試 Widget 創建...")
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.all_drivers_straight_line_speed_analysis import AllDriversStraightLineSpeedWidget
        
        app = QApplication.instance() or QApplication(sys.argv)
        widget = AllDriversStraightLineSpeedWidget()
        print("✅ Widget 創建成功")
        return True
    except Exception as e:
        print(f"❌ Widget 創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_module_initialization():
    """測試模組初始化"""
    print("\n[TEST 4] 測試模組初始化...")
    try:
        from modules.gui.all_drivers_straight_line_speed_analysis import AllDriversStraightLineSpeedModule
        
        module = AllDriversStraightLineSpeedModule(
            parent=None,
            year=2024,
            race="Japan",
            session="Q"
        )
        print("✅ 模組創建成功")
        return True
    except Exception as e:
        print(f"❌ 模組初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主程式"""
    print("=" * 80)
    print("Demo 5: 全車手直線速度分析 - 整合測試")
    print("=" * 80)
    
    results = []
    
    # 測試 1: Import
    results.append(("模組 Import", test_imports()))
    
    # 測試 2: 資料載入器
    results.append(("資料載入器", test_data_loader()))
    
    # 測試 3: Widget 創建
    results.append(("Widget 創建", test_widget_creation()))
    
    # 測試 4: 模組初始化
    results.append(("模組初始化", test_module_initialization()))
    
    # 顯示結果
    print("\n" + "=" * 80)
    print("測試結果摘要")
    print("=" * 80)
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    # 總結
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print("=" * 80)
    print(f"總計: {passed}/{total} 測試通過")
    print("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
