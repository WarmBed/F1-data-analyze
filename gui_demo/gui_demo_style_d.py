#!/usr/bin/env python3
"""
F1T GUI Demo - 風格D: 專業F1分析工作站風格
Demo for Style D: Professional F1 Analysis Workstation
融合深色主題、高信息密度與專業分析工具設計
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame, QToolBar, QAction, QMenuBar, QMenu, QGridLayout, QLCDNumber,
    QTextEdit, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

class F1AnalysisWidget(QWidget):
    """F1專業分析小部件"""
    
    def __init__(self, title, content_type="table"):
        super().__init__()
        self.setObjectName("F1AnalysisWidget")
        self.init_widget(title, content_type)
        
    def init_widget(self, title, content_type):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 標題欄
        title_frame = QFrame()
        title_frame.setObjectName("WidgetTitle")
        title_frame.setFixedHeight(22)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(6, 2, 6, 2)
        
        title_label = QLabel(title)
        title_label.setObjectName("TitleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 控制按鈕
        expand_btn = QPushButton("□")
        expand_btn.setFixedSize(16, 16)
        close_btn = QPushButton("×")
        close_btn.setFixedSize(16, 16)
        title_layout.addWidget(expand_btn)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_frame)
        
        # 內容區域
        if content_type == "table":
            content = self.create_data_table()
        elif content_type == "monitor":
            content = self.create_system_monitor()
        elif content_type == "telemetry":
            content = self.create_telemetry_display()
        else:
            content = QLabel("數據載入中...")
            
        layout.addWidget(content)
        
    def create_data_table(self):
        """創建數據表格"""
        table = QTableWidget(8, 6)
        table.setObjectName("F1DataTable")
        table.setHorizontalHeaderLabels(["位置", "車手", "時間", "差距", "輪胎", "狀態"])
        
        # F1數據
        data = [
            ["1", "VER", "1:22.456", "-", "SOFT", "🟢"],
            ["2", "LEC", "1:22.789", "+0.333", "SOFT", "🟢"],
            ["3", "HAM", "1:23.123", "+0.667", "MED", "🟡"],
            ["4", "RUS", "1:23.456", "+1.000", "MED", "🟡"],
            ["5", "NOR", "1:23.789", "+1.333", "HARD", "🔴"],
            ["6", "PIA", "1:24.123", "+1.667", "HARD", "🔴"],
            ["7", "SAI", "1:24.456", "+2.000", "SOFT", "🟢"],
            ["8", "ALO", "1:24.789", "+2.333", "MED", "🟡"]
        ]
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                # 位置著色
                if col == 0:
                    pos = int(value)
                    if pos <= 3:
                        item.setBackground(QColor("#2E7D32"))  # 綠色
                    elif pos <= 10:
                        item.setBackground(QColor("#1976D2"))  # 藍色
                    else:
                        item.setBackground(QColor("#424242"))  # 灰色
                    item.setForeground(Qt.white)
                table.setItem(row, col, item)
                
        table.resizeColumnsToContents()
        return table
        
    def create_system_monitor(self):
        """創建系統監控面板"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(4)
        
        # CPU監控
        cpu_frame = QFrame()
        cpu_frame.setObjectName("MonitorFrame")
        cpu_layout = QVBoxLayout(cpu_frame)
        cpu_layout.addWidget(QLabel("CPU使用率"))
        cpu_lcd = QLCDNumber(2)
        cpu_lcd.setObjectName("SystemLCD")
        cpu_lcd.display(45)
        cpu_layout.addWidget(cpu_lcd)
        cpu_layout.addWidget(QLabel("45%"))
        
        # 記憶體監控
        mem_frame = QFrame()
        mem_frame.setObjectName("MonitorFrame")
        mem_layout = QVBoxLayout(mem_frame)
        mem_layout.addWidget(QLabel("記憶體"))
        mem_lcd = QLCDNumber(3)
        mem_lcd.setObjectName("SystemLCD")
        mem_lcd.display(2.1)
        mem_layout.addWidget(mem_lcd)
        mem_layout.addWidget(QLabel("2.1GB"))
        
        # 網路監控
        net_frame = QFrame()
        net_frame.setObjectName("MonitorFrame")
        net_layout = QVBoxLayout(net_frame)
        net_layout.addWidget(QLabel("網路速度"))
        net_lcd = QLCDNumber(3)
        net_lcd.setObjectName("SystemLCD")
        net_lcd.display(1.2)
        net_layout.addWidget(net_lcd)
        net_layout.addWidget(QLabel("1.2MB/s"))
        
        layout.addWidget(cpu_frame, 0, 0)
        layout.addWidget(mem_frame, 0, 1)
        layout.addWidget(net_frame, 1, 0, 1, 2)
        
        return widget
        
    def create_telemetry_display(self):
        """創建遙測數據顯示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 遙測數據表格
        table = QTableWidget(6, 4)
        table.setObjectName("F1DataTable")
        table.setHorizontalHeaderLabels(["參數", "當前值", "最大值", "狀態"])
        
        telemetry_data = [
            ["速度", "312 km/h", "334 km/h", "🟢"],
            ["引擎轉速", "11,500 RPM", "12,000 RPM", "🟡"],
            ["輪胎溫度", "95°C", "110°C", "🟢"],
            ["煞車溫度", "680°C", "750°C", "🟡"],
            ["DRS", "開啟", "-", "🟢"],
            ["ERS", "充電中", "-", "🔴"]
        ]
        
        for row, row_data in enumerate(telemetry_data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                table.setItem(row, col, item)
                
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        return widget

class StyleDMainWindow(QMainWindow):
    """風格D: 專業F1分析工作站主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏎️ F1 Professional Analysis Workstation v5.5 - Style D")
        self.setMinimumSize(1400, 900)
        self.init_ui()
        self.apply_style_d()
        
    def init_ui(self):
        """初始化用戶界面"""
        # 創建工具欄
        self.create_professional_toolbar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)
        
        # 參數控制區
        param_frame = self.create_professional_parameter_panel()
        main_layout.addWidget(param_frame)
        
        # 主工作區 - 三段式分割
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # 左側功能和監控面板
        left_panel = self.create_left_control_panel()
        content_splitter.addWidget(left_panel)
        
        # 中央分析工作區
        center_panel = self.create_center_analysis_workspace()
        content_splitter.addWidget(center_panel)
        
        # 右側數據和圖表面板
        right_panel = self.create_right_data_panel()
        content_splitter.addWidget(right_panel)
        
        # 設置分割比例 - 專業分析布局
        content_splitter.setSizes([250, 800, 350])
        main_layout.addWidget(content_splitter)
        
        # 專業狀態列
        self.create_professional_status_bar()
        
    def create_professional_toolbar(self):
        """創建專業工具欄"""
        toolbar = QToolBar()
        toolbar.setObjectName("ProfessionalToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        # 分析工具
        toolbar.addAction("🏁 新建分析", self.new_analysis)
        toolbar.addAction("📂 載入數據", self.load_data)
        toolbar.addAction("💾 保存結果", self.save_results)
        toolbar.addSeparator()
        
        # 執行控制
        toolbar.addAction("▶️ 執行", self.run_analysis)
        toolbar.addAction("⏸️ 暫停", self.pause_analysis)
        toolbar.addAction("⏹️ 停止", self.stop_analysis)
        toolbar.addSeparator()
        
        # 專業工具
        toolbar.addAction("📊 數據視覺化", self.data_visualization)
        toolbar.addAction("🔄 即時更新", self.real_time_update)
        toolbar.addAction("🎯 精確分析", self.precision_analysis)
        
    def create_professional_parameter_panel(self):
        """創建專業參數面板"""
        frame = QFrame()
        frame.setObjectName("ProfessionalParameterFrame")
        frame.setFixedHeight(60)
        
        layout = QGridLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # 第一行 - 基本參數
        layout.addWidget(QLabel("賽季:"), 0, 0)
        year_combo = QComboBox()
        year_combo.addItems(["2024", "2025"])
        year_combo.setCurrentText("2025")
        year_combo.setFixedSize(70, 24)
        layout.addWidget(year_combo, 0, 1)
        
        layout.addWidget(QLabel("大獎賽:"), 0, 2)
        race_combo = QComboBox()
        race_combo.addItems(["Japan", "Singapore", "Las Vegas", "Qatar", "Abu Dhabi"])
        race_combo.setCurrentText("Japan")
        race_combo.setFixedSize(100, 24)
        layout.addWidget(race_combo, 0, 3)
        
        layout.addWidget(QLabel("賽段:"), 0, 4)
        session_combo = QComboBox()
        session_combo.addItems(["Race", "Qualifying", "FP1", "FP2", "FP3", "Sprint"])
        session_combo.setCurrentText("Race")
        session_combo.setFixedSize(80, 24)
        layout.addWidget(session_combo, 0, 5)
        
        # 第二行 - 分析參數
        layout.addWidget(QLabel("主車手:"), 1, 0)
        driver1_combo = QComboBox()
        driver1_combo.addItems(["VER", "LEC", "HAM", "RUS", "NOR", "PIA", "SAI", "ALO"])
        driver1_combo.setCurrentText("VER")
        driver1_combo.setFixedSize(70, 24)
        layout.addWidget(driver1_combo, 1, 1)
        
        layout.addWidget(QLabel("比較車手:"), 1, 2)
        driver2_combo = QComboBox()
        driver2_combo.addItems(["LEC", "VER", "HAM", "RUS", "NOR", "PIA", "SAI", "ALO"])
        driver2_combo.setCurrentText("LEC")
        driver2_combo.setFixedSize(70, 24)
        layout.addWidget(driver2_combo, 1, 3)
        
        # 系統控制
        realtime_cb = QCheckBox("即時更新")
        realtime_cb.setChecked(True)
        layout.addWidget(realtime_cb, 1, 4)
        
        advanced_cb = QCheckBox("進階模式")
        layout.addWidget(advanced_cb, 1, 5)
        
        # 操作按鈕
        execute_btn = QPushButton("🚀 執行分析")
        execute_btn.setFixedSize(90, 24)
        layout.addWidget(execute_btn, 0, 6, 2, 1)
        
        return frame
        
    def create_left_control_panel(self):
        """創建左側控制面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 功能模組區域
        modules_widget = F1AnalysisWidget("分析模組", "tree")
        modules_content = QWidget()
        modules_layout = QVBoxLayout(modules_content)
        
        # 搜尋框
        search_box = QLineEdit()
        search_box.setPlaceholderText("🔍 搜尋分析功能...")
        search_box.setFixedHeight(24)
        modules_layout.addWidget(search_box)
        
        # 功能樹
        tree = QTreeWidget()
        tree.setObjectName("ProfessionalTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(12)
        
        # 即時監控
        monitor = QTreeWidgetItem(tree, ["📊 即時監控"])
        monitor.setExpanded(True)
        QTreeWidgetItem(monitor, ["🏁 比賽狀態"])
        QTreeWidgetItem(monitor, ["🚗 車手位置"])
        QTreeWidgetItem(monitor, ["⏱️ 圈速監控"])
        QTreeWidgetItem(monitor, ["🛞 輪胎狀況"])
        
        # 基礎分析
        basic = QTreeWidgetItem(tree, ["📋 基礎分析"])
        basic.setExpanded(True)
        QTreeWidgetItem(basic, ["🌧️ 降雨強度分析"])
        QTreeWidgetItem(basic, ["🛣️ 賽道分析"])
        QTreeWidgetItem(basic, ["🏆 進站分析"])
        QTreeWidgetItem(basic, ["📈 位置變化"])
        
        # 進階分析
        advanced = QTreeWidgetItem(tree, ["🔬 進階分析"])
        advanced.setExpanded(True)
        QTreeWidgetItem(advanced, ["📡 車手遙測"])
        QTreeWidgetItem(advanced, ["🤝 雙車手比較"])
        QTreeWidgetItem(advanced, ["🎯 彎道分析"])
        QTreeWidgetItem(advanced, ["📊 策略分析"])
        
        modules_layout.addWidget(tree)
        
        # 替換原來的內容
        modules_widget.layout().removeItem(modules_widget.layout().itemAt(1))
        modules_widget.layout().addWidget(modules_content)
        
        layout.addWidget(modules_widget)
        
        # 系統監控區域
        monitor_widget = F1AnalysisWidget("系統監控", "monitor")
        layout.addWidget(monitor_widget)
        
        return widget
        
    def create_center_analysis_workspace(self):
        """創建中央分析工作區"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 工作區標題
        title_frame = QFrame()
        title_frame.setObjectName("WorkspaceTitle")
        title_frame.setFixedHeight(28)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(8, 4, 8, 4)
        
        title_label = QLabel("🏎️ 主要分析工作區")
        title_label.setObjectName("WorkspaceTitleLabel")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 工作區控制
        layout_btn = QPushButton("佈局")
        layout_btn.setFixedSize(50, 20)
        window_btn = QPushButton("視窗")
        window_btn.setFixedSize(50, 20)
        
        title_layout.addWidget(layout_btn)
        title_layout.addWidget(window_btn)
        
        layout.addWidget(title_frame)
        
        # 分頁式工作區
        tab_widget = QTabWidget()
        tab_widget.setObjectName("ProfessionalTabs")
        tab_widget.setTabsClosable(True)
        tab_widget.setMovable(True)
        
        # 主分析頁面
        main_tab = QWidget()
        main_layout = QGridLayout(main_tab)
        main_layout.setSpacing(2)
        
        # 添加多個分析小部件
        pos_widget = F1AnalysisWidget("車手位置分析", "table")
        main_layout.addWidget(pos_widget, 0, 0)
        
        lap_widget = F1AnalysisWidget("圈速比較", "table")
        main_layout.addWidget(lap_widget, 0, 1)
        
        telemetry_widget = F1AnalysisWidget("遙測數據", "telemetry")
        main_layout.addWidget(telemetry_widget, 1, 0, 1, 2)
        
        tab_widget.addTab(main_tab, "🏁 主要分析")
        
        # 比較分析頁面
        compare_tab = QWidget()
        compare_layout = QVBoxLayout(compare_tab)
        
        # 比較分析內容
        compare_widget = F1AnalysisWidget("VER vs LEC 比較分析", "table")
        compare_layout.addWidget(compare_widget)
        
        tab_widget.addTab(compare_tab, "🤝 車手比較")
        
        # 即時監控頁面
        live_tab = QWidget()
        live_layout = QGridLayout(live_tab)
        
        # 即時數據小部件
        live_positions = F1AnalysisWidget("即時位置", "table")
        live_layout.addWidget(live_positions, 0, 0)
        
        live_timing = F1AnalysisWidget("即時計時", "table")
        live_layout.addWidget(live_timing, 0, 1)
        
        tab_widget.addTab(live_tab, "📡 即時監控")
        
        layout.addWidget(tab_widget)
        
        return widget
        
    def create_right_data_panel(self):
        """創建右側數據面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 數據摘要
        summary_widget = F1AnalysisWidget("數據摘要", "table")
        layout.addWidget(summary_widget, 1)
        
        # 圖表區域
        chart_widget = F1AnalysisWidget("圖表視覺化", "table")
        layout.addWidget(chart_widget, 2)
        
        # 日誌和狀態
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(2, 2, 2, 2)
        
        # 日誌標題
        log_title = QFrame()
        log_title.setObjectName("WidgetTitle")
        log_title.setFixedHeight(22)
        log_title_layout = QHBoxLayout(log_title)
        log_title_layout.setContentsMargins(6, 2, 6, 2)
        log_title_layout.addWidget(QLabel("系統日誌"))
        log_layout.addWidget(log_title)
        
        # 日誌內容
        log_text = QTextEdit()
        log_text.setObjectName("LogDisplay")
        log_text.setMaximumHeight(120)
        log_text.setPlainText("""[13:28:45] INFO: 降雨分析模組載入完成
[13:28:44] DEBUG: FastF1 快取命中: Japan_2025_Race
[13:28:43] WARN: API回應時間: 2.3秒
[13:28:42] INFO: 開始執行車手比較分析
[13:28:41] INFO: 連接F1數據源成功
[13:28:40] DEBUG: 系統初始化完成""")
        log_layout.addWidget(log_text)
        
        layout.addWidget(log_widget, 1)
        
        return widget
        
    def create_professional_status_bar(self):
        """創建專業狀態列"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 狀態指標
        connection_label = QLabel("🟢 數據連線正常")
        cache_label = QLabel("💾 快取: 256MB")
        api_label = QLabel("📡 API: 健康")
        cpu_label = QLabel("⚙️ CPU: 45%")
        analysis_label = QLabel("📊 分析: 就緒")
        
        # 分隔符
        def create_separator():
            sep = QLabel(" | ")
            sep.setObjectName("StatusSeparator")
            return sep
        
        status_bar.addWidget(connection_label)
        status_bar.addWidget(create_separator())
        status_bar.addWidget(cache_label)
        status_bar.addWidget(create_separator())
        status_bar.addWidget(api_label)
        status_bar.addWidget(create_separator())
        status_bar.addWidget(cpu_label)
        status_bar.addWidget(create_separator())
        status_bar.addWidget(analysis_label)
        
        # 時間戳
        time_label = QLabel("🕒 2025-08-25 13:28:45")
        time_label.setObjectName("TimeStamp")
        status_bar.addPermanentWidget(time_label)
        
    # 事件處理方法
    def new_analysis(self): print("新建分析")
    def load_data(self): print("載入數據")
    def save_results(self): print("保存結果")
    def run_analysis(self): print("執行分析")
    def pause_analysis(self): print("暫停分析")
    def stop_analysis(self): print("停止分析")
    def data_visualization(self): print("數據視覺化")
    def real_time_update(self): print("即時更新")
    def precision_analysis(self): print("精確分析")
        
    def apply_style_d(self):
        """應用風格D樣式 - 專業F1分析工作站風格"""
        style = """
        /* 主視窗 - 深色專業主題 */
        QMainWindow {
            background-color: #1A1A1A;
            color: #FFFFFF;
            font-family: "Segoe UI", "Arial", sans-serif;
            font-size: 9pt;
        }
        
        /* 專業工具欄 */
        #ProfessionalToolbar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2C2C2C, stop:1 #1E1E1E);
            border-bottom: 1px solid #404040;
            color: #FFFFFF;
            font-size: 9pt;
            spacing: 3px;
        }
        #ProfessionalToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 4px 8px;
            margin: 1px;
            color: #FFFFFF;
        }
        #ProfessionalToolbar QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #404040, stop:1 #2C2C2C);
            border: 1px solid #505050;
        }
        #ProfessionalToolbar QToolButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #1E1E1E, stop:1 #0E0E0E);
        }
        
        /* 專業參數面板 */
        #ProfessionalParameterFrame {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2A2A2A, stop:1 #1F1F1F);
            border: 1px solid #404040;
            border-radius: 4px;
        }
        
        /* 下拉選單 - F1風格 */
        QComboBox {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #3A3A3A, stop:1 #2A2A2A);
            border: 1px solid #505050;
            border-radius: 3px;
            padding: 2px 6px;
            color: #FFFFFF;
            font-weight: bold;
        }
        QComboBox:hover {
            border-color: #0078D4;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #4A4A4A, stop:1 #3A3A3A);
        }
        QComboBox:focus {
            border-color: #00BCF2;
            border-width: 2px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
            background: #404040;
        }
        QComboBox::down-arrow {
            image: none;
            border: 1px solid #606060;
            background: #505050;
            width: 8px;
            height: 6px;
        }
        QComboBox QAbstractItemView {
            background: #2A2A2A;
            border: 1px solid #505050;
            color: #FFFFFF;
            selection-background-color: #0078D4;
        }
        
        /* 按鈕 - F1專業風格 */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #0078D4, stop:1 #005A9E);
            border: 1px solid #0060B6;
            border-radius: 3px;
            color: white;
            font-weight: bold;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #1084DA, stop:1 #0066A4);
            border-color: #0066BC;
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #005A9E, stop:1 #004578);
        }
        
        /* 搜尋框 */
        QLineEdit {
            background: #2A2A2A;
            border: 1px solid #505050;
            border-radius: 3px;
            padding: 4px 8px;
            color: #FFFFFF;
        }
        QLineEdit:focus {
            border-color: #00BCF2;
            border-width: 2px;
        }
        QLineEdit::placeholder {
            color: #808080;
        }
        
        /* 功能樹 - 專業風格 */
        #ProfessionalTree {
            background: #1E1E1E;
            border: 1px solid #404040;
            color: #FFFFFF;
            outline: none;
            font-size: 9pt;
        }
        #ProfessionalTree::item {
            height: 22px;
            border: none;
            padding: 2px 4px;
        }
        #ProfessionalTree::item:hover {
            background: #2A2A2A;
            border: 1px solid #404040;
        }
        #ProfessionalTree::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #0078D4, stop:1 #005A9E);
            color: white;
        }
        
        /* 專業分頁 */
        #ProfessionalTabs::pane {
            border: 1px solid #404040;
            background: #1A1A1A;
        }
        #ProfessionalTabs QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2C2C2C, stop:1 #1E1E1E);
            border: 1px solid #404040;
            border-radius: 4px 4px 0 0;
            padding: 6px 12px;
            margin-right: 2px;
            color: #CCCCCC;
            font-weight: bold;
        }
        #ProfessionalTabs QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #0078D4, stop:1 #005A9E);
            color: white;
            border-bottom: none;
        }
        #ProfessionalTabs QTabBar::tab:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #3C3C3C, stop:1 #2E2E2E);
            color: white;
        }
        
        /* F1分析小部件 */
        #F1AnalysisWidget {
            background: #1E1E1E;
            border: 1px solid #404040;
            border-radius: 4px;
        }
        
        /* 小部件標題 */
        #WidgetTitle {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2C2C2C, stop:1 #1E1E1E);
            border-bottom: 1px solid #404040;
            border-radius: 4px 4px 0 0;
        }
        #TitleLabel {
            color: #FFFFFF;
            font-weight: bold;
            font-size: 9pt;
        }
        
        /* 工作區標題 */
        #WorkspaceTitle {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2A2A2A, stop:1 #1F1F1F);
            border: 1px solid #404040;
            border-radius: 4px;
        }
        #WorkspaceTitleLabel {
            color: #00BCF2;
            font-weight: bold;
            font-size: 10pt;
        }
        
        /* F1數據表格 */
        #F1DataTable {
            background: #1A1A1A;
            border: 1px solid #404040;
            gridline-color: #2A2A2A;
            color: #FFFFFF;
            font-size: 8pt;
        }
        #F1DataTable QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2C2C2C, stop:1 #1E1E1E);
            border: 1px solid #404040;
            color: #FFFFFF;
            font-weight: bold;
            padding: 4px;
        }
        #F1DataTable::item {
            padding: 2px;
            border: none;
        }
        #F1DataTable::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #0078D4, stop:1 #005A9E);
            color: white;
        }
        
        /* 監控框架 */
        #MonitorFrame {
            background: #1E1E1E;
            border: 1px solid #404040;
            border-radius: 3px;
            padding: 4px;
        }
        
        /* 系統LCD顯示 */
        #SystemLCD {
            background: #000000;
            border: 1px solid #404040;
            color: #00FF00;
            border-radius: 2px;
        }
        
        /* 日誌顯示 */
        #LogDisplay {
            background: #0A0A0A;
            border: 1px solid #404040;
            color: #CCCCCC;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 8pt;
        }
        
        /* 狀態列 - 專業風格 */
        QStatusBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2A2A2A, stop:1 #1F1F1F);
            border-top: 1px solid #404040;
            color: #CCCCCC;
            font-size: 8pt;
        }
        #StatusSeparator {
            color: #606060;
        }
        #TimeStamp {
            color: #00BCF2;
            font-weight: bold;
        }
        
        /* CheckBox - F1風格 */
        QCheckBox {
            color: #FFFFFF;
            font-size: 9pt;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #505050;
            border-radius: 2px;
            background: #2A2A2A;
        }
        QCheckBox::indicator:checked {
            background: #0078D4;
            border-color: #005A9E;
            image: none;
        }
        QCheckBox::indicator:checked::after {
            content: "✓";
            color: white;
            font-weight: bold;
        }
        QCheckBox::indicator:hover {
            border-color: #00BCF2;
        }
        
        /* 標籤 */
        QLabel {
            color: #FFFFFF;
        }
        
        /* 滾動條 */
        QScrollBar:vertical {
            background: #2A2A2A;
            width: 12px;
            border: 1px solid #404040;
        }
        QScrollBar::handle:vertical {
            background: #505050;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #606060;
        }
        """
        
        self.setStyleSheet(style)

def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setApplicationName("F1T GUI Demo - Style D")
    app.setOrganizationName("F1T Professional Analysis Team")
    
    # 設置應用程式字體
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # 創建主視窗
    window = StyleDMainWindow()
    window.show()
    
    # 顯示歡迎訊息
    print("🏎️ F1T GUI Demo - 風格D (專業F1分析工作站) 已啟動")
    print("📊 這是一個融合深色主題和高信息密度的專業分析界面")
    print("🔧 包含完整的F1專業分析工具功能")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
