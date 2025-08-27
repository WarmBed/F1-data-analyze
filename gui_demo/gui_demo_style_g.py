#!/usr/bin/env python3
"""
F1T GUI Demo - 風格G: 緊湊工業化專業F1工作站
Demo for Style G: Compact Industrial Professional F1 Workstation
基於方案D，移除系統監控，更緊湊的布局，工業風格按鈕
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame, QToolBar, QAction, QMenuBar, QMenu, QGridLayout, QLCDNumber,
    QTextEdit, QScrollArea, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
import math

class DraggableSubWindow(QMdiSubWindow):
    """可拖動的子視窗"""
    
    def __init__(self, title="子視窗"):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        
        # 設置可拖動
        self.setProperty("movable", True)
        
        # 創建內容
        content = QWidget()
        self.setWidget(content)
        return content

class StyleGMainWindow(QMainWindow):
    """風格G: 緊湊工業化專業F1工作站主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Data Analysis Pro - Compact Industrial v7.0 - Style G")
        self.setMinimumSize(1600, 900)
        self.init_ui()
        self.apply_style_g()
        
    def init_ui(self):
        """初始化用戶界面"""
        # 創建菜單欄
        self.create_compact_menubar()
        
        # 創建工具欄
        self.create_compact_toolbar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 更緊湊
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(1)
        
        # 緊湊參數控制區
        param_frame = self.create_compact_parameter_panel()
        main_layout.addWidget(param_frame)
        
        # 主要分析區域
        analysis_splitter = QSplitter(Qt.Horizontal)
        analysis_splitter.setChildrenCollapsible(False)
        
        # 左側功能樹 - 更窄
        left_panel = self.create_compact_function_tree()
        analysis_splitter.addWidget(left_panel)
        
        # 中央工作區域 - MDI多視窗
        center_panel = self.create_mdi_workspace()
        analysis_splitter.addWidget(center_panel)
        
        # 右側數據面板 - 更窄
        right_panel = self.create_compact_data_panel()
        analysis_splitter.addWidget(right_panel)
        
        # 設置緊湊分割比例
        analysis_splitter.setSizes([160, 1100, 180])
        main_layout.addWidget(analysis_splitter)
        
        # 緊湊狀態列
        self.create_compact_status_bar()
        
    def create_compact_menubar(self):
        """創建緊湊菜單欄"""
        menubar = self.menuBar()
        
        # 檔案菜單
        file_menu = menubar.addMenu('檔案')
        file_menu.addAction('新增工作區', self.new_workspace)
        file_menu.addAction('開啟數據...', self.open_data)
        file_menu.addAction('儲存設定', self.save_settings)
        file_menu.addSeparator()
        file_menu.addAction('匯出報告...', self.export_report)
        file_menu.addAction('離開', self.close)
        
        # 分析菜單
        analysis_menu = menubar.addMenu('分析')
        analysis_menu.addAction('圈速分析', self.lap_analysis)
        analysis_menu.addAction('遙測比較', self.telemetry_comparison)
        analysis_menu.addAction('進站分析', self.pitstop_analysis)
        analysis_menu.addAction('輪胎分析', self.tire_analysis)
        
        # 檢視菜單
        view_menu = menubar.addMenu('檢視')
        view_menu.addAction('重新排列視窗', self.tile_windows)
        view_menu.addAction('層疊視窗', self.cascade_windows)
        view_menu.addAction('放大', self.zoom_in)
        view_menu.addAction('縮小', self.zoom_out)
        
        # 工具菜單
        tools_menu = menubar.addMenu('工具')
        tools_menu.addAction('數據驗證', self.data_validation)
        tools_menu.addAction('報告產生器', self.report_generator)
        tools_menu.addAction('系統設定', self.system_settings)
        
    def create_compact_toolbar(self):
        """創建緊湊工具欄"""
        toolbar = QToolBar()
        toolbar.setObjectName("CompactToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setFixedHeight(26)
        self.addToolBar(toolbar)
        
        # 檔案操作
        toolbar.addAction("📁", self.open_data)
        toolbar.addAction("💾", self.save_settings)
        toolbar.addSeparator()
        
        # 分析工具
        toolbar.addAction("📊", self.lap_analysis)
        toolbar.addAction("📈", self.telemetry_comparison)
        toolbar.addAction("⛽", self.pitstop_analysis)
        toolbar.addSeparator()
        
        # 檢視控制
        toolbar.addAction("🔍+", self.zoom_in)
        toolbar.addAction("🔍-", self.zoom_out)
        toolbar.addAction("📐", self.fit_view)
        toolbar.addSeparator()
        
        # 視窗管理
        toolbar.addAction("⊞", self.tile_windows)
        toolbar.addAction("⧉", self.cascade_windows)
        
    def create_compact_parameter_panel(self):
        """創建緊湊參數控制面板"""
        frame = QFrame()
        frame.setObjectName("CompactParameterFrame")
        frame.setFixedHeight(28)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # 緊湊參數選擇
        layout.addWidget(QLabel("賽季:"))
        year_combo = QComboBox()
        year_combo.addItems(["2025", "2024", "2023"])
        year_combo.setCurrentText("2025")
        year_combo.setFixedSize(50, 18)
        layout.addWidget(year_combo)
        
        layout.addWidget(QLabel("大獎賽:"))
        race_combo = QComboBox()
        race_combo.addItems(["Japan", "Monaco", "Silverstone"])
        race_combo.setCurrentText("Japan")
        race_combo.setFixedSize(70, 18)
        layout.addWidget(race_combo)
        
        layout.addWidget(QLabel("賽段:"))
        session_combo = QComboBox()
        session_combo.addItems(["Race", "Qualifying", "Practice"])
        session_combo.setCurrentText("Race")
        session_combo.setFixedSize(65, 18)
        layout.addWidget(session_combo)
        
        # 分隔線
        layout.addWidget(QLabel("|"))
        
        layout.addWidget(QLabel("車手1:"))
        driver1_combo = QComboBox()
        driver1_combo.addItems(["VER", "LEC", "HAM", "RUS"])
        driver1_combo.setCurrentText("VER")
        driver1_combo.setFixedSize(45, 18)
        layout.addWidget(driver1_combo)
        
        layout.addWidget(QLabel("車手2:"))
        driver2_combo = QComboBox()
        driver2_combo.addItems(["LEC", "VER", "HAM", "RUS"])
        driver2_combo.setCurrentText("LEC")
        driver2_combo.setFixedSize(45, 18)
        layout.addWidget(driver2_combo)
        
        # 分隔線
        layout.addWidget(QLabel("|"))
        
        layout.addWidget(QLabel("功能:"))
        function_combo = QComboBox()
        function_combo.addItems(["圈速分析", "遙測比較", "進站分析"])
        function_combo.setCurrentText("圈速分析")
        function_combo.setFixedSize(70, 18)
        layout.addWidget(function_combo)
        
        layout.addStretch()
        
        # 緊湊工業風格按鈕
        analyze_btn = QPushButton("分析")
        analyze_btn.setObjectName("CompactIndustrialButton")
        analyze_btn.setFixedSize(40, 18)
        layout.addWidget(analyze_btn)
        
        export_btn = QPushButton("匯出")
        export_btn.setObjectName("CompactIndustrialButton")
        export_btn.setFixedSize(40, 18)
        layout.addWidget(export_btn)
        
        return frame
        
    def create_compact_function_tree(self):
        """創建緊湊功能樹"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # 緊湊標題
        title_frame = QFrame()
        title_frame.setObjectName("CompactTreeTitle")
        title_frame.setFixedHeight(16)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(2, 1, 2, 1)
        title_layout.addWidget(QLabel("分析功能"))
        layout.addWidget(title_frame)
        
        # 功能樹
        tree = QTreeWidget()
        tree.setObjectName("CompactFunctionTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(8)
        tree.setRootIsDecorated(True)
        
        # 基礎分析
        basic_group = QTreeWidgetItem(tree, ["🏁 基礎分析"])
        basic_group.setExpanded(True)
        QTreeWidgetItem(basic_group, ["降雨分析"])
        QTreeWidgetItem(basic_group, ["賽道分析"])
        QTreeWidgetItem(basic_group, ["進站分析"])
        QTreeWidgetItem(basic_group, ["事故分析"])
        
        # 單車手分析
        single_group = QTreeWidgetItem(tree, ["🚗 單車手分析"])
        single_group.setExpanded(True)
        QTreeWidgetItem(single_group, ["遙測分析"])
        QTreeWidgetItem(single_group, ["圈速分析"])
        QTreeWidgetItem(single_group, ["超車分析"])
        QTreeWidgetItem(single_group, ["DNF分析"])
        
        # 比較分析
        compare_group = QTreeWidgetItem(tree, ["⚡ 比較分析"])
        QTreeWidgetItem(compare_group, ["車手比較"])
        QTreeWidgetItem(compare_group, ["圈速比較"])
        QTreeWidgetItem(compare_group, ["遙測比較"])
        QTreeWidgetItem(compare_group, ["性能趨勢"])
        
        # 進階分析
        advanced_group = QTreeWidgetItem(tree, ["🔬 進階分析"])
        QTreeWidgetItem(advanced_group, ["彎道分析"])
        QTreeWidgetItem(advanced_group, ["輪胎分析"])
        QTreeWidgetItem(advanced_group, ["燃料分析"])
        QTreeWidgetItem(advanced_group, ["策略分析"])
        
        layout.addWidget(tree)
        
        return widget
        
    def create_mdi_workspace(self):
        """創建MDI多視窗工作區"""
        mdi_area = QMdiArea()
        mdi_area.setObjectName("CompactMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 創建可拖動的子視窗
        
        # 圈速分析視窗
        lap_window = QMdiSubWindow()
        lap_window.setWindowTitle("圈速分析")
        lap_content = self.create_lap_analysis_widget()
        lap_window.setWidget(lap_content)
        lap_window.setFixedSize(450, 250)
        mdi_area.addSubWindow(lap_window)
        lap_window.move(10, 10)
        lap_window.show()
        
        # 遙測比較視窗
        telemetry_window = QMdiSubWindow()
        telemetry_window.setWindowTitle("遙測比較")
        telemetry_content = self.create_telemetry_comparison_widget()
        telemetry_window.setWidget(telemetry_content)
        telemetry_window.setFixedSize(450, 250)
        mdi_area.addSubWindow(telemetry_window)
        telemetry_window.move(470, 10)
        telemetry_window.show()
        
        # 基礎統計視窗
        stats_window = QMdiSubWindow()
        stats_window.setWindowTitle("基礎統計")
        stats_content = self.create_basic_stats_widget()
        stats_window.setWidget(stats_content)
        stats_window.setFixedSize(450, 180)
        mdi_area.addSubWindow(stats_window)
        stats_window.move(10, 270)
        stats_window.show()
        
        # 最慢圈分析視窗
        slowest_window = QMdiSubWindow()
        slowest_window.setWindowTitle("最慢圈分析")
        slowest_content = self.create_slowest_lap_widget()
        slowest_window.setWidget(slowest_content)
        slowest_window.setFixedSize(450, 180)
        mdi_area.addSubWindow(slowest_window)
        slowest_window.move(470, 270)
        slowest_window.show()
        
        return mdi_area
        
    def create_lap_analysis_widget(self):
        """創建圈速分析小部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # 數據表格
        table = QTableWidget(8, 4)
        table.setObjectName("CompactDataTable")
        table.setHorizontalHeaderLabels(["位置", "車手", "時間", "差距"])
        table.verticalHeader().setVisible(False)
        
        # 填充數據
        data = [
            ("1", "VER", "1:29.347", "-"),
            ("2", "LEC", "1:29.534", "+0.187"),
            ("3", "HAM", "1:29.678", "+0.331"),
            ("4", "RUS", "1:29.892", "+0.545"),
            ("5", "NOR", "1:30.125", "+0.778"),
            ("6", "PIA", "1:30.234", "+0.887"),
            ("7", "SAI", "1:30.456", "+1.109"),
            ("8", "ALO", "1:30.567", "+1.220")
        ]
        
        for row, (pos, driver, time, gap) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(pos))
            table.setItem(row, 1, QTableWidgetItem(driver))
            table.setItem(row, 2, QTableWidgetItem(time))
            table.setItem(row, 3, QTableWidgetItem(gap))
            
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        return widget
        
    def create_telemetry_comparison_widget(self):
        """創建遙測比較小部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        table = QTableWidget(6, 3)
        table.setObjectName("CompactDataTable")
        table.setHorizontalHeaderLabels(["參數", "VER", "LEC"])
        table.verticalHeader().setVisible(False)
        
        data = [
            ("最高速度", "324.5 km/h", "322.1 km/h"),
            ("平均速度", "198.3 km/h", "196.7 km/h"),
            ("最大煞車", "5.2G", "5.0G"),
            ("最大G力", "4.8G", "4.6G"),
            ("最高RPM", "11,850", "11,800"),
            ("換檔次數", "156", "162")
        ]
        
        for row, (param, ver, lec) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(param))
            table.setItem(row, 1, QTableWidgetItem(ver))
            table.setItem(row, 2, QTableWidgetItem(lec))
            
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        return widget
        
    def create_basic_stats_widget(self):
        """創建基礎統計小部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        table = QTableWidget(5, 2)
        table.setObjectName("CompactDataTable")
        table.setHorizontalHeaderLabels(["統計項目", "數值"])
        table.verticalHeader().setVisible(False)
        
        data = [
            ("總圈數", "53"),
            ("完成車手", "18"),
            ("DNF車手", "2"),
            ("安全車", "1次"),
            ("黃旗", "3次")
        ]
        
        for row, (item, value) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(item))
            table.setItem(row, 1, QTableWidgetItem(value))
            
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        return widget
        
    def create_slowest_lap_widget(self):
        """創建最慢圈分析小部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        table = QTableWidget(5, 4)
        table.setObjectName("CompactDataTable")
        table.setHorizontalHeaderLabels(["位置", "車手", "時間", "原因"])
        table.verticalHeader().setVisible(False)
        
        data = [
            ("18", "STR", "1:45.234", "進站"),
            ("17", "OCO", "1:42.567", "煞車問題"),
            ("16", "GAS", "1:39.123", "輪胎磨損"),
            ("15", "BOT", "1:36.789", "DRS故障"),
            ("14", "ZHO", "1:35.456", "引擎限制")
        ]
        
        for row, (pos, driver, time, reason) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(pos))
            table.setItem(row, 1, QTableWidgetItem(driver))
            table.setItem(row, 2, QTableWidgetItem(time))
            table.setItem(row, 3, QTableWidgetItem(reason))
            
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        return widget
        
    def create_compact_data_panel(self):
        """創建緊湊數據面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # 即時數據監控
        monitor_group = QGroupBox("即時數據")
        monitor_group.setObjectName("CompactGroup")
        monitor_layout = QVBoxLayout(monitor_group)
        monitor_layout.setContentsMargins(2, 4, 2, 2)
        monitor_layout.setSpacing(1)
        
        # 緊湊數據表格
        data_table = QTableWidget(6, 2)
        data_table.setObjectName("CompactDataTable")
        data_table.setHorizontalHeaderLabels(["項目", "數值"])
        data_table.verticalHeader().setVisible(False)
        data_table.setShowGrid(True)
        
        # 填充數據
        parameters = [
            ("速度", "324.5"),
            ("RPM", "11,850"),
            ("煞車", "85%"),
            ("節流", "100%"),
            ("齒輪", "7"),
            ("圈數", "15/53")
        ]
        
        for row, (param, value) in enumerate(parameters):
            data_table.setItem(row, 0, QTableWidgetItem(param))
            data_table.setItem(row, 1, QTableWidgetItem(value))
            
        data_table.resizeColumnsToContents()
        data_table.setFixedHeight(130)
        
        monitor_layout.addWidget(data_table)
        layout.addWidget(monitor_group)
        
        # 分析狀態
        status_group = QGroupBox("分析狀態")
        status_group.setObjectName("CompactGroup")
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(2, 4, 2, 2)
        status_layout.setSpacing(1)
        
        # 進度指示
        progress_label = QLabel("處理進度:")
        status_layout.addWidget(progress_label)
        
        progress_bar = QProgressBar()
        progress_bar.setValue(75)
        progress_bar.setFixedHeight(12)
        status_layout.addWidget(progress_bar)
        
        # 狀態信息
        status_layout.addWidget(QLabel("狀態: 分析中"))
        status_layout.addWidget(QLabel("記錄: 12,540"))
        status_layout.addWidget(QLabel("錯誤: 0"))
        status_layout.addWidget(QLabel("品質: 99.8%"))
        
        layout.addWidget(status_group)
        
        # 快速操作
        quick_group = QGroupBox("快速操作")
        quick_group.setObjectName("CompactGroup")
        quick_layout = QVBoxLayout(quick_group)
        quick_layout.setContentsMargins(2, 4, 2, 2)
        quick_layout.setSpacing(1)
        
        fastest_btn = QPushButton("最快圈")
        fastest_btn.setObjectName("CompactIndustrialButton")
        fastest_btn.setFixedHeight(18)
        quick_layout.addWidget(fastest_btn)
        
        compare_btn = QPushButton("車手比較")
        compare_btn.setObjectName("CompactIndustrialButton")
        compare_btn.setFixedHeight(18)
        quick_layout.addWidget(compare_btn)
        
        sector_btn = QPushButton("扇區分析")
        sector_btn.setObjectName("CompactIndustrialButton")
        sector_btn.setFixedHeight(18)
        quick_layout.addWidget(sector_btn)
        
        layout.addWidget(quick_group)
        
        layout.addStretch()
        
        return widget
        
    def create_compact_status_bar(self):
        """創建緊湊狀態列"""
        status_bar = QStatusBar()
        status_bar.setFixedHeight(18)
        self.setStatusBar(status_bar)
        
        # 狀態指示
        ready_label = QLabel("🟢 就緒")
        ready_label.setObjectName("StatusReady")
        
        data_label = QLabel("📊 數據: 已載入")
        analysis_label = QLabel("⚡ 分析: 進行中")
        session_label = QLabel("🏁 會話: Japan 2025 Race")
        
        status_bar.addWidget(ready_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(data_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(analysis_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(session_label)
        
        # 右側版本信息
        version_label = QLabel("F1T v7.0 | 緊湊模式")
        version_label.setObjectName("VersionInfo")
        status_bar.addPermanentWidget(version_label)
        
    # 事件處理方法
    def new_workspace(self): print("新增工作區")
    def open_data(self): print("開啟數據")
    def save_settings(self): print("儲存設定")
    def export_report(self): print("匯出報告")
    def lap_analysis(self): print("圈速分析")
    def telemetry_comparison(self): print("遙測比較")
    def pitstop_analysis(self): print("進站分析")
    def tire_analysis(self): print("輪胎分析")
    def tile_windows(self): print("重新排列視窗")
    def cascade_windows(self): print("層疊視窗")
    def zoom_in(self): print("放大")
    def zoom_out(self): print("縮小")
    def fit_view(self): print("適合檢視")
    def data_validation(self): print("數據驗證")
    def report_generator(self): print("報告產生器")
    def system_settings(self): print("系統設定")
        
    def apply_style_g(self):
        """應用風格G樣式 - 緊湊工業化專業F1工作站"""
        style = """
        /* 主視窗 - 緊湊深色主題 */
        QMainWindow {
            background-color: #1A1A1A;
            color: #FFFFFF;
            font-family: "Arial", "Helvetica", sans-serif;
            font-size: 8pt;
        }
        
        /* 菜單欄 - 緊湊風格 */
        QMenuBar {
            background-color: #2B2B2B;
            border-bottom: 1px solid #404040;
            color: #FFFFFF;
            font-size: 8pt;
            padding: 1px;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 2px 6px;
            border-radius: 0px;
        }
        QMenuBar::item:selected {
            background-color: #404040;
        }
        QMenu {
            background-color: #2B2B2B;
            border: 1px solid #404040;
            color: #FFFFFF;
            padding: 1px;
        }
        QMenu::item {
            padding: 2px 8px;
            border-radius: 0px;
        }
        QMenu::item:selected {
            background-color: #404040;
        }
        
        /* 緊湊工具欄 */
        #CompactToolbar {
            background-color: #2B2B2B;
            border-bottom: 1px solid #404040;
            color: #FFFFFF;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        #CompactToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #FFFFFF;
            font-size: 10pt;
            border-radius: 0px;
        }
        #CompactToolbar QToolButton:hover {
            background-color: #404040;
            border: 1px solid #555555;
        }
        #CompactToolbar QToolButton:pressed {
            background-color: #1A1A1A;
        }
        
        /* 緊湊參數面板 */
        #CompactParameterFrame {
            background-color: #2B2B2B;
            border: 1px solid #404040;
            border-radius: 0px;
        }
        
        /* 緊湊工業按鈕樣式 */
        #CompactIndustrialButton {
            background-color: #3A3A3A;
            border: 1px solid #555555;
            color: #FFFFFF;
            padding: 1px 3px;
            font-size: 8pt;
            border-radius: 0px;
            font-weight: bold;
        }
        #CompactIndustrialButton:hover {
            background-color: #4A4A4A;
            border-color: #666666;
        }
        #CompactIndustrialButton:pressed {
            background-color: #2A2A2A;
            border-color: #333333;
        }
        
        /* 緊湊群組框 */
        #CompactGroup {
            font-weight: bold;
            font-size: 8pt;
            color: #CCCCCC;
            border: 1px solid #404040;
            border-radius: 0px;
            margin-top: 4px;
            padding-top: 2px;
        }
        #CompactGroup::title {
            subcontrol-origin: margin;
            left: 3px;
            padding: 0 2px 0 2px;
            color: #FFFFFF;
        }
        
        /* 下拉選單 - 緊湊工業風格 */
        QComboBox {
            background-color: #3A3A3A;
            border: 1px solid #555555;
            color: #FFFFFF;
            padding: 1px 2px;
            font-size: 8pt;
            border-radius: 0px;
        }
        QComboBox:hover {
            border-color: #666666;
        }
        QComboBox::drop-down {
            border: none;
            width: 12px;
            background-color: #404040;
            border-radius: 0px;
        }
        QComboBox QAbstractItemView {
            background-color: #3A3A3A;
            border: 1px solid #555555;
            color: #FFFFFF;
            selection-background-color: #404040;
        }
        
        /* 功能樹標題 */
        #CompactTreeTitle {
            background-color: #2B2B2B;
            border-bottom: 1px solid #404040;
            color: #FFFFFF;
            font-weight: bold;
        }
        
        /* 緊湊功能樹 */
        #CompactFunctionTree {
            background-color: #1A1A1A;
            border: 1px solid #404040;
            color: #FFFFFF;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #2B2B2B;
        }
        #CompactFunctionTree::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        #CompactFunctionTree::item:hover {
            background-color: #2B2B2B;
        }
        #CompactFunctionTree::item:selected {
            background-color: #404040;
            color: #FFFFFF;
        }
        
        /* MDI工作區 */
        #CompactMDIArea {
            background-color: #1A1A1A;
            border: 1px solid #404040;
        }
        
        /* MDI子視窗 */
        QMdiSubWindow {
            background-color: #2B2B2B;
            border: 1px solid #404040;
            border-radius: 0px;
        }
        QMdiSubWindow::title {
            background-color: #404040;
            color: #FFFFFF;
            font-size: 8pt;
            font-weight: bold;
            padding: 2px;
        }
        
        /* 緊湊數據表格 */
        #CompactDataTable {
            background-color: #1A1A1A;
            alternate-background-color: #2B2B2B;
            color: #FFFFFF;
            gridline-color: #404040;
            font-size: 8pt;
            border: 1px solid #404040;
            border-radius: 0px;
        }
        #CompactDataTable::item {
            padding: 1px;
            border: none;
        }
        #CompactDataTable::item:selected {
            background-color: #404040;
        }
        #CompactDataTable QHeaderView::section {
            background-color: #2B2B2B;
            color: #FFFFFF;
            padding: 1px;
            border: 1px solid #404040;
            font-weight: bold;
            font-size: 8pt;
            border-radius: 0px;
        }
        
        /* 搜尋框 */
        QLineEdit {
            background-color: #3A3A3A;
            border: 1px solid #555555;
            color: #FFFFFF;
            padding: 1px 2px;
            font-size: 8pt;
            border-radius: 0px;
        }
        QLineEdit:focus {
            border-color: #666666;
        }
        
        /* 進度條 */
        QProgressBar {
            border: 1px solid #404040;
            border-radius: 0px;
            text-align: center;
            font-size: 8pt;
            background-color: #1A1A1A;
            color: #FFFFFF;
        }
        QProgressBar::chunk {
            background-color: #0078D4;
            border-radius: 0px;
        }
        
        /* 滑桿 */
        QSlider::groove:horizontal {
            border: 1px solid #404040;
            height: 3px;
            background: #1A1A1A;
            border-radius: 0px;
        }
        QSlider::handle:horizontal {
            background: #555555;
            border: 1px solid #404040;
            width: 6px;
            border-radius: 0px;
            margin: -1px 0;
        }
        QSlider::handle:horizontal:hover {
            background: #666666;
        }
        
        /* CheckBox */
        QCheckBox {
            color: #FFFFFF;
            font-size: 8pt;
        }
        QCheckBox::indicator {
            width: 8px;
            height: 8px;
            border: 1px solid #555555;
            background-color: #3A3A3A;
            border-radius: 0px;
        }
        QCheckBox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        
        /* 狀態列 */
        QStatusBar {
            background-color: #2B2B2B;
            border-top: 1px solid #404040;
            color: #CCCCCC;
            font-size: 8pt;
        }
        #StatusReady {
            color: #00AA00;
            font-weight: bold;
        }
        #VersionInfo {
            color: #0078D4;
            font-weight: bold;
        }
        
        /* 標籤 */
        QLabel {
            color: #FFFFFF;
            font-size: 8pt;
        }
        
        /* 滾動條 */
        QScrollBar:vertical {
            background-color: #2B2B2B;
            width: 6px;
            border: 1px solid #404040;
            border-radius: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 0px;
            min-height: 10px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
        
        self.setStyleSheet(style)

def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setApplicationName("F1T GUI Demo - Style G")
    app.setOrganizationName("F1T Compact Industrial Team")
    
    # 設置應用程式字體
    font = QFont("Arial", 8)
    app.setFont(font)
    
    # 創建主視窗
    window = StyleGMainWindow()
    window.show()
    
    # 顯示歡迎訊息
    print("🏭 F1T GUI Demo - 風格G (緊湊工業化專業F1工作站) 已啟動")
    print("⚙️ 基於方案D，移除系統監控，更緊湊的布局")
    print("🔧 工業風格平面化按鈕，所有視窗可拖動")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
