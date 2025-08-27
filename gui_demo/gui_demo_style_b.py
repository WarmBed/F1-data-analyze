#!/usr/bin/env python3
"""
F1T GUI Demo - 風格B: 專業工程風格
Demo for Style B: Professional Engineering Design
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

class StyleBMainWindow(QMainWindow):
    """風格B: 專業工程主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚙️ F1 Analysis Engineering Station v5.5 - 風格B Demo")
        self.setMinimumSize(1200, 800)
        self.init_ui()
        self.apply_style_b()
        
    def init_ui(self):
        """初始化用戶界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # 參數控制區 (使用GroupBox)
        param_group = self.create_parameter_group()
        main_layout.addWidget(param_group)
        
        # 主工作區
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左側功能樹 (使用GroupBox)
        left_group = self.create_function_group()
        content_splitter.addWidget(left_group)
        
        # 右側工作區 (使用GroupBox)
        right_group = self.create_workspace_group()
        content_splitter.addWidget(right_group)
        
        # 設置分割比例
        content_splitter.setSizes([350, 850])
        main_layout.addWidget(content_splitter)
        
        # 狀態列
        self.create_engineering_status_bar()
        
    def create_parameter_group(self):
        """創建參數控制群組"""
        group = QGroupBox("⚙️ 系統參數配置")
        group.setObjectName("ParameterGroup")
        
        layout = QHBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(15)
        
        # 配置框架
        config_frame = QFrame()
        config_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        config_layout = QHBoxLayout(config_frame)
        
        # 年份選擇
        year_combo = QComboBox()
        year_combo.addItems(["2024", "2025"])
        year_combo.setCurrentText("2025")
        year_combo.setFixedSize(80, 30)
        
        # 賽事選擇
        race_combo = QComboBox()
        race_combo.addItems(["Japan", "Singapore", "Las Vegas", "Qatar", "Abu Dhabi"])
        race_combo.setCurrentText("Japan")
        race_combo.setFixedSize(120, 30)
        
        # 賽段選擇
        session_combo = QComboBox()
        session_combo.addItems(["R", "Q", "FP1", "FP2", "FP3", "S"])
        session_combo.setCurrentText("R")
        session_combo.setFixedSize(60, 30)
        
        # 系統狀態
        link_checkbox = QCheckBox("數據聯動")
        link_checkbox.setChecked(True)
        
        debug_checkbox = QCheckBox("偵錯模式")
        debug_checkbox.setChecked(False)
        
        config_layout.addWidget(QLabel("年份:"))
        config_layout.addWidget(year_combo)
        config_layout.addWidget(QLabel("賽事:"))
        config_layout.addWidget(race_combo)
        config_layout.addWidget(QLabel("賽段:"))
        config_layout.addWidget(session_combo)
        config_layout.addStretch()
        config_layout.addWidget(link_checkbox)
        config_layout.addWidget(debug_checkbox)
        
        # 控制按鈕框架
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        control_layout = QHBoxLayout(control_frame)
        
        # 控制按鈕
        exec_btn = QPushButton("執行")
        exec_btn.setFixedSize(70, 30)
        
        batch_btn = QPushButton("批次")
        batch_btn.setFixedSize(70, 30)
        
        stop_btn = QPushButton("停止")
        stop_btn.setFixedSize(70, 30)
        
        cache_btn = QPushButton("清快取")
        cache_btn.setFixedSize(70, 30)
        
        reset_btn = QPushButton("重置")
        reset_btn.setFixedSize(70, 30)
        
        control_layout.addWidget(exec_btn)
        control_layout.addWidget(batch_btn)
        control_layout.addWidget(stop_btn)
        control_layout.addWidget(cache_btn)
        control_layout.addWidget(reset_btn)
        
        layout.addWidget(config_frame)
        layout.addWidget(control_frame)
        
        return group
        
    def create_function_group(self):
        """創建功能導航群組"""
        group = QGroupBox("📋 功能模組導航")
        group.setObjectName("FunctionGroup")
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(8)
        
        # 搜尋和篩選框架
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.StyledPanel)
        search_layout = QVBoxLayout(search_frame)
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("搜尋功能模組...")
        search_box.setFixedHeight(28)
        
        filter_layout = QHBoxLayout()
        show_all = QCheckBox("全部")
        show_all.setChecked(True)
        show_favorites = QCheckBox("收藏")
        show_recent = QCheckBox("最近")
        
        filter_layout.addWidget(show_all)
        filter_layout.addWidget(show_favorites)
        filter_layout.addWidget(show_recent)
        filter_layout.addStretch()
        
        search_layout.addWidget(search_box)
        search_layout.addLayout(filter_layout)
        
        layout.addWidget(search_frame)
        
        # 功能樹
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setObjectName("FunctionTree")
        
        # 系統狀態
        status = QTreeWidgetItem(tree, ["🔧 系統狀態監控"])
        status.setExpanded(True)
        QTreeWidgetItem(status, ["📊 CPU: 45%"])
        QTreeWidgetItem(status, ["💾 RAM: 2.1GB"])
        QTreeWidgetItem(status, ["🌡️ 溫度: 正常"])
        
        # 收藏夾
        favorites = QTreeWidgetItem(tree, ["⭐ 快速存取"])
        favorites.setExpanded(True)
        QTreeWidgetItem(favorites, ["🏆 車手最快進站"])
        QTreeWidgetItem(favorites, ["📡 雙車手比較"])
        QTreeWidgetItem(favorites, ["🎯 動態彎道檢測"])
        
        # 基礎分析模組
        basic = QTreeWidgetItem(tree, ["📋 基礎分析引擎"])
        basic.setExpanded(True)
        rain_item = QTreeWidgetItem(basic, ["🌧️ 降雨強度分析器"])
        rain_item.setData(0, Qt.UserRole, "rain_intensity")
        
        track_item = QTreeWidgetItem(basic, ["🛣️ 賽道路線分析器"])
        track_item.setData(0, Qt.UserRole, "track_analysis")
        
        pitstop_item = QTreeWidgetItem(basic, ["🏆 車手最快進站"])
        pitstop_item.setData(0, Qt.UserRole, "fastest_pitstop")
        
        team_item = QTreeWidgetItem(basic, ["🏁 車隊進站排行"])
        team_item.setData(0, Qt.UserRole, "team_pitstop")
        
        detail_item = QTreeWidgetItem(basic, ["🛞 進站詳細記錄"])
        detail_item.setData(0, Qt.UserRole, "pitstop_details")
        
        # 進階分析模組
        advanced = QTreeWidgetItem(tree, ["🔬 進階分析引擎"])
        advanced.setExpanded(True)
        telemetry_item = QTreeWidgetItem(advanced, ["📡 車手詳細遙測"])
        telemetry_item.setData(0, Qt.UserRole, "telemetry")
        
        compare_item = QTreeWidgetItem(advanced, ["🤝 雙車手比較分析"])
        compare_item.setData(0, Qt.UserRole, "driver_comparison")
        
        corner_item = QTreeWidgetItem(advanced, ["🎯 動態彎道檢測"])
        corner_item.setData(0, Qt.UserRole, "corner_detection")
        
        position_item = QTreeWidgetItem(advanced, ["📈 賽事位置變化"])
        position_item.setData(0, Qt.UserRole, "position_analysis")
        
        # 系統管理
        system = QTreeWidgetItem(tree, ["🚀 系統管理工具"])
        QTreeWidgetItem(system, ["📊 數據導出管理"])
        QTreeWidgetItem(system, ["🔄 暫存最佳化"])
        QTreeWidgetItem(system, ["🔍 系統診斷工具"])
        QTreeWidgetItem(system, ["📋 效能監控"])
        
        layout.addWidget(tree)
        
        # 添加點擊事件
        tree.itemClicked.connect(self.on_tree_item_clicked)
        
        return group
        
    def create_workspace_group(self):
        """創建工作區群組"""
        group = QGroupBox("📊 分析工作台")
        group.setObjectName("WorkspaceGroup")
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # 分頁容器
        tab_widget = QTabWidget()
        tab_widget.setTabsClosable(True)
        tab_widget.setMovable(True)
        tab_widget.setObjectName("WorkspaceTabs")
        
        # 第一個分頁 - 降雨分析工程檢視
        mdi_area1 = QMdiArea()
        mdi_area1.setObjectName("EngineeringMDI")
        tab_widget.addTab(mdi_area1, "🌧️ 降雨分析")
        
        # 添加工程檢視表格
        self.add_engineering_window(mdi_area1, "降雨強度數據檢視", self.create_engineering_table())
        
        # 第二個分頁 - 車手比較工程檢視
        mdi_area2 = QMdiArea()
        mdi_area2.setObjectName("EngineeringMDI")
        tab_widget.addTab(mdi_area2, "🤝 車手比較")
        
        # 添加性能監控分頁
        performance_widget = self.create_performance_monitor()
        tab_widget.addTab(performance_widget, "📊 性能監控")
        
        # 添加新分頁按鈕
        tab_widget.addTab(QWidget(), "+")
        tab_widget.tabBarClicked.connect(self.on_tab_clicked)
        
        layout.addWidget(tab_widget)
        
        return group
        
    def add_engineering_window(self, mdi_area, title, content):
        """添加工程檢視視窗到MDI區域"""
        sub_window = QMdiSubWindow()
        sub_window.setWidget(content)
        sub_window.setWindowTitle(title)
        sub_window.resize(500, 350)
        mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
    def create_engineering_table(self):
        """創建工程檢視表格"""
        table = QTableWidget(8, 5)
        table.setObjectName("EngineeringTable")
        table.setHorizontalHeaderLabels(["時間戳", "降雨強度", "賽道狀況", "溫度", "狀態"])
        
        # 工程數據
        data = [
            ["2025-08-25 13:23:45.123", "HIGH", "濕滑", "18.5°C", "⚠️"],
            ["2025-08-25 13:24:12.456", "MEDIUM", "潮濕", "19.2°C", "✅"],
            ["2025-08-25 13:24:38.789", "LOW", "乾燥", "20.1°C", "✅"],
            ["2025-08-25 13:25:05.012", "NONE", "乾燥", "21.0°C", "✅"],
            ["2025-08-25 13:25:32.345", "MEDIUM", "潮濕", "19.8°C", "✅"],
            ["2025-08-25 13:26:01.678", "HIGH", "濕滑", "18.1°C", "⚠️"],
            ["2025-08-25 13:26:28.901", "EXTREME", "積水", "17.5°C", "🚨"],
            ["2025-08-25 13:26:55.234", "LOW", "乾燥中", "19.5°C", "✅"]
        ]
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                if col == 4:  # 狀態欄位
                    if "🚨" in value:
                        item.setBackground(Qt.red)
                    elif "⚠️" in value:
                        item.setBackground(Qt.yellow)
                table.setItem(row, col, item)
                
        return table
        
    def create_performance_monitor(self):
        """創建性能監控面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 系統資源框架
        resource_frame = QFrame()
        resource_frame.setFrameStyle(QFrame.StyledPanel)
        resource_layout = QHBoxLayout(resource_frame)
        
        # CPU監控
        cpu_group = QGroupBox("CPU 使用率")
        cpu_layout = QVBoxLayout(cpu_group)
        cpu_progress = QProgressBar()
        cpu_progress.setValue(45)
        cpu_layout.addWidget(cpu_progress)
        cpu_layout.addWidget(QLabel("45% (4/8 核心)"))
        
        # 記憶體監控
        mem_group = QGroupBox("記憶體使用")
        mem_layout = QVBoxLayout(mem_group)
        mem_progress = QProgressBar()
        mem_progress.setValue(67)
        mem_layout.addWidget(mem_progress)
        mem_layout.addWidget(QLabel("2.1GB / 16GB"))
        
        # 網路監控
        net_group = QGroupBox("網路狀態")
        net_layout = QVBoxLayout(net_group)
        net_progress = QProgressBar()
        net_progress.setValue(23)
        net_layout.addWidget(net_progress)
        net_layout.addWidget(QLabel("下載: 1.2MB/s"))
        
        resource_layout.addWidget(cpu_group)
        resource_layout.addWidget(mem_group)
        resource_layout.addWidget(net_group)
        
        layout.addWidget(resource_frame)
        
        # 日誌框架
        log_group = QGroupBox("系統日誌")
        log_layout = QVBoxLayout(log_group)
        
        log_table = QTableWidget(5, 3)
        log_table.setHorizontalHeaderLabels(["時間", "等級", "訊息"])
        
        log_data = [
            ["13:26:55", "INFO", "降雨分析模組載入完成"],
            ["13:26:54", "DEBUG", "FastF1 快取命中: rain_2025_Japan"],
            ["13:26:53", "WARN", "API回應時間較慢: 2.3秒"],
            ["13:26:52", "INFO", "開始執行降雨強度分析"],
            ["13:26:51", "INFO", "系統初始化完成"]
        ]
        
        for row, row_data in enumerate(log_data):
            for col, value in enumerate(row_data):
                log_table.setItem(row, col, QTableWidgetItem(value))
                
        log_layout.addWidget(log_table)
        layout.addWidget(log_group)
        
        return widget
        
    def create_engineering_status_bar(self):
        """創建工程狀態列"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 工程狀態指標
        cpu_label = QLabel("🔧 CPU: 45%")
        mem_label = QLabel("💾 記憶體: 2.1GB")
        cache_label = QLabel("📦 快取: 156MB")
        api_label = QLabel("📡 API: 連線中")
        error_label = QLabel("🔍 錯誤: 0")
        process_label = QLabel("⚙️ 程序: 運行中")
        
        # 工程時間戳
        timestamp_label = QLabel("🕒 2025-08-25 13:26:55")
        
        status_bar.addWidget(cpu_label)
        status_bar.addWidget(mem_label)
        status_bar.addWidget(cache_label)
        status_bar.addWidget(api_label)
        status_bar.addWidget(error_label)
        status_bar.addWidget(process_label)
        status_bar.addPermanentWidget(timestamp_label)
        
    def on_tree_item_clicked(self, item, column):
        """處理功能樹點擊事件"""
        if item.parent():  # 只處理子項目
            function_name = item.text(0)
            function_id = item.data(0, Qt.UserRole)
            print(f"選擇功能: {function_name} (ID: {function_id})")
            
    def on_tab_clicked(self, index):
        """處理分頁點擊事件"""
        tab_widget = self.sender()
        if tab_widget.tabText(index) == "+":
            # 添加新工程分頁
            new_mdi = QMdiArea()
            new_mdi.setObjectName("EngineeringMDI")
            count = tab_widget.count()
            tab_widget.insertTab(count-1, new_mdi, f"🔬 新分析 {count-1}")
            tab_widget.setCurrentIndex(count-1)
        
    def apply_style_b(self):
        """應用風格B樣式"""
        style = """
        /* 主視窗 - 工程風格 */
        QMainWindow {
            background-color: #F5F6FA;
            color: #2F3640;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 9pt;
        }
        
        /* 群組框 */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #A4B0BE;
            border-radius: 8px;
            margin: 5px 0;
            padding-top: 10px;
            background-color: #FFFFFF;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: #2F3640;
            background-color: #FFFFFF;
        }
        
        /* 框架 */
        QFrame {
            border: 1px solid #A4B0BE;
            border-radius: 4px;
            background-color: #F8F9FA;
            margin: 2px;
        }
        
        /* 下拉選單 - 工程風格 */
        QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #57606F;
            border-radius: 4px;
            padding: 4px 8px;
            font-family: "Consolas", monospace;
            font-size: 8pt;
        }
        QComboBox:hover {
            border-color: #3742FA;
        }
        QComboBox:focus {
            border-color: #2F3542;
            border-width: 2px;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox::down-arrow {
            image: none;
            border: 1px solid #57606F;
            background-color: #A4B0BE;
        }
        
        /* 按鈕 - 工程風格 */
        QPushButton {
            background-color: #F1F2F6;
            border: 1px solid #57606F;
            border-radius: 4px;
            padding: 6px 12px;
            font-family: "Consolas", monospace;
            font-size: 8pt;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #DDD6FE;
            border-color: #3742FA;
        }
        QPushButton:pressed {
            background-color: #C7D2FE;
            border-color: #2F3542;
        }
        
        /* 搜尋框 - 工程風格 */
        QLineEdit {
            background-color: #FFFFFF;
            border: 1px solid #57606F;
            border-radius: 4px;
            padding: 6px 10px;
            font-family: "Consolas", monospace;
            font-size: 8pt;
        }
        QLineEdit:focus {
            border-color: #3742FA;
            border-width: 2px;
        }
        
        /* 功能樹 - 工程風格 */
        #FunctionTree {
            background-color: #FFFFFF;
            border: 1px solid #A4B0BE;
            border-radius: 4px;
            outline: none;
            font-family: "Consolas", monospace;
            font-size: 8pt;
        }
        #FunctionTree::item {
            height: 24px;
            border: none;
            padding: 2px 6px;
        }
        #FunctionTree::item:hover {
            background-color: #EEF2FF;
            border: 1px solid #C7D2FE;
        }
        #FunctionTree::item:selected {
            background-color: #3742FA;
            color: white;
        }
        #FunctionTree::branch:closed:has-children {
            image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAJCAYAAADgkQYQAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFYSURBVBiVY/j//z8DGgABBBYWFgYQYGBgYGBhYWHABSD+//8/w/8/fxn+/PnD8PfvX4a/f/8y/Pv3j+H///8M//79Y/j37x/D379/GX7//s3w+/dvht+/fzP8+vWL4devXwy/fv1i+PXrF8OvX78Yfv36xfDr1y+GX79+Mfz69Yvh169fDL9+/WL49esXw69fvxh+/frF8OvXL4Zfv34x/Pr1i+HXr18Mv379Yvj16xfDr1+/GH79+sXw69cvhl+/fjH8+vWL4devXwy/fv1i+PXrF8OvX78Yfv36xfDr1y+GX79+Mfz69Yvh169fDL9+/WL49esXw69fvxh+/frF8OvXL4Zfv34x/Pr1i+HXr18Mv379Yvj16xfDr1+/GH79+sXw69cvhl+/fjH8+vWL4devXwy/fv1i+PXrF8OvX78Yfv36xfDr1y+GX79+Mfz69Yvh169fDL9+/WL49esXw69fvxh+/frF8OvXL4Zfv34x/Pr1CwAAP8klrQAAAABJRU5ErkJggg==);
        }
        
        /* 分頁標籤 - 工程風格 */
        #WorkspaceTabs::pane {
            border: 1px solid #A4B0BE;
            border-radius: 4px;
            background-color: #FFFFFF;
        }
        #WorkspaceTabs QTabBar::tab {
            background-color: #F1F2F6;
            border: 1px solid #A4B0BE;
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
            margin-right: 1px;
            font-family: "Consolas", monospace;
            font-size: 8pt;
            font-weight: bold;
        }
        #WorkspaceTabs QTabBar::tab:selected {
            background-color: #FFFFFF;
            border-bottom: none;
            color: #3742FA;
        }
        #WorkspaceTabs QTabBar::tab:hover {
            background-color: #EEF2FF;
            border-color: #3742FA;
        }
        
        /* MDI區域 - 工程風格 */
        #EngineeringMDI {
            background-color: #F8F9FA;
            border: 1px solid #A4B0BE;
        }
        QMdiSubWindow {
            border: 1px solid #57606F;
            border-radius: 4px;
            background-color: #FFFFFF;
        }
        
        /* 表格 - 工程風格 */
        #EngineeringTable {
            background-color: #FFFFFF;
            border: 1px solid #A4B0BE;
            border-radius: 4px;
            gridline-color: #DDD6FE;
            font-family: "Consolas", monospace;
            font-size: 8pt;
        }
        #EngineeringTable QHeaderView::section {
            background-color: #F1F2F6;
            border: 1px solid #A4B0BE;
            padding: 6px;
            font-weight: bold;
            font-family: "Consolas", monospace;
        }
        
        /* 狀態列 - 工程風格 */
        QStatusBar {
            background-color: #F1F2F6;
            border-top: 1px solid #A4B0BE;
            color: #2F3640;
            font-family: "Consolas", monospace;
            font-size: 7pt;
        }
        QProgressBar {
            border: 1px solid #57606F;
            border-radius: 3px;
            background-color: #F8F9FA;
            text-align: center;
            font-family: "Consolas", monospace;
            font-size: 7pt;
        }
        QProgressBar::chunk {
            background-color: #3742FA;
            border-radius: 2px;
        }
        
        /* CheckBox - 工程風格 */
        QCheckBox {
            font-family: "Consolas", monospace;
            font-size: 8pt;
            color: #2F3640;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #57606F;
            border-radius: 2px;
            background-color: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background-color: #3742FA;
            border-color: #2F3542;
        }
        QCheckBox::indicator:checked::after {
            content: "✓";
            color: white;
            font-weight: bold;
        }
        """
        
        self.setStyleSheet(style)

def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setApplicationName("F1T GUI Demo - Style B")
    app.setOrganizationName("F1T Engineering Team")
    
    # 設置應用程式字體
    font = QFont("Consolas", 9)
    app.setFont(font)
    
    # 創建主視窗
    window = StyleBMainWindow()
    window.show()
    
    # 顯示歡迎訊息
    print("⚙️ F1T GUI Demo - 風格B (專業工程) 已啟動")
    print("📋 這是一個展示風格B界面設計的Demo")
    print("🔧 包含完整的工程監控和系統管理功能")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
