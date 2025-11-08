#!/usr/bin/env python3
"""
測試車手比賽排名分析模組
Test Driver Position Analysis Module
"""

import sys
from PyQt5.QtWidgets import QApplication

def test_import():
    """測試模組導入"""
    print("=== 測試 1: 模組導入 ===")
    try:
        from modules.gui.driver_position_analysis import (
            DriverPositionAnalysisModule,
            DriverPositionAnalysisMDI,
            DriverPositionAnalysisWidget
        )
        print("✅ 模組導入成功")
        print(f"   - DriverPositionAnalysisModule: {DriverPositionAnalysisModule}")
        print(f"   - DriverPositionAnalysisMDI: {DriverPositionAnalysisMDI}")
        print(f"   - DriverPositionAnalysisWidget: {DriverPositionAnalysisWidget}")
        return True
    except Exception as e:
        print(f"❌ 模組導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_widget_creation():
    """測試 Widget 創建"""
    print("\n=== 測試 2: Widget 創建 ===")
    try:
        from modules.gui.driver_position_analysis import DriverPositionAnalysisWidget
        
        app = QApplication.instance() or QApplication(sys.argv)
        widget = DriverPositionAnalysisWidget()
        
        print("✅ Widget 創建成功")
        print(f"   - Widget 類型: {type(widget)}")
        print(f"   - 表格欄位數: {widget.table.columnCount()}")
        print(f"   - 表格行數: {widget.table.rowCount()}")
        
        return True
    except Exception as e:
        print(f"❌ Widget 創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_data():
    """測試模擬數據填充"""
    print("\n=== 測試 3: 模擬數據填充 ===")
    try:
        from modules.gui.driver_position_analysis import DriverPositionAnalysisWidget
        
        app = QApplication.instance() or QApplication(sys.argv)
        widget = DriverPositionAnalysisWidget()
        
        # 模擬數據
        mock_data = [
            {
                "driver": "VER",
                "team": "Red Bull Racing",
                "starting_position": 1,
                "finishing_position": 1,
                "best_position": 1,
                "worst_position": 2,
            },
            {
                "driver": "LEC",
                "team": "Ferrari",
                "starting_position": 3,
                "finishing_position": 2,
                "best_position": 2,
                "worst_position": 4,
            },
            {
                "driver": "PER",
                "team": "Red Bull Racing",
                "starting_position": 2,
                "finishing_position": 3,
                "best_position": 2,
                "worst_position": 5,
            },
        ]
        
        widget.populate_table(mock_data)
        
        print("✅ 數據填充成功")
        print(f"   - 填充行數: {widget.table.rowCount()}")
        
        # 顯示 Widget
        widget.setWindowTitle("測試: 車手比賽排名分析")
        widget.resize(1200, 600)
        widget.show()
        
        print("\n💡 Widget 已顯示，關閉視窗以繼續測試...")
        app.exec_()
        
        return True
    except Exception as e:
        print(f"❌ 數據填充失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試流程"""
    print("🧪 開始測試車手比賽排名分析模組\n")
    
    results = []
    
    # 測試 1: 導入
    results.append(("模組導入", test_import()))
    
    # 測試 2: Widget 創建
    results.append(("Widget 創建", test_widget_creation()))
    
    # 測試 3: 模擬數據
    results.append(("模擬數據填充", test_mock_data()))
    
    # 總結
    print("\n" + "=" * 50)
    print("📊 測試總結:")
    print("=" * 50)
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"  {status}: {name}")
    
    all_passed = all(result[1] for result in results)
    print("=" * 50)
    if all_passed:
        print("🎉 所有測試通過!")
    else:
        print("⚠️  部分測試失敗，請檢查錯誤訊息")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
