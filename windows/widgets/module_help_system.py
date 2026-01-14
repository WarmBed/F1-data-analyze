# -*- coding: utf-8 -*-
"""
F1T GUI - Module Help System
=============================

模組說明系統 - 為每個 MDI 視窗提供獨立的幫助說明。

包含：
- ModuleHelpRegistry: 註冊和獲取模組說明內容
- ModuleHelpDialog: 顯示說明的對話框

Author: F1T Team
Date: 2026-01-11
"""

from typing import Dict, Optional, List, Tuple
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 引入翻譯函數
try:
    from core.gui_i18n import tr
except ImportError:
    def tr(key, default=None, *args, **kwargs):
        return default if default else key


class ModuleHelpRegistry:
    """
    模組說明註冊表
    
    存儲每個模組的幫助內容，支援多語言。
    幫助內容使用 tr() 函數進行翻譯。
    """
    
    # 模組說明內容
    # 格式: module_key -> (title_key, description_key, features_key, colors_key)
    _registry: Dict[str, Dict[str, str]] = {}
    
    @classmethod
    def register_all(cls):
        """註冊所有模組的說明內容"""
        # ========== Driver Strategy ==========
        cls._registry["driver_strategy"] = {
            "title": "help_driver_strategy_title",
            "description": "help_driver_strategy_desc",
            "features": "help_driver_strategy_features",
            "colors": "help_driver_strategy_colors",
        }
        
        # ========== Top Speed History ==========
        cls._registry["top_speed_history"] = {
            "title": "help_top_speed_history_title",
            "description": "help_top_speed_history_desc",
            "features": "help_top_speed_history_features",
            "colors": "help_top_speed_history_colors",
        }
        
        # ========== Track Map ==========
        cls._registry["track_map"] = {
            "title": "help_track_map_title",
            "description": "help_track_map_desc",
            "features": "help_track_map_features",
            "colors": "help_track_map_colors",
        }
        
        # ========== Live Ranking ==========
        cls._registry["ranking_tower"] = {
            "title": "help_ranking_tower_title",
            "description": "help_ranking_tower_desc",
            "features": "help_ranking_tower_features",
            "colors": "help_ranking_tower_colors",
        }
        
        # ========== Lap History ==========
        cls._registry["lap_history_lap_time"] = {
            "title": "help_lap_history_title",
            "description": "help_lap_history_desc",
            "features": "help_lap_history_features",
            "colors": "help_lap_history_colors",
        }
        
        # ========== SF% History ==========
        cls._registry["sf_percentage_chart"] = {
            "title": "help_sf_percentage_title",
            "description": "help_sf_percentage_desc",
            "features": "help_sf_percentage_features",
            "colors": "help_sf_percentage_colors",
        }
        
        # ========== Throttle 95% History ==========
        cls._registry["throttle_history"] = {
            "title": "help_throttle_history_title",
            "description": "help_throttle_history_desc",
            "features": "help_throttle_history_features",
            "colors": "help_throttle_history_colors",
        }
        
        # ========== Sector Comparison ==========
        cls._registry["sector_comparison_s1"] = {
            "title": "help_sector_comparison_title",
            "description": "help_sector_comparison_desc",
            "features": "help_sector_comparison_features",
            "colors": "help_sector_comparison_colors",
        }
        cls._registry["sector_comparison_s2"] = cls._registry["sector_comparison_s1"]
        cls._registry["sector_comparison_s3"] = cls._registry["sector_comparison_s1"]
        
        # ========== Speed Trace ==========
        cls._registry["speed_trace"] = {
            "title": "help_speed_trace_title",
            "description": "help_speed_trace_desc",
            "features": "help_speed_trace_features",
            "colors": "help_speed_trace_colors",
        }
        
        # ========== Telemetry Traces ==========
        for trace_type in ["throttle_trace", "brake_trace", "gear_trace", "drs_trace", "rpm_trace"]:
            cls._registry[trace_type] = {
                "title": f"help_{trace_type}_title",
                "description": f"help_{trace_type}_desc",
                "features": f"help_{trace_type}_features",
                "colors": f"help_{trace_type}_colors",
            }
        
        # ========== Circle Map ==========
        cls._registry["circle_map"] = {
            "title": "help_circle_map_title",
            "description": "help_circle_map_desc",
            "features": "help_circle_map_features",
            "colors": "help_circle_map_colors",
        }
        
        # ========== Pit Window ==========
        cls._registry["pit_window"] = {
            "title": "help_pit_window_title",
            "description": "help_pit_window_desc",
            "features": "help_pit_window_features",
            "colors": "help_pit_window_colors",
        }
        
        # ========== Tyre Strategy ==========
        cls._registry["tyre_strategy"] = {
            "title": "help_tyre_strategy_title",
            "description": "help_tyre_strategy_desc",
            "features": "help_tyre_strategy_features",
            "colors": "help_tyre_strategy_colors",
        }
        
        # ========== Battle Insight ==========
        cls._registry["battle_insight"] = {
            "title": "help_battle_insight_title",
            "description": "help_battle_insight_desc",
            "features": "help_battle_insight_features",
            "colors": "help_battle_insight_colors",
        }
        
        # ========== Chase Strategy ==========
        cls._registry["chase_strategy"] = {
            "title": "help_chase_strategy_title",
            "description": "help_chase_strategy_desc",
            "features": "help_chase_strategy_features",
            "colors": "help_chase_strategy_colors",
        }
        
        # ========== Track & Weather ==========
        cls._registry["track_weather"] = {
            "title": "help_track_weather_title",
            "description": "help_track_weather_desc",
            "features": "help_track_weather_features",
            "colors": "help_track_weather_colors",
        }
        
        # ========== Traffic Timeline ==========
        cls._registry["live_traffic_timeline"] = {
            "title": "help_traffic_timeline_title",
            "description": "help_traffic_timeline_desc",
            "features": "help_traffic_timeline_features",
            "colors": "help_traffic_timeline_colors",
        }
        
        # ========== Race Control Messages ==========
        cls._registry["race_control_messages"] = {
            "title": "help_race_control_title",
            "description": "help_race_control_desc",
            "features": "help_race_control_features",
            "colors": "help_race_control_colors",
        }
        
        # ========== Lap Time Distribution ==========
        cls._registry["lap_time_distribution"] = {
            "title": "help_lap_distribution_title",
            "description": "help_lap_distribution_desc",
            "features": "help_lap_distribution_features",
            "colors": "help_lap_distribution_colors",
        }
        
        # ========== Phase 2: Telemetry Analysis ==========
        for module in ["speed_analysis", "throttle_analysis", "brake_analysis", 
                       "gear_analysis", "rpm_analysis", "telemetry_comparison"]:
            cls._registry[module] = {
                "title": f"help_{module}_title",
                "description": f"help_{module}_desc",
                "features": f"help_{module}_features",
                "colors": f"help_{module}_colors",
            }
        
        # ========== Phase 3: Advanced Analysis ==========
        for module in ["long_run", "ideal_lap", "pitstop_analysis", "lap_box_plot"]:
            cls._registry[module] = {
                "title": f"help_{module}_title",
                "description": f"help_{module}_desc",
                "features": f"help_{module}_features",
                "colors": f"help_{module}_colors",
            }
        
        # ========== Phase 4: Prediction ==========
        for module in ["fp2_prediction", "qualifying_prediction", "race_prediction"]:
            cls._registry[module] = {
                "title": f"help_{module}_title",
                "description": f"help_{module}_desc",
                "features": f"help_{module}_features",
                "colors": f"help_{module}_colors",
            }
        
        # ========== Phase 5: Multi-Season ==========
        for module in ["pole_defense", "start_reaction", "season_progress",
                       "driver_standings", "constructor_standings", "pit_loss_table"]:
            cls._registry[module] = {
                "title": f"help_{module}_title",
                "description": f"help_{module}_desc",
                "features": f"help_{module}_features",
                "colors": f"help_{module}_colors",
            }
        
        # ========== Additional Modules ==========
        for module in ["tire_analysis", "accident_analysis", "weather_timeline", 
                       "position_analysis", "control_panel"]:
            cls._registry[module] = {
                "title": f"help_{module}_title",
                "description": f"help_{module}_desc",
                "features": f"help_{module}_features",
                "colors": f"help_{module}_colors",
            }
        
        # ========== 通用回退 ==========
        cls._registry["_default"] = {
            "title": "help_default_title",
            "description": "help_default_desc",
            "features": "help_default_features",
            "colors": "help_default_colors",
        }
    
    @classmethod
    def get_help_content(cls, module_key: str) -> Dict[str, str]:
        """
        獲取模組的幫助內容
        
        Args:
            module_key: 模組鍵值（如 "driver_strategy", "track_map"）
            
        Returns:
            包含翻譯後內容的字典
        """
        # 確保已註冊
        if not cls._registry:
            cls.register_all()
        
        # 獲取模組說明，若無則使用預設
        help_keys = cls._registry.get(module_key, cls._registry.get("_default", {}))
        
        # 翻譯內容
        return {
            "title": tr(help_keys.get("title", ""), help_keys.get("title", "")),
            "description": tr(help_keys.get("description", ""), ""),
            "features": tr(help_keys.get("features", ""), ""),
            "colors": tr(help_keys.get("colors", ""), ""),
        }
    
    @classmethod
    def get_module_key_from_title(cls, window_title: str) -> str:
        """
        從視窗標題推斷模組鍵值
        
        Args:
            window_title: MDI 視窗標題
            
        Returns:
            模組鍵值
        """
        title_lower = window_title.lower()
        
        # 標題到模組鍵的映射
        title_mappings = {
            "driver strategy": "driver_strategy",
            "車手策略": "driver_strategy",
            "top speed": "top_speed_history",
            "最高速": "top_speed_history",
            "track map": "track_map",
            "賽道地圖": "track_map",
            "ranking": "ranking_tower",
            "排名": "ranking_tower",
            "lap history": "lap_history_lap_time",
            "圈速歷史": "lap_history_lap_time",
            "sf%": "sf_percentage_chart",
            "throttle 95%": "throttle_history",
            "油門 95%": "throttle_history",
            "sector comparison": "sector_comparison_s1",
            "分段比較": "sector_comparison_s1",
            "speed trace": "speed_trace",
            "速度追蹤": "speed_trace",
            "throttle trace": "throttle_trace",
            "油門追蹤": "throttle_trace",
            "brake trace": "brake_trace",
            "煞車追蹤": "brake_trace",
            "gear trace": "gear_trace",
            "檔位追蹤": "gear_trace",
            "drs trace": "drs_trace",
            "drs追蹤": "drs_trace",
            "rpm trace": "rpm_trace",
            "轉速追蹤": "rpm_trace",
            "circle map": "circle_map",
            "圓形地圖": "circle_map",
            "pit window": "pit_window",
            "進站窗口": "pit_window",
            "tyre strategy": "tyre_strategy",
            "輪胎策略": "tyre_strategy",
            "battle insight": "battle_insight",
            "戰鬥分析": "battle_insight",
            "chase strategy": "chase_strategy",
            "追趕策略": "chase_strategy",
            "track & weather": "track_weather",
            "賽道與天氣": "track_weather",
            "traffic": "live_traffic_timeline",
            "車流": "live_traffic_timeline",
            "race control": "race_control_messages",
            "比賽控制": "race_control_messages",
            "lap time distribution": "lap_time_distribution",
            "圈速分布": "lap_time_distribution",
            
            # Phase 2: Telemetry Analysis
            "speed analysis": "speed_analysis",
            "速度分析": "speed_analysis",
            "throttle analysis": "throttle_analysis",
            "油門分析": "throttle_analysis",
            "brake analysis": "brake_analysis",
            "煞車分析": "brake_analysis",
            "gear analysis": "gear_analysis",
            "檔位分析": "gear_analysis",
            "rpm analysis": "rpm_analysis",
            "rpm分析": "rpm_analysis",
            "telemetry": "telemetry_comparison",
            "遙測": "telemetry_comparison",
            
            # Phase 3: Advanced Analysis
            "long run": "long_run",
            "長跑": "long_run",
            "ideal lap": "ideal_lap",
            "理想圈": "ideal_lap",
            "pitstop": "pitstop_analysis",
            "進站分析": "pitstop_analysis",
            "box plot": "lap_box_plot",
            "箱型圖": "lap_box_plot",
            
            # Phase 4: Prediction
            "fp2": "fp2_prediction",
            "qualifying prediction": "qualifying_prediction",
            "排位預測": "qualifying_prediction",
            "race prediction": "race_prediction",
            "正賽預測": "race_prediction",
            
            # Phase 5: Multi-Season
            "pole defense": "pole_defense",
            "桿位": "pole_defense",
            "start reaction": "start_reaction",
            "起跑": "start_reaction",
            "season progress": "season_progress",
            "賽季": "season_progress",
            "driver standing": "driver_standings",
            "車手積分": "driver_standings",
            "constructor": "constructor_standings",
            "車隊積分": "constructor_standings",
            "pit loss": "pit_loss_table",
            "進站時間損失": "pit_loss_table",
            "ピットタイムロス": "pit_loss_table",
            
            # Additional
            "tire": "tire_analysis",
            "輪胎分析": "tire_analysis",
            "accident": "accident_analysis",
            "事故": "accident_analysis",
            "weather timeline": "weather_timeline",
            "天氣": "weather_timeline",
            "position": "position_analysis",
            "位置": "position_analysis",
            "control panel": "control_panel",
            "控制面板": "control_panel",
        }
        
        for pattern, key in title_mappings.items():
            if pattern in title_lower:
                return key
        
        return "_default"


class ModuleHelpDialog(QDialog):
    """
    模組說明對話框
    
    顯示模組的功能說明、使用方法和顏色圖例。
    """
    
    def __init__(self, module_key: str, window_title: str = "", parent=None):
        super().__init__(parent)
        
        self.module_key = module_key
        self.window_title = window_title
        
        self._setup_ui()
    
    def _setup_ui(self):
        """設置 UI"""
        # 視窗設置
        self.setWindowTitle(tr("module_help_title", "Module Help"))
        self.setMinimumSize(450, 350)
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 深色主題
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                background-color: transparent;
            }
            QScrollArea {
                border: none;
                background-color: #2b2b2b;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555555;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # 獲取幫助內容
        content = ModuleHelpRegistry.get_help_content(self.module_key)
        
        # 標題
        title_label = QLabel(content.get("title", self.window_title))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #4fc3f7; margin-bottom: 8px;")
        main_layout.addWidget(title_label)
        
        # 滾動區域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # 功能說明
        if content.get("description"):
            self._add_section(scroll_layout, tr("help_section_description", "Description"), content["description"])
        
        # 功能特點
        if content.get("features"):
            self._add_section(scroll_layout, tr("help_section_features", "Features"), content["features"])
        
        # 顏色圖例 - 使用專門的顏色顯示方法
        if content.get("colors"):
            self._add_color_section(scroll_layout, tr("help_section_colors", "Color Legend"), content["colors"])
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)
        
        # 關閉按鈕
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton(tr("close", "Close"))
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
    
    def _add_section(self, layout: QVBoxLayout, title: str, content: str):
        """添加說明區塊"""
        # 區塊標題
        section_title = QLabel(title)
        section_font = QFont()
        section_font.setPointSize(11)
        section_font.setBold(True)
        section_title.setFont(section_font)
        section_title.setStyleSheet("color: #81c784; margin-top: 8px;")
        layout.addWidget(section_title)
        
        # 分隔線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #555555;")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        # 內容
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("color: #e0e0e0; line-height: 1.5; padding: 4px 0;")
        layout.addWidget(content_label)
    
    def _add_color_section(self, layout: QVBoxLayout, title: str, content: str):
        """添加顏色圖例區塊，包含實際顏色範例"""
        # 區塊標題
        section_title = QLabel(title)
        section_font = QFont()
        section_font.setPointSize(11)
        section_font.setBold(True)
        section_title.setFont(section_font)
        section_title.setStyleSheet("color: #81c784; margin-top: 8px;")
        layout.addWidget(section_title)
        
        # 分隔線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #555555;")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        # 顏色範例區域
        color_widget = QWidget()
        color_layout = QVBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 8, 0, 0)
        color_layout.setSpacing(6)
        
        # 解析內容並添加顏色範例
        lines = content.split('\n')
        current_section = None
        
        for line_text in lines:
            line_text = line_text.strip()
            if not line_text:
                continue
            
            # 檢測區塊標題（以【】包圍）
            if line_text.startswith('【') and '】' in line_text:
                current_section = line_text
                section_label = QLabel(line_text)
                section_label.setStyleSheet("color: #ffd54f; font-weight: bold; margin-top: 8px;")
                color_layout.addWidget(section_label)
                continue
            
            # 處理顏色項目
            color_item = self._create_color_item(line_text)
            if color_item:
                color_layout.addWidget(color_item)
            else:
                # 普通文字
                text_label = QLabel(line_text)
                text_label.setWordWrap(True)
                text_label.setStyleSheet("color: #e0e0e0; padding-left: 4px;")
                color_layout.addWidget(text_label)
        
        layout.addWidget(color_widget)
    
    def _create_color_item(self, text: str) -> QWidget:
        """創建帶有顏色方塊的項目"""
        # 顏色映射表
        color_map = {
            # 背景顏色
            '黃色背景': ('#b8860b', '#000000'),  # (bg, text)
            '紅色背景': ('#8b0000', '#ffffff'),
            '深灰背景': ('#1a1a1a', '#ffffff'),
            '深灰色背景': ('#1a1a1a', '#ffffff'),
            # 數字/文字顏色
            '紫色數字': (None, '#a855f7'),
            '綠色數字': (None, '#22c55e'),
            '黃色數字': (None, '#eab308'),
            '紅色數字': (None, '#ef4444'),
            '紫色': (None, '#a855f7'),
            '綠色': (None, '#22c55e'),
            '黃色': (None, '#eab308'),
            '紅色': (None, '#ef4444'),
            # 差距顏色
            '綠色差距': (None, '#22c55e'),
            '紅色差距': (None, '#ef4444'),
            # 輪胎
            '紅色圓圈': ('#ff0000', '#ffffff'),
            '黃色圓圈': ('#ffd700', '#000000'),
            '白色圓圈': ('#ffffff', '#000000'),
            # 車隊顏色
            '深藍色': (None, '#1e41ff'),
            '深藍圓點': ('#1e41ff', '#ffffff'),
            '紅色圓點': ('#dc0000', '#ffffff'),
            '青綠圓點': ('#00d2be', '#000000'),
            '青綠色': (None, '#00d2be'),
            '橙色': (None, '#ff8700'),
            '淺藍色': (None, '#64c4ff'),
            '深綠色': (None, '#006f62'),
            '白色': (None, '#ffffff'),
            # 區段
            '綠色區段': ('#22c55e', '#000000'),
            '黃色區段': ('#eab308', '#000000'),
            '紅色區段': ('#ef4444', '#ffffff'),
        }
        
        # 檢查是否包含可顯示的顏色
        matched_color = None
        for color_key, colors in color_map.items():
            if color_key in text:
                matched_color = (color_key, colors)
                break
        
        if not matched_color:
            return None
        
        color_key, (bg_color, text_color) = matched_color
        
        # 創建水平布局
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(4, 2, 4, 2)
        item_layout.setSpacing(8)
        
        # 創建顏色方塊
        color_box = QLabel()
        color_box.setFixedSize(20, 20)
        
        if bg_color:
            # 背景色方塊
            color_box.setStyleSheet(f"""
                background-color: {bg_color};
                border: 1px solid #666666;
                border-radius: 3px;
            """)
            if '圓' in color_key:
                color_box.setStyleSheet(f"""
                    background-color: {bg_color};
                    border: 1px solid #666666;
                    border-radius: 10px;
                """)
        else:
            # 文字顏色方塊（顯示文字 "A"）
            color_box.setText("A")
            color_box.setAlignment(Qt.AlignCenter)
            color_box.setStyleSheet(f"""
                color: {text_color};
                background-color: #1a1a1a;
                border: 1px solid #666666;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            """)
        
        item_layout.addWidget(color_box)
        
        # 文字說明
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #e0e0e0;")
        item_layout.addWidget(text_label, stretch=1)
        
        return item_widget


def show_module_help(window_title: str, parent=None):
    """
    顯示模組幫助對話框
    
    Args:
        window_title: MDI 視窗標題
        parent: 父視窗
    """
    module_key = ModuleHelpRegistry.get_module_key_from_title(window_title)
    dialog = ModuleHelpDialog(module_key, window_title, parent)
    dialog.exec_()
