#!/usr/bin/env python3
"""
F1T GUI Demo - 風格E: MoTeC風格專業數據分析工作站
Demo for Style E: MoTeC-Style Professional Data Analysis Workstation
模仿MoTeC i2 Pro數據分析軟體的界面設計
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame, QToolBar, QAction, QMenuBar, QMenu, QGridLayout, QLCDNumber,
    QTextEdit, QScrollArea, QSlider, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPainter, QPen
import math

class MoTeCDataChannelWidget(QWidget):
    """MoTeC風格數據通道小部件"""
    
    def __init__(self, channel_name, data_type="graph"):
        super().__init__()
        self.setObjectName("DataChannelWidget")
        self.channel_name = channel_name
        self.data_type = data_type
        self.setMinimumHeight(120)
        self.init_widget()
        
    def init_widget(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # 通道標題欄
        title_frame = QFrame()
        title_frame.setObjectName("ChannelTitle")
        title_frame.setFixedHeight(18)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(4, 2, 4, 2)
        
        title_label = QLabel(self.channel_name)
        title_label.setObjectName("ChannelLabel")
        title_layout.addWidget(title_label)
        
        # 數值顯示
        if self.data_type == "speed":
            value_label = QLabel("324.5 km/h")
            value_label.setObjectName("SpeedValue")
        elif self.data_type == "rpm":
            value_label = QLabel("11,850 RPM")
            value_label.setObjectName("RPMValue")
        elif self.data_type == "brake":
            value_label = QLabel("85%")
            value_label.setObjectName("BrakeValue")
        elif self.data_type == "gear":
            value_label = QLabel("7")
            value_label.setObjectName("GearValue")
        else:
            value_label = QLabel("100.0")
            value_label.setObjectName("DefaultValue")
            
        title_layout.addStretch()
        title_layout.addWidget(value_label)
        
        layout.addWidget(title_frame)
        
        # 圖表區域（模擬）
        chart_widget = QWidget()
        chart_widget.setObjectName("ChartArea")
        chart_widget.setMinimumHeight(100)
        layout.addWidget(chart_widget)

class MoTeCInstrumentWidget(QWidget):
    """MoTeC風格儀表小部件"""
    
    def __init__(self, instrument_type="gauge"):
        super().__init__()
        self.setObjectName("InstrumentWidget")
        self.instrument_type = instrument_type
        self.setFixedSize(120, 120)
        self.init_instrument()
        
    def init_instrument(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        if self.instrument_type == "rpm":
            label = QLabel("Engine RPM")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            value_label = QLabel("11,850")
            value_label.setObjectName("InstrumentValue")
            value_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(value_label)
            
        elif self.instrument_type == "speed":
            label = QLabel("Speed")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            value_label = QLabel("324")
            value_label.setObjectName("InstrumentValue")
            value_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(value_label)
            
            unit_label = QLabel("km/h")
            unit_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(unit_label)
            
        elif self.instrument_type == "gear":
            layout.addWidget(QLabel(""))  # spacer
            gear_label = QLabel("7")
            gear_label.setObjectName("GearDisplay")
            gear_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(gear_label)
            layout.addWidget(QLabel(""))  # spacer

class StyleEMainWindow(QMainWindow):
    """風格E: MoTeC風格專業數據分析工作站主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Data Analysis Pro - MoTeC Style v5.5 - Style E")
        self.setMinimumSize(1600, 1000)
        self.init_ui()
        self.apply_style_e()
        
    def init_ui(self):
        """初始化用戶界面"""
        # 創建菜單欄
        self.create_motec_menubar()
        
        # 創建工具欄
        self.create_motec_toolbar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # 參數控制區
        param_frame = self.create_motec_parameter_panel()
        main_layout.addWidget(param_frame)
        
        # 主要分析區域
        analysis_splitter = QSplitter(Qt.Horizontal)
        analysis_splitter.setChildrenCollapsible(False)
        
        # 左側數據樹
        left_panel = self.create_motec_data_tree()
        analysis_splitter.addWidget(left_panel)
        
        # 中央圖表區域
        center_panel = self.create_motec_chart_area()
        analysis_splitter.addWidget(center_panel)
        
        # 設置分割比例
        analysis_splitter.setSizes([200, 1400])
        main_layout.addWidget(analysis_splitter)
        
        # 底部儀表和賽道區域
        bottom_panel = self.create_motec_bottom_panel()
        main_layout.addWidget(bottom_panel)
        
        # MoTeC風格狀態列
        self.create_motec_status_bar()
        
    def create_motec_menubar(self):
        """創建MoTeC風格菜單欄"""
        menubar = self.menuBar()
        
        # 檔案菜單
        file_menu = menubar.addMenu('File')
        file_menu.addAction('New Workspace', self.new_workspace)
        file_menu.addAction('Open Data...', self.open_data)
        file_menu.addAction('Save Workspace', self.save_workspace)
        file_menu.addSeparator()
        file_menu.addAction('Export Report...', self.export_report)
        file_menu.addAction('Exit', self.close)
        
        # 數據菜單
        data_menu = menubar.addMenu('Data')
        data_menu.addAction('Load Session...', self.load_session)
        data_menu.addAction('Import Telemetry...', self.import_telemetry)
        data_menu.addAction('Data Manager...', self.data_manager)
        
        # 分析菜單
        analysis_menu = menubar.addMenu('Analysis')
        analysis_menu.addAction('Math Channels...', self.math_channels)
        analysis_menu.addAction('Histogram...', self.histogram)
        analysis_menu.addAction('Scatter Plot...', self.scatter_plot)
        analysis_menu.addAction('Report Generator...', self.report_generator)
        
        # 檢視菜單
        view_menu = menubar.addMenu('View')
        view_menu.addAction('Zoom In', self.zoom_in)
        view_menu.addAction('Zoom Out', self.zoom_out)
        view_menu.addAction('Fit to Window', self.fit_window)
        view_menu.addSeparator()
        view_menu.addAction('Show Track Map', self.show_track_map)
        view_menu.addAction('Show Instruments', self.show_instruments)
        
    def create_motec_toolbar(self):
        """創建MoTeC風格工具欄"""
        toolbar = QToolBar()
        toolbar.setObjectName("MoTeCToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.addToolBar(toolbar)
        
        # 檔案操作
        toolbar.addAction("📁", self.open_data)
        toolbar.addAction("💾", self.save_workspace)
        toolbar.addSeparator()
        
        # 檢視控制
        toolbar.addAction("🔍+", self.zoom_in)
        toolbar.addAction("🔍-", self.zoom_out)
        toolbar.addAction("📐", self.fit_window)
        toolbar.addSeparator()
        
        # 分析工具
        toolbar.addAction("📊", self.histogram)
        toolbar.addAction("📈", self.scatter_plot)
        toolbar.addAction("🧮", self.math_channels)
        toolbar.addSeparator()
        
        # 播放控制
        toolbar.addAction("⏮️", self.first_frame)
        toolbar.addAction("⏪", self.prev_frame)
        toolbar.addAction("▶️", self.play)
        toolbar.addAction("⏩", self.next_frame)
        toolbar.addAction("⏭️", self.last_frame)
        
    def create_motec_parameter_panel(self):
        """創建MoTeC風格參數面板"""
        frame = QFrame()
        frame.setObjectName("MoTeCParameterFrame")
        frame.setFixedHeight(40)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)
        
        # 會話選擇
        layout.addWidget(QLabel("Session:"))
        session_combo = QComboBox()
        session_combo.addItems(["Japan 2025 - Race", "Japan 2025 - Qualifying", "Japan 2025 - Practice"])
        session_combo.setCurrentText("Japan 2025 - Race")
        session_combo.setFixedSize(150, 24)
        layout.addWidget(session_combo)
        
        # 車手選擇
        layout.addWidget(QLabel("Driver:"))
        driver_combo = QComboBox()
        driver_combo.addItems(["VER - Max Verstappen", "LEC - Charles Leclerc", "HAM - Lewis Hamilton"])
        driver_combo.setCurrentText("VER - Max Verstappen")
        driver_combo.setFixedSize(150, 24)
        layout.addWidget(driver_combo)
        
        # 圈數範圍
        layout.addWidget(QLabel("Lap:"))
        lap_spinner = QSpinBox()
        lap_spinner.setRange(1, 70)
        lap_spinner.setValue(15)
        lap_spinner.setFixedSize(60, 24)
        layout.addWidget(lap_spinner)
        
        layout.addWidget(QLabel("to"))
        
        lap_end_spinner = QSpinBox()
        lap_end_spinner.setRange(1, 70)
        lap_end_spinner.setValue(25)
        lap_end_spinner.setFixedSize(60, 24)
        layout.addWidget(lap_end_spinner)
        
        layout.addStretch()
        
        # 同步選項
        sync_cb = QCheckBox("Sync Cursors")
        sync_cb.setChecked(True)
        layout.addWidget(sync_cb)
        
        overlay_cb = QCheckBox("Overlay Mode")
        layout.addWidget(overlay_cb)
        
        layout.addStretch()
        
        # 時間範圍
        layout.addWidget(QLabel("Time Range:"))
        time_slider = QSlider(Qt.Horizontal)
        time_slider.setRange(0, 100)
        time_slider.setValue(50)
        time_slider.setFixedWidth(200)
        layout.addWidget(time_slider)
        
        return frame
        
    def create_motec_data_tree(self):
        """創建MoTeC風格數據樹"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # 標題
        title_frame = QFrame()
        title_frame.setObjectName("DataTreeTitle")
        title_frame.setFixedHeight(22)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(4, 2, 4, 2)
        title_layout.addWidget(QLabel("Data Channels"))
        layout.addWidget(title_frame)
        
        # 搜尋框
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search channels...")
        search_box.setFixedHeight(20)
        layout.addWidget(search_box)
        
        # 數據樹
        tree = QTreeWidget()
        tree.setObjectName("MoTeCDataTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(12)
        
        # 速度數據
        speed_group = QTreeWidgetItem(tree, ["🚗 Speed"])
        speed_group.setExpanded(True)
        QTreeWidgetItem(speed_group, ["Ground Speed"])
        QTreeWidgetItem(speed_group, ["Wheel Speed FL"])
        QTreeWidgetItem(speed_group, ["Wheel Speed FR"])
        QTreeWidgetItem(speed_group, ["Wheel Speed RL"])
        QTreeWidgetItem(speed_group, ["Wheel Speed RR"])
        
        # 引擎數據
        engine_group = QTreeWidgetItem(tree, ["⚙️ Engine"])
        engine_group.setExpanded(True)
        QTreeWidgetItem(engine_group, ["Engine RPM"])
        QTreeWidgetItem(engine_group, ["Throttle Position"])
        QTreeWidgetItem(engine_group, ["Engine Temperature"])
        QTreeWidgetItem(engine_group, ["Oil Pressure"])
        QTreeWidgetItem(engine_group, ["Fuel Flow"])
        
        # 煞車系統
        brake_group = QTreeWidgetItem(tree, ["🛑 Brakes"])
        brake_group.setExpanded(True)
        QTreeWidgetItem(brake_group, ["Brake Pressure"])
        QTreeWidgetItem(brake_group, ["Brake Temp FL"])
        QTreeWidgetItem(brake_group, ["Brake Temp FR"])
        QTreeWidgetItem(brake_group, ["Brake Temp RL"])
        QTreeWidgetItem(brake_group, ["Brake Temp RR"])
        
        # 懸吊系統
        suspension_group = QTreeWidgetItem(tree, ["🔧 Suspension"])
        QTreeWidgetItem(suspension_group, ["Ride Height FL"])
        QTreeWidgetItem(suspension_group, ["Ride Height FR"])
        QTreeWidgetItem(suspension_group, ["Damper FL"])
        QTreeWidgetItem(suspension_group, ["Damper FR"])
        
        # 空氣動力學
        aero_group = QTreeWidgetItem(tree, ["✈️ Aerodynamics"])
        QTreeWidgetItem(aero_group, ["Front Wing Angle"])
        QTreeWidgetItem(aero_group, ["Rear Wing Angle"])
        QTreeWidgetItem(aero_group, ["DRS Position"])
        
        # GPS和定位
        gps_group = QTreeWidgetItem(tree, ["🌐 GPS/Position"])
        QTreeWidgetItem(gps_group, ["Latitude"])
        QTreeWidgetItem(gps_group, ["Longitude"])
        QTreeWidgetItem(gps_group, ["Track Position"])
        QTreeWidgetItem(gps_group, ["Distance"])
        
        layout.addWidget(tree)
        
        # 通道統計
        stats_frame = QFrame()
        stats_frame.setObjectName("ChannelStats")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(4, 4, 4, 4)
        stats_layout.addWidget(QLabel("Channel Statistics"))
        stats_layout.addWidget(QLabel("Min: 0.00"))
        stats_layout.addWidget(QLabel("Max: 324.50"))
        stats_layout.addWidget(QLabel("Avg: 156.75"))
        layout.addWidget(stats_frame)
        
        return widget
        
    def create_motec_chart_area(self):
        """創建MoTeC風格圖表區域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        # 圖表堆疊
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(1)
        
        # 速度圖表
        speed_chart = MoTeCDataChannelWidget("Ground Speed [km/h]", "speed")
        chart_layout.addWidget(speed_chart)
        
        # RPM圖表
        rpm_chart = MoTeCDataChannelWidget("Engine RPM", "rpm")
        chart_layout.addWidget(rpm_chart)
        
        # 煞車壓力圖表
        brake_chart = MoTeCDataChannelWidget("Brake Pressure [%]", "brake")
        chart_layout.addWidget(brake_chart)
        
        # 齒輪圖表
        gear_chart = MoTeCDataChannelWidget("Gear", "gear")
        chart_layout.addWidget(gear_chart)
        
        # 節流閥圖表
        throttle_chart = MoTeCDataChannelWidget("Throttle Position [%]", "throttle")
        chart_layout.addWidget(throttle_chart)
        
        layout.addWidget(chart_container)
        
        return widget
        
    def create_motec_bottom_panel(self):
        """創建MoTeC風格底部面板"""
        panel = QWidget()
        panel.setFixedHeight(140)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # 賽道圖區域
        track_frame = QFrame()
        track_frame.setObjectName("TrackMapFrame")
        track_layout = QVBoxLayout(track_frame)
        track_layout.setContentsMargins(4, 4, 4, 4)
        
        track_title = QLabel("Track Map - Suzuka Circuit")
        track_title.setObjectName("TrackTitle")
        track_layout.addWidget(track_title)
        
        track_widget = QWidget()
        track_widget.setObjectName("TrackMap")
        track_widget.setMinimumSize(200, 100)
        track_layout.addWidget(track_widget)
        
        layout.addWidget(track_frame, 1)
        
        # 儀表區域
        instruments_frame = QFrame()
        instruments_frame.setObjectName("InstrumentsFrame")
        instruments_layout = QGridLayout(instruments_frame)
        instruments_layout.setContentsMargins(4, 4, 4, 4)
        instruments_layout.setSpacing(4)
        
        # RPM表
        rpm_instrument = MoTeCInstrumentWidget("rpm")
        instruments_layout.addWidget(rpm_instrument, 0, 0)
        
        # 速度表
        speed_instrument = MoTeCInstrumentWidget("speed")
        instruments_layout.addWidget(speed_instrument, 0, 1)
        
        # 齒輪顯示
        gear_instrument = MoTeCInstrumentWidget("gear")
        instruments_layout.addWidget(gear_instrument, 0, 2)
        
        # 數值顯示區
        values_frame = QFrame()
        values_frame.setObjectName("ValuesFrame")
        values_layout = QGridLayout(values_frame)
        values_layout.setContentsMargins(4, 4, 4, 4)
        
        # 添加各種數值顯示
        values_layout.addWidget(QLabel("Lap Time:"), 0, 0)
        values_layout.addWidget(QLabel("1:29.347"), 0, 1)
        values_layout.addWidget(QLabel("Sector 1:"), 1, 0)
        values_layout.addWidget(QLabel("26.148"), 1, 1)
        values_layout.addWidget(QLabel("Sector 2:"), 2, 0)
        values_layout.addWidget(QLabel("35.672"), 2, 1)
        values_layout.addWidget(QLabel("Sector 3:"), 3, 0)
        values_layout.addWidget(QLabel("27.527"), 3, 1)
        
        instruments_layout.addWidget(values_frame, 0, 3)
        
        layout.addWidget(instruments_frame, 1)
        
        return panel
        
    def create_motec_status_bar(self):
        """創建MoTeC風格狀態列"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 數據狀態
        data_label = QLabel("📊 Data: Loaded")
        cursor_label = QLabel("⏱️ Cursor: 15.2 sec")
        position_label = QLabel("📍 Position: 1250.5 m")
        lap_label = QLabel("🏁 Lap: 15/53")
        
        status_bar.addWidget(data_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(cursor_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(position_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(lap_label)
        
        # 右側信息
        session_label = QLabel("Session: Japan 2025 Race - VER")
        session_label.setObjectName("SessionInfo")
        status_bar.addPermanentWidget(session_label)
        
    # 事件處理方法
    def new_workspace(self): print("New Workspace")
    def open_data(self): print("Open Data")
    def save_workspace(self): print("Save Workspace")
    def export_report(self): print("Export Report")
    def load_session(self): print("Load Session")
    def import_telemetry(self): print("Import Telemetry")
    def data_manager(self): print("Data Manager")
    def math_channels(self): print("Math Channels")
    def histogram(self): print("Histogram")
    def scatter_plot(self): print("Scatter Plot")
    def report_generator(self): print("Report Generator")
    def zoom_in(self): print("Zoom In")
    def zoom_out(self): print("Zoom Out")
    def fit_window(self): print("Fit Window")
    def show_track_map(self): print("Show Track Map")
    def show_instruments(self): print("Show Instruments")
    def first_frame(self): print("First Frame")
    def prev_frame(self): print("Previous Frame")
    def play(self): print("Play")
    def next_frame(self): print("Next Frame")
    def last_frame(self): print("Last Frame")
        
    def apply_style_e(self):
        """應用風格E樣式 - MoTeC風格專業數據分析工作站"""
        style = """
        /* 主視窗 - MoTeC深色主題 */
        QMainWindow {
            background-color: #0F0F0F;
            color: #FFFFFF;
            font-family: "Arial", "Helvetica", sans-serif;
            font-size: 8pt;
        }
        
        /* 菜單欄 - MoTeC風格 */
        QMenuBar {
            background-color: #1E1E1E;
            border-bottom: 1px solid #333333;
            color: #FFFFFF;
            font-size: 8pt;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        QMenuBar::item:selected {
            background-color: #333333;
        }
        QMenu {
            background-color: #1E1E1E;
            border: 1px solid #333333;
            color: #FFFFFF;
        }
        QMenu::item:selected {
            background-color: #333333;
        }
        
        /* MoTeC工具欄 */
        #MoTeCToolbar {
            background-color: #1A1A1A;
            border-bottom: 1px solid #333333;
            color: #FFFFFF;
            font-size: 8pt;
            spacing: 1px;
        }
        #MoTeCToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 3px;
            margin: 1px;
            color: #FFFFFF;
            font-size: 12pt;
        }
        #MoTeCToolbar QToolButton:hover {
            background-color: #333333;
            border: 1px solid #555555;
        }
        #MoTeCToolbar QToolButton:pressed {
            background-color: #111111;
        }
        
        /* MoTeC參數面板 */
        #MoTeCParameterFrame {
            background-color: #1A1A1A;
            border: 1px solid #333333;
        }
        
        /* 下拉選單 - MoTeC風格 */
        QComboBox {
            background-color: #2A2A2A;
            border: 1px solid #444444;
            color: #FFFFFF;
            padding: 2px 4px;
            font-size: 8pt;
        }
        QComboBox:hover {
            border-color: #666666;
        }
        QComboBox::drop-down {
            border: none;
            width: 16px;
            background-color: #333333;
        }
        QComboBox QAbstractItemView {
            background-color: #2A2A2A;
            border: 1px solid #444444;
            color: #FFFFFF;
            selection-background-color: #444444;
        }
        
        /* 數據樹標題 */
        #DataTreeTitle {
            background-color: #1E1E1E;
            border-bottom: 1px solid #333333;
        }
        
        /* MoTeC數據樹 */
        #MoTeCDataTree {
            background-color: #0F0F0F;
            border: 1px solid #333333;
            color: #FFFFFF;
            outline: none;
            font-size: 8pt;
        }
        #MoTeCDataTree::item {
            height: 18px;
            border: none;
            padding: 1px 2px;
        }
        #MoTeCDataTree::item:hover {
            background-color: #1A1A1A;
        }
        #MoTeCDataTree::item:selected {
            background-color: #333333;
            color: #FFFFFF;
        }
        
        /* 數據通道小部件 */
        #DataChannelWidget {
            background-color: #0A0A0A;
            border: 1px solid #222222;
            border-radius: 2px;
        }
        
        /* 通道標題 */
        #ChannelTitle {
            background-color: #1A1A1A;
            border-bottom: 1px solid #333333;
        }
        #ChannelLabel {
            color: #CCCCCC;
            font-weight: bold;
            font-size: 8pt;
        }
        
        /* 數值顯示 */
        #SpeedValue {
            color: #00FF00;
            font-weight: bold;
            font-size: 8pt;
        }
        #RPMValue {
            color: #FFFF00;
            font-weight: bold;
            font-size: 8pt;
        }
        #BrakeValue {
            color: #FF4444;
            font-weight: bold;
            font-size: 8pt;
        }
        #GearValue {
            color: #00CCFF;
            font-weight: bold;
            font-size: 8pt;
        }
        #DefaultValue {
            color: #FFFFFF;
            font-weight: bold;
            font-size: 8pt;
        }
        
        /* 圖表區域 */
        #ChartArea {
            background-color: #000000;
            border: 1px solid #333333;
        }
        
        /* 賽道圖框架 */
        #TrackMapFrame {
            background-color: #0F0F0F;
            border: 1px solid #333333;
        }
        #TrackTitle {
            color: #CCCCCC;
            font-weight: bold;
            font-size: 8pt;
        }
        #TrackMap {
            background-color: #000000;
            border: 1px solid #222222;
        }
        
        /* 儀表框架 */
        #InstrumentsFrame {
            background-color: #0F0F0F;
            border: 1px solid #333333;
        }
        #InstrumentWidget {
            background-color: #1A1A1A;
            border: 1px solid #333333;
            border-radius: 4px;
        }
        #InstrumentValue {
            color: #00FF00;
            font-weight: bold;
            font-size: 14pt;
        }
        #GearDisplay {
            color: #00CCFF;
            font-weight: bold;
            font-size: 24pt;
        }
        
        /* 數值框架 */
        #ValuesFrame {
            background-color: #1A1A1A;
            border: 1px solid #333333;
        }
        
        /* 通道統計 */
        #ChannelStats {
            background-color: #0F0F0F;
            border: 1px solid #333333;
            color: #CCCCCC;
            font-size: 7pt;
        }
        
        /* 搜尋框 */
        QLineEdit {
            background-color: #2A2A2A;
            border: 1px solid #444444;
            color: #FFFFFF;
            padding: 2px 4px;
            font-size: 8pt;
        }
        QLineEdit:focus {
            border-color: #666666;
        }
        
        /* 滑桿 */
        QSlider::groove:horizontal {
            border: 1px solid #333333;
            height: 6px;
            background: #0F0F0F;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #666666;
            border: 1px solid #444444;
            width: 12px;
            border-radius: 6px;
            margin: -3px 0;
        }
        QSlider::handle:horizontal:hover {
            background: #888888;
        }
        
        /* 數字框 */
        QSpinBox {
            background-color: #2A2A2A;
            border: 1px solid #444444;
            color: #FFFFFF;
            padding: 2px;
            font-size: 8pt;
        }
        
        /* CheckBox */
        QCheckBox {
            color: #FFFFFF;
            font-size: 8pt;
        }
        QCheckBox::indicator {
            width: 12px;
            height: 12px;
            border: 1px solid #444444;
            background-color: #2A2A2A;
        }
        QCheckBox::indicator:checked {
            background-color: #666666;
            border-color: #888888;
        }
        
        /* 狀態列 */
        QStatusBar {
            background-color: #1A1A1A;
            border-top: 1px solid #333333;
            color: #CCCCCC;
            font-size: 7pt;
        }
        #SessionInfo {
            color: #00CCFF;
            font-weight: bold;
        }
        
        /* 標籤 */
        QLabel {
            color: #FFFFFF;
            font-size: 8pt;
        }
        
        /* 滾動條 */
        QScrollBar:vertical {
            background-color: #1A1A1A;
            width: 10px;
            border: 1px solid #333333;
        }
        QScrollBar::handle:vertical {
            background-color: #444444;
            border-radius: 3px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        """
        
        self.setStyleSheet(style)

def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setApplicationName("F1T GUI Demo - Style E")
    app.setOrganizationName("F1T MoTeC-Style Analysis Team")
    
    # 設置應用程式字體
    font = QFont("Arial", 8)
    app.setFont(font)
    
    # 創建主視窗
    window = StyleEMainWindow()
    window.show()
    
    # 顯示歡迎訊息
    print("🏎️ F1T GUI Demo - 風格E (MoTeC風格專業數據分析) 已啟動")
    print("📊 這是一個模仿MoTeC i2 Pro數據分析軟體的專業界面")
    print("🔧 包含完整的賽車數據分析功能和專業工具")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
