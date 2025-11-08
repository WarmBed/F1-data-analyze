#!/usr/bin/env python3
"""
啟動畫面 GUI 啟動測試
測試完整的 GUI 啟動流程（包含啟動畫面）
此測試會實際啟動 GUI 並自動關閉
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 確保可以導入模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui_startup_with_splash():
    """測試帶啟動畫面的 GUI 啟動"""
    print("=" * 60)
    print("啟動畫面 GUI 啟動測試")
    print("=" * 60)
    
    print("\n[測試] 導入主程式模組...")
    try:
        # 模擬 main() 函數的啟動流程
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtGui import QFont
        from PyQt5.QtCore import QTimer
        
        print("✅ PyQt5 模組導入成功")
        
        from modules.gui.splash_screen import create_splash_screen
        from core.gui_i18n import tr, get_gui_language
        
        print("✅ 啟動畫面模組導入成功")
        print(f"✅ 當前語言: {get_gui_language()}")
        
    except ImportError as e:
        print(f"❌ 模組導入失敗: {e}")
        return False
    
    print("\n[測試] 創建應用程式...")
    app = QApplication(sys.argv)
    
    app.setApplicationName("F1T Professional Racing Analysis Workstation")
    app.setOrganizationName("F1T Professional Racing Analysis Team")
    
    font = QFont("Arial", 8)
    app.setFont(font)
    
    app.setQuitOnLastWindowClosed(True)
    print("✅ QApplication 創建成功")
    
    print("\n[測試] 創建啟動畫面...")
    splash = create_splash_screen(2)  # Version 2: 白底黑字
    splash.show()
    app.processEvents()
    print("✅ 啟動畫面顯示成功")
    
    # 模擬進度更新
    print("\n[測試] 模擬初始化進度...")
    
    progress_updates = [
        (0, tr('splash_initializing')),
        (10, tr('splash_loading_window')),
        (20, tr('splash_loading_state')),
        (30, tr('splash_loading_calendar')),
        (40, tr('splash_loading_colors')),
        (55, tr('splash_loading_ui')),
        (70, tr('splash_applying_style')),
        (85, tr('splash_setup_linkage')),
        (95, tr('splash_setup_api')),
        (100, tr('splash_complete'))
    ]
    
    for i, (progress, message) in enumerate(progress_updates):
        splash.set_progress(progress, message)
        app.processEvents()
        print(f"  [{i+1}/10] {progress}%: {message}")
        QTimer.singleShot(200 * (i + 1), lambda: None)
    
    print("✅ 進度更新完成")
    
    # 嘗試導入主視窗（但不實際創建）
    print("\n[測試] 驗證主視窗模組...")
    try:
        # 檢查 StyleHMainWindow 是否接受 progress_callback 參數
        import inspect
        from f1t_gui_main import StyleHMainWindow
        
        sig = inspect.signature(StyleHMainWindow.__init__)
        params = list(sig.parameters.keys())
        
        print(f"  StyleHMainWindow.__init__ 參數: {params}")
        
        if 'progress_callback' in params:
            print("✅ progress_callback 參數已添加")
        else:
            print("❌ progress_callback 參數缺失")
            return False
            
    except Exception as e:
        print(f"❌ 主視窗模組驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[測試] 3秒後自動關閉...")
    QTimer.singleShot(3000, splash.close)
    QTimer.singleShot(3500, app.quit)
    
    # 執行應用程式（會自動關閉）
    app.exec_()
    
    print("\n✅ 所有測試通過")
    return True

if __name__ == "__main__":
    try:
        success = test_gui_startup_with_splash()
        print("\n" + "=" * 60)
        if success:
            print("✅ 啟動畫面整合測試成功")
            sys.exit(0)
        else:
            print("❌ 啟動畫面整合測試失敗")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
