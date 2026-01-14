#!/usr/bin/env python3
"""測試 PedalBehaviorAnalysisMDI 創建"""
import sys
import traceback

print("=" * 60)
print("測試 PedalBehaviorAnalysisMDI")
print("=" * 60)

try:
    print("\n1. 創建 QApplication...")
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    print("   OK")
    
    print("\n2. 導入 PedalBehaviorAnalysisMDI...")
    from modules.gui.lap_analysis.pedal_behavior_analysis.pedal_behavior_analysis_mdi import PedalBehaviorAnalysisMDI
    print("   OK")
    
    print("\n3. 創建實例...")
    mdi = PedalBehaviorAnalysisMDI(year=2025, race="Japan", session="R")
    print("   OK")
    
    print("\n4. 獲取 widget...")
    widget = mdi.get_widget()
    print(f"   OK - Widget: {widget}")
    
    print("\n5. 獲取標題...")
    title = mdi.get_title()
    print(f"   OK - Title: {title}")
    
    print("\n" + "=" * 60)
    print("所有測試通過!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n錯誤: {e}")
    traceback.print_exc()
    sys.exit(1)
