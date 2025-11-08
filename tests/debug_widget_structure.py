"""
調試工具：檢查 MDI 視窗的實際 widget 結構
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QWidget, QVBoxLayout, QPushButton

def inspect_widget_tree(widget, indent=0, max_depth=5):
    """遞歸檢查 widget 樹"""
    if indent > max_depth:
        return
    
    prefix = "  " * indent
    class_name = widget.__class__.__name__
    print(f"{prefix}- {class_name}: {widget}")
    
    # 檢查是否有特殊屬性
    if hasattr(widget, 'data_manager'):
        print(f"{prefix}  ✅ 有 data_manager")
    if hasattr(widget, 'year'):
        print(f"{prefix}  ✅ 有 year 屬性")
    
    # 檢查 layout
    if hasattr(widget, 'layout') and widget.layout():
        layout = widget.layout()
        print(f"{prefix}  Layout: {layout.__class__.__name__} (items: {layout.count()})")
        for i in range(min(layout.count(), 3)):  # 只檢查前3個
            item = layout.itemAt(i)
            if item and item.widget():
                inspect_widget_tree(item.widget(), indent + 1, max_depth)
    
    # 檢查 children
    children = widget.children()
    if len(children) > 0 and indent < 2:
        print(f"{prefix}  Children: {len(children)} 個")
        for i, child in enumerate(children[:3]):  # 只檢查前3個
            if isinstance(child, QWidget):
                print(f"{prefix}  Child[{i}]: {child.__class__.__name__}")


if __name__ == "__main__":
    print("=" * 60)
    print("Widget 結構檢查工具")
    print("=" * 60)
    print("\n請在 F1T GUI 中：")
    print("1. 開啟 Rain Analysis")
    print("2. 在 Python Console 中執行：")
    print("   from debug_widget_structure import inspect_widget_tree")
    print("   mdi_area = main_window.tab_widget.widget(1)  # Tab 1")
    print("   subwindow = mdi_area.subWindowList()[0]")
    print("   inspect_widget_tree(subwindow.widget())")
    print("\n" + "=" * 60)
