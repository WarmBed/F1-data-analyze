"""
F1T GUI - 分頁架構 + 彈出功能 完整 DEMO
========================================

功能展示:
✅ 歡迎頁標籤 (永不移除)
✅ 動態創建分析標籤頁
✅ 每個標籤有獨立的 MDI 區域
✅ 標籤右鍵選單 (彈出/關閉)
✅ MDI 視窗彈出到獨立視窗
✅ 多螢幕支援

作者: F1T Team
日期: 2025-10-11
版本: 1.0.0 (完整 DEMO)
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMdiArea, QMdiSubWindow, QLabel, QPushButton, 
    QComboBox, QGroupBox, QMenu, QAction, QMessageBox, QTextEdit,
    QSplitter, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QPen, QBrush

# ============================================================================
# 核心組件 1: CustomMdiArea (從 f1t_gui_main.py 複製)
# ============================================================================

class CustomMdiArea(QMdiArea):
    """自定義 MDI 區域 - 支援右鍵選單和視窗管理"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setActivationOrder(QMdiArea.CreationOrder)
        self.setViewMode(QMdiArea.SubWindowView)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)
        
        # 設置背景顏色
        self.setStyleSheet("""
            CustomMdiArea {
                background-color: #F5F5F5;
            }
        """)
        print("[DEMO] CustomMdiArea 初始化完成")
    
    def contextMenuEvent(self, event):
        """右鍵選單"""
        menu = QMenu(self)
        
        # 視窗管理選項
        cascade_action = menu.addAction("🔲 層疊視窗")
        cascade_action.triggered.connect(self.cascadeSubWindows)
        
        tile_action = menu.addAction("⬜ 平舖視窗")
        tile_action.triggered.connect(self.tileSubWindows)
        
        menu.addSeparator()
        
        close_all_action = menu.addAction("❌ 關閉所有視窗")
        close_all_action.triggered.connect(self.closeAllSubWindows)
        
        menu.exec_(event.globalPos())
    
    def addSubWindow(self, widget, flags=None):
        """添加子視窗並應用樣式"""
        if flags is not None:
            subwindow = super().addSubWindow(widget, flags)
        else:
            subwindow = super().addSubWindow(widget)
        
        # 設置子視窗樣式 - 隱藏標題列但保留邊框
        if subwindow:
            subwindow.setStyleSheet("""
                QMdiSubWindow::title {
                    height: 0px;
                    margin: 0px;
                    padding: 0px;
                    background: transparent;
                    border: none;
                }
                QMdiSubWindow {
                    border: 2px solid #666666;
                    border-radius: 2px;
                    background-color: #FFFFFF;
                }
            """)
        
        return subwindow


# ============================================================================
# 核心組件 2: PopoutSubWindow (簡化版)
# ============================================================================

class PopoutSubWindow(QMdiSubWindow):
    """支援彈出功能的 MDI 子視窗 (DEMO 簡化版)"""
    
    resized = pyqtSignal()
    window_closed = pyqtSignal()
    
    def __init__(self, title="", parent_mdi=None, **kwargs):
        super().__init__()
        self.parent_mdi = parent_mdi
        self.is_popped_out = False
        self.standalone_window = None
        
        self.setWindowTitle(title)
        self.setObjectName("DemoSubWindow")
        
        print(f"[DEMO] PopoutSubWindow '{title}' 初始化完成")
    
    def pop_out(self):
        """彈出到獨立視窗"""
        if self.is_popped_out:
            print(f"[DEMO] '{self.windowTitle()}' 已經是獨立視窗")
            return
        
        print(f"[DEMO] 彈出視窗: {self.windowTitle()}")
        
        # 創建獨立視窗
        self.standalone_window = ResizableStandaloneWindow()
        self.standalone_window.setWindowTitle(f"🔓 {self.windowTitle()}")
        
        # 獲取內容 Widget
        content = self.widget()
        if content:
            # 從 MDI 子視窗移除
            self.setWidget(None)
            
            # 添加到獨立視窗
            self.standalone_window.setCentralWidget(content)
        
        # 設置視窗尺寸和位置
        geometry = self.geometry()
        self.standalone_window.setGeometry(
            geometry.x() + 100,  # 偏移以避免完全重疊
            geometry.y() + 100,
            max(geometry.width(), 600),
            max(geometry.height(), 400)
        )
        
        # 顯示獨立視窗
        self.standalone_window.show()
        
        # 隱藏 MDI 子視窗
        self.hide()
        
        self.is_popped_out = True
        print(f"[DEMO] ✅ '{self.windowTitle()}' 已彈出為獨立視窗")
    
    def pop_back_in(self):
        """彈回 MDI 區域"""
        if not self.is_popped_out or not self.standalone_window:
            print(f"[DEMO] '{self.windowTitle()}' 不是獨立視窗")
            return
        
        print(f"[DEMO] 彈回視窗: {self.windowTitle()}")
        
        # 獲取內容 Widget
        content = self.standalone_window.centralWidget()
        if content:
            # 從獨立視窗移除
            self.standalone_window.setCentralWidget(None)
            
            # 添加回 MDI 子視窗
            self.setWidget(content)
        
        # 關閉獨立視窗
        self.standalone_window.close()
        self.standalone_window = None
        
        # 顯示 MDI 子視窗
        self.show()
        
        self.is_popped_out = False
        print(f"[DEMO] ✅ '{self.windowTitle()}' 已彈回 MDI 區域")
    
    def toggle_popout(self):
        """切換彈出狀態"""
        if self.is_popped_out:
            self.pop_back_in()
        else:
            self.pop_out()


# ============================================================================
# 核心組件 3: ResizableStandaloneWindow (簡化版)
# ============================================================================

class ResizableStandaloneWindow(QMainWindow):
    """可調整大小的獨立視窗 (DEMO 簡化版)"""
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.resize_margin = 10
        self.resizing = False
        self.resize_direction = None
        
        # 設置樣式
        self.setStyleSheet("""
            QMainWindow {
                border: 2px solid #CCCCCC;
                background-color: #FFFFFF;
            }
            QMainWindow:hover {
                border: 2px solid #999999;
            }
        """)
        
        print("[DEMO] ResizableStandaloneWindow 初始化完成")
    
    def mousePressEvent(self, event):
        """滑鼠按下"""
        if event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """滑鼠移動"""
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            event.accept()
            return
        
        # 更新游標
        direction = self.get_resize_direction(event.pos())
        if direction:
            if direction in ['bottom']:
                self.setCursor(Qt.SizeVerCursor)
            elif direction in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif direction in ['bottom-right']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif direction in ['bottom-left']:
                self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """滑鼠釋放"""
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def get_resize_direction(self, pos):
        """判斷調整方向"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        margin = self.resize_margin
        
        # 角落區域
        if x <= margin and y >= h - margin:
            return 'bottom-left'
        elif x >= w - margin and y >= h - margin:
            return 'bottom-right'
        # 邊緣區域
        elif y >= h - margin:
            return 'bottom'
        elif x <= margin:
            return 'left'
        elif x >= w - margin:
            return 'right'
        
        return None
    
    def perform_resize(self, global_pos):
        """執行調整大小"""
        if not self.resize_direction:
            return
        
        delta = global_pos - self.resize_start_pos
        old_geometry = self.resize_start_geometry
        
        new_x = old_geometry.x()
        new_y = old_geometry.y()
        new_width = old_geometry.width()
        new_height = old_geometry.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geometry.x() + delta.x()
            new_width = old_geometry.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geometry.width() + delta.x()
        
        if 'bottom' in self.resize_direction:
            new_height = old_geometry.height() + delta.y()
        
        # 限制最小大小
        min_size = self.minimumSize()
        if new_width < min_size.width():
            if 'left' in self.resize_direction:
                new_x = old_geometry.x() + old_geometry.width() - min_size.width()
            new_width = min_size.width()
        
        if new_height < min_size.height():
            new_height = min_size.height()
        
        # 應用新的幾何形狀
        self.setGeometry(new_x, new_y, new_width, new_height)


# ============================================================================
# 示範組件: 簡單的分析模組
# ============================================================================

class DemoAnalysisModule(QWidget):
    """示範用的分析模組"""
    
    def __init__(self, module_name, color="#4CAF50"):
        super().__init__()
        self.module_name = module_name
        self.color = color
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title = QLabel(f"📊 {module_name}")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 18pt;
                font-weight: bold;
                color: {color};
                padding: 10px;
            }}
        """)
        layout.addWidget(title)
        
        # 說明文字
        description = QTextEdit()
        description.setReadOnly(True)
        description.setHtml(f"""
            <h3>🎯 {module_name} 模組</h3>
            <p>這是一個示範用的分析模組,用於測試分頁架構和彈出功能。</p>
            
            <h4>✨ 功能特點:</h4>
            <ul>
                <li>✅ 獨立的 MDI 工作區域</li>
                <li>✅ 支援彈出為獨立視窗</li>
                <li>✅ 多螢幕支援</li>
                <li>✅ 可調整視窗大小</li>
            </ul>
            
            <h4>🔧 測試操作:</h4>
            <ol>
                <li>在標籤頁上右鍵點擊,選擇 "🔓 彈出標籤為獨立視窗"</li>
                <li>在獨立視窗中工作</li>
                <li>完成後關閉獨立視窗,自動彈回標籤頁</li>
            </ol>
            
            <p style="color: {color}; font-weight: bold;">
                當前模組顏色: {color}
            </p>
        """)
        layout.addWidget(description)
        
        # 操作按鈕
        btn_layout = QHBoxLayout()
        
        add_window_btn = QPushButton("➕ 添加測試視窗")
        add_window_btn.clicked.connect(self.add_test_window)
        btn_layout.addWidget(add_window_btn)
        
        layout.addLayout(btn_layout)
    
    def add_test_window(self):
        """添加測試視窗到 MDI 區域"""
        # 尋找父級的 MDI 區域
        parent = self.parent()
        while parent:
            if isinstance(parent, QMdiArea):
                self._add_window_to_mdi(parent)
                return
            parent = parent.parent()
        
        QMessageBox.information(self, "提示", "未找到 MDI 區域")
    
    def _add_window_to_mdi(self, mdi_area):
        """添加測試視窗"""
        # 創建測試內容
        test_widget = QWidget()
        test_layout = QVBoxLayout(test_widget)
        
        label = QLabel(f"🧪 測試視窗\n來自 {self.module_name}")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            QLabel {{
                font-size: 14pt;
                color: {self.color};
                padding: 20px;
                background-color: #F5F5F5;
                border-radius: 5px;
            }}
        """)
        test_layout.addWidget(label)
        
        # 創建彈出子視窗
        sub_window = PopoutSubWindow(
            title=f"{self.module_name} - 測試視窗",
            parent_mdi=mdi_area
        )
        sub_window.setWidget(test_widget)
        
        # 添加到 MDI 區域
        mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        # 設置初始大小
        sub_window.resize(400, 300)
        
        print(f"[DEMO] 已添加測試視窗到 {self.module_name}")


# ============================================================================
# 歡迎頁組件
# ============================================================================

class WelcomeWidget(QWidget):
    """歡迎頁"""
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 標題
        title = QLabel("🏎️ F1T 分頁架構 DEMO")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 28pt;
                font-weight: bold;
                color: #E10600;
                padding: 20px;
            }
        """)
        layout.addWidget(title)
        
        # 說明區域
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 2px solid #DEE2E6;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        welcome_text = QTextEdit()
        welcome_text.setReadOnly(True)
        welcome_text.setHtml("""
            <h2 style="color: #E10600;">🎯 功能展示</h2>
            
            <h3>✅ 已實現的功能:</h3>
            <ul style="font-size: 11pt; line-height: 1.6;">
                <li><b>快速新增標籤頁</b> - 點擊 "➕ 新增標籤頁" 自動創建（分頁一、分頁二...）</li>
                <li><b>動態添加視窗</b> - 點擊頂部按鈕在當前標籤頁添加分析視窗</li>
                <li><b>智能處理</b> - 在歡迎頁點擊添加視窗會自動創建新標籤</li>
                <li><b>獨立 MDI 區域</b> - 每個標籤頁都有自己的 MDI 工作區域</li>
                <li><b>標籤彈出功能</b> - 右鍵點擊標籤可彈出為獨立視窗</li>
                <li><b>MDI 視窗彈出</b> - MDI 子視窗也可彈出為獨立視窗</li>
                <li><b>多螢幕支援</b> - 可將視窗拖拉到不同螢幕</li>
                <li><b>所有標籤可關閉</b> - 包括歡迎頁在內的所有標籤都可以關閉</li>
            </ul>
            
            <h3>🧪 快速上手:</h3>
            <ol style="font-size: 11pt; line-height: 1.6;">
                <li><b>創建工作區</b>: 點擊 "➕ 新增標籤頁"（自動命名為 "分頁一"）</li>
                <li><b>添加視窗</b>: 點擊頂部的分析按鈕（🌧️ 🏁 ⏱️ ⚡）</li>
                <li><b>繼續添加</b>: 在同一標籤頁中添加更多視窗</li>
                <li><b>創建更多標籤</b>: 需要時再點擊 "➕"（分頁二、分頁三...）</li>
                <li><b>管理視窗</b>: 右鍵點擊 MDI 區域 → 層疊/平舖視窗</li>
            </ol>
            
            <h3>💡 使用技巧:</h3>
            <ul style="font-size: 11pt; line-height: 1.6;">
                <li><b>快速開始</b>: 在歡迎頁直接點擊分析按鈕，自動創建標籤並添加視窗</li>
                <li><b>專案管理</b>: 用標籤頁組織不同的分析任務</li>
                <li><b>雙螢幕工作</b>: 彈出標籤到第二螢幕，提高效率</li>
                <li><b>整理空間</b>: 不需要的標籤可以直接關閉（包括歡迎頁）</li>
            </ul>
            
            <p style="color: #28A745; font-size: 12pt; font-weight: bold; margin-top: 20px;">
                ⚡ 點擊 "➕ 新增標籤頁" 或直接點擊分析按鈕開始！
            </p>
        """)
        info_layout.addWidget(welcome_text)
        
        layout.addWidget(info_frame)


# ============================================================================
# 主視窗
# ============================================================================

class DemoMainWindow(QMainWindow):
    """DEMO 主視窗 - 分頁架構 + 彈出功能"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1T GUI - 分頁架構 + 彈出功能 完整 DEMO")
        self.setGeometry(100, 100, 1200, 800)
        
        # 追蹤已創建的標籤頁
        self.analysis_tabs = {}  # {module_name: tab_index}
        self.tab_widgets = {}    # {tab_index: widget}
        self.tab_counter = 0     # 標籤頁計數器
        
        self._setup_ui()
        
        print("[DEMO] 主視窗初始化完成")
    
    def _setup_ui(self):
        """設置 UI"""
        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 頂部工具欄
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 標籤頁容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("AnalysisTabWidget")
        self.tab_widget.setTabsClosable(True)  # 允許關閉標籤
        self.tab_widget.setMovable(True)       # 允許拖拉標籤
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self._show_tab_context_menu)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        
        # 設置標籤頁樣式
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #CCCCCC;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #E10600;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #F5F5F5;
            }
        """)
        
        layout.addWidget(self.tab_widget)
        
        # 創建歡迎頁
        self._create_welcome_tab()
    
    def _create_toolbar(self):
        """創建工具欄"""
        toolbar = QFrame()
        toolbar.setFrameShape(QFrame.StyledPanel)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border-bottom: 2px solid #DEE2E6;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        
        # 標題
        title = QLabel("🏎️ F1T DEMO - 快速測試")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #E10600;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 新增：添加新標籤頁按鈕（直接創建，不顯示選單）
        add_tab_btn = QPushButton("➕ 新增標籤頁")
        add_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_tab_btn.clicked.connect(self.create_new_blank_tab)
        layout.addWidget(add_tab_btn)
        
        layout.addSpacing(20)
        
        # 快速添加視窗按鈕（添加到當前標籤頁）
        self._add_quick_button(layout, "🌧️ 降雨分析", "Rain Analysis", "#2196F3")
        self._add_quick_button(layout, "⏱️ 圈速分析", "Lap Analysis", "#4CAF50")
        self._add_quick_button(layout, "🏁 輪胎策略", "Tire Strategy", "#FF9800")
        self._add_quick_button(layout, "⚡ 遙測比較", "Telemetry Compare", "#9C27B0")
        
        return toolbar
    
    def _add_quick_button(self, layout, text, module_name, color):
        """添加快速添加視窗按鈕（添加到當前標籤頁）"""
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
        """)
        btn.clicked.connect(lambda: self.add_window_to_current_tab(module_name, color))
        layout.addWidget(btn)
    
    def _darken_color(self, color):
        """將顏色變暗"""
        qcolor = QColor(color)
        h, s, v, a = qcolor.getHsv()
        qcolor.setHsv(h, s, max(0, v - 30), a)
        return qcolor.name()
    
    def _create_welcome_tab(self):
        """創建歡迎頁標籤"""
        welcome_widget = WelcomeWidget()
        
        # 添加為第一個標籤頁
        index = self.tab_widget.addTab(welcome_widget, "🏠 歡迎")
        
        # 設置 objectName 用於識別
        self.tab_widget.widget(index).setObjectName("welcome_tab")
        
        # 歡迎頁現在可以關閉（移除特殊保護）
        # close_button = self.tab_widget.tabBar().tabButton(index, self.tab_widget.tabBar().RightSide)
        # if close_button:
        #     close_button.hide()
        
        print("[DEMO] ✅ 歡迎頁已創建 (可關閉)")
    
    def create_new_blank_tab(self):
        """創建新的空白標籤頁（自動命名：分頁一、分頁二...）"""
        self.tab_counter += 1
        tab_name = f"📋 分頁{self.tab_counter}"
        
        print(f"[DEMO] 創建空白標籤頁: {tab_name}")
        
        # 創建容器 Widget
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # 創建 MDI 區域
        mdi_area = CustomMdiArea()
        tab_layout.addWidget(mdi_area)
        
        # 添加標籤頁
        index = self.tab_widget.addTab(tab_container, tab_name)
        
        # 記錄標籤頁
        self.tab_widgets[index] = {
            'container': tab_container,
            'mdi_area': mdi_area,
            'module_name': tab_name,
            'is_popped_out': False,
            'standalone_window': None
        }
        
        # 切換到新標籤頁
        self.tab_widget.setCurrentIndex(index)
        
        print(f"[DEMO] ✅ 標籤頁 '{tab_name}' 已創建")
    
    def _show_add_tab_menu(self):
        """顯示添加標籤頁選單"""
        menu = QMenu(self)
        
        # 添加不同類型的標籤頁選項
        modules = [
            ("🌧️ 降雨分析", "Rain Analysis", "#2196F3"),
            ("⏱️ 圈速分析", "Lap Analysis", "#4CAF50"),
            ("🏁 輪胎策略", "Tire Strategy", "#FF9800"),
            ("⚡ 遙測比較", "Telemetry Compare", "#9C27B0"),
        ]
        
        for text, module_name, color in modules:
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, m=module_name, c=color: self.create_analysis_tab(m, c))
        
        # 在按鈕位置顯示選單
        menu.exec_(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def add_window_to_current_tab(self, module_name, color="#4CAF50"):
        """添加視窗到當前活動的標籤頁"""
        current_index = self.tab_widget.currentIndex()
        
        # 檢查是否是歡迎頁
        current_widget = self.tab_widget.widget(current_index)
        if current_widget and current_widget.objectName() == "welcome_tab":
            # 如果當前是歡迎頁，自動創建新標籤頁後再添加視窗
            self.create_new_blank_tab()
            # 遞迴調用，此時當前標籤已經是新建的空白標籤
            self.add_window_to_current_tab(module_name, color)
            return
        
        # 獲取當前標籤頁的數據
        tab_data = self.tab_widgets.get(current_index)
        if not tab_data:
            QMessageBox.warning(
                self,
                "錯誤",
                "無法獲取當前標籤頁資訊！"
            )
            return
        
        mdi_area = tab_data.get('mdi_area')
        if not mdi_area:
            QMessageBox.warning(
                self,
                "錯誤",
                "當前標籤頁沒有 MDI 區域！"
            )
            return
        
        print(f"[DEMO] 在當前標籤頁添加視窗: {module_name}")
        
        # 創建分析模組
        analysis_module = DemoAnalysisModule(module_name, color)
        sub_window = PopoutSubWindow(
            title=f"{module_name} - 視窗 #{mdi_area.subWindowList().__len__() + 1}",
            parent_mdi=mdi_area
        )
        sub_window.setWidget(analysis_module)
        
        # 添加到當前 MDI 區域
        mdi_area.addSubWindow(sub_window)
        sub_window.show()
        sub_window.resize(500, 350)
        
        # 層疊排列（讓新視窗稍微偏移）
        existing_windows = mdi_area.subWindowList()
        if len(existing_windows) > 1:
            offset = (len(existing_windows) - 1) * 30
            sub_window.move(offset, offset)
        
        print(f"[DEMO] ✅ 已添加 '{module_name}' 到當前標籤頁")
    
    def create_analysis_tab(self, module_name, color="#4CAF50"):
        """創建分析標籤頁"""
        # 檢查是否已存在
        if module_name in self.analysis_tabs:
            existing_index = self.analysis_tabs[module_name]
            self.tab_widget.setCurrentIndex(existing_index)
            print(f"[DEMO] 標籤頁 '{module_name}' 已存在,切換到該頁")
            return
        
        print(f"[DEMO] 創建分析標籤頁: {module_name}")
        
        # 創建容器 Widget
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # 創建 MDI 區域
        mdi_area = CustomMdiArea()
        tab_layout.addWidget(mdi_area)
        
        # 創建分析模組並添加到 MDI
        analysis_module = DemoAnalysisModule(module_name, color)
        sub_window = PopoutSubWindow(
            title=f"{module_name} - 主視窗",
            parent_mdi=mdi_area
        )
        sub_window.setWidget(analysis_module)
        
        mdi_area.addSubWindow(sub_window)
        sub_window.show()
        sub_window.resize(600, 400)
        
        # 添加標籤頁
        tab_icon = self._get_module_icon(module_name)
        tab_text = f"{tab_icon} {module_name}"
        index = self.tab_widget.addTab(tab_container, tab_text)
        
        # 記錄標籤頁
        self.analysis_tabs[module_name] = index
        self.tab_widgets[index] = {
            'container': tab_container,
            'mdi_area': mdi_area,
            'module_name': module_name,
            'is_popped_out': False,
            'standalone_window': None
        }
        
        # 切換到新標籤頁
        self.tab_widget.setCurrentIndex(index)
        
        print(f"[DEMO] ✅ 標籤頁 '{module_name}' 已創建")
    
    def _get_module_icon(self, module_name):
        """獲取模組圖標"""
        icon_map = {
            "Rain Analysis": "🌧️",
            "Lap Analysis": "⏱️",
            "Tire Strategy": "🏁",
            "Telemetry Compare": "⚡"
        }
        return icon_map.get(module_name, "📊")
    
    def _show_tab_context_menu(self, position):
        """顯示標籤右鍵選單"""
        # 獲取點擊的標籤索引
        tab_bar = self.tab_widget.tabBar()
        index = tab_bar.tabAt(position)
        
        if index < 0:
            return
        
        # 檢查是否是歡迎頁
        widget = self.tab_widget.widget(index)
        if widget and widget.objectName() == "welcome_tab":
            print("[DEMO] 歡迎頁不支援右鍵選單")
            return
        
        # 創建右鍵選單
        menu = QMenu(self)
        
        # 檢查是否已彈出
        tab_data = self.tab_widgets.get(index, {})
        is_popped = tab_data.get('is_popped_out', False)
        
        if is_popped:
            pop_in_action = menu.addAction("🔒 彈回標籤頁")
            pop_in_action.triggered.connect(lambda: self._pop_tab_back_in(index))
        else:
            pop_out_action = menu.addAction("🔓 彈出為獨立視窗")
            pop_out_action.triggered.connect(lambda: self._pop_tab_out(index))
        
        menu.addSeparator()
        
        close_action = menu.addAction("❌ 關閉標籤頁")
        close_action.triggered.connect(lambda: self._close_tab(index))
        
        # 顯示選單
        menu.exec_(tab_bar.mapToGlobal(position))
    
    def _pop_tab_out(self, index):
        """彈出標籤頁為獨立視窗"""
        if index not in self.tab_widgets:
            return
        
        tab_data = self.tab_widgets[index]
        if tab_data.get('is_popped_out', False):
            print(f"[DEMO] 標籤頁已經是獨立視窗")
            return
        
        module_name = tab_data['module_name']
        print(f"[DEMO] 彈出標籤頁: {module_name}")
        
        # 創建獨立視窗
        standalone = ResizableStandaloneWindow()
        standalone.setWindowTitle(f"🔓 {module_name}")
        standalone.setMinimumSize(600, 400)
        
        # 獲取容器 Widget
        container = tab_data['container']
        
        # 從標籤頁移除
        self.tab_widget.removeTab(index)
        
        # 添加到獨立視窗
        standalone.setCentralWidget(container)
        
        # 設置視窗位置和大小
        standalone.setGeometry(200, 200, 800, 600)
        standalone.show()
        
        # 更新狀態
        tab_data['is_popped_out'] = True
        tab_data['standalone_window'] = standalone
        
        # 連接關閉信號
        standalone.destroyed.connect(lambda: self._on_standalone_closed(index))
        
        print(f"[DEMO] ✅ 標籤頁 '{module_name}' 已彈出為獨立視窗")
    
    def _pop_tab_back_in(self, index):
        """彈回標籤頁"""
        if index not in self.tab_widgets:
            return
        
        tab_data = self.tab_widgets[index]
        if not tab_data.get('is_popped_out', False):
            print(f"[DEMO] 標籤頁不是獨立視窗")
            return
        
        module_name = tab_data['module_name']
        print(f"[DEMO] 彈回標籤頁: {module_name}")
        
        # 獲取獨立視窗和容器
        standalone = tab_data.get('standalone_window')
        if not standalone:
            return
        
        container = standalone.centralWidget()
        if not container:
            return
        
        # 從獨立視窗移除
        standalone.setCentralWidget(None)
        
        # 添加回標籤頁
        icon = self._get_module_icon(module_name)
        tab_text = f"{icon} {module_name}"
        new_index = self.tab_widget.addTab(container, tab_text)
        
        # 關閉獨立視窗
        standalone.close()
        
        # 更新狀態
        tab_data['is_popped_out'] = False
        tab_data['standalone_window'] = None
        
        # 更新索引記錄
        self.analysis_tabs[module_name] = new_index
        self.tab_widgets[new_index] = tab_data
        if new_index != index:
            del self.tab_widgets[index]
        
        # 切換到新標籤頁
        self.tab_widget.setCurrentIndex(new_index)
        
        print(f"[DEMO] ✅ 標籤頁 '{module_name}' 已彈回")
    
    def _on_standalone_closed(self, index):
        """獨立視窗被關閉時自動彈回"""
        print(f"[DEMO] 獨立視窗被關閉,自動彈回標籤頁")
        # 使用 QTimer 延遲處理,避免在銷毀過程中操作
        QTimer.singleShot(100, lambda: self._pop_tab_back_in(index))
    
    def _close_tab(self, index):
        """關閉標籤頁"""
        # 移除歡迎頁的特殊保護 - 所有標籤頁都可以關閉
        # widget = self.tab_widget.widget(index)
        # if widget and widget.objectName() == "welcome_tab":
        #     QMessageBox.information(
        #         self,
        #         "提示",
        #         "歡迎頁不能關閉！\n\n這是分頁架構的核心特性之一。"
        #     )
        #     return
        
        # 獲取模組名稱
        if index in self.tab_widgets:
            tab_data = self.tab_widgets[index]
            module_name = tab_data['module_name']
            
            # 如果是彈出狀態,先關閉獨立視窗
            if tab_data.get('is_popped_out', False):
                standalone = tab_data.get('standalone_window')
                if standalone:
                    standalone.close()
            
            # 移除記錄
            del self.tab_widgets[index]
            del self.analysis_tabs[module_name]
            
            print(f"[DEMO] 關閉標籤頁: {module_name}")
        
        # 移除標籤頁
        self.tab_widget.removeTab(index)


# ============================================================================
# 主程式入口
# ============================================================================

def main():
    """主程式"""
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyle("Fusion")
    
    # 創建主視窗
    window = DemoMainWindow()
    window.show()
    
    print("\n" + "="*60)
    print("🏎️  F1T GUI - 分頁架構 + 彈出功能 完整 DEMO")
    print("="*60)
    print("\n📋 測試指南:")
    print("  1. 點擊頂部按鈕創建分析標籤頁")
    print("  2. 右鍵點擊標籤可彈出為獨立視窗")
    print("  3. 在 MDI 區域內添加子視窗測試")
    print("  4. 嘗試關閉歡迎頁 (會被阻止)")
    print("  5. 測試多螢幕拖拉功能")
    print("\n✨ 開始測試吧！\n")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
