#!/usr/bin/env python3
"""
連動 UI 組件
提供標準化的連動按鈕和狀態指示器
"""

from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from typing import Optional


class LinkageButton(QPushButton):
    """
    標準化的連動按鈕
    
    特點：
    - 統一的藍色主題樣式
    - 狀態指示（啟用/停用）
    - 可選的文字和圖標
    """
    
    linkage_toggled = pyqtSignal(bool)  # 連動狀態切換信號
    
    def __init__(self, text: str = "🔗 連動", enabled: bool = True, parent=None):
        super().__init__(text, parent)
        
        self.linkage_enabled = enabled
        self.setup_ui()
        
        # 連接點擊信號
        self.clicked.connect(self.toggle_linkage)
    
    def setup_ui(self):
        """設置UI樣式"""
        self.setFixedSize(80, 30)
        self.setFont(QFont("Arial", 9))
        self.update_style()
    
    def update_style(self):
        """更新按鈕樣式"""
        if self.linkage_enabled:
            # 啟用狀態 - 藍色主題
            style = """
            QPushButton {
                background-color: #1e90ff;
                color: white;
                border: 2px solid #4169e1;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4169e1;
                border-color: #0000cd;
            }
            QPushButton:pressed {
                background-color: #0000cd;
            }
            """
        else:
            # 停用狀態 - 灰色主題
            style = """
            QPushButton {
                background-color: #808080;
                color: #d3d3d3;
                border: 2px solid #696969;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #696969;
            }
            QPushButton:pressed {
                background-color: #556b2f;
            }
            """
        
        self.setStyleSheet(style)
    
    def toggle_linkage(self):
        """切換連動狀態"""
        self.set_linkage_enabled(not self.linkage_enabled)
        self.linkage_toggled.emit(self.linkage_enabled)
    
    def set_linkage_enabled(self, enabled: bool):
        """設置連動狀態"""
        if self.linkage_enabled != enabled:
            self.linkage_enabled = enabled
            self.update_style()
    
    def is_linkage_enabled(self) -> bool:
        """獲取連動狀態"""
        return self.linkage_enabled


class LinkageStatusIndicator(QLabel):
    """
    連動狀態指示器
    
    顯示當前的連動狀態（主開關 + 個別開關）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.master_enabled = True
        self.individual_enabled = True
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """設置UI"""
        self.setFixedSize(24, 24)
        self.setAlignment(Qt.AlignCenter)
    
    def update_status(self):
        """更新狀態顯示"""
        if self.master_enabled and self.individual_enabled:
            # 完全啟用 - 綠色
            self.setText("🟢")
            self.setToolTip("連動已啟用")
        elif self.master_enabled:
            # 主開關啟用，個別停用 - 黃色
            self.setText("🟡")
            self.setToolTip("主連動已啟用，個別連動已停用")
        else:
            # 主開關停用 - 紅色
            self.setText("🔴")
            self.setToolTip("主連動已停用")
    
    def set_master_enabled(self, enabled: bool):
        """設置主開關狀態"""
        self.master_enabled = enabled
        self.update_status()
    
    def set_individual_enabled(self, enabled: bool):
        """設置個別開關狀態"""
        self.individual_enabled = enabled
        self.update_status()


class LinkageControlPanel(QWidget):
    """
    連動控制面板
    
    包含：
    - 主連動開關
    - 個別連動開關
    - 狀態指示器
    - 清除連動按鈕
    """
    
    master_linkage_toggled = pyqtSignal(bool)
    individual_linkage_toggled = pyqtSignal(bool)
    clear_linkage_requested = pyqtSignal()
    
    def __init__(self, show_master: bool = True, show_individual: bool = True, parent=None):
        super().__init__(parent)
        
        self.show_master = show_master
        self.show_individual = show_individual
        
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 狀態指示器
        self.status_indicator = LinkageStatusIndicator(self)
        layout.addWidget(self.status_indicator)
        
        # 主連動按鈕
        if self.show_master:
            self.master_button = LinkageButton("🔗 主連動", True, self)
            self.master_button.linkage_toggled.connect(self.master_linkage_toggled)
            self.master_button.linkage_toggled.connect(self.status_indicator.set_master_enabled)
            layout.addWidget(self.master_button)
        
        # 個別連動按鈕
        if self.show_individual:
            self.individual_button = LinkageButton("🔗 連動", True, self)
            self.individual_button.linkage_toggled.connect(self.individual_linkage_toggled)
            self.individual_button.linkage_toggled.connect(self.status_indicator.set_individual_enabled)
            layout.addWidget(self.individual_button)
        
        # 清除按鈕
        self.clear_button = QPushButton("🗑", self)
        self.clear_button.setFixedSize(30, 30)
        self.clear_button.setToolTip("清除所有連動標記")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: 1px solid #ff5252;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
            QPushButton:pressed {
                background-color: #f44336;
            }
        """)
        self.clear_button.clicked.connect(self.clear_linkage_requested)
        layout.addWidget(self.clear_button)
    
    def set_master_linkage_enabled(self, enabled: bool):
        """設置主連動狀態"""
        if hasattr(self, 'master_button'):
            self.master_button.set_linkage_enabled(enabled)
        self.status_indicator.set_master_enabled(enabled)
    
    def set_individual_linkage_enabled(self, enabled: bool):
        """設置個別連動狀態"""
        if hasattr(self, 'individual_button'):
            self.individual_button.set_linkage_enabled(enabled)
        self.status_indicator.set_individual_enabled(enabled)
    
    def is_master_linkage_enabled(self) -> bool:
        """獲取主連動狀態"""
        return getattr(self, 'master_button', None) and self.master_button.is_linkage_enabled()
    
    def is_individual_linkage_enabled(self) -> bool:
        """獲取個別連動狀態"""
        return getattr(self, 'individual_button', None) and self.individual_button.is_linkage_enabled()


class LinkageToolBar(QFrame):
    """
    連動工具欄
    
    可嵌入到各種容器中的標準化連動控制工具欄
    """
    
    master_linkage_toggled = pyqtSignal(bool)
    individual_linkage_toggled = pyqtSignal(bool)
    clear_linkage_requested = pyqtSignal()
    
    def __init__(self, title: str = "", show_master: bool = True, show_individual: bool = True, parent=None):
        super().__init__(parent)
        
        self.title = title
        self.show_master = show_master
        self.show_individual = show_individual
        
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        
        # 標題
        if self.title:
            title_label = QLabel(self.title, self)
            title_label.setFont(QFont("Arial", 9, QFont.Bold))
            title_label.setStyleSheet("color: #2c3e50;")
            layout.addWidget(title_label)
        
        # 彈性空間
        layout.addStretch()
        
        # 連動控制面板
        self.control_panel = LinkageControlPanel(self.show_master, self.show_individual, self)
        self.control_panel.master_linkage_toggled.connect(self.master_linkage_toggled)
        self.control_panel.individual_linkage_toggled.connect(self.individual_linkage_toggled)
        self.control_panel.clear_linkage_requested.connect(self.clear_linkage_requested)
        layout.addWidget(self.control_panel)
    
    def set_master_linkage_enabled(self, enabled: bool):
        """設置主連動狀態"""
        self.control_panel.set_master_linkage_enabled(enabled)
    
    def set_individual_linkage_enabled(self, enabled: bool):
        """設置個別連動狀態"""
        self.control_panel.set_individual_linkage_enabled(enabled)
    
    def is_master_linkage_enabled(self) -> bool:
        """獲取主連動狀態"""
        return self.control_panel.is_master_linkage_enabled()
    
    def is_individual_linkage_enabled(self) -> bool:
        """獲取個別連動狀態"""
        return self.control_panel.is_individual_linkage_enabled()


def create_linkage_button(text: str = "🔗 連動", enabled: bool = True, parent=None) -> LinkageButton:
    """
    快速創建標準化的連動按鈕
    
    Args:
        text: 按鈕文字
        enabled: 初始狀態
        parent: 父組件
    
    Returns:
        LinkageButton: 配置好的連動按鈕
    """
    return LinkageButton(text, enabled, parent)


def create_linkage_toolbar(title: str = "", show_master: bool = True, show_individual: bool = True, parent=None) -> LinkageToolBar:
    """
    快速創建標準化的連動工具欄
    
    Args:
        title: 工具欄標題
        show_master: 是否顯示主連動按鈕
        show_individual: 是否顯示個別連動按鈕
        parent: 父組件
    
    Returns:
        LinkageToolBar: 配置好的連動工具欄
    """
    return LinkageToolBar(title, show_master, show_individual, parent)
