#!/usr/bin/env python3
"""
F1T 事故綜合分析 MDI 模組
基於 FEATURE_20250831_事故統計總覽Widget開發規格 實現
參考進站分析模組的成功架構設計
修正版：移除 PyQt5 不支援的 CSS 屬性
"""

import sys
import os
import json
import datetime
import traceback
import subprocess
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QStatusBar, QToolBar, QAction,
    QHeaderView, QDialog, QDialogButtonBox, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QTextEdit, QMessageBox, QFrame,
    QTabWidget, QScrollArea, QSplitter, QAbstractItemView, QLineEdit,
    QBoxLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 導入翻譯函數
from core.gui_i18n import tr

# 導入分析模組介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    # 如果都失敗，定義一個基本的接口
    from PyQt5.QtCore import QObject
    class IAnalysisModule(QObject):
        def __init__(self, parent=None):
            super().__init__(parent)

# API 化後的數據管理器
from .accident_data_manager import AccidentDataManager


class AccidentStatisticsWidget(QWidget):
    """事故統計總覽Widget - Function 6數據展示 (完全按照規格實現)"""
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.statistics_data = {}
        self._simplified_cards = False
        self.setup_ui()
        
    def setup_ui(self):
        """設置使用者界面 - 簡化設計：統計表格 + 車手圖表 + Safety Periods"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)  # 減少邊距
        layout.setSpacing(8)  # 大幅減少間距
        
        # 第1行：Flag Statistics - 統計表格（固定高度，橫向顯示）
        self.statistics_table = self.setup_statistics_table()
        layout.addWidget(self.statistics_table, 0)  # stretch = 0，不擴展
        
        # 第2行：Driver Incident Frequency - 車手事故頻率條形圖（內容驅動）
        self.driver_chart = DriverIncidentBarChart()
        layout.addWidget(self.driver_chart, 0)  # stretch = 0，不擴展
        
        # 第3行：Safety Periods（可擴展）
        self.safety_periods_widget = SafetyPeriodsWidget()
        layout.addWidget(self.safety_periods_widget, 1)  # stretch = 1，可擴展
        
        # 保存舊的引用以保持相容性
        self.cards_layout = None  # 不再使用卡片
        self.tables_layout = None  # 不再使用舊表格
        self.tables_container = QWidget()
        
        # 狀態列
        self.status_layout = QHBoxLayout()
        layout.addLayout(self.status_layout)
    
    def resizeEvent(self, event):
        """響應式調整 - 簡化設計：主要針對表格和圖表優化"""
        super().resizeEvent(event)

        # ⚠️ 移除干擾代碼：不再動態調整 stats_table 高度
        # 簡化設計採用固定高度，所有組件都是垂直堆疊
        # Flag Statistics Summary: 固定 80px (容器) + 55px (表格)
        # Driver Chart: 內容驅動高度
        # Safety Periods: 可擴展填充剩餘空間
        pass
        
    def setup_statistics_cards(self):
        """設置統計卡片區域 - 新版本：Track Limit、雙黃旗、黃旗、紅旗次數"""
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        # Track Limit 違規卡片
        self.track_limit_card = self.create_stat_card(
            tr("track_limit_violations", "⚠️ Track Limit"),
            "0",
            tr("violations_count", "(違規次數)"),
            "#FF9800",
            simple_title="⚠️▲",
        )
        cards_layout.addWidget(self.track_limit_card)
        
        # 雙黃旗卡片
        self.double_yellow_card = self.create_stat_card(
            tr("double_yellow_flag", "🟡🟡 雙黃旗"), 
            "0", 
            tr("display_count", "(出示次數)"),
            "#FFC107",
            simple_title="🟡🟡",
        )
        cards_layout.addWidget(self.double_yellow_card)
        
        # 黃旗卡片
        self.yellow_flag_card = self.create_stat_card(
            tr("yellow_flag", "🟡 黃旗"), 
            "0", 
            tr("display_count", "(出示次數)"),
            "#FFEB3B",
            simple_title="🟡",
        )
        cards_layout.addWidget(self.yellow_flag_card)
        
        # 紅旗卡片
        self.red_flag_card = self.create_stat_card(
            tr("red_flag", "🔴 紅旗"), 
            "0", 
            tr("display_count", "(出示次數)"),
            "#F44336",
            simple_title="🔴",
        )
        cards_layout.addWidget(self.red_flag_card)

        self._update_card_display_mode()

        return cards_layout
    
    def setup_statistics_table(self):
        """設置統計表格 - 橫向顯示，無外框"""
        # 創建容器 Widget（無邊框）
        container = QWidget()
        
        # ⚠️ 修復：增加容器高度以容納完整的表格內容
        container.setFixedHeight(64)  # 增加高度確保所有內容可見
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 水平可擴展，垂直固定
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
        layout.setSpacing(0)  # 無間距
        layout.setAlignment(Qt.AlignTop)  # ⚠️ 關鍵修復：內容向上對齊
        
        # 標題標籤 - 隱藏
        # title_label = QLabel(tr('flag_statistics_summary', '📊 Flag Statistics Summary'))
        # title_label.setStyleSheet("""
        #     QLabel {
        #         font-size: 14px;
        #         font-weight: bold;
        #         color: #333;
        #         margin-bottom: 5px;
        #     }
        # """)
        # layout.addWidget(title_label)
        
        # 建立橫向統計表格
        self.stats_table = QTableWidget()
        self.stats_table.setRowCount(1)  # 只有一行數據
        self.stats_table.setColumnCount(4)  # 四個旗標類型
        
        # 設置橫向標題
        self.stats_table.setHorizontalHeaderLabels([
            tr("track_limit_short", "⚠️ Track Limit"),
            tr("double_yellow_short", "🟡🟡 Double Yellow"),
            tr("yellow_flag_short", "🟡 Yellow Flag"),
            tr("red_flag_short", "🔴 Red Flag")
        ])
        
        # 設置表格樣式 - 允許欄位自動調整寬度
        self.stats_table.setAlternatingRowColors(False)
        self.stats_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        # ✅ 修復：使用 Stretch 模式讓欄位平均分配空間，確保內容完整顯示
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        
        # ⚠️ 深度修復：調整高度參數以正確顯示數字
        # 計算：標題行(24px) + 數據行(36px) + 邊框(4px) = 64px
        self.stats_table.setFixedHeight(64)  # 增加高度確保數字不被截斷
        
        # 設置標題行高度
        header = self.stats_table.horizontalHeader()
        header.setFixedHeight(24)  # 標題行增加到 24px，確保標題完整顯示
        
        # 設置數據行高度 - 增加到 36px 以確保數字不被截斷
        self.stats_table.setRowHeight(0, 36)  # 數據行 36px，確保數字完整顯示
        
        # 設置大小政策：水平可擴展，垂直固定（與Driver Chart類似的行為）
        self.stats_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 簡潔樣式，數字置中且清晰可見
        self.stats_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                text-align: center;
                padding: 6px 4px;
                font-size: 20px;
                font-weight: bold;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 4px 2px;
                font-size: 11px;
                font-weight: bold;
                text-align: center;
                height: 24px;
            }
        """)
        
        # 初始化橫向數據（一行四列） - 使用 Qt.AlignCenter 確保數字置中顯示
        for col in range(4):
            item = QTableWidgetItem("0")
            item.setTextAlignment(Qt.AlignCenter)  # ⚠️ 關鍵修復：確保數字置中
            self.stats_table.setItem(0, col, item)
        
        layout.addWidget(self.stats_table)
        return container
        
    def create_stat_card(
        self,
        title,
        value,
        subtitle,
        color,
        *,
        simple_title: Optional[str] = None,
    ):
        """創建統計卡片 (修正版：恢復原始背景、黃色文字改黑色、完全移除數值方框)"""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        
        # 根據顏色決定文字顏色
        if color in ["#FFC107", "#FFEB3B"]:  # 黃色系改為黑色文字
            text_color = "#000000"
        else:
            text_color = color
        
        # 標題標籤
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 14px; 
            font-weight: bold; 
            color: {text_color};
            margin-bottom: 5px;
            background-color: transparent;
            border: none;
        """)
        layout.addWidget(title_label)
        
        # 主數值標籤 (完全移除方框樣式)
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"""
            font-size: 32px; 
            font-weight: bold; 
            color: {text_color};
            margin: 10px 0;
            background-color: transparent;
            border: none;
            padding: 0px;
        """)
        layout.addWidget(value_label)
        
        # 副標題標籤 (隱藏)
        # subtitle_label = QLabel(subtitle)
        # subtitle_label.setAlignment(Qt.AlignCenter)
        # subtitle_label.setStyleSheet("""
        #     font-size: 11px; 
        #     color: #666;
        #     margin-top: 5px;
        # """)
        # layout.addWidget(subtitle_label)
        
        # 儲存標籤參考以便後續更新
        card.title_label = title_label
        card.value_label = value_label
        card.full_title = title
        card.simple_title = simple_title or title
        card.full_title_stylesheet = title_label.styleSheet()
        card.full_value_stylesheet = value_label.styleSheet()
        card.text_color = text_color
        card.simple_title_stylesheet = (
            "\n".join(
                [
                    "font-size: 20px;",
                    "font-weight: bold;",
                    f"color: {text_color};",
                    "background-color: transparent;",
                    "border: none;",
                    "margin: 0px;",
                ]
            )
        )
        card.simple_value_stylesheet = (
            "\n".join(
                [
                    "font-size: 24px;",
                    "font-weight: bold;",
                    f"color: {text_color};",
                    "margin: 4px 0;",
                    "background-color: transparent;",
                    "border: none;",
                    "padding: 0px;",
                ]
            )
        )
        # card.subtitle_label = subtitle_label  # 已隱藏
        
        return card

    def _update_card_display_mode(self) -> None:
        cards = [
            getattr(self, "track_limit_card", None),
            getattr(self, "double_yellow_card", None),
            getattr(self, "yellow_flag_card", None),
            getattr(self, "red_flag_card", None),
        ]

        widget_width = max(1, self.width())
        emoji_font_size = max(16, min(40, int(widget_width * 0.045)))
        value_font_size = max(14, min(36, int(widget_width * 0.04)))

        for card in cards:
            if not card or not hasattr(card, "title_label"):
                continue

            if self._simplified_cards:
                card.title_label.setText(card.simple_title)
                card.title_label.setStyleSheet(
                    "\n".join(
                        [
                            f"font-size: {emoji_font_size}px;",
                            "font-weight: bold;",
                            f"color: {card.text_color};",
                            "background-color: transparent;",
                            "border: none;",
                            "margin: 0px;",
                        ]
                    )
                )
                card.value_label.setStyleSheet(
                    "\n".join(
                        [
                            f"font-size: {value_font_size}px;",
                            "font-weight: bold;",
                            f"color: {card.text_color};",
                            "margin: 4px 0;",
                            "background-color: transparent;",
                            "border: none;",
                            "padding: 0px;",
                        ]
                    )
                )
            else:
                card.title_label.setText(card.full_title)
                card.title_label.setStyleSheet(card.full_title_stylesheet)
                card.value_label.setStyleSheet(card.full_value_stylesheet)
        
    def setup_flag_statistics_table(self):
        """設置旗標統計表格"""
        group_box = QGroupBox(tr('flag_statistics_details', '🚩 Flag Statistics Details'))
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group_box)
        
        # 建立表格
        self.flag_table = QTableWidget()
        self.flag_table.setColumnCount(4)
        self.flag_table.setHorizontalHeaderLabels([
            tr('flag_type', 'Flag Type'),
            tr('count', 'Count'),
            tr('reason', 'Reason'),
            tr('track_sector', 'Track Sector')
        ])
        
        # 設置表格樣式
        self.flag_table.setAlternatingRowColors(True)
        self.flag_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.flag_table.horizontalHeader().setStretchLastSection(True)
        self.flag_table.verticalHeader().setVisible(False)
        
        # 設置欄位寬度
        self.flag_table.setColumnWidth(0, 100)   # 旗標類型
        self.flag_table.setColumnWidth(1, 60)    # 次數
        self.flag_table.setColumnWidth(2, 150)   # 原因
        
        layout.addWidget(self.flag_table)
        return group_box
        
    def setup_penalty_list_table(self):
        """設置處罰清單表格"""
        group_box = QGroupBox(tr('penalty_list', '⚖️ Penalty List'))
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group_box)
        
        # 建立表格
        self.penalty_table = QTableWidget()
        self.penalty_table.setColumnCount(4)
        self.penalty_table.setHorizontalHeaderLabels([
            tr('driver', 'Driver'),
            tr('violation_type', 'Violation Type'),
            tr('penalty', 'Penalty'),
            tr('lap_number', 'Lap')
        ])
        
        # 設置表格樣式
        self.penalty_table.setAlternatingRowColors(True)
        self.penalty_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.penalty_table.horizontalHeader().setStretchLastSection(True)
        self.penalty_table.verticalHeader().setVisible(False)
        
        # 設置欄位寬度
        self.penalty_table.setColumnWidth(0, 80)    # 車手
        self.penalty_table.setColumnWidth(1, 120)   # 違規類型
        self.penalty_table.setColumnWidth(2, 100)   # 處罰
        self.penalty_table.setColumnWidth(3, 60)    # 圈數
        
        layout.addWidget(self.penalty_table)
        return group_box
        
    def setup_time_distribution_chart(self):
        """設置時間分佈圖表區域 (按照規格ASCII圖表設計)"""
        group_box = QGroupBox(tr('accident_time_distribution_chart', '📈 Accident Time Distribution Chart'))
        group_box.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group_box)
        
        # 使用ASCII圖表 (按照規格)
        self.chart_area = QTextEdit()
        self.chart_area.setReadOnly(True)
        self.chart_area.setMaximumHeight(200)
        self.chart_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        
        layout.addWidget(self.chart_area)
        return group_box
        
    def update_statistics_data(self, json_data):
        """更新統計數據 - 簡化設計版本：統計表格 + 車手圖表 + Safety Periods"""
        try:
            print(f"[AccidentStatisticsWidget] 開始更新數據 (簡化設計)")
            
            # 更新統計表格 (替代卡片)
            self.update_statistics_table_from_json(json_data)
            
            # 更新車手事故頻率圖表
            self.update_driver_incident_chart(json_data)
            
            # 更新 Safety Periods
            self.update_safety_periods_data(json_data)
            
            print(f"[AccidentStatisticsWidget] 數據更新完成 (簡化設計)")
            
        except Exception as e:
            print(f"[AccidentStatisticsWidget] 數據更新失敗: {e}")
            traceback.print_exc()
            
    def update_statistics_table_from_json(self, json_data):
        """從JSON數據更新統計表格 - 替代卡片更新"""
        try:
            # 從JSON數據中提取統計信息
            data_section = json_data.get('data', {})
            all_incidents = data_section.get('all_incidents', [])
            
            # 計算各種旗標次數
            track_limit_count = 0
            double_yellow_count = 0
            yellow_count = 0
            red_count = 0
            
            for incident in all_incidents:
                message = incident.get('message', '').upper()
                category = incident.get('category', '').upper()
                
                # Track Limit違規
                if 'TRACK LIMITS' in message or 'TRACK LIMIT' in message:
                    track_limit_count += 1
                
                # 檢查 category 字段
                if category == 'YELLOW_FLAG':
                    # 檢查是否為雙黃旗
                    if 'DOUBLE YELLOW' in message:
                        double_yellow_count += 1
                    else:
                        yellow_count += 1
                elif category == 'RED_FLAG':
                    red_count += 1
            
            # 更新橫向表格數據（一行四列） - 確保數字置中顯示
            counts = [track_limit_count, double_yellow_count, yellow_count, red_count]
            
            for col, count in enumerate(counts):
                if hasattr(self, 'stats_table'):
                    item = QTableWidgetItem(str(count))
                    item.setTextAlignment(Qt.AlignCenter)  # ⚠️ 關鍵修復：確保數字置中
                    self.stats_table.setItem(0, col, item)
            
            print(f"[AccidentStatisticsWidget] 統計表格更新: Track Limit={track_limit_count}, 雙黃旗={double_yellow_count}, 黃旗={yellow_count}, 紅旗={red_count}")
            
        except Exception as e:
            print(f"[AccidentStatisticsWidget] 統計表格更新失敗: {e}")
            
    def update_driver_incident_chart(self, json_data):
        """更新車手事故頻率圖表"""
        try:
            data_section = json_data.get('data', {})
            all_incidents = data_section.get('all_incidents', [])
            
            # 統計每個車手的事故數量
            driver_incidents = {}
            for incident in all_incidents:
                # ✅ 修復：正確讀取 driver_codes 列表（複數形式）
                driver_codes = incident.get('driver_codes', [])
                for driver in driver_codes:
                    # ✅ 過濾無效車手代碼
                    if driver and driver != 'UNK' and driver.strip():
                        driver_incidents[driver] = driver_incidents.get(driver, 0) + 1
            
            self.driver_chart.update_chart_data(driver_incidents)
            
        except Exception as e:
            print(f"[AccidentStatisticsWidget] 車手事故圖表更新失敗: {e}")
            
    def update_safety_periods_data(self, json_data):
        """更新安全車時段數據"""
        try:
            data_section = json_data.get('data', {})
            safety_periods = data_section.get('safety_periods', [])
            
            self.safety_periods_widget.update_safety_periods_data(safety_periods)
            
        except Exception as e:
            print(f"[AccidentStatisticsWidget] Safety Periods 更新失敗: {e}")
            
    def update_statistics_cards_from_json(self, json_data):
        """從JSON數據更新統計卡片"""
        try:
            # 從JSON數據中提取統計信息 - 正確的數據路徑
            data_section = json_data.get('data', {})
            all_incidents = data_section.get('all_incidents', [])
            
            # 計算各種旗標次數
            track_limit_count = 0
            double_yellow_count = 0
            yellow_count = 0
            red_count = 0
            
            for incident in all_incidents:
                message = incident.get('message', '').upper()
                category = incident.get('category', '').upper()
                flags_mentioned = incident.get('flags_mentioned', [])
                
                # Track Limit違規
                if 'TRACK LIMITS' in message or 'TRACK LIMIT' in message:
                    track_limit_count += 1
                
                # 檢查 category 字段
                if category == 'YELLOW_FLAG':
                    # 檢查是否為雙黃旗
                    if 'DOUBLE YELLOW' in message:
                        double_yellow_count += 1
                    else:
                        yellow_count += 1
                elif category == 'RED_FLAG':
                    red_count += 1
                
                # 檢查 flags_mentioned 字段
                for flag_info in flags_mentioned:
                    if isinstance(flag_info, dict):
                        flag_type = flag_info.get('type', '').upper()
                        
                        if flag_type == 'DOUBLE_YELLOW_FLAG':
                            double_yellow_count += 1
                        elif flag_type == 'YELLOW_FLAG' and 'DOUBLE' not in message:
                            yellow_count += 1
                        elif flag_type == 'RED_FLAG':
                            red_count += 1
            
            # 更新卡片數值
            self.track_limit_card.value_label.setText(str(track_limit_count))
            self.double_yellow_card.value_label.setText(str(double_yellow_count))
            self.yellow_flag_card.value_label.setText(str(yellow_count))
            self.red_flag_card.value_label.setText(str(red_count))
            
            print(f"[AccidentStatisticsWidget] 統計更新 - Track Limit: {track_limit_count}, 雙黃旗: {double_yellow_count}, 黃旗: {yellow_count}, 紅旗: {red_count}")
            print(f"[AccidentStatisticsWidget] 檢查了 {len(all_incidents)} 個事件")
            
        except Exception as e:
            print(f"[AccidentStatisticsWidget] 更新統計卡片失敗: {e}")
    
    def update_flag_table_from_json(self, json_data):
        """從JSON數據更新旗標表格"""
        try:
            # 從JSON數據中提取統計信息 - 正確的數據路徑
            data_section = json_data.get('data', {})
            all_incidents = data_section.get('all_incidents', [])
            # 篩選有旗標相關的事件（category包含FLAG或flags_mentioned不為空）
            flag_incidents = [inc for inc in all_incidents 
                            if 'FLAG' in inc.get('category', '').upper() or 
                               inc.get('flags_mentioned', [])]
            
            self.flag_table.setRowCount(len(flag_incidents))
            
            for row, incident in enumerate(flag_incidents):
                category = incident.get('category', 'Unknown')
                lap = incident.get('lap', 'N/A')
                message = incident.get('message', 'N/A')
                sector = incident.get('sector', 'N/A')
                
                # 顯示 category 作為旗標類型
                self.flag_table.setItem(row, 0, QTableWidgetItem(category))
                self.flag_table.setItem(row, 1, QTableWidgetItem(str(lap)))
                self.flag_table.setItem(row, 2, QTableWidgetItem(message))
                self.flag_table.setItem(row, 3, QTableWidgetItem(str(sector)))
            
            print(f"[AccidentStatisticsWidget] 旗標表格更新完成，共 {len(flag_incidents)} 項")
            
        except Exception as e:
            print(f"[AccidentStatisticsWidget] 更新旗標表格失敗: {e}")
    
    def update_penalty_table_from_json(self, json_data):
        """從JSON數據更新處罰表格"""
        try:
            # 從JSON數據中提取統計信息 - 正確的數據路徑  
            data_section = json_data.get('data', {})
            all_incidents = data_section.get('all_incidents', [])
            penalty_incidents = [inc for inc in all_incidents if 'PENALTY' in inc.get('message', '').upper()]
            
            self.penalty_table.setRowCount(len(penalty_incidents))
            
            for row, incident in enumerate(penalty_incidents):
                driver_codes = incident.get('driver_codes', [])
                driver = driver_codes[0] if driver_codes else 'Unknown'
                violation_type = incident.get('category', 'Unknown')
                penalty_desc = incident.get('message', 'N/A')
                lap = incident.get('lap', 'N/A')
                
                self.penalty_table.setItem(row, 0, QTableWidgetItem(str(driver)))
                self.penalty_table.setItem(row, 1, QTableWidgetItem(violation_type))
                self.penalty_table.setItem(row, 2, QTableWidgetItem(penalty_desc))
                self.penalty_table.setItem(row, 3, QTableWidgetItem(str(lap)))
            
            print(f"[AccidentStatisticsWidget] 處罰表格更新完成，共 {len(penalty_incidents)} 項")
            
        except Exception as e:
            print(f"[AccidentStatisticsWidget] 更新處罰表格失敗: {e}")
            
    def clear_table(self):
        """清除表格數據"""
        if hasattr(self, 'flag_table'):
            self.flag_table.setRowCount(0)
        if hasattr(self, 'penalty_table'):
            self.penalty_table.setRowCount(0)
        print(f"[AccidentStatisticsWidget] 表格數據已清除")
        
    def show_loading_state(self):
        """顯示載入狀態"""
        # 重置所有卡片為0
        if hasattr(self, 'track_limit_card'):
            self.track_limit_card.value_label.setText("0")
        if hasattr(self, 'double_yellow_card'):
            self.double_yellow_card.value_label.setText("0")
        if hasattr(self, 'yellow_flag_card'):
            self.yellow_flag_card.value_label.setText("0")
        if hasattr(self, 'red_flag_card'):
            self.red_flag_card.value_label.setText("0")
            
        # 清空表格
        self.clear_table()
        print(f"[AccidentStatisticsWidget] 顯示載入狀態")
            
    def update_driver_involvement_table(self, driver_involvement):
        """更新車手涉入統計表格 (適應新的數據格式)"""
        # 如果沒有車手涉入數據，顯示空表格
        if not driver_involvement:
            self.driver_table.setRowCount(1)
            no_data_item = QTableWidgetItem(tr('no_driver_involvement_data', 'No driver involvement data'))
            no_data_item.setTextAlignment(Qt.AlignCenter)
            self.driver_table.setItem(0, 0, no_data_item)
            for col in range(1, 4):
                empty_item = QTableWidgetItem("-")
                empty_item.setTextAlignment(Qt.AlignCenter)
                self.driver_table.setItem(0, col, empty_item)
            return
            
        # 如果是字典格式，轉換為列表
        if isinstance(driver_involvement, dict):
            driver_data = []
            total = sum(driver_involvement.values()) if driver_involvement.values() else 1
            
            for i, (driver, count) in enumerate(driver_involvement.items(), 1):
                percentage = (count / total) * 100 if total > 0 else 0
                driver_data.append({
                    "driver": driver,
                    "incidents": count,
                    "percentage": percentage,
                    "rank": i
                })
        else:
            driver_data = driver_involvement
            
        self.driver_table.setRowCount(len(driver_data))
        
        for row, driver in enumerate(driver_data):
            # 車手代碼
            driver_item = QTableWidgetItem(driver.get("driver", "Unknown"))
            driver_item.setTextAlignment(Qt.AlignCenter)
            self.driver_table.setItem(row, 0, driver_item)
            
            # 涉入次數
            incidents_item = QTableWidgetItem(str(driver.get("incidents", 0)))
            incidents_item.setTextAlignment(Qt.AlignCenter)
            self.driver_table.setItem(row, 1, incidents_item)
            
            # 百分比
            percentage = driver.get("percentage", 0)
            percentage_item = QTableWidgetItem(f"{percentage:.1f}%")
            percentage_item.setTextAlignment(Qt.AlignCenter)
            self.driver_table.setItem(row, 2, percentage_item)
            
            # 排名
            rank_item = QTableWidgetItem(str(driver.get("rank", 0)))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.driver_table.setItem(row, 3, rank_item)
            
    def update_time_distribution_chart(self, time_distribution):
        """更新時間分佈圖表 (適應新的數據格式)"""
        if not time_distribution:
            self.chart_area.setPlainText(tr('no_time_distribution_data', 'No time distribution data'))
            return
            
        # 生成ASCII柱狀圖
        chart_text = self.generate_ascii_chart(time_distribution)
        self.chart_area.setPlainText(chart_text)
        
    def generate_ascii_chart(self, time_distribution):
        """生成ASCII柱狀圖 (適應新的數據格式)"""
        if not time_distribution:
            return tr('no_data_to_display', 'No data to display')
            
        chart_lines = []
        chart_lines.append(tr('lap_incident_distribution', 'Lap Incident Distribution'))
        chart_lines.append(tr('incident_count', 'Incident Count'))
        chart_lines.append("  ^")
        
        # 如果是字典格式 (lap -> count)，轉換處理
        if isinstance(time_distribution, dict):
            # 找出最大值用於縮放
            max_incidents = max(int(count) for count in time_distribution.values()) if time_distribution.values() else 0
            
            # 取前 10 個最高的圈數
            sorted_laps = sorted(time_distribution.items(), key=lambda x: int(x[1]), reverse=True)[:10]
            
            # 生成圖表
            for i in range(max_incidents, 0, -1):
                line = f"{i:2d} │"
                for lap, count in sorted_laps:
                    incidents = int(count)
                    if incidents >= i:
                        line += " ■"
                    else:
                        line += "  "
                chart_lines.append(line)
                
            # X軸
            x_axis = "   └" + "──" * len(sorted_laps)
            chart_lines.append(x_axis)
            
            labels_line = "    "
            for lap, count in sorted_laps:
                labels_line += f"{lap:2}"
            chart_lines.append(labels_line)
            chart_lines.append("     " + tr('lap_label', 'Lap'))
            
        return "\n".join(chart_lines)
        
    def update_status_bar(self, stats):
        """更新狀態列信息 (參考進站分析模式)"""
        # 清理現有狀態
        for i in reversed(range(self.status_layout.count())):
            child = self.status_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 計算統計信息
        total_accidents = stats.get("total_accidents", 0)
        most_dangerous_period = self.get_most_dangerous_period(stats.get("time_distribution", []))
        most_involved_driver = self.get_most_involved_driver(stats.get("driver_involvement", []))
        
        # 添加狀態標籤
        status_items = [
            tr('status_total_accidents', '📊 Total: {count} accidents').format(count=total_accidents),
            tr('status_data_source_json', '📄 Source: JSON'),
            tr('status_last_updated', "⏱️ Updated: {timestamp}").format(
                timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ),
            tr('status_most_dangerous_lap', '🎯 Most risky lap: {lap}').format(
                lap=most_dangerous_period
            ),
            tr('status_most_involved_driver', '🏁 Most involved: {driver}').format(
                driver=most_involved_driver
            ),
            tr('status_ai_generation_enabled', '🤖 Smart insights: enabled'),
        ]
        
        for item in status_items:
            label = QLabel(item)
            label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 11px;
                    padding: 3px 8px;
                    margin: 0 2px;
                }
            """)
            self.status_layout.addWidget(label)
            
        self.status_layout.addStretch()
        
    def get_most_dangerous_period(self, time_distribution):
        """獲取最危險的時間段"""
        if not time_distribution:
            return tr('unknown', 'Unknown')
            
        max_period = max(time_distribution, key=lambda x: x.get("accidents", 0))
        return max_period.get("period", tr('unknown', 'Unknown'))
        
    def get_most_involved_driver(self, driver_involvement):
        """獲取最多涉入的車手"""
        if not driver_involvement:
            return tr('unknown', 'Unknown')
            
        max_driver = max(driver_involvement, key=lambda x: x.get("incidents", 0))
        driver_code = max_driver.get("driver", "Unknown")
        incidents = max_driver.get("incidents", 0)
        return tr(
            'most_involved_driver_format',
            '{driver} ({count} incidents)'
        ).format(driver=driver_code, count=incidents)


class AccidentAnalysisModule(IAnalysisModule):
    """事故綜合分析主模組 (參考進站分析架構)"""
    
    # 信號定義
    parameter_update_received = pyqtSignal(str, str, str)  # year, race, session
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 模組基本資訊
        self._module_name = "AccidentAnalysis"
        self._display_name = tr('accident_comprehensive_analysis', 'Accident Comprehensive Analysis')
        self._version = "1.0.0"
        self._description = tr('accident_module_description', 'F1 Accident Statistics Analysis and Visualization')
        
        # ✅ 添加 analysis_type 屬性，用於進度條系統識別
        self.analysis_type = "accident"
        
        # 參數
        self.current_year = None
        self.current_race = None 
        self.current_session = None
        self.parameter_provider = None
        
        # 同步設定
        self.sync_enabled = True
        
        # UI 組件
        self._main_widget = None
        self.tab_widget = None
        self.statistics_widget = None
        
        # 初始化數據管理器
        self.data_manager = AccidentDataManager(self)
        
    def setup_ui(self):
        """設置主界面 (參考進站分析分頁設計)"""
        # 創建主要 Widget
        self._main_widget = QWidget()
        layout = QVBoxLayout(self._main_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 分頁容器 (與進站分析模組相同的簡潔風格)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("AccidentAnalysisTabWidget")
        
        # 分頁1: 事故統計總覽 (按照規格實現)
        self.statistics_widget = AccidentStatisticsWidget(self.data_manager)
        self.tab_widget.addTab(self.statistics_widget, f"📊 {tr('accident_statistics', 'Accident Statistics')}")
        
        # 分頁2: 詳細事故列表
        self.detailed_list_widget = AccidentDetailedListWidget(self.data_manager)
        self.tab_widget.addTab(self.detailed_list_widget, f"📋 {tr('detailed_records', 'Detailed Records')}")
        
        layout.addWidget(self.tab_widget)
        
        # 連接分頁切換事件
        self.tab_widget.currentChanged.connect(self.onTabChanged)
        
        # 設置信號連接
        self.setup_connections()
    
    def setup_connections(self):
        """設置信號連接 (參考進站分析模式)"""
        # 連接統計數據信號
        self.data_manager.statistics_loaded.connect(self.statistics_widget.update_statistics_data)
        self.data_manager.statistics_reload_requested.connect(self.reload_statistics_data)
        
        # 連接所有事件數據信號
        print(f"[DEBUG] 連接 all_incidents_loaded 信號到 {self.detailed_list_widget}")
        self.data_manager.all_incidents_loaded.connect(self.detailed_list_widget.update_data)
        self.data_manager.all_incidents_reload_requested.connect(self.reload_all_incidents_data)
        
        # 連接錯誤信號
        self.data_manager.error_occurred.connect(self.on_error_occurred)
        
        # 訂閱參數變更
        if hasattr(self, 'parameter_provider') and self.parameter_provider:
            if hasattr(self.parameter_provider, 'parametersChanged'):
                self.parameter_provider.parametersChanged.connect(self.onParametersChanged)
    
    def onParametersChanged(self, year, race, session):
        """參數變更時的處理邏輯 (參考進站分析)"""
        self.current_year = year
        self.current_race = race
        self.current_session = session
        
        # 更新參數顯示
        self.params_label.setText(f"{year} {race} {session}")
        self.title_label.setText(f"{tr('accident_comprehensive_analysis', 'Accident Comprehensive Analysis')} - {year} {race} {session}")
        
        # 載入當前分頁數據
        current_index = self.tab_widget.currentIndex()
        
        print(f"[SYNC_DATA] 參數變更，當前分頁: {current_index}")
        
        if current_index == 0:  # 統計總覽分頁
            print(f"[SYNC_DATA] 載入統計數據: {year} {race} {session}")
            self.load_data()
        elif current_index == 1:  # 詳細記錄分頁
            print(f"[SYNC_DATA] 載入詳細記錄數據: {year} {race} {session}")
            if hasattr(self.detailed_list_widget, "show_loading_state"):
                self.detailed_list_widget.show_loading_state()
            self.data_manager.load_all_incidents_data(year, race, session)
        # 其他分頁的處理將在後續開發
    
    def onTabChanged(self, index):
        """分頁切換處理 - 修正版本"""
        if not all([self.current_year, self.current_race, self.current_session]):
            return
            
        print(f"[TAB_SWITCH] 切換到分頁 {index}")
        
        if index == 0:  # 統計總覽分頁
            print(f"[TAB_SWITCH] 載入統計數據: {self.current_year} {self.current_race} {self.current_session}")
            # 直接調用新的數據載入方法
            self.load_data()
        elif index == 1:  # 詳細記錄分頁
            print(f"[TAB_SWITCH] 載入詳細記錄數據: {self.current_year} {self.current_race} {self.current_session}")
            # 載入詳細記錄數據
            if hasattr(self.detailed_list_widget, "show_loading_state"):
                self.detailed_list_widget.show_loading_state()
            self.data_manager.load_all_incidents_data(
                self.current_year, self.current_race, self.current_session)
    
    def reload_statistics_data(self):
        """重新載入統計數據 (CLI完成後調用，參考進站分析)"""
        print(f"[AccidentAnalysisModule] 重新載入統計數據")
        if not all([self.current_year, self.current_race, self.current_session]):
            return
        self.data_manager.loadAccidentStatistics(
            self.current_year,
            self.current_race,
            self.current_session,
            force_refresh=True,
        )
    
    def reload_all_incidents_data(self):
        """重新載入所有事件數據 (CLI完成後調用)"""
        print(f"[AccidentAnalysisModule] 重新載入所有事件數據")
        if not all([self.current_year, self.current_race, self.current_session]):
            return
        self.data_manager.load_all_incidents_data(
            self.current_year,
            self.current_race,
            self.current_session,
            force_refresh=True,
        )
    
    def on_error_occurred(self, error_message):
        """錯誤處理"""
        print(f"[AccidentAnalysisModule] 錯誤: {error_message}")
        # 使用None作為parent，避免類型錯誤
        QMessageBox.warning(None, tr('accident_analysis_error', 'Accident Analysis Error'), error_message)
    
    # ===========================================
    # IAnalysisModule 接口實現 (必需的抽象方法)
    # ===========================================
    
    @property
    def module_name(self) -> str:
        """返回模組名稱"""
        return "AccidentAnalysis"
        
    @property  
    def display_name(self) -> str:
        """返回顯示名稱"""
        return tr('accident_comprehensive_analysis', 'Accident Comprehensive Analysis')
        
    @property
    def version(self) -> str:
        """返回模組版本"""
        return "1.0.0"
        
    @property
    def description(self) -> str:
        """返回模組描述"""
        return "F1 事故統計分析與可視化"
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            parent_widget: 父級 widget
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 設置UI
            self.setup_ui()
            
            # 設置連接
            self.setup_connections()
            
            # 設置初始化狀態
            self.set_initialized(True)
            
            print(f"✅ [ACCIDENT_MODULE] 模組已初始化")
            
            # 參照進站分析流程：如果已有參數，立即載入數據
            if self.current_year and self.current_race and self.current_session:
                print(f"🚀 [ACCIDENT_MODULE] 預先載入事故分析數據: {self.current_year} {self.current_race} {self.current_session}")
                self.load_data()
            else:
                print(f"📋 [ACCIDENT_MODULE] 等待參數同步後載入數據...")
            
            return True
        except Exception as e:
            print(f"[ERROR] [ACCIDENT_MODULE] 模組初始化失敗: {str(e)}")
            return False
    
    def get_widget(self):
        """返回模組的主要 Widget"""
        return self._main_widget
    
    def get_default_size(self):
        """獲取預設視窗大小 - GUI系統要求的方法"""
        return (900, 700)  # 寬度, 高度
    
    def get_window_title(self, year: str, race: str, session: str) -> str:
        """Generate window title - 只顯示模組名稱，不包含年份/賽事/賽段"""
        from core.gui_i18n import tr, get_gui_language
        language = get_gui_language()
        if language == 'zh':
            return f"{tr('accident_analysis')}"
        else:
            return f"Accident Analysis"
    
    def update_parameters(self, year: int, race: str, session: str) -> None:
        """
        更新分析參數
        
        Args:
            year: 年份
            race: 賽事名稱  
            session: 賽段
        """
        try:
            # 檢查參數是否有變化
            params_changed = (
                self.current_year is None or str(self.current_year) != str(year) or 
                self.current_race is None or self.current_race != race or 
                self.current_session is None or self.current_session != session
            )
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race  
            self.current_session = session
            
            # 更新參數顯示
            if hasattr(self, 'params_label'):
                self.params_label.setText(f"{year} {race} {session}")
            if hasattr(self, 'title_label'):
                self.title_label.setText(f"{tr('accident_comprehensive_analysis', 'Accident Comprehensive Analysis')} - {year} {race} {session}")
            
            # 如果參數有變化，重新載入數據
            if params_changed:
                print(f"🔄 [ACCIDENT_MODULE] 參數變更觸發數據重載: {year} {race} {session}")
                self.load_data()
                
        except Exception as e:
            print(f"[ERROR] [ACCIDENT_MODULE] 更新參數失敗: {str(e)}")
            self.emit_error(f"更新參數失敗: {str(e)}")
    
    def load_data(self, force_refresh: bool = False, **kwargs) -> bool:
        """透過資料管理器載入事故統計資料（API 優先）。"""
        if not all([self.current_year, self.current_race, self.current_session]):
            print("[WARNING] [ACCIDENT_MODULE] 缺少必要參數，無法載入數據")
            print(
                f"[WARNING] [ACCIDENT_MODULE] 當前參數: year={self.current_year}, "
                f"race={self.current_race}, session={self.current_session}"
            )
            return False

        print("🔄 [ACCIDENT_MODULE] ========== 載入事故分析數據 ==========")
        print(
            f"🔄 [ACCIDENT_MODULE] 載入參數: "
            f"{self.current_year} {self.current_race} {self.current_session}"
        )

        if hasattr(self.statistics_widget, "show_loading_state"):
            self.statistics_widget.show_loading_state()
        if hasattr(self.detailed_list_widget, "show_loading_state"):
            self.detailed_list_widget.show_loading_state()

        result = self.data_manager.loadAccidentStatistics(
            self.current_year,
            self.current_race,
            self.current_session,
            force_refresh=force_refresh or kwargs.get("force_refresh", False),
        )

        if not result and hasattr(self, "error_label"):
            self.error_label.setText(tr('accident_data_load_failed', 'Accident data failed to load, please try again later.'))
            self.error_label.show()

        return result

    def _start_cli_generation(self, year: str, race: str, session: str) -> bool:
        """
        啟動 CLI 生成流程 - 非阻塞方式（參照進站分析模組）
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
        """
        try:
            # 儲存參數供後續使用
            self._generation_params = (year, race, session)
            
            # 啟動 CLI 生成
            success = self._generate_accident_data_via_cli(year, race, session)
            
            if success:
                # 啟動定時器檢查檔案是否生成完成
                self._start_generation_monitoring(year, race, session)
                return True
            else:
                print(f"❌ [ACCIDENT_MODULE] 啟動CLI生成失敗: {year} {race} {session}")
                return False
                
        except Exception as e:
            print(f"❌ [ACCIDENT_MODULE] 啟動生成時發生錯誤: {e}")
            return False

    def _generate_accident_data_via_cli(self, year: str, race: str, session: str) -> bool:
        """
        [已禁用] 透過 CLI 工具生成事故數據
        
        ⚠️ API-ONLY 模式: 此方法已改為提示訊息，不再執行 CLI
        系統只允許：
        1. 通過 REST API 獲取數據
        2. 讀取已存在的本地 JSON 檔案
        3. 手動在終端執行 CLI 命令
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
            
        Returns:
            bool: 始終返回 False（已禁用）
        """
        try:
            print(f"[ACCIDENT_MODULE] ========== [API-ONLY] 數據生成請求 ==========")
            print(f"[ACCIDENT_MODULE] ⚠️  [API-ONLY] CLI 調用已禁用")
            print(f"[ACCIDENT_MODULE] 請求: 事故分析 | {year} {race} {session}")
            
            # 生成建議的 CLI 命令（供用戶手動執行）
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "8",  # 功能8: 事故分析
                "-y", str(year),
                "-r", race,
                "-s", session
            ]
            
            manual_command = ' '.join(command)
            
            print(f"[ACCIDENT_MODULE] 💡 提示：請使用以下方式獲取數據：")
            print(f"[ACCIDENT_MODULE] 💡 方案1 [推薦]: 通過 REST API 調用 Function 8")
            print(f"[ACCIDENT_MODULE] 💡   API 端點: POST /api/v2/analysis/execute?function_id=8")
            print(f"[ACCIDENT_MODULE] 💡 方案2: 手動執行 CLI 命令：")
            print(f"[ACCIDENT_MODULE] 💡   {manual_command}")
            
            return False
            
        except Exception as e:
            print(f"❌ [ACCIDENT_MODULE] 處理生成請求時發生錯誤: {e}")
            return False

    def _start_generation_monitoring(self, year: str, race: str, session: str):
        """
        啟動檔案生成監控（參照進站分析模組）
        
        Args:
            year: 年份
            race: 賽事名稱  
            session: 賽段代碼
        """
        # 確保定時器存在
        if not hasattr(self, '_generation_timer'):
            self._generation_timer = QTimer()
            self._generation_timer.timeout.connect(self._check_generation_progress)
        
        if not hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer = QTimer()
            self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        print(f"⏰ [ACCIDENT_MODULE] 啟動檔案生成監控，每5秒檢查一次...")
        self._generation_timer.start(5000)
        self._generation_timeout_timer.start(180000)

    def _check_generation_progress(self):
        """檢查檔案生成進度（參照進站分析模組）"""
        if not hasattr(self, '_generation_params'):
            return
            
        year, race, session = self._generation_params
        
        # 檢查目標檔案是否已生成
        json_file_path = self.get_json_file_path()
        
        if json_file_path and os.path.exists(json_file_path):
            print(f"✅ [ACCIDENT_MODULE] 檔案生成完成: {json_file_path}")
            
            # 停止監控
            if hasattr(self, '_generation_timer'):
                self._generation_timer.stop()
            if hasattr(self, '_generation_timeout_timer'):
                self._generation_timeout_timer.stop()
            
            # 載入生成的數據
            try:
                print(f"📊 [ACCIDENT_MODULE] 開始載入新生成的數據...")
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # 處理並更新統計數據
                self.process_json_data(json_data)
                print(f"✅ [ACCIDENT_MODULE] 新生成的事故分析數據載入完成")
                
                # 更新UI提示
                if hasattr(self, 'error_label'):
                    self.error_label.setText(f"✅ 事故分析數據生成並載入成功")
                    self.error_label.show()
                    # 5秒後隱藏成功訊息
                    QTimer.singleShot(5000, lambda: self.error_label.hide())
                
            except Exception as e:
                print(f"❌ [ACCIDENT_MODULE] 載入新生成數據失敗: {e}")
                if hasattr(self, 'error_label'):
                    self.error_label.setText(f"{tr('load_failed', 'Load failed')}: {str(e)}")
                    self.error_label.show()
        else:
            print(f"⏳ [ACCIDENT_MODULE] 檔案尚未生成，繼續等待...")

    def _on_generation_timeout(self):
        """生成超時處理（參照進站分析模組）"""
        print(f"⏰ [ACCIDENT_MODULE] 檔案生成超時，停止監控")
        
        # 停止所有定時器
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()
        
        # 顯示超時訊息
        if hasattr(self, 'error_label'):
            self.error_label.setText(f"❌ 數據生成超時，請檢查網路連線或稍後再試")
            self.error_label.show()
            
        print(f"❌ [ACCIDENT_MODULE] 數據生成流程已超時")

    def search_and_suggest_files(self):
        """搜尋並建議可能的檔案（參照進站分析流程）"""
        print(f"🔍 [ACCIDENT_MODULE] ========== 搜尋可用的事故分析檔案 ==========")
        
        # 搜尋 json_exports 目錄下的相關檔案
        json_exports_dir = os.path.join(os.getcwd(), 'json_exports')
        if os.path.exists(json_exports_dir):
            print(f"📂 [ACCIDENT_MODULE] 搜尋目錄: {json_exports_dir}")
            
            # 搜尋包含當前年份和比賽的檔案
            pattern = f"*{self.current_year}*{self.current_race}*all_incidents_summary*"
            search_pattern = os.path.join(json_exports_dir, pattern)
            
            try:
                import glob
                matching_files = glob.glob(search_pattern)
                
                if matching_files:
                    print(f"🎯 [ACCIDENT_MODULE] 找到 {len(matching_files)} 個相關檔案:")
                    for i, file_path in enumerate(matching_files, 1):
                        filename = os.path.basename(file_path)
                        print(f"   {i}. {filename}")
                        
                    # 建議使用第一個找到的檔案
                    suggested_file = matching_files[0]
                    print(f"💡 [ACCIDENT_MODULE] 建議使用: {os.path.basename(suggested_file)}")
                    
                else:
                    print(f"❌ [ACCIDENT_MODULE] 未找到符合的檔案")
                    print(f"❌ [ACCIDENT_MODULE] 搜尋模式: {pattern}")
                    
            except Exception as e:
                print(f"❌ [ACCIDENT_MODULE] 搜尋檔案時發生錯誤: {e}")
        else:
            print(f"❌ [ACCIDENT_MODULE] json_exports 目錄不存在: {json_exports_dir}")
            
        print(f"🔍 [ACCIDENT_MODULE] =============================================")
    
    def get_json_file_path(self):
        """獲取JSON檔案路徑"""
        # 建構檔案名稱，例如: all_incidents_summary_2025_Japan_R.json
        filename = f"all_incidents_summary_{self.current_year}_{self.current_race}_{self.current_session}.json"
        json_path = os.path.join("json", filename)
        
        # 如果檔案不存在，嘗試其他可能的命名格式
        if not os.path.exists(json_path):
            # 嘗試用完整比賽名稱
            possible_names = [
                f"all_incidents_summary_{self.current_year}_{self.current_race}.json",
                f"all_incidents_summary_{self.current_year}_Japanese_Grand_Prix.json",
                f"all_incidents_summary_{self.current_year}_{self.current_race}_Grand_Prix.json"
            ]
            
            for alt_name in possible_names:
                alt_path = os.path.join("json", alt_name)
                if os.path.exists(alt_path):
                    print(f"🔍 [ACCIDENT_MODULE] 找到替代檔案: {alt_name}")
                    return alt_path
        
        return json_path
    
    def process_json_data(self, json_data):
        """處理JSON數據並更新統計"""
        try:
            # 更新統計 widget
            self.statistics_widget.update_statistics_data(json_data)
            
        except Exception as e:
            print(f"❌ [ACCIDENT_MODULE] 處理JSON數據失敗: {e}")
    
    def update_statistics_cards(self, json_data):
        """更新統計卡片 - 這個方法現在移動到 AccidentStatisticsWidget"""
        # 這個方法的功能已經移動到 AccidentStatisticsWidget.update_statistics_cards_from_json
        print(f"[ACCIDENT_MODULE] 統計卡片更新功能已移動到 AccidentStatisticsWidget")
    
    def update_flag_table(self, json_data):
        """更新旗標表格 - 這個方法現在移動到 AccidentStatisticsWidget"""
        # 這個方法的功能已經移動到 AccidentStatisticsWidget.update_flag_table_from_json
        print(f"[ACCIDENT_MODULE] 旗標表格更新功能已移動到 AccidentStatisticsWidget")
    
    def update_penalty_table(self, json_data):
        """更新處罰表格 - 這個方法現在移動到 AccidentStatisticsWidget"""
        # 這個方法的功能已經移動到 AccidentStatisticsWidget.update_penalty_table_from_json
        print(f"[ACCIDENT_MODULE] 處罰表格更新功能已移動到 AccidentStatisticsWidget")
    
    def refresh_analysis(self) -> None:
        """刷新分析"""
        print(f"🔄 [ACCIDENT_MODULE] 刷新分析")
        self.load_data()
    
    def clear_data(self) -> None:
        """清除數據"""
        if hasattr(self, 'statistics_widget'):
            self.statistics_widget.clear_table()
        print(f"🧹 [ACCIDENT_MODULE] 數據已清除")
    
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據"""
        # 暫未實現，返回成功狀態
        print(f"📤 [ACCIDENT_MODULE] 匯出數據到 {export_path} (格式: {export_format}) - 功能開發中")
        return True
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據"""
        return {
            'module': 'accident_analysis',
            'year': self.current_year,
            'race': self.current_race,
            'session': self.current_session,
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def get_module_info(self):
        """模組信息"""
        return {
            'name': tr('accident_comprehensive_analysis', 'Accident Comprehensive Analysis'),
            'description': tr('accident_module_info_desc', 'Provides comprehensive statistics and analysis of F1 accidents'),
            'version': '1.0.0',
            'author': 'F1T Development Team'
        }


# ================================================================================================
# PROFESSIONAL WIDGETS - 專業 Widget 類 (類似進站分析模組風格)
# ================================================================================================

class AccidentDetailedListWidget(QWidget):
    """所有事件詳細列表 Widget - 基於功能8實現 (All Incidents Summary)"""
    
    def __init__(self, data_manager=None, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.incidents_data = []
        self.filtered_data = []
        self.current_filters = {}
        self._last_incident_path = ""
        
        # 建立欄位映射：JSON英文欄位 -> 中文顯示
        self.field_mapping = {
            "sequence_number": tr('sequence_number', 'No.'),
            "lap": tr('lap', 'Lap'), 
            "time": tr('time', 'Time'),
            "message": tr('event_description', 'Event Description'),
            "category": tr('category', 'Category'),
            "severity": tr('severity', 'Severity'),
            "impact": tr('impact_level', 'Impact'),
            "sector": tr('sector', 'Sector'),
            "flags_mentioned": tr('flags', 'Flags'),
            "involved_drivers": tr('drivers', 'Drivers')
        }
        
        # 建立反向映射：中文顯示 -> JSON英文欄位
        self.reverse_field_mapping = {v: k for k, v in self.field_mapping.items()}
        
        self.setup_ui()
        self.setup_connections()
        
    def get_field_value(self, incident, chinese_field_name, default=""):
        """通過中文欄位名獲取JSON數據值"""
        english_field = self.reverse_field_mapping.get(chinese_field_name, chinese_field_name)
        return incident.get(english_field, default)
        
    def setup_ui(self):
        """設置使用者界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 篩選工具列
        self.setup_filter_toolbar(layout)
        
        # 統計摘要列
        self.setup_statistics_bar(layout)
        
        # 主要表格
        self.setup_main_table(layout)
        
    def setup_filter_toolbar(self, layout):
        """設置篩選工具列"""
        toolbar_layout = QHBoxLayout()
        
        # 類別篩選
        self.category_combo = QComboBox()
        self.category_combo.addItem(tr('all_categories', 'All Categories'), "")
        toolbar_layout.addWidget(QLabel(tr('category', 'Category') + ":"))
        toolbar_layout.addWidget(self.category_combo)
        
        # 嚴重程度篩選
        self.severity_combo = QComboBox()
        self.severity_combo.addItem(tr('all_severities', 'All Severities'), "")
        toolbar_layout.addWidget(QLabel(tr('severity', 'Severity') + ":"))
        toolbar_layout.addWidget(self.severity_combo)
        
        # 影響程度篩選
        self.impact_combo = QComboBox()
        self.impact_combo.addItem(tr('all_impacts', 'All Impacts'), "")
        toolbar_layout.addWidget(QLabel(tr('impact_level', 'Impact') + ":"))
        toolbar_layout.addWidget(self.impact_combo)
        
        # 關鍵字搜尋
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"🔍 {tr('search_event_description', 'Search event description or keywords...')}")
        toolbar_layout.addWidget(self.search_input)
        
        # 刷新按鈕
        self.refresh_button = QPushButton(f"🔄 {tr('refresh', 'Refresh')}")
        self.refresh_button.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self.refresh_button)
        
        layout.addLayout(toolbar_layout)
        
    def setup_statistics_bar(self, layout):
        """設置統計摘要列"""
        self.stats_frame = QFrame()
        self.stats_frame.setFrameStyle(QFrame.StyledPanel)
        self.stats_frame.setFixedHeight(40)
        
        stats_layout = QHBoxLayout(self.stats_frame)
        self.stats_label = QLabel(tr('loading', 'Loading...'))
        self.stats_label.setStyleSheet("font-weight: bold; color: #495057;")
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(self.stats_frame)
        
    def setup_main_table(self, layout):
        """設置主要表格"""
        self.table_widget = QTableWidget()
        self.setup_table_structure()
        layout.addWidget(self.table_widget)
        
    def setup_table_structure(self):
        """設置表格結構"""
        headers = [
            tr('sequence_number', 'No.'),
            tr('lap', 'Lap'),
            tr('time', 'Time'),
            tr('event_description', 'Event Description'),
            tr('category', 'Category'),
            tr('severity', 'Severity'),
            tr('impact_level', 'Impact'),
            tr('sector', 'Sector'),
            tr('flags', 'Flags'),
            tr('drivers', 'Drivers')
        ]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 表格屬性
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSortingEnabled(True)
        
        # 響應式列寬設定 - 允許手動調整
        header = self.table_widget.horizontalHeader()
        
        # 設定初始寬度
        self.table_widget.setColumnWidth(0, 40)   # 序號
        self.table_widget.setColumnWidth(1, 50)   # 圈數
        self.table_widget.setColumnWidth(2, 80)   # 時間
        self.table_widget.setColumnWidth(3, 200)  # 事件描述
        self.table_widget.setColumnWidth(4, 100)  # 類別
        self.table_widget.setColumnWidth(5, 80)   # 嚴重程度
        self.table_widget.setColumnWidth(6, 80)   # 影響程度
        self.table_widget.setColumnWidth(7, 60)   # 區段
        self.table_widget.setColumnWidth(8, 120)  # 旗幟
        self.table_widget.setColumnWidth(9, 60)   # 車手
        
        # 所有欄位都設為可手動調整
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        
    def setup_connections(self):
        """設置信號連接"""
        # UI事件連接
        self.category_combo.currentTextChanged.connect(self.apply_filters)
        self.severity_combo.currentTextChanged.connect(self.apply_filters)
        self.impact_combo.currentTextChanged.connect(self.apply_filters)
        self.search_input.textChanged.connect(self.apply_filters)
        
    def update_data(self, data: Dict[str, Any]):
        """更新事件數據"""
        try:
            print(f"[DEBUG] AccidentDetailedListWidget.update_data 被呼叫")
            print(f"[DEBUG] 數據類型: {type(data)}")
            print(f"[DEBUG] 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            incidents_list = self._validate_incidents_data(data)
            if incidents_list is None:
                print(f"[ERROR] 數據驗證失敗")
                self.show_error_message("無效的事件數據格式")
                return

            self.incidents_data = incidents_list
            print(
                f"[DEBUG] 成功取得事件列表，數量: {len(self.incidents_data)}，來源路徑: "
                f"{self._last_incident_path or 'unknown'}"
            )

            # 重置狀態樣式
            self.stats_label.setStyleSheet("font-weight: bold; color: #495057;")

            # 更新篩選選項
            self.update_filter_options()
            
            # 應用當前篩選
            self.apply_filters()
            
            # 更新統計
            self.update_statistics()
            
        except Exception as e:
            print(f"[ERROR] 更新事件數據失敗: {str(e)}")
            self.show_error_message(f"更新事件數據失敗: {str(e)}")
            
    def _validate_incidents_data(self, data: Dict[str, Any]) -> bool:
        """驗證事件數據格式（參考AccidentDataManager的驗證邏輯）"""
        try:
            incidents, path = self._extract_incidents_list(data)

            if incidents is None:
                print(
                    "[ERROR] [VALIDATE] AccidentDetailedListWidget: 無法在資料中找到事故列表"
                )
                return None

            if not isinstance(incidents, list):
                print(
                    "[ERROR] [VALIDATE] AccidentDetailedListWidget: 事故列表不是 list 類型"
                )
                return None

            self._last_incident_path = " -> ".join(path) if path else "data.all_incidents"
            print(
                f"[OK] [VALIDATE] AccidentDetailedListWidget: 數據格式驗證通過，匹配路徑: {self._last_incident_path}"
            )
            return incidents
        except Exception as e:
            print(f"[ERROR] [VALIDATE] AccidentDetailedListWidget: 數據驗證異常: {e}")
            return None

    def _extract_incidents_list(
        self, data: Any
    ) -> Tuple[Optional[List[Dict[str, Any]]], List[str]]:
        """在多層資料結構中尋找事故列表，回傳列表及其路徑。"""

        target_keys = {"all_incidents", "incidents", "incident_records", "incident_list"}
        visited: Set[int] = set()

        def _search(node: Any, breadcrumbs: List[str]) -> Tuple[Optional[List[Dict[str, Any]]], List[str]]:
            node_id = id(node)
            if node_id in visited:
                return None, []
            visited.add(node_id)

            if isinstance(node, dict):
                for key in target_keys:
                    value = node.get(key)
                    if isinstance(value, list):
                        return value, breadcrumbs + [key]
                for key, value in node.items():
                    result, path = _search(value, breadcrumbs + [key])
                    if result is not None:
                        return result, path
            elif isinstance(node, list):
                for item in node:
                    result, path = _search(item, breadcrumbs)
                    if result is not None:
                        return result, path
            return None, []

        if isinstance(data, list):
            return data, ["<list>"]

        if not isinstance(data, dict):
            return None, []

        return _search(data, [])
            
    def update_filter_options(self):
        """更新篩選選項（直接使用 JSON 欄位名稱）"""
        # 收集所有唯一值
        categories = set()
        severities = set()
        impacts = set()
        
        for incident in self.incidents_data:
            # 直接使用 JSON 欄位名
            category = incident.get("category", "")
            if category:
                categories.add(category)
                
            severity = incident.get("severity", "")
            if severity:
                severities.add(severity)
                
            impact = incident.get("impact", "")
            if impact:
                impacts.add(impact)
        
        # 更新下拉選單
        self._update_combo_options(self.category_combo, sorted(categories))
        self._update_combo_options(self.severity_combo, sorted(severities))
        self._update_combo_options(self.impact_combo, sorted(impacts))
        
    def _update_combo_options(self, combo: QComboBox, options: list):
        """更新下拉選單選項"""
        current_text = combo.currentText()
        default_text = combo.itemText(0) if combo.count() > 0 else "全部"
        default_data = combo.itemData(0) if combo.count() > 0 else ""

        combo.clear()
        combo.addItem(default_text or "全部", default_data if default_data is not None else "")
        
        for option in options:
            if option:  # 排除空值
                combo.addItem(option, option)
                
        # 恢復之前的選擇
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
            
    def apply_filters(self):
        """應用篩選條件（使用實際的JSON欄位名稱）"""
        # 收集篩選條件
        filters = {
            "category": self.category_combo.currentData() if self.category_combo.currentData() else "",
            "severity": self.severity_combo.currentData() if self.severity_combo.currentData() else "",
            "impact": self.impact_combo.currentData() if self.impact_combo.currentData() else "",
            "search": self.search_input.text().strip().lower()
        }
        
        # 篩選數據
        self.filtered_data = []
        for incident in self.incidents_data:
            if self._matches_filters(incident, filters):
                self.filtered_data.append(incident)
        
        print(f"[DEBUG] 篩選結果: {len(self.filtered_data)}/{len(self.incidents_data)} 個事件")
        
        # 更新表格
        self.populate_table()
        
        # 更新統計
        self.update_statistics()
        
    def _matches_filters(self, incident: dict, filters: dict) -> bool:
        """檢查事件是否符合篩選條件（使用欄位映射）"""
        # 類別篩選
        if filters["category"] and incident.get("category") != filters["category"]:
            return False
            
        # 嚴重程度篩選
        if filters["severity"] and incident.get("severity") != filters["severity"]:
            return False
            
        # 影響程度篩選
        if filters["impact"] and incident.get("impact") != filters["impact"]:
            return False
            
        # 文字搜尋
        if filters["search"]:
            search_text = filters["search"].lower()
            searchable_fields = [
                str(incident.get("message", "")),
                str(incident.get("involved_drivers", "")),
                str(incident.get("sequence_number", "")),
                str(incident.get("lap", "")),
                self.get_flag_summary(incident)  # 加入旗幟搜索
            ]
            
            search_content = " ".join(searchable_fields).lower()
            if search_text not in search_content:
                return False
                
        return True
        
    def populate_table(self):
        """填充表格數據（直接使用英文欄位名）"""
        self.table_widget.setRowCount(len(self.filtered_data))
        
        for row, incident in enumerate(self.filtered_data):
            # 序號
            seq_num = incident.get("sequence_number", row + 1)
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(seq_num)))
            
            # 圈數
            lap = incident.get("lap", "")
            self.table_widget.setItem(row, 1, QTableWidgetItem(str(lap)))
            
            # 時間
            time_str = incident.get("time", "")
            self.table_widget.setItem(row, 2, QTableWidgetItem(str(time_str)))
            
            # 事件描述
            message = incident.get("message", "")
            self.table_widget.setItem(row, 3, QTableWidgetItem(str(message)))
            
            # 類別
            category = incident.get("category", "")
            self.table_widget.setItem(row, 4, QTableWidgetItem(str(category)))
            
            # 嚴重程度（帶顏色）
            severity = incident.get("severity", "")
            severity_item = QTableWidgetItem(str(severity))
            severity_item.setBackground(QColor(self.get_severity_color(severity)))
            self.table_widget.setItem(row, 5, severity_item)
            
            # 影響程度（帶顏色）
            impact = incident.get("impact", "")
            impact_item = QTableWidgetItem(str(impact))
            impact_item.setBackground(QColor(self.get_impact_color(impact)))
            self.table_widget.setItem(row, 6, impact_item)
            
            # 區段
            sector = incident.get("sector", "N/A")
            self.table_widget.setItem(row, 7, QTableWidgetItem(str(sector)))
            
            # 旗幟
            flags = self.get_flag_summary(incident)
            flag_item = QTableWidgetItem(flags)
            flag_item.setBackground(QColor(self.get_flag_color(flags)))
            self.table_widget.setItem(row, 8, flag_item)
            
            # 車手
            drivers = incident.get("involved_drivers", "")
            # 如果是列表，轉換為字符串
            if isinstance(drivers, list):
                # 如果列表元素是字典，提取driver_code或合適的字段
                driver_names = []
                for driver in drivers:
                    if isinstance(driver, dict):
                        # 優先使用driver_code，然後car_number
                        driver_name = driver.get('driver_code', driver.get('car_number', str(driver)))
                        driver_names.append(driver_name)
                    else:
                        driver_names.append(str(driver))
                drivers = ", ".join(driver_names)
            elif drivers is None:
                drivers = ""
            self.table_widget.setItem(row, 9, QTableWidgetItem(str(drivers)))
            
    def get_severity_color(self, severity: str) -> str:
        """獲取嚴重程度顏色"""
        colors = {
            "LOW": "#d4edda",      # 淺綠色
            "MEDIUM": "#fff3cd",   # 淺黃色
            "HIGH": "#f8d7da",     # 淺橙色
            "CRITICAL": "#f5c6cb"  # 淺紅色
        }
        return colors.get(severity, "#ffffff")
        
    def get_impact_color(self, impact: str) -> str:
        """獲取影響程度顏色"""
        colors = {
            "MONITORING": "#e2e3e5",    # 淺灰色
            "WARNING": "#fff3cd",       # 淺黃色
            "PENALTY": "#f8d7da",       # 淺橙色
            "RACE_AFFECTING": "#f5c6cb" # 淺紅色
        }
        return colors.get(impact, "#ffffff")
        
    def get_flag_summary(self, incident: Dict[str, Any]) -> str:
        """獲取旗幟摘要"""
        flags_mentioned = incident.get("flags_mentioned", "")
        
        # 如果沒有旗幟信息，返回空字符串
        if not flags_mentioned:
            return ""
        
        # 如果是列表，處理每個旗幟
        if isinstance(flags_mentioned, list) and len(flags_mentioned) > 0:
            flag_symbols = []
            for flag in flags_mentioned:
                if isinstance(flag, dict):
                    flag_type = flag.get('type', '').upper()
                    description = flag.get('description', '').upper()
                    
                    if flag_type == 'DOUBLE_YELLOW_FLAG':
                        flag_symbols.append('🟡🟡')  # 兩個黃色旗子代表雙黃旗
                    elif flag_type == 'YELLOW_FLAG':
                        # 檢查是否為雙黃旗（從描述中判斷）
                        if 'DOUBLE YELLOW' in description:
                            flag_symbols.append('🟡🟡')  # 兩個黃色旗子
                        else:
                            flag_symbols.append('🟡')   # 單個黃色旗子
                    elif flag_type == 'RED_FLAG':
                        flag_symbols.append('🔴')
                    elif flag_type == 'GREEN_FLAG':
                        flag_symbols.append('🟢')
                    elif flag_type == 'BLUE_FLAG':
                        flag_symbols.append('🔵')
                    elif flag_type == 'CHEQUERED_FLAG':
                        flag_symbols.append('🏁')
                    elif flag_type == 'SAFETY_CAR':
                        flag_symbols.append('🚗')
                    elif flag_type == 'VIRTUAL_SAFETY_CAR':
                        flag_symbols.append('🚨')
                    else:
                        flag_symbols.append('🏳️')
                elif isinstance(flag, str):
                    # 處理舊格式的字符串旗幟
                    flag_upper = flag.upper()
                    if 'DOUBLE YELLOW' in flag_upper:
                        flag_symbols.append('🟡🟡')  # 兩個黃色旗子
                    elif 'YELLOW' in flag_upper:
                        flag_symbols.append('🟡')
                    elif 'RED' in flag_upper:
                        flag_symbols.append('🔴')
                    elif 'GREEN' in flag_upper:
                        flag_symbols.append('🟢')
                    elif 'BLUE' in flag_upper:
                        flag_symbols.append('🔵')
                    elif 'CHEQUERED' in flag_upper:
                        flag_symbols.append('🏁')
                    elif 'SAFETY' in flag_upper:
                        flag_symbols.append('🚗')
                    else:
                        flag_symbols.append('🏳️')
            
            return " ".join(flag_symbols) if flag_symbols else ""
        
        return ""
        
    def get_flag_color(self, flags: str) -> str:
        """獲取旗幟背景顏色 - 統一使用白色背景"""
        # 按照需求，旗標的地方保持白色底色
        return "#ffffff"
        
    def update_statistics(self):
        """更新統計摘要"""
        if not self.filtered_data:
            self.stats_label.setText(tr('no_incident_data', 'No incident data'))
            return
            
        total = len(self.filtered_data)
        
        # 按類別統計
        category_counts = {}
        for incident in self.filtered_data:
            category = incident.get("category", "")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # 構建統計文字
        stats_parts = [f"{tr('total_events', 'Total Events')}: {total}"]
        
        # 顯示主要類別
        main_categories = ["PIT_RELATED", "TRACK_LIMITS", "INVESTIGATION", "PENALTY"]
        for category in main_categories:
            if category in category_counts:
                # 簡化類別名稱顯示
                display_name = {
                    "PIT_RELATED": tr('pit_related', 'PIT Related'),
                    "TRACK_LIMITS": tr('track_limits', 'Track Limits'), 
                    "INVESTIGATION": tr('investigation', 'Investigation'),
                    "PENALTY": tr('penalty_cat', 'Penalty')
                }.get(category, category)
                stats_parts.append(f"{display_name}: {category_counts[category]}")
        
        # 其他類別總計
        other_count = sum(count for cat, count in category_counts.items() 
                         if cat not in main_categories)
        if other_count > 0:
            stats_parts.append(f"{tr('other', 'Other')}: {other_count}")
        
        self.stats_label.setText(" | ".join(stats_parts))
        
    def refresh_data(self):
        """刷新數據"""
        if self.data_manager and hasattr(self.data_manager, 'load_all_incidents_data'):
            # 需要從父模組獲取當前參數
            parent_module = self.parent()
            while parent_module and not hasattr(parent_module, 'current_year'):
                parent_module = parent_module.parent()
                
            if parent_module:
                self.data_manager.load_all_incidents_data(
                    parent_module.current_year,
                    parent_module.current_race,
                    parent_module.current_session,
                    force_refresh=True,
                )
                
    def show_error_message(self, message: str):
        """顯示錯誤訊息"""
        print(f"[ERROR] [ALL_INCIDENTS_WIDGET] {message}")
        # 在UI上顯示錯誤狀態
        self.stats_label.setText(f"錯誤: {message}")
        self.stats_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        
    def show_loading_state(self):
        """顯示載入狀態"""
        self.stats_label.setText(tr('loading_incident_data', 'Loading incident data...'))
        self.stats_label.setStyleSheet("color: #6c757d; font-weight: bold;")
        self.table_widget.setRowCount(0)


class AccidentSeverityWidget(QWidget):
    """事故嚴重程度分析 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 標題區
        title_label = QLabel("📊 事故嚴重程度分析")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1f2937;
                padding: 10px;
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
        """)
        layout.addWidget(title_label)
        
        # 卡片容器
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(10)
        
        # 嚴重程度卡片
        self.severity_cards = {}
        severity_types = [
            ("輕微", "#22c55e", "🟢"),
            ("中等", "#f59e0b", "🟡"), 
            ("嚴重", "#ef4444", "🔴"),
            ("極嚴重", "#991b1b", "⚫")
        ]
        
        for i, (severity, color, icon) in enumerate(severity_types):
            card = self.create_severity_card(severity, color, icon)
            self.severity_cards[severity] = card
            cards_layout.addWidget(card, i // 2, i % 2)
            
        layout.addWidget(cards_widget)
        
        # 詳細表格
        self.severity_table = QTableWidget()
        self.severity_table.setColumnCount(4)
        self.severity_table.setHorizontalHeaderLabels([
            "嚴重程度", "事故數量", "佔比", "典型後果"
        ])
        
        self.severity_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e2e8f0;
                background-color: white;
                alternate-background-color: #f8fafc;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                padding: 8px;
                font-weight: bold;
                color: #374151;
            }
        """)
        
        layout.addWidget(self.severity_table)
        
    def create_severity_card(self, severity: str, color: str, icon: str) -> QFrame:
        """創建嚴重程度卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 圖標和標題
        title_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        title_label = QLabel(severity)
        title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 數量標籤
        count_label = QLabel("0")
        count_label.setObjectName(f"{severity}_count")
        count_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1f2937;")
        
        # 百分比標籤
        percent_label = QLabel("0%")
        percent_label.setObjectName(f"{severity}_percent")
        percent_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        
        layout.addLayout(title_layout)
        layout.addWidget(count_label)
        layout.addWidget(percent_label)
        
        return card
        
    def update_data(self, data: Dict[str, Any]):
        """更新數據"""
        if not data or 'severity_distribution' not in data:
            return
            
        severity_data = data['severity_distribution']
        
        # 更新卡片
        for severity, card in self.severity_cards.items():
            count = severity_data.get(severity, {}).get('count', 0)
            percent = severity_data.get(severity, {}).get('percentage', 0)
            
            count_label = card.findChild(QLabel, f"{severity}_count")
            percent_label = card.findChild(QLabel, f"{severity}_percent")
            
            if count_label:
                count_label.setText(str(count))
            if percent_label:
                percent_label.setText(f"{percent:.1f}%")
        
        # 更新表格
        self.severity_table.setRowCount(len(severity_data))
        for row, (severity, info) in enumerate(severity_data.items()):
            self.severity_table.setItem(row, 0, QTableWidgetItem(severity))
            self.severity_table.setItem(row, 1, QTableWidgetItem(str(info.get('count', 0))))
            self.severity_table.setItem(row, 2, QTableWidgetItem(f"{info.get('percentage', 0):.1f}%"))
            self.severity_table.setItem(row, 3, QTableWidgetItem(str(info.get('typical_consequence', 'N/A'))))


class AccidentKeyEventsWidget(QWidget):
    """關鍵事故事件 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 標題區
        title_label = QLabel("🔥 關鍵事故事件")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1f2937;
                padding: 10px;
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
        """)
        layout.addWidget(title_label)
        
        # 滾動區域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.events_widget = QWidget()
        self.events_layout = QVBoxLayout(self.events_widget)
        self.events_layout.setSpacing(10)
        
        scroll_area.setWidget(self.events_widget)
        layout.addWidget(scroll_area)
        
    def update_data(self, data: Dict[str, Any]):
        """更新數據"""
        # 清除舊的事件卡片
        for i in reversed(range(self.events_layout.count())):
            child = self.events_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not data or 'key_events' not in data:
            return
            
        key_events = data['key_events']
        
        for event in key_events:
            event_card = self.create_event_card(event)
            self.events_layout.addWidget(event_card)
        
        self.events_layout.addStretch()
        
    def create_event_card(self, event: Dict[str, Any]) -> QFrame:
        """創建事故事件卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 事件標題
        title_layout = QHBoxLayout()
        
        severity_icon = "🔴" if event.get('severity') == '嚴重' else "🟡" if event.get('severity') == '中等' else "🟢"
        icon_label = QLabel(severity_icon)
        icon_label.setStyleSheet("font-size: 18px;")
        
        title_label = QLabel(f"第 {event.get('lap', 'N/A')} 圈 - {event.get('type', '未知事故')}")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1f2937;")
        
        time_label = QLabel(str(event.get('time', 'N/A')))
        time_label.setStyleSheet("font-size: 12px; color: #6b7280;")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(time_label)
        
        # 事件詳情
        details_label = QLabel(f"涉及車手: {event.get('drivers', 'N/A')}")
        details_label.setStyleSheet("font-size: 12px; color: #374151; margin: 5px 0;")
        
        consequence_label = QLabel(f"後果: {event.get('consequence', 'N/A')}")
        consequence_label.setStyleSheet("font-size: 12px; color: #374151;")
        
        layout.addLayout(title_layout)
        layout.addWidget(details_label)
        layout.addWidget(consequence_label)
        
        return card


class SafetyPeriodsWidget(QWidget):
    """🏁 Safety Periods Widget - 安全車時段統計"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置 Safety Periods UI - 無外框版本"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
        layout.setSpacing(5)  # 減少間距
        
        # 標題標籤
        title_label = QLabel(tr('safety_periods', '🏁 Safety Periods (2 total)'))
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                margin-bottom: 3px;
            }
        """)
        layout.addWidget(title_label)
        
        # 創建 Safety Periods 表格
        self.safety_table = QTableWidget()
        self.safety_table.setColumnCount(4)
        self.safety_table.setHorizontalHeaderLabels([
            tr('period', 'Period'),
            tr('start_lap', 'Start Lap'),
            tr('end_lap', 'End Lap'),
            tr('reason', 'Reason')
        ])
        
        # 設置表格樣式 - 簡潔版本
        self.safety_table.setAlternatingRowColors(True)
        self.safety_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.safety_table.horizontalHeader().setStretchLastSection(True)
        self.safety_table.verticalHeader().setVisible(False)
        
        # 設置可擴展的高度 - 隨視窗拖拉而放大
        self.safety_table.setMinimumHeight(100)  # 最小高度
        # 移除最大高度限制，讓它可以隨視窗擴展
        
        # 設置大小政策：垂直方向可擴展
        self.safety_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 簡潔的表格樣式
        self.safety_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # 設置欄位寬度
        self.safety_table.setColumnWidth(0, 60)    # Period
        self.safety_table.setColumnWidth(1, 80)    # Start Lap
        self.safety_table.setColumnWidth(2, 80)    # End Lap
        
        layout.addWidget(self.safety_table)
        
    def update_safety_periods_data(self, safety_periods_data):
        """更新 Safety Periods 數據 - 僅使用真實數據"""
        if not safety_periods_data:
            # ⚠️ 禁用模擬數據政策：顯示無數據訊息
            self.safety_table.setRowCount(1)
            self.safety_table.setItem(0, 0, QTableWidgetItem("-"))
            self.safety_table.setItem(0, 1, QTableWidgetItem("-"))
            self.safety_table.setItem(0, 2, QTableWidgetItem("-"))
            self.safety_table.setItem(0, 3, QTableWidgetItem(tr('no_safety_periods', 'No safety car periods in this session')))
            return
            
        # 處理實際數據
        self.safety_table.setRowCount(len(safety_periods_data))
        
        for row, period in enumerate(safety_periods_data):
            self.safety_table.setItem(row, 0, QTableWidgetItem(period.get('type', 'SC')))
            self.safety_table.setItem(row, 1, QTableWidgetItem(str(period.get('start_lap', ''))))
            self.safety_table.setItem(row, 2, QTableWidgetItem(str(period.get('end_lap', '')))) 
            self.safety_table.setItem(row, 3, QTableWidgetItem(period.get('reason', '')))


class PenaltiesSummaryWidget(QGroupBox):
    """⚖️ Penalties Summary Widget - 處罰統計摘要"""
    
    def __init__(self, parent=None):
        super().__init__(tr('penalties_summary', '⚖️ Penalties (4 total)'), parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置 Penalties Summary UI"""
        # 設置 GroupBox 樣式
        self.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 處罰類型統計卡片區域
        cards_layout = QHBoxLayout()
        
        # 時間處罰卡片
        self.time_penalty_card = self.create_penalty_card(
            tr('time_penalties', 'Time'),
            "2",
            "#FF9800"
        )
        cards_layout.addWidget(self.time_penalty_card)
        
        # 位置處罰卡片  
        self.position_penalty_card = self.create_penalty_card(
            tr('position_penalties', 'Grid'),
            "1", 
            "#F44336"
        )
        cards_layout.addWidget(self.position_penalty_card)
        
        # 警告卡片
        self.warning_card = self.create_penalty_card(
            tr('warnings', 'Warnings'),
            "1",
            "#FFC107" 
        )
        cards_layout.addWidget(self.warning_card)
        
        layout.addLayout(cards_layout)
        
        # 最嚴重處罰顯示
        self.severe_penalty_label = QLabel(tr('most_severe', 'Most severe: 5-second time penalty (VER)'))
        self.severe_penalty_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #374151;
                padding: 5px;
                background-color: rgba(239, 68, 68, 0.1);
                border-radius: 4px;
                margin-top: 5px;
            }
        """)
        layout.addWidget(self.severe_penalty_label)
        
    def create_penalty_card(self, title, count, color):
        """創建處罰統計卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)
        
        # 標題
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 12px; 
            font-weight: bold; 
            color: {color};
        """)
        layout.addWidget(title_label)
        
        # 計數
        count_label = QLabel(count)
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: bold; 
            color: {color};
        """)
        layout.addWidget(count_label)
        
        # 儲存標籤引用以便更新
        card.count_label = count_label
        
        return card
        
    def update_penalties_data(self, penalties_data):
        """更新處罰數據"""
        if not penalties_data:
            # 使用預設示例數據
            self.time_penalty_card.count_label.setText("2")
            self.position_penalty_card.count_label.setText("1")
            self.warning_card.count_label.setText("1")
            self.severe_penalty_label.setText(tr('most_severe_example', 'Most severe: 5-second time penalty (VER)'))
            return
            
        # 處理實際數據
        time_penalties = sum(1 for p in penalties_data if 'time' in p.get('type', '').lower())
        position_penalties = sum(1 for p in penalties_data if 'grid' in p.get('type', '').lower())
        warnings = sum(1 for p in penalties_data if 'warning' in p.get('type', '').lower())
        
        self.time_penalty_card.count_label.setText(str(time_penalties))
        self.position_penalty_card.count_label.setText(str(position_penalties))
        self.warning_card.count_label.setText(str(warnings))
        
        # 找出最嚴重的處罰
        if penalties_data:
            most_severe = max(penalties_data, key=lambda x: x.get('severity_score', 0))
            driver = most_severe.get('driver', 'N/A')
            penalty_type = most_severe.get('type', 'N/A')
            self.severe_penalty_label.setText(f"Most severe: {penalty_type} ({driver})")


class DriverIncidentBarChart(QFrame):
    """🏆 Driver Incident Frequency - 車手事故頻率條形圖"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.incident_data = {}
        
    def setup_ui(self):
        """設置條形圖UI - 無外框版本"""
        # 移除外框
        self.setFrameStyle(QFrame.NoFrame)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
        layout.setSpacing(5)  # 減少間距
        
        # 標題
        title_label = QLabel(tr('driver_incident_frequency', '🏆 Driver Incident Frequency'))
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #333;
            margin-bottom: 3px;
        """)
        layout.addWidget(title_label)
        
        # 圖表區域 - 動態調整但以內容為主，放大字體
        self.chart_area = QLabel()
        self.chart_area.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                color: #374151;
                line-height: 1.2;
            }
        """)
        self.chart_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # 設置大小政策：水平方向擴展，垂直方向以內容為主
        self.chart_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # 調整高度以配合放大的內容
        self.chart_area.setMinimumHeight(140)  # 增加最小高度
        self.chart_area.setMaximumHeight(220)  # 增加最大高度
        
        layout.addWidget(self.chart_area)
        
    def update_chart_data(self, driver_incidents):
        """更新圖表數據 - 僅使用真實數據"""
        if not driver_incidents:
            # ⚠️ 禁用模擬數據政策：顯示無數據訊息
            self.chart_area.setText(tr('no_incident_data', 'No driver incident data available\n\nPlease load accident analysis data from API or CLI'))
            return
            
        self._render_chart(driver_incidents)
        
    def _render_chart(self, data):
        """渲染ASCII條形圖 - 放大1px，完美對齊線條"""
        if not data:
            self.chart_area.setText(tr('no_data_available', 'No incident data available'))
            return
            
        # 排序數據
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
        max_value = max(data.values()) if data else 1
        
        # 放大條形圖寬度 - 增加1px效果
        max_bar_width = 40  # 從35增加到40
        
        chart_lines = []
        
        # 添加標題行 - 使用固定寬度確保完美對齊
        header = f"{'Driver':<6} │ {'Incidents':^40} │ {'Count':>5}"
        separator = "───────┼─" + "─" * 40 + "─┼──────"
        
        chart_lines.append(header)
        chart_lines.append(separator)
        
        for driver, count in sorted_data[:8]:  # 只顯示前8名
            # 計算條形長度
            bar_length = int((count / max_value) * max_bar_width) if max_value > 0 else 0
            bar = "█" * bar_length
            
            # 格式化輸出 - 完美對齊所有列
            # Driver: 左對齊6字符, Bar: 左對齊40字符, Count: 右對齊5字符
            line = f"{driver:<6} │ {bar:<40} │ {count:>5}"
            chart_lines.append(line)
        
        chart_text = "\n".join(chart_lines)
        self.chart_area.setText(chart_text)


# 註冊模組到工廠
try:
    from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
    ModuleFactory.register_module(ModuleTypes.ACCIDENT_ANALYSIS, AccidentAnalysisModule)
    print(f"[OK] [MODULE_FACTORY] 事故分析模組已註冊")
except ImportError as e:
    print(f"[WARNING] [MODULE_FACTORY] 事故分析模組註冊失敗: {e}")


if __name__ == "__main__":
    print("F1T 事故綜合分析模組 - 獨立測試模式")
    print("此模組需要在F1T GUI主程式中使用")
