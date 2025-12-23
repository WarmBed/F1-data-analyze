#!/usr/bin/env python3
"""
FIA Parts Classification Analysis - Demo Launcher
==================================================

統一 Demo 選擇器 - 讓用戶選擇要執行的 Demo 版本

Author: F1T Team
Date: 2025-11-07
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QTextEdit, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.gui_i18n import tr


class DemoLauncher(QDialog):
    """Demo 選擇器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_demo = None
        self.setup_ui()
    
    def setup_ui(self):
        """設置 UI"""
        self.setWindowTitle(tr('demo_launcher_title', 'FIA Parts Classification - Demo Launcher'))
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("🏎️ FIA Parts Classification Analysis")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel(tr('select_demo', '請選擇要執行的 Demo 版本'))
        subtitle.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Demo 按鈕組
        demos = [
            {
                'id': 1,
                'title': '📊 Demo 1 - 極簡統計版',
                'description': '• 3 個排行表格（賽事/車隊/車手 Top 10）\n• 基本過濾控制\n• 適合：快速查看整體排名',
                'complexity': '⭐',
                'features': '統計排行',
                'visual': '⭐',
                'interactive': '⭐'
            },
            {
                'id': 2,
                'title': '📈 Demo 2 - 圖表展示版',
                'description': '• 4 個 Matplotlib 圖表（賽事/車隊/車手長條圖 + 類型圓餅圖）\n• 視覺化分析\n• 適合：視覺化報告和趨勢分析',
                'complexity': '⭐⭐',
                'features': '視覺化',
                'visual': '⭐⭐⭐⭐⭐',
                'interactive': '⭐'
            },
            {
                'id': 3,
                'title': '🎛️ Demo 3 - 互動過濾版',
                'description': '• 完整過濾控制（賽事/車隊/車手/類型/信心度）\n• 即時過濾更新\n• 適合：深度探索和自訂過濾條件',
                'complexity': '⭐⭐⭐',
                'features': '互動過濾',
                'visual': '⭐⭐',
                'interactive': '⭐⭐⭐⭐⭐'
            },
            {
                'id': 4,
                'title': '📝 Demo 4 - 詳細表格版 ⭐ (推薦)',
                'description': '• 完整 7 欄位記錄表格（序號/賽事/車隊/車手/類型/信心度/描述）\n• 信心度和類型顏色標記\n• 模仿 accident_analysis 實現\n• 適合：專業分析和查看所有變更細節',
                'complexity': '⭐⭐⭐⭐',
                'features': '完整記錄',
                'visual': '⭐⭐',
                'interactive': '⭐⭐⭐'
            },
            {
                'id': 5,
                'title': '🖼️ Demo 5 - 儀表板綜合版',
                'description': '• Grid Layout 多區塊佈局\n• 統計卡片 + 圓餅圖 + 2 個表格\n• 平衡所有功能\n• 適合：全面展示和管理層報告',
                'complexity': '⭐⭐⭐⭐',
                'features': '綜合儀表板',
                'visual': '⭐⭐⭐⭐',
                'interactive': '⭐⭐'
            }
        ]
        
        for demo in demos:
            group = self.create_demo_group(demo)
            layout.addWidget(group)
        
        layout.addStretch()
        
        # 底部按鈕
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton(tr('cancel', 'Cancel'))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def create_demo_group(self, demo: dict) -> QGroupBox:
        """創建 Demo 組"""
        group = QGroupBox()
        group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding: 15px;
                background-color: #ecf0f1;
            }
            QGroupBox:hover {
                background-color: #d5dbdb;
            }
        """)
        
        layout = QHBoxLayout(group)
        
        # 左側：標題和描述
        left_layout = QVBoxLayout()
        
        title = QLabel(demo['title'])
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        left_layout.addWidget(title)
        
        desc = QLabel(demo['description'])
        desc.setStyleSheet("font-size: 11px; color: #34495e;")
        desc.setWordWrap(True)
        left_layout.addWidget(desc)
        
        # 評分
        ratings = QLabel(f"複雜度: {demo['complexity']} | 視覺化: {demo['visual']} | 互動性: {demo['interactive']}")
        ratings.setStyleSheet("font-size: 10px; color: #7f8c8d; margin-top: 5px;")
        left_layout.addWidget(ratings)
        
        layout.addLayout(left_layout, stretch=3)
        
        # 右側：按鈕
        btn = QPushButton(tr('run_demo', 'Run Demo'))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        btn.clicked.connect(lambda: self.run_demo(demo['id']))
        layout.addWidget(btn, alignment=Qt.AlignVCenter)
        
        return group
    
    def run_demo(self, demo_id: int):
        """執行 Demo"""
        self.selected_demo = demo_id
        self.accept()


def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    launcher = DemoLauncher()
    if launcher.exec_() == QDialog.Accepted:
        demo_id = launcher.selected_demo
        
        if demo_id == 1:
            from demo_1_simple_stats import SimpleStatsWidget
            window = SimpleStatsWidget(2025)
            window.setWindowTitle("Demo 1: Simple Statistics")
        elif demo_id == 2:
            from demo_2_chart_focus import ChartFocusWidget
            window = ChartFocusWidget(2025)
            window.setWindowTitle("Demo 2: Chart Focus")
        elif demo_id == 3:
            from demo_3_interactive_filter import InteractiveFilterWidget
            window = InteractiveFilterWidget(2025)
            window.setWindowTitle("Demo 3: Interactive Filter")
        elif demo_id == 4:
            from demo_4_detailed_table import ClassificationDetailedTableWidget
            window = ClassificationDetailedTableWidget(2025)
            window.setWindowTitle("Demo 4: Detailed Table (Recommended)")
        elif demo_id == 5:
            from demo_5_dashboard import DashboardWidget
            window = DashboardWidget(2025)
            window.setWindowTitle("Demo 5: Dashboard")
        else:
            return
        
        window.resize(1200, 800)
        window.show()
        sys.exit(app.exec_())
    else:
        print("Demo launcher cancelled")


if __name__ == "__main__":
    main()
