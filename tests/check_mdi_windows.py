"""
檢查當前 MDI 區域中有多少視窗
"""
import sys
from PyQt5.QtWidgets import QApplication

def check_mdi_windows():
    """檢查所有 MDI 視窗"""
    app = QApplication.instance()
    if not app:
        print("❌ GUI 未運行")
        return
    
    # 找到主視窗
    main_window = None
    for widget in app.topLevelWidgets():
        if widget.objectName() == "F1TelemetryStation":
            main_window = widget
            break
    
    if not main_window:
        print("❌ 找不到主視窗")
        return
    
    print(f"✅ 找到主視窗: {main_window.windowTitle()}")
    
    # 檢查所有分頁
    tab_widget = main_window.tab_widget
    print(f"\n📊 分頁總數: {tab_widget.count()}")
    
    total_windows = 0
    for i in range(tab_widget.count()):
        tab_name = tab_widget.tabText(i)
        widget = tab_widget.widget(i)
        
        print(f"\n📑 分頁 [{i}]: {tab_name}")
        print(f"   - Widget 類型: {type(widget).__name__}")
        
        if hasattr(widget, 'subWindowList'):
            subwindows = widget.subWindowList()
            print(f"   - MDI 視窗數量: {len(subwindows)}")
            total_windows += len(subwindows)
            
            for j, subwin in enumerate(subwindows):
                title = subwin.windowTitle()
                visible = subwin.isVisible()
                size = subwin.size()
                pos = subwin.pos()
                
                print(f"      [{j+1}] '{title}'")
                print(f"          - 可見: {visible}")
                print(f"          - 尺寸: {size.width()}x{size.height()}")
                print(f"          - 位置: ({pos.x()}, {pos.y()})")
                print(f"          - 類型: {type(subwin).__name__}")
    
    print(f"\n🎯 總計: {total_windows} 個 MDI 視窗")

if __name__ == "__main__":
    check_mdi_windows()
