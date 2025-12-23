#!/usr/bin/env python3
"""測試 PartsAnalysisMDI 初始化"""

import sys
from PyQt5.QtWidgets import QApplication

# 創建 QApplication（必須）
app = QApplication(sys.argv)

try:
    from modules.gui.partupdated_analysis.parts_analysis_mdi import PartsAnalysisMDI
    
    print("=" * 60)
    print("測試 PartsAnalysisMDI 初始化")
    print("=" * 60)
    
    # 創建 MDI 實例
    print("\n步驟 1: 創建 PartsAnalysisMDI 實例...")
    mdi = PartsAnalysisMDI(parent=None)
    print("✅ PartsAnalysisMDI 實例創建成功")
    
    # 設置參數提供者
    class FakeProvider:
        def get_current_year(self):
            return 2025
    
    print("\n步驟 2: 設置參數提供者...")
    mdi.parameter_provider = FakeProvider()
    mdi.year = "2025"
    print("✅ 參數提供者設置成功")
    
    # 初始化模組
    print("\n步驟 3: 調用 initialize_module()...")
    result = mdi.initialize_module(parent_widget=None)
    print(f"✅ initialize_module() 返回: {result}")
    
    # 檢查 parts_widget
    print("\n步驟 4: 檢查 parts_widget...")
    widget = mdi.get_widget()
    print(f"✅ get_widget() 返回: {widget}")
    print(f"   類型: {type(widget)}")
    
    if widget:
        print("\n✅✅✅ 所有測試通過！")
    else:
        print("\n❌ parts_widget 為 None")
    
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
