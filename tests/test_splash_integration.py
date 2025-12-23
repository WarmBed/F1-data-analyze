#!/usr/bin/env python3
"""
啟動畫面整合測試腳本
測試啟動畫面與 GUI 主視窗的整合是否正常工作
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

def test_splash_integration():
    """測試啟動畫面整合"""
    print("=" * 60)
    print("啟動畫面整合測試")
    print("=" * 60)
    
    # 測試 1: 導入檢查
    print("\n[測試 1] 檢查模組導入...")
    try:
        from modules.gui.splash_screen import create_splash_screen
        from core.gui_i18n import tr, get_gui_language
        print("✅ 模組導入成功")
    except ImportError as e:
        print(f"❌ 模組導入失敗: {e}")
        return False
    
    # 測試 2: 翻譯鍵檢查
    print("\n[測試 2] 檢查翻譯鍵是否存在...")
    translation_keys = [
        'splash_initializing',
        'splash_loading_window',
        'splash_loading_state',
        'splash_loading_calendar',
        'splash_loading_colors',
        'splash_loading_ui',
        'splash_applying_style',
        'splash_setup_linkage',
        'splash_setup_api',
        'splash_complete',
        'splash_error_continue',
        'splash_error_opening',
        'error_initialization_failed',
        'error_init_message'
    ]
    
    missing_keys = []
    for key in translation_keys:
        translation = tr(key)
        if translation == key:  # 如果翻譯鍵不存在，會返回鍵本身
            # 再檢查一次，因為有些鍵可能剛好翻譯成自己
            from core.gui_i18n import _gui_translator
            if key not in _gui_translator._translations:
                missing_keys.append(key)
        print(f"  {key}: {translation}")
    
    if missing_keys:
        print(f"❌ 缺少翻譯鍵: {missing_keys}")
        return False
    print("✅ 所有翻譯鍵存在")
    
    # 測試 3: 啟動畫面創建測試
    print("\n[測試 3] 測試啟動畫面創建...")
    app = QApplication(sys.argv)
    
    try:
        splash = create_splash_screen(2)  # Version 2
        splash.show()
        print("✅ 啟動畫面創建成功")
        
        # 模擬進度更新
        print("\n[測試 4] 模擬進度更新...")
        progress_points = [
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
        
        for i, (progress, message) in enumerate(progress_points):
            splash.set_progress(progress, message)
            app.processEvents()
            print(f"  [{i+1}/10] {progress}%: {message}")
            QTimer.singleShot(200 * (i + 1), lambda: None)  # 延遲
        
        print("✅ 進度更新測試通過")
        
        # 3秒後關閉
        QTimer.singleShot(3000, splash.close)
        QTimer.singleShot(3500, app.quit)
        
        app.exec_()
        
        print("\n✅ 啟動畫面整合測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 啟動畫面測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("測試語言:", end=" ")
    from core.gui_i18n import get_gui_language
    print(get_gui_language())
    
    success = test_splash_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有測試通過")
        sys.exit(0)
    else:
        print("❌ 測試失敗")
        sys.exit(1)
