"""
測試性能監控視窗是否正常顯示
"""

from PyQt5.QtWidgets import QApplication
import sys

# 確保使用現有的 QApplication
app = QApplication.instance()
if app is None:
    print("❌ QApplication 不存在")
    sys.exit(1)

print("✅ QApplication 存在")

# 嘗試打開監控視窗
try:
    from performance_monitor_widget import show_monitor
    print("\n開始打開性能監控視窗...")
    window = show_monitor()
    
    if window:
        print(f"\n視窗狀態:")
        print(f"  - 可見: {window.isVisible()}")
        print(f"  - 標題: {window.windowTitle()}")
        print(f"  - 位置: ({window.x()}, {window.y()})")
        print(f"  - 大小: {window.width()}x{window.height()}")
        print(f"  - 最小化: {window.isMinimized()}")
        print(f"  - 最大化: {window.isMaximized()}")
        
        # 列出所有頂層視窗
        print(f"\n所有頂層視窗:")
        for widget in app.topLevelWidgets():
            if widget.isVisible():
                print(f"  - {widget.windowTitle()} ({widget.__class__.__name__})")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
