# -*- coding: utf-8 -*-
"""
FunctionTreeBuilder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from core.gui_i18n import tr
from windows.widgets.context_menu_tree_widget import ContextMenuTreeWidget

from core.logger import get_logger

logger = get_logger(__name__)


class FunctionTreeBuilder:
    """從 f1t_gui_main.py 提取的 create_professional_function_tree 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_professional_function_tree(self):
        """創建專業功能樹"""
        widget = QWidget()
        widget.setObjectName("FunctionTreeWidget")  # 添加對象名稱
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        
        # 標題
        title_frame = QFrame()
        title_frame.setObjectName("FunctionTreeTitle")
        title_frame.setFixedHeight(16)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(2, 1, 2, 1)
        title_layout.addWidget(QLabel(tr("analysis_modules", "Analysis Modules")))
        layout.addWidget(title_frame)
        
        # 支援右鍵選單的功能樹
        tree = ContextMenuTreeWidget(self.main_window)
        tree.setObjectName("ProfessionalFunctionTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(12)  # 增加縮排以容納三層結構
        tree.setRootIsDecorated(True)
        
        # 啟用列寬度自適應內容
        tree.header().setStretchLastSection(True)
        tree.setColumnCount(1)
        
        # 存儲為實例屬性以便清理
        self.main_window.function_tree = tree
        
        # ========== Historical Analysis (歷史靜態分析) ==========
        historical_group = QTreeWidgetItem(tree, [tr("historical_analysis", "Historical Analysis")])
        historical_group.setExpanded(False)  # 預設收合
        
        # Race Overview (賽事總覽)
        race_overview_group = QTreeWidgetItem(historical_group, [tr("race_overview", "Race Overview")])
        race_overview_group.setExpanded(False)
        QTreeWidgetItem(race_overview_group, [tr("temp_analysis", "Temperature Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("track_analysis", "Track Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("pitstop_analysis", "Pitstop Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("accident_analysis", "Accident Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("tire_strategy_analysis", "Tire Strategy Analysis")])
        QTreeWidgetItem(race_overview_group, [tr("driver_position_analysis", "Driver Race Position")])
        QTreeWidgetItem(race_overview_group, [tr("traffic_analysis", "Traffic Analysis")])
        
        # Telemetry Analysis (遙測分析)
        telemetry_group = QTreeWidgetItem(historical_group, [tr("telemetry_analysis", "Telemetry Analysis")])
        telemetry_group.setExpanded(False)
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("speed_analysis", "Speed Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("brake_analysis", "Brake Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("throttle_analysis_sub", "Throttle Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("gear_analysis", "Gear Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("rpm_analysis", "RPM Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("acceleration_analysis", "Acceleration Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("speed_diff_analysis", "Speed Diff Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("distance_diff_analysis", "Distance Diff Analysis")])
        QTreeWidgetItem(telemetry_group, ["    (L) " + tr("time_diff_analysis", "Time Diff Analysis")])
        
        # Lap Performance (圈速表現)
        lap_performance_group = QTreeWidgetItem(historical_group, [tr("lap_performance", "Lap Performance")])
        lap_performance_group.setExpanded(False)
        QTreeWidgetItem(lap_performance_group, ["    (D) " + tr("detailed_lap_table", "Detailed Lap Table")])
        QTreeWidgetItem(lap_performance_group, ["    (D) " + tr("lap_time_box_plot_sub", "Lap Time Box Plot")])
        QTreeWidgetItem(lap_performance_group, ["    (T) " + tr("throttle_box_plot", "Throttle Box Plot")])
        QTreeWidgetItem(lap_performance_group, ["    (T) " + tr("throttle_line_chart", "Throttle Line Chart")])
        
        # Ideal Lap & Sectors (理想圈速與分段)
        ideal_lap_group = QTreeWidgetItem(historical_group, [tr("ideal_lap_sectors", "Ideal Lap & Sectors")])
        ideal_lap_group.setExpanded(False)
        QTreeWidgetItem(ideal_lap_group, ["    " + tr("ideal_lap_ranking_table", "Ideal Lap Ranking Table")])
        QTreeWidgetItem(ideal_lap_group, ["    " + tr("ideal_lap_sector_comparison", "Sector Comparison")])
        QTreeWidgetItem(ideal_lap_group, ["    " + tr("ideal_lap_sector_heatmap", "Sector Heat Map")])
        
        # Speed & Corner Analysis (速度與彎道)
        speed_corner_group = QTreeWidgetItem(historical_group, [tr("speed_corner_analysis", "Speed & Corner Analysis")])
        speed_corner_group.setExpanded(False)
        QTreeWidgetItem(speed_corner_group, ["    " + tr("all_drivers_straight_speed", "Straight Speed & Acceleration")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("all_drivers_max_speed", "All Drivers Max Speed")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("all_drivers_acceleration_chart", "Acceleration Chart")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("all_drivers_brake_chart", "Brake Chart")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("all_drivers_brake_performance", "Brake Performance")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("all_drivers_brake_all_laps_analysis", "All Drivers Brake All Laps Analysis")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("low_speed_corner_analysis", "Low-Speed Corners")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("mid_speed_corner_analysis", "Mid-Speed Corners")])
        QTreeWidgetItem(speed_corner_group, ["    " + tr("high_speed_corner_analysis", "High-Speed Corners")])
        
        # Prediction Models (預測模型)
        prediction_group = QTreeWidgetItem(historical_group, [tr("prediction_models", "Prediction Models")])
        prediction_group.setExpanded(False)
        QTreeWidgetItem(prediction_group, ["    " + tr("qualifying_prediction_table", "FP3 → Q Prediction")])
        QTreeWidgetItem(prediction_group, ["    " + tr("fp2_qualifying_prediction_table", "FP2 → Q Prediction")])
        QTreeWidgetItem(prediction_group, ["    " + tr("race_prediction_table", "Q → R Prediction")])
        
        # ========== Multi-Season Analysis (多賽季分析) ==========
        multi_season_group = QTreeWidgetItem(tree, [tr("multi_season_analysis", "Multi-Season Analysis")])
        multi_season_group.setExpanded(False)
        QTreeWidgetItem(multi_season_group, [tr("historical_track_map", "Historical Track Map")])
        QTreeWidgetItem(multi_season_group, [tr("season_start_reaction", "Season Start Reaction")])
        QTreeWidgetItem(multi_season_group, [tr("pole_defense_statistics", "Pole Defense Statistics")])
        
        # ========== Live Timing ==========
        live_timing_group = QTreeWidgetItem(tree, [tr("live_timing_tree", "Live Timing")])
        live_timing_group.setExpanded(False)  # 預設收合
        
        # Live Timing 子項目 - 已啟用的模組
        lt_enabled_items = [
            ("live_timing_track_map", "Track Map"),
            ("live_timing_circle_map", "Circle Map"),
            ("live_timing_ranking", "Live Ranking"),
            ("live_timing_pit_window", "Pit Window"),
            ("live_timing_tyre_strategy", "Tyre Strategy"),
            ("live_timing_driver_strategy", "Driver Strategy"),
            ("live_timing_lap_distribution", "Lap Time Distribution"),
            ("live_timing_race_control", "Race Control Messages"),
            ("live_timing_speed_trace", "Speed Trace"),
            ("live_timing_throttle_trace", "Throttle Trace"),
            ("live_timing_brake_trace", "Brake Trace"),
            ("live_timing_gear_trace", "Gear Trace"),
            ("live_timing_drs_trace", "DRS Trace"),
            ("live_timing_rpm_trace", "RPM Trace"),
            # ("live_timing_battle_insight", "Battle Insight"),  # ❌ 已禁用（性能優化）
            ("live_timing_chase_strategy", "Chase Strategy"),
            ("live_timing_track_weather", "Track & Weather"),
            ("live_traffic_timeline", "Traffic Timeline"),
        ]
        for key, default in lt_enabled_items:
            QTreeWidgetItem(live_timing_group, [tr(key, default)])
        
        # Lap History 子群組
        lap_history_group = QTreeWidgetItem(live_timing_group, [tr("lap_history_group", "Lap History")])
        lap_history_items = [
            ("lap_history_lap_time", "Lap History - Lap Time"),
            ("lap_history_s1", "Lap History - S1"),
            ("lap_history_s2", "Lap History - S2"),
            ("lap_history_s3", "Lap History - S3"),
            ("throttle_history", "Throttle 95%"),
            ("sf_percentage_chart", "SF% History"),
        ]
        for key, default in lap_history_items:
            QTreeWidgetItem(lap_history_group, [tr(key, default)])
        
        # Sector Comparison 子群組 (兩車手比較曲線圖)
        sector_comparison_group = QTreeWidgetItem(live_timing_group, [tr("sector_comparison_group", "Sector Comparison")])
        sector_comparison_items = [
            ("sector_comparison_s1", "S1 Comparison"),
            ("sector_comparison_s2", "S2 Comparison"),
            ("sector_comparison_s3", "S3 Comparison"),
        ]
        for key, default in sector_comparison_items:
            QTreeWidgetItem(sector_comparison_group, [tr(key, default)])
        
        # 自動調整列寬以適應內容（但允許用戶手動調整）
        tree.resizeColumnToContents(0)
        
        layout.addWidget(tree)
        
        return widget
