#!/usr/bin/env python3
"""
F1T GUI Demo - 風格C: 90年代復古專業風格
Demo for Style C: 90s Retro Professional Design
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame, QToolBar, QAction, QMenuBar, QMenu
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

class StyleCMainWindow(QMainWindow):
    """風格C: 90年代復古專業主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Analysis Professional Workstation v5.5 - Style C")
        self.setMinimumSize(1200, 800)
        self.init_ui()
        self.apply_style_c()
        
    def init_ui(self):
        """初始化用戶界面"""
        # 創建菜單欄
        self.create_menu_bar()
        
        # 創建工具欄
        self.create_toolbar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 緊湊間距
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)
        
        # 參數控制區 - 緊湊設計
        param_frame = self.create_compact_parameter_panel()
        main_layout.addWidget(param_frame)
        
        # 主工作區
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # 左側功能面板 - 緊湊版
        left_panel = self.create_compact_function_panel()
        content_splitter.addWidget(left_panel)
        
        # 右側工作區 - 緊湊版
        right_panel = self.create_compact_workspace()
        content_splitter.addWidget(right_panel)
        
        # 設置分割比例 - 更多空間給工作區
        content_splitter.setSizes([280, 920])
        main_layout.addWidget(content_splitter)
        
        # 狀態列 - 緊湊信息
        self.create_compact_status_bar()
        
    def create_menu_bar(self):
        """創建90年代風格菜單欄"""
        menubar = self.menuBar()
        
        # 檔案菜單
        file_menu = menubar.addMenu('檔案(&F)')
        file_menu.addAction('新建分析(&N)', self.new_analysis)
        file_menu.addAction('開啟檔案(&O)', self.open_file)
        file_menu.addAction('儲存結果(&S)', self.save_results)
        file_menu.addSeparator()
        file_menu.addAction('離開(&X)', self.close)
        
        # 分析菜單
        analysis_menu = menubar.addMenu('分析(&A)')
        analysis_menu.addAction('執行分析(&R)', self.run_analysis)
        analysis_menu.addAction('批次處理(&B)', self.batch_process)
        analysis_menu.addAction('停止處理(&S)', self.stop_process)
        
        # 工具菜單
        tools_menu = menubar.addMenu('工具(&T)')
        tools_menu.addAction('清除快取(&C)', self.clear_cache)
        tools_menu.addAction('系統診斷(&D)', self.system_diagnostic)
        tools_menu.addAction('效能監控(&P)', self.performance_monitor)
        
        # 說明菜單
        help_menu = menubar.addMenu('說明(&H)')
        help_menu.addAction('關於(&A)', self.about)
        
    def create_toolbar(self):
        """創建90年代風格工具欄"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        self.addToolBar(toolbar)
        
        # 工具按鈕
        toolbar.addAction('新建', self.new_analysis)
        toolbar.addAction('開啟', self.open_file)
        toolbar.addAction('儲存', self.save_results)
        toolbar.addSeparator()
        toolbar.addAction('執行', self.run_analysis)
        toolbar.addAction('停止', self.stop_process)
        toolbar.addSeparator()
        toolbar.addAction('清快取', self.clear_cache)
        
    def create_compact_parameter_panel(self):
        """創建緊湊參數面板"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        frame.setObjectName("ParameterFrame")
        frame.setFixedHeight(50)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)
        
        # 參數組1 - 基本設定
        layout.addWidget(QLabel("年份:"))
        year_combo = QComboBox()
        year_combo.addItems(["2024", "2025"])
        year_combo.setCurrentText("2025")
        year_combo.setFixedSize(65, 22)
        layout.addWidget(year_combo)
        
        layout.addWidget(QLabel("賽事:"))
        race_combo = QComboBox()
        race_combo.addItems(["Japan", "Singapore", "Las Vegas", "Qatar", "Abu Dhabi"])
        race_combo.setCurrentText("Japan")
        race_combo.setFixedSize(85, 22)
        layout.addWidget(race_combo)
        
        layout.addWidget(QLabel("賽段:"))
        session_combo = QComboBox()
        session_combo.addItems(["R", "Q", "FP1", "FP2", "FP3", "S"])
        session_combo.setCurrentText("R")
        session_combo.setFixedSize(45, 22)
        layout.addWidget(session_combo)
        
        # 分隔線
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # 系統控制
        link_cb = QCheckBox("聯動")
        link_cb.setChecked(True)
        layout.addWidget(link_cb)
        
        debug_cb = QCheckBox("偵錯")
        layout.addWidget(debug_cb)
        
        # 分隔線
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        # 操作按鈕
        exec_btn = QPushButton("執行")
        exec_btn.setFixedSize(50, 22)
        layout.addWidget(exec_btn)
        
        batch_btn = QPushButton("批次")
        batch_btn.setFixedSize(50, 22)
        layout.addWidget(batch_btn)
        
        stop_btn = QPushButton("停止")
        stop_btn.setFixedSize(50, 22)
        layout.addWidget(stop_btn)
        
        cache_btn = QPushButton("清快取")
        cache_btn.setFixedSize(55, 22)
        layout.addWidget(cache_btn)
        
        layout.addStretch()
        
        # 狀態指示器
        status_label = QLabel("就緒")
        status_label.setObjectName("StatusIndicator")
        layout.addWidget(status_label)
        
        return frame
        
    def create_compact_function_panel(self):
        """創建緊湊功能面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # 標題欄
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        title_frame.setFixedHeight(24)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(4, 2, 4, 2)
        title_label = QLabel("功能模組")
        title_label.setObjectName("PanelTitle")
        title_layout.addWidget(title_label)
        layout.addWidget(title_frame)
        
        # 搜尋框
        search_box = QLineEdit()
        search_box.setPlaceholderText("搜尋...")
        search_box.setFixedHeight(20)
        layout.addWidget(search_box)
        
        # 篩選按鈕組
        filter_frame = QFrame()
        filter_frame.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(2, 2, 2, 2)
        filter_layout.setSpacing(2)
        
        all_btn = QPushButton("全部")
        all_btn.setFixedSize(35, 18)
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        
        fav_btn = QPushButton("收藏")
        fav_btn.setFixedSize(35, 18)
        fav_btn.setCheckable(True)
        
        recent_btn = QPushButton("最近")
        recent_btn.setFixedSize(35, 18)
        recent_btn.setCheckable(True)
        
        filter_layout.addWidget(all_btn)
        filter_layout.addWidget(fav_btn)
        filter_layout.addWidget(recent_btn)
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)
        
        # 功能樹 - 緊湊版
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setObjectName("FunctionTree")
        tree.setIndentation(15)
        tree.setRootIsDecorated(True)
        
        # 系統監控 (折疊)
        monitor = QTreeWidgetItem(tree, ["系統監控"])
        QTreeWidgetItem(monitor, ["CPU: 45%"])
        QTreeWidgetItem(monitor, ["RAM: 2.1GB"])
        QTreeWidgetItem(monitor, ["快取: 156MB"])
        
        # 快速存取
        quick = QTreeWidgetItem(tree, ["快速存取"])
        quick.setExpanded(True)
        QTreeWidgetItem(quick, ["車手最快進站"])
        QTreeWidgetItem(quick, ["雙車手比較"])
        QTreeWidgetItem(quick, ["動態彎道檢測"])
        
        # 基礎分析
        basic = QTreeWidgetItem(tree, ["基礎分析"])
        basic.setExpanded(True)
        rain_item = QTreeWidgetItem(basic, ["降雨強度分析"])
        rain_item.setData(0, Qt.UserRole, "rain_intensity")
        
        track_item = QTreeWidgetItem(basic, ["賽道路線分析"])
        track_item.setData(0, Qt.UserRole, "track_analysis")
        
        pitstop_item = QTreeWidgetItem(basic, ["最快進站分析"])
        pitstop_item.setData(0, Qt.UserRole, "fastest_pitstop")
        
        team_item = QTreeWidgetItem(basic, ["車隊進站排行"])
        team_item.setData(0, Qt.UserRole, "team_pitstop")
        
        detail_item = QTreeWidgetItem(basic, ["進站詳細記錄"])
        detail_item.setData(0, Qt.UserRole, "pitstop_details")
        
        # 進階分析
        advanced = QTreeWidgetItem(tree, ["進階分析"])
        advanced.setExpanded(True)
        telemetry_item = QTreeWidgetItem(advanced, ["車手詳細遙測"])
        telemetry_item.setData(0, Qt.UserRole, "telemetry")
        
        compare_item = QTreeWidgetItem(advanced, ["雙車手比較"])
        compare_item.setData(0, Qt.UserRole, "driver_comparison")
        
        corner_item = QTreeWidgetItem(advanced, ["動態彎道檢測"])
        corner_item.setData(0, Qt.UserRole, "corner_detection")
        
        position_item = QTreeWidgetItem(advanced, ["位置變化分析"])
        position_item.setData(0, Qt.UserRole, "position_analysis")
        
        # 系統工具
        system = QTreeWidgetItem(tree, ["系統工具"])
        QTreeWidgetItem(system, ["數據導出"])
        QTreeWidgetItem(system, ["快取管理"])
        QTreeWidgetItem(system, ["系統診斷"])
        QTreeWidgetItem(system, ["效能監控"])
        
        layout.addWidget(tree)
        
        # 添加點擊事件
        tree.itemClicked.connect(self.on_tree_item_clicked)
        
        return widget
        
    def create_compact_workspace(self):
        """創建緊湊工作區"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # 標題欄
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        title_frame.setFixedHeight(24)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(4, 2, 4, 2)
        title_label = QLabel("分析工作區")
        title_label.setObjectName("PanelTitle")
        title_layout.addWidget(title_label)
        
        # 工作區控制按鈕
        new_tab_btn = QPushButton("新分頁")
        new_tab_btn.setFixedSize(50, 18)
        
        close_tab_btn = QPushButton("關閉")
        close_tab_btn.setFixedSize(40, 18)
        
        title_layout.addStretch()
        title_layout.addWidget(new_tab_btn)
        title_layout.addWidget(close_tab_btn)
        
        layout.addWidget(title_frame)
        
        # 分頁容器 - 緊湊版
        tab_widget = QTabWidget()
        tab_widget.setObjectName("CompactTabs")
        tab_widget.setTabsClosable(True)
        tab_widget.setMovable(True)
        
        # 第一個分頁 - 降雨分析
        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setContentsMargins(2, 2, 2, 2)
        tab1_layout.setSpacing(2)
        
        # 數據表格
        data_table = self.create_compact_data_table()
        tab1_layout.addWidget(data_table)
        
        tab_widget.addTab(tab1_widget, "降雨分析")
        
        # 第二個分頁 - 車手比較
        tab2_widget = QWidget()
        tab2_layout = QVBoxLayout(tab2_widget)
        tab2_layout.setContentsMargins(2, 2, 2, 2)
        
        # 比較表格
        compare_table = self.create_comparison_table()
        tab2_layout.addWidget(compare_table)
        
        tab_widget.addTab(tab2_widget, "車手比較")
        
        # 第三個分頁 - 系統監控
        tab3_widget = self.create_system_monitor()
        tab_widget.addTab(tab3_widget, "系統監控")
        
        layout.addWidget(tab_widget)
        
        return widget
        
    def create_compact_data_table(self):
        """創建緊湊數據表格"""
        table = QTableWidget(12, 6)
        table.setObjectName("DataTable")
        table.setHorizontalHeaderLabels(["時間", "強度", "狀況", "溫度", "濕度", "狀態"])
        
        # 緊湊數據 - 更多行
        data = [
            ["13:23:45", "HIGH", "濕滑", "18.5", "85%", "警告"],
            ["13:24:12", "MED", "潮濕", "19.2", "78%", "正常"],
            ["13:24:38", "LOW", "乾燥", "20.1", "65%", "正常"],
            ["13:25:05", "NONE", "乾燥", "21.0", "55%", "正常"],
            ["13:25:32", "MED", "潮濕", "19.8", "72%", "正常"],
            ["13:26:01", "HIGH", "濕滑", "18.1", "88%", "警告"],
            ["13:26:28", "EXTM", "積水", "17.5", "95%", "危險"],
            ["13:26:55", "LOW", "乾燥中", "19.5", "68%", "正常"],
            ["13:27:22", "NONE", "乾燥", "21.2", "58%", "正常"],
            ["13:27:49", "LOW", "微濕", "20.8", "62%", "正常"],
            ["13:28:16", "MED", "潮濕", "19.9", "75%", "注意"],
            ["13:28:43", "HIGH", "濕滑", "18.8", "82%", "警告"]
        ]
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                # 狀態著色
                if col == 5:  # 狀態欄
                    if value == "危險":
                        item.setBackground(Qt.red)
                        item.setForeground(Qt.white)
                    elif value == "警告":
                        item.setBackground(Qt.yellow)
                    elif value == "注意":
                        item.setBackground(Qt.cyan)
                table.setItem(row, col, item)
                
        # 調整欄位寬度
        table.resizeColumnsToContents()
        
        return table
        
    def create_comparison_table(self):
        """創建車手比較表格"""
        table = QTableWidget(10, 5)
        table.setObjectName("DataTable")
        table.setHorizontalHeaderLabels(["圈數", "VER時間", "LEC時間", "差距", "狀態"])
        
        # 比較數據
        data = [
            ["1", "1:22.456", "1:22.789", "+0.333", "VER領先"],
            ["2", "1:21.892", "1:22.134", "+0.242", "VER領先"],
            ["3", "1:22.045", "1:21.987", "-0.058", "LEC領先"],
            ["4", "1:21.756", "1:22.211", "+0.455", "VER領先"],
            ["5", "1:22.134", "1:22.098", "-0.036", "LEC領先"],
            ["6", "1:21.645", "1:22.456", "+0.811", "VER領先"],
            ["7", "1:22.234", "1:22.187", "-0.047", "LEC領先"],
            ["8", "1:21.934", "1:22.345", "+0.411", "VER領先"],
            ["9", "1:22.076", "1:22.198", "+0.122", "VER領先"],
            ["10", "1:21.798", "1:22.089", "+0.291", "VER領先"]
        ]
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                # 差距著色
                if col == 3:  # 差距欄
                    if value.startswith("-"):
                        item.setBackground(Qt.green)
                    elif float(value.replace("+", "")) > 0.3:
                        item.setBackground(Qt.lightGray)
                table.setItem(row, col, item)
                
        table.resizeColumnsToContents()
        return table
        
    def create_system_monitor(self):
        """創建系統監控面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # 資源監控框架
        resource_frame = QFrame()
        resource_frame.setFrameStyle(QFrame.StyledPanel)
        resource_layout = QHBoxLayout(resource_frame)
        resource_layout.setContentsMargins(4, 4, 4, 4)
        resource_layout.setSpacing(4)
        
        # CPU監控
        cpu_frame = QFrame()
        cpu_frame.setFrameStyle(QFrame.Box)
        cpu_layout = QVBoxLayout(cpu_frame)
        cpu_layout.setContentsMargins(4, 2, 4, 2)
        cpu_layout.addWidget(QLabel("CPU"))
        cpu_progress = QProgressBar()
        cpu_progress.setValue(45)
        cpu_progress.setFixedHeight(16)
        cpu_layout.addWidget(cpu_progress)
        cpu_layout.addWidget(QLabel("45%"))
        
        # 記憶體監控
        mem_frame = QFrame()
        mem_frame.setFrameStyle(QFrame.Box)
        mem_layout = QVBoxLayout(mem_frame)
        mem_layout.setContentsMargins(4, 2, 4, 2)
        mem_layout.addWidget(QLabel("記憶體"))
        mem_progress = QProgressBar()
        mem_progress.setValue(67)
        mem_progress.setFixedHeight(16)
        mem_layout.addWidget(mem_progress)
        mem_layout.addWidget(QLabel("2.1GB"))
        
        # 網路監控
        net_frame = QFrame()
        net_frame.setFrameStyle(QFrame.Box)
        net_layout = QVBoxLayout(net_frame)
        net_layout.setContentsMargins(4, 2, 4, 2)
        net_layout.addWidget(QLabel("網路"))
        net_progress = QProgressBar()
        net_progress.setValue(23)
        net_progress.setFixedHeight(16)
        net_layout.addWidget(net_progress)
        net_layout.addWidget(QLabel("1.2MB/s"))
        
        resource_layout.addWidget(cpu_frame)
        resource_layout.addWidget(mem_frame)
        resource_layout.addWidget(net_frame)
        
        layout.addWidget(resource_frame)
        
        # 日誌表格
        log_table = QTableWidget(8, 3)
        log_table.setObjectName("DataTable")
        log_table.setHorizontalHeaderLabels(["時間", "等級", "訊息"])
        
        log_data = [
            ["13:28:45", "INFO", "降雨分析模組載入完成"],
            ["13:28:44", "DEBUG", "FastF1 快取命中"],
            ["13:28:43", "WARN", "API回應時間較慢"],
            ["13:28:42", "INFO", "開始執行分析"],
            ["13:28:41", "INFO", "系統初始化完成"],
            ["13:28:40", "DEBUG", "載入配置檔案"],
            ["13:28:39", "INFO", "連接數據庫"],
            ["13:28:38", "INFO", "啟動系統"]
        ]
        
        for row, row_data in enumerate(log_data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                if col == 1:  # 等級欄
                    if value == "WARN":
                        item.setBackground(Qt.yellow)
                    elif value == "DEBUG":
                        item.setBackground(Qt.lightGray)
                log_table.setItem(row, col, item)
                
        log_table.resizeColumnsToContents()
        layout.addWidget(log_table)
        
        return widget
        
    def create_compact_status_bar(self):
        """創建緊湊狀態列"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 緊湊狀態指標
        cpu_label = QLabel("CPU:45%")
        mem_label = QLabel("RAM:2.1GB")
        cache_label = QLabel("快取:156MB")
        api_label = QLabel("API:連線")
        error_label = QLabel("錯誤:0")
        
        # 分隔符
        sep1 = QLabel("|")
        sep2 = QLabel("|")
        sep3 = QLabel("|")
        sep4 = QLabel("|")
        
        # 時間戳
        time_label = QLabel("2025-08-25 13:28:45")
        
        status_bar.addWidget(cpu_label)
        status_bar.addWidget(sep1)
        status_bar.addWidget(mem_label)
        status_bar.addWidget(sep2)
        status_bar.addWidget(cache_label)
        status_bar.addWidget(sep3)
        status_bar.addWidget(api_label)
        status_bar.addWidget(sep4)
        status_bar.addWidget(error_label)
        status_bar.addPermanentWidget(time_label)
        
    # 事件處理方法
    def on_tree_item_clicked(self, item, column):
        if item.parent():
            function_name = item.text(0)
            function_id = item.data(0, Qt.UserRole)
            print(f"選擇功能: {function_name} (ID: {function_id})")
            
    # 菜單和工具欄事件處理
    def new_analysis(self): print("新建分析")
    def open_file(self): print("開啟檔案")
    def save_results(self): print("儲存結果")
    def run_analysis(self): print("執行分析")
    def batch_process(self): print("批次處理")
    def stop_process(self): print("停止處理")
    def clear_cache(self): print("清除快取")
    def system_diagnostic(self): print("系統診斷")
    def performance_monitor(self): print("效能監控")
    def about(self): print("關於")
        
    def apply_style_c(self):
        """應用風格C樣式 - 90年代復古專業風格"""
        style = """
        /* 主視窗 - 90年代風格 */
        QMainWindow {
            background-color: #C0C0C0;
            color: #000000;
            font-family: "MS Sans Serif", "Tahoma", sans-serif;
            font-size: 8pt;
        }
        
        /* 菜單欄 - 經典風格 */
        QMenuBar {
            background-color: #C0C0C0;
            border-bottom: 1px solid #808080;
            font-size: 8pt;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 2px 8px;
        }
        QMenuBar::item:selected {
            background-color: #0078D4;
            color: white;
        }
        QMenu {
            background-color: #C0C0C0;
            border: 1px solid #808080;
            font-size: 8pt;
        }
        QMenu::item {
            padding: 2px 20px;
        }
        QMenu::item:selected {
            background-color: #0078D4;
            color: white;
        }
        
        /* 工具欄 - 90年代風格 */
        QToolBar {
            background-color: #C0C0C0;
            border: 1px solid #808080;
            spacing: 1px;
            font-size: 8pt;
        }
        QToolBar QToolButton {
            border: 1px solid transparent;
            padding: 2px 4px;
            margin: 1px;
        }
        QToolBar QToolButton:hover {
            border: 1px outset #C0C0C0;
            background-color: #E0E0E0;
        }
        QToolBar QToolButton:pressed {
            border: 1px inset #C0C0C0;
            background-color: #A0A0A0;
        }
        
        /* 參數框架 */
        #ParameterFrame {
            background-color: #C0C0C0;
            border: 1px inset #C0C0C0;
        }
        
        /* 下拉選單 - 經典風格 */
        QComboBox {
            background-color: white;
            border: 1px inset #C0C0C0;
            padding: 1px 2px;
            font-size: 8pt;
        }
        QComboBox:hover {
            border: 1px inset #808080;
        }
        QComboBox::drop-down {
            border: none;
            width: 16px;
            background-color: #C0C0C0;
        }
        QComboBox::down-arrow {
            image: none;
            border: 1px outset #C0C0C0;
            background-color: #C0C0C0;
            width: 10px;
            height: 6px;
        }
        
        /* 按鈕 - 經典90年代風格 */
        QPushButton {
            background-color: #C0C0C0;
            border: 1px outset #C0C0C0;
            padding: 2px 4px;
            font-size: 8pt;
            font-weight: normal;
        }
        QPushButton:hover {
            background-color: #E0E0E0;
        }
        QPushButton:pressed {
            border: 1px inset #C0C0C0;
            background-color: #A0A0A0;
        }
        QPushButton:checked {
            border: 1px inset #C0C0C0;
            background-color: #A0A0A0;
        }
        
        /* 搜尋框 - 經典風格 */
        QLineEdit {
            background-color: white;
            border: 1px inset #C0C0C0;
            padding: 1px 2px;
            font-size: 8pt;
        }
        QLineEdit:focus {
            border: 1px inset #808080;
        }
        
        /* 功能樹 - 經典風格 */
        #FunctionTree {
            background-color: white;
            border: 1px inset #C0C0C0;
            outline: none;
            font-size: 8pt;
        }
        #FunctionTree::item {
            height: 18px;
            border: none;
            padding: 1px;
        }
        #FunctionTree::item:hover {
            background-color: #E0E0FF;
        }
        #FunctionTree::item:selected {
            background-color: #0078D4;
            color: white;
        }
        #FunctionTree::branch:closed:has-children {
            image: none;
            border: none;
        }
        #FunctionTree::branch:open:has-children {
            image: none;
            border: none;
        }
        
        /* 分頁標籤 - 經典風格 */
        #CompactTabs::pane {
            border: 1px inset #C0C0C0;
            background-color: #C0C0C0;
        }
        #CompactTabs QTabBar::tab {
            background-color: #C0C0C0;
            border: 1px outset #C0C0C0;
            padding: 2px 8px;
            margin: 0px 1px;
            font-size: 8pt;
        }
        #CompactTabs QTabBar::tab:selected {
            background-color: white;
            border-bottom: none;
        }
        #CompactTabs QTabBar::tab:hover {
            background-color: #E0E0E0;
        }
        
        /* 表格 - 經典風格 */
        #DataTable {
            background-color: white;
            border: 1px inset #C0C0C0;
            gridline-color: #C0C0C0;
            font-size: 8pt;
        }
        #DataTable QHeaderView::section {
            background-color: #C0C0C0;
            border: 1px outset #C0C0C0;
            padding: 2px;
            font-weight: bold;
            font-size: 8pt;
        }
        #DataTable::item {
            padding: 1px;
            border: none;
        }
        #DataTable::item:selected {
            background-color: #0078D4;
            color: white;
        }
        
        /* 面板標題 */
        #PanelTitle {
            font-weight: bold;
            font-size: 8pt;
            color: #000000;
        }
        
        /* 狀態指示器 */
        #StatusIndicator {
            background-color: #008000;
            color: white;
            padding: 2px 6px;
            border: 1px inset #C0C0C0;
            font-size: 8pt;
        }
        
        /* 框架 - 經典邊框 */
        QFrame {
            border: 1px inset #C0C0C0;
            background-color: #C0C0C0;
        }
        QFrame[frameShape="4"] { /* VLine */
            border: none;
            background-color: #808080;
            max-width: 1px;
        }
        QFrame[frameShape="5"] { /* HLine */
            border: none;
            background-color: #808080;
            max-height: 1px;
        }
        
        /* 狀態列 - 經典風格 */
        QStatusBar {
            background-color: #C0C0C0;
            border-top: 1px solid #808080;
            color: #000000;
            font-size: 8pt;
        }
        QProgressBar {
            border: 1px inset #C0C0C0;
            background-color: #C0C0C0;
            text-align: center;
            font-size: 8pt;
        }
        QProgressBar::chunk {
            background-color: #0078D4;
        }
        
        /* CheckBox - 經典風格 */
        QCheckBox {
            font-size: 8pt;
            color: #000000;
        }
        QCheckBox::indicator {
            width: 12px;
            height: 12px;
            border: 1px inset #C0C0C0;
            background-color: white;
        }
        QCheckBox::indicator:checked {
            background-color: white;
            image: none;
        }
        QCheckBox::indicator:checked::after {
            content: "✓";
            color: black;
            font-weight: bold;
        }
        
        /* 群組框 - 經典風格 */
        QGroupBox {
            font-weight: bold;
            border: 1px solid #808080;
            margin: 2px 0;
            padding-top: 8px;
            background-color: #C0C0C0;
            font-size: 8pt;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            color: #000000;
            background-color: #C0C0C0;
        }
        """
        
        self.setStyleSheet(style)

def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setApplicationName("F1T GUI Demo - Style C")
    app.setOrganizationName("F1T Professional Team")
    
    # 設置應用程式字體 - 90年代風格
    font = QFont("MS Sans Serif", 8)
    app.setFont(font)
    
    # 創建主視窗
    window = StyleCMainWindow()
    window.show()
    
    # 顯示歡迎訊息
    print("🖥️ F1T GUI Demo - 風格C (90年代復古專業) 已啟動")
    print("📋 這是一個展示90年代經典界面設計的Demo")
    print("🔧 緊湊高效的專業工作環境")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
