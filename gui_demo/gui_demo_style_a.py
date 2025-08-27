#!/usr/bin/env python3
"""
F1T GUI Demo - 風格A: 現代扁平化風格
Demo for Style A: Modern Flat Design
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

class StyleAMainWindow(QMainWindow):
    """風格A: 現代扁平化主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏎️ F1 Analysis GUI v5.5 - 風格A Demo")
        self.setMinimumSize(1200, 800)
        self.init_ui()
        self.apply_style_a()
        
    def init_ui(self):
        """初始化用戶界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 參數控制區
        param_widget = self.create_parameter_panel()
        main_layout.addWidget(param_widget)
        
        # 主工作區
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左側功能樹
        left_panel = self.create_function_tree()
        content_splitter.addWidget(left_panel)
        
        # 右側MDI區域
        right_panel = self.create_mdi_workspace()
        content_splitter.addWidget(right_panel)
        
        # 設置分割比例
        content_splitter.setSizes([300, 900])
        main_layout.addWidget(content_splitter)
        
        # 狀態列
        self.create_status_bar()
        
    def create_parameter_panel(self):
        """創建參數控制面板"""
        panel = QWidget()
        panel.setObjectName("ParameterPanel")
        panel.setFixedHeight(80)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(20)
        
        # 年份選擇
        year_combo = QComboBox()
        year_combo.addItems(["2024", "2025"])
        year_combo.setCurrentText("2025")
        year_combo.setFixedSize(100, 40)
        
        # 賽事選擇
        race_combo = QComboBox()
        race_combo.addItems(["Japan", "Singapore", "Las Vegas", "Qatar", "Abu Dhabi"])
        race_combo.setCurrentText("Japan")
        race_combo.setFixedSize(120, 40)
        
        # 賽段選擇
        session_combo = QComboBox()
        session_combo.addItems(["R", "Q", "FP1", "FP2", "FP3", "S"])
        session_combo.setCurrentText("R")
        session_combo.setFixedSize(80, 40)
        
        # 聯動開關
        link_checkbox = QCheckBox("聯動模式")
        link_checkbox.setChecked(True)
        
        # 控制按鈕
        exec_btn = QPushButton("執行")
        exec_btn.setFixedSize(80, 40)
        
        batch_btn = QPushButton("批次")
        batch_btn.setFixedSize(80, 40)
        
        stop_btn = QPushButton("停止")
        stop_btn.setFixedSize(80, 40)
        
        cache_btn = QPushButton("清快取")
        cache_btn.setFixedSize(80, 40)
        
        # 布局
        layout.addWidget(QLabel("年份:"))
        layout.addWidget(year_combo)
        layout.addWidget(QLabel("賽事:"))
        layout.addWidget(race_combo)
        layout.addWidget(QLabel("賽段:"))
        layout.addWidget(session_combo)
        layout.addStretch()
        layout.addWidget(link_checkbox)
        layout.addStretch()
        layout.addWidget(exec_btn)
        layout.addWidget(batch_btn)
        layout.addWidget(stop_btn)
        layout.addWidget(cache_btn)
        
        return panel
        
    def create_function_tree(self):
        """創建功能樹狀導航"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 搜尋框
        search_box = QLineEdit()
        search_box.setPlaceholderText("🔍 搜尋功能...")
        search_box.setFixedHeight(35)
        layout.addWidget(search_box)
        
        # 功能樹
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        
        # 收藏夾
        favorites = QTreeWidgetItem(tree, ["⭐ 收藏夾"])
        favorites.setExpanded(True)
        QTreeWidgetItem(favorites, ["📁 車手分析"])
        QTreeWidgetItem(favorites, ["📁 賽事分析"])
        
        # 基礎分析模組
        basic = QTreeWidgetItem(tree, ["📋 基礎分析模組"])
        basic.setExpanded(True)
        QTreeWidgetItem(basic, ["🌧️ 降雨強度分析"])
        QTreeWidgetItem(basic, ["🛣️ 賽道路線分析"])
        QTreeWidgetItem(basic, ["🏆 車手最快進站"])
        QTreeWidgetItem(basic, ["🏁 車隊進站排行"])
        QTreeWidgetItem(basic, ["🛞 進站詳細記錄"])
        
        # 進階分析模組
        advanced = QTreeWidgetItem(tree, ["🔧 進階分析模組"])
        advanced.setExpanded(True)
        QTreeWidgetItem(advanced, ["📡 車手詳細遙測"])
        QTreeWidgetItem(advanced, ["🤝 雙車手比較"])
        QTreeWidgetItem(advanced, ["🎯 動態彎道檢測"])
        QTreeWidgetItem(advanced, ["📈 賽事位置變化"])
        
        # 系統功能
        system = QTreeWidgetItem(tree, ["🚀 系統功能"])
        QTreeWidgetItem(system, ["📊 數據導出管理"])
        QTreeWidgetItem(system, ["🔄 暫存優化"])
        QTreeWidgetItem(system, ["🔍 系統診斷"])
        
        layout.addWidget(tree)
        
        # 添加點擊事件
        tree.itemClicked.connect(self.on_tree_item_clicked)
        
        return widget
        
    def create_mdi_workspace(self):
        """創建MDI工作區"""
        # 分頁容器
        tab_widget = QTabWidget()
        tab_widget.setTabsClosable(True)
        tab_widget.setMovable(True)
        
        # 第一個分頁 - 降雨分析
        mdi_area1 = QMdiArea()
        tab_widget.addTab(mdi_area1, "降雨分析")
        
        # 添加示例視窗
        self.add_sample_window(mdi_area1, "降雨強度數據", self.create_sample_table())
        
        # 第二個分頁 - 車手比較
        mdi_area2 = QMdiArea()
        tab_widget.addTab(mdi_area2, "車手比較")
        
        # 添加新分頁按鈕
        tab_widget.addTab(QWidget(), "+")
        tab_widget.tabBarClicked.connect(self.on_tab_clicked)
        
        return tab_widget
        
    def add_sample_window(self, mdi_area, title, content):
        """添加示例視窗到MDI區域"""
        sub_window = QMdiSubWindow()
        sub_window.setWidget(content)
        sub_window.setWindowTitle(title)
        sub_window.resize(400, 300)
        mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
    def create_sample_table(self):
        """創建示例表格"""
        table = QTableWidget(5, 3)
        table.setHorizontalHeaderLabels(["時間", "降雨強度", "賽道狀況"])
        
        # 示例數據
        data = [
            ["1:23:45", "HIGH", "濕滑"],
            ["1:24:12", "MEDIUM", "潮濕"],
            ["1:24:38", "LOW", "乾燥"],
            ["1:25:05", "NONE", "乾燥"],
            ["1:25:32", "MEDIUM", "潮濕"]
        ]
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                table.setItem(row, col, QTableWidgetItem(value))
                
        return table
        
    def create_status_bar(self):
        """創建狀態列"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # 進度條
        progress = QProgressBar()
        progress.setValue(80)
        progress.setMaximumWidth(150)
        
        # 狀態標籤
        cache_label = QLabel("💾 快取: 156MB")
        api_label = QLabel("📡 API: 🔴")
        error_label = QLabel("⚠️ 錯誤: 無")
        memory_label = QLabel("🖥️ 記憶體: 2.1GB")
        
        status_bar.addWidget(QLabel("📊 進度:"))
        status_bar.addWidget(progress)
        status_bar.addPermanentWidget(cache_label)
        status_bar.addPermanentWidget(api_label)
        status_bar.addPermanentWidget(error_label)
        status_bar.addPermanentWidget(memory_label)
        
    def on_tree_item_clicked(self, item, column):
        """處理功能樹點擊事件"""
        if item.parent():  # 只處理子項目
            function_name = item.text(0)
            print(f"選擇功能: {function_name}")
            
    def on_tab_clicked(self, index):
        """處理分頁點擊事件"""
        tab_widget = self.sender()
        if tab_widget.tabText(index) == "+":
            # 添加新分頁
            new_mdi = QMdiArea()
            count = tab_widget.count()
            tab_widget.insertTab(count-1, new_mdi, f"新分析 {count-1}")
            tab_widget.setCurrentIndex(count-1)
        
    def apply_style_a(self):
        """應用風格A樣式"""
        style = """
        /* 主視窗 */
        QMainWindow {
            background-color: #FFFFFF;
            color: #2C3E50;
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            font-size: 9pt;
        }
        
        /* 參數面板 */
        #ParameterPanel {
            background-color: #F5F5F5;
            border-radius: 12px;
            border: 1px solid #E5E7EB;
        }
        
        /* 下拉選單 */
        QComboBox {
            background-color: #FFFFFF;
            border: 2px solid #BDC3C7;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 9pt;
        }
        QComboBox:hover {
            border-color: #3498DB;
        }
        QComboBox:focus {
            border-color: #2980B9;
        }
        
        /* 按鈕 */
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #3498DB, stop:1 #2980B9);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 9pt;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #5DADE2, stop:1 #3498DB);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #2980B9, stop:1 #1F618D);
        }
        
        /* 搜尋框 */
        QLineEdit {
            background-color: #FFFFFF;
            border: 2px solid #BDC3C7;
            border-radius: 18px;
            padding: 8px 15px;
            font-size: 9pt;
        }
        QLineEdit:focus {
            border-color: #3498DB;
        }
        
        /* 功能樹 */
        QTreeWidget {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            outline: none;
            font-size: 9pt;
        }
        QTreeWidget::item {
            height: 32px;
            border-radius: 6px;
            margin: 2px;
            padding: 4px 8px;
        }
        QTreeWidget::item:hover {
            background-color: #F8FAFF;
            border: 1px solid #D6EAF8;
        }
        QTreeWidget::item:selected {
            background-color: #3498DB;
            color: white;
        }
        
        /* 分頁標籤 */
        QTabWidget::pane {
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            background-color: #F8FAFF;
        }
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #F8F9FA, stop:1 #E9ECEF);
            border: 1px solid #DEE2E6;
            border-radius: 8px 8px 0 0;
            padding: 10px 16px;
            margin-right: 2px;
            font-size: 9pt;
        }
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #FFFFFF, stop:1 #F8FAFF);
            border-bottom: none;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #E8F4FD, stop:1 #D6EAF8);
        }
        
        /* MDI區域 */
        QMdiArea {
            background-color: #F8FAFF;
        }
        QMdiSubWindow {
            border: 1px solid #D6EAF8;
            border-radius: 8px;
            background-color: #FFFFFF;
        }
        
        /* 表格 */
        QTableWidget {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            gridline-color: #F1F2F6;
        }
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                        stop:0 #F8F9FA, stop:1 #E9ECEF);
            border: 1px solid #DEE2E6;
            padding: 8px;
            font-weight: bold;
        }
        
        /* 狀態列 */
        QStatusBar {
            background-color: #F5F5F5;
            border-top: 1px solid #E5E7EB;
            color: #2C3E50;
            font-size: 8pt;
        }
        QProgressBar {
            border: 1px solid #BDC3C7;
            border-radius: 6px;
            background-color: #ECF0F1;
            text-align: center;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #3498DB, stop:1 #2980B9);
            border-radius: 5px;
        }
        
        /* CheckBox */
        QCheckBox {
            font-size: 9pt;
            color: #2C3E50;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid #BDC3C7;
            background-color: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background-color: #3498DB;
            border-color: #2980B9;
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
    app.setApplicationName("F1T GUI Demo - Style A")
    app.setOrganizationName("F1T Team")
    
    # 設置應用程式字體
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 創建主視窗
    window = StyleAMainWindow()
    window.show()
    
    # 顯示歡迎訊息
    print("🎨 F1T GUI Demo - 風格A (現代扁平化) 已啟動")
    print("📋 這是一個展示風格A界面設計的Demo")
    print("🔧 包含所有主要UI組件的展示")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
