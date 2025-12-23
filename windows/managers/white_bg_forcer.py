# -*- coding: utf-8 -*-
"""
WhiteBgForcer - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtGui import QPalette

logger = get_logger(__name__)


class WhiteBgForcer:
    """從 f1t_gui_main.py 提取的 force_white_background 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def force_white_background(self, mdi_area):
        """深度修復QMdiArea背景問題 - 設定為白色"""
        #print(f"[DESIGN] DEBUG: force_white_background called for {mdi_area.objectName()}")
        
        # 方法1: 設置調色板
        mdi_area.setAutoFillBackground(True)
        palette = mdi_area.palette()
        palette.setColor(QPalette.Background, QColor(245, 245, 245))
        palette.setColor(QPalette.Base, QColor(245, 245, 245))
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        mdi_area.setPalette(palette)
        #print(f"[OK] Palette set for {mdi_area.objectName()}")
        
        # 方法2: 直接設置背景畫筆
        mdi_area.setBackground(QBrush(QColor(245, 245, 245)))
        #print(f"[OK] Background brush set for {mdi_area.objectName()}")
        
        # 方法3: 設置viewport背景（QMdiArea內部使用QScrollArea）
        def fix_viewport():
            try:
                #print(f"[TOOL] Fixing viewport for {mdi_area.objectName()}")
                # 查找內部的viewport小部件
                child_count = 0
                for child in mdi_area.findChildren(QWidget):
                    # 排除 Live Timing 模組及其子 widget (使用 property 識別)
                    if child.property("is_live_timing_widget"):
                        continue
                    # 向上查找父層是否為 Live Timing widget
                    parent = child.parent()
                    is_live_timing_child = False
                    while parent:
                        if parent.property("is_live_timing_widget"):
                            is_live_timing_child = True
                            break
                        parent = parent.parent()
                    if is_live_timing_child:
                        continue
                        
                    if hasattr(child, 'setAutoFillBackground'):
                        child.setAutoFillBackground(True)
                        child_palette = child.palette()
                        child_palette.setColor(QPalette.Background, QColor(245, 245, 245))
                        child_palette.setColor(QPalette.Base, QColor(245, 245, 245))
                        child_palette.setColor(QPalette.Window, QColor(245, 245, 245))
                        child.setPalette(child_palette)
                        child_count += 1
                        
                #print(f"[PACKAGE] Fixed {child_count} child widgets")
                        
                # 特別處理viewport
                if hasattr(mdi_area, 'viewport'):
                    viewport = mdi_area.viewport()
                    if viewport:
                        viewport.setAutoFillBackground(True)
                        viewport_palette = viewport.palette()
                        viewport_palette.setColor(QPalette.Background, QColor(245, 245, 245))
                        viewport_palette.setColor(QPalette.Base, QColor(245, 245, 245))
                        viewport_palette.setColor(QPalette.Window, QColor(245, 245, 245))
                        viewport.setPalette(viewport_palette)
                        
                # 強制重繪整個MDI區域
                mdi_area.repaint()
            except:
                pass  # 忽略任何錯誤，繼續其他修復方法
        
        # 延遲執行viewport修復（等MDI完全初始化）
        QTimer.singleShot(100, fix_viewport)
        QTimer.singleShot(200, fix_viewport)  # 再次執行確保修復
        
        # 方法4: 強制內聯樣式
        mdi_area.setStyleSheet(f"""
            QMdiArea#{mdi_area.objectName()} {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea QWidget {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} > QWidget {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
        """)
        
        # 方法5: 創建白色背景小部件覆蓋（終極方案）
        def create_white_overlay():
            try:
                # 創建一個白色背景小部件作為底層
                overlay = QWidget(mdi_area)
                overlay.setStyleSheet("background-color: #F5F5F5;")
                overlay.setGeometry(mdi_area.rect())
                overlay.lower()  # 放到最底層
                overlay.show()
                
                # 連接resize事件，確保覆蓋層始終填滿MDI區域
                def resize_overlay():
                    if overlay and not overlay.isHidden():
                        overlay.setGeometry(mdi_area.rect())
                
                mdi_area.resizeEvent = lambda event: (
                    QMdiArea.resizeEvent(mdi_area, event),
                    resize_overlay()
                )[-1]
                
            except:
                pass
        
        # 延遲創建覆蓋層
        QTimer.singleShot(300, create_white_overlay)
