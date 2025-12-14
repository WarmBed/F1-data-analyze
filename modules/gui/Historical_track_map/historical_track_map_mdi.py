#!/usr/bin/env python3
"""
Historical Track Map MDI
歷年賽道旗幟統計 MDI 視窗

整合賽道地圖、高程圖表和旗幟統計表格的 MDI 視窗管理器
基於 UniversalAnalysisMDI 架構實現

Author: F1T Team
Date: 2025-11-11
Version: 1.0.0
"""

import sys
import os
import time
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QMessageBox, QSplitter,
    QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPen, QFont

from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)

# 導入基類
try:
    from ..base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入數據載入器
try:
    from .historical_track_map_data_loader import HistoricalTrackMapDataLoader, HistoricalTrackMapApiWorker
except ImportError:
    from modules.gui.Historical_track_map.historical_track_map_data_loader import HistoricalTrackMapDataLoader, HistoricalTrackMapApiWorker

# 導入賽道組件
try:
    from modules.gui.track_analysis.track_map_widget import TrackMapWidget
    from modules.gui.track_elevation.elevation_chart_widget_pyqt5 import ElevationChartWidget
except ImportError as e:
    logger.error(f"[HISTORICAL_TRACK_MAP_MDI] 無法導入賽道組件: {e}")
    TrackMapWidget = None
    ElevationChartWidget = None


class SpeedLegendWidget(QWidget):
    """
    速度圖例 Widget - 顯示速度漸變色條
    
    垂直顯示：
    - 頂部：最高速度 (藍色)
    - 中間：顏色漸變
    - 底部：最低速度 (紅色)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_speed = 0
        self.max_speed = 0
        self.setFixedWidth(60)  # 固定寬度 60px
        self.setMinimumHeight(150)  # 最小高度
        
    def set_speed_range(self, min_speed: float, max_speed: float):
        """設置速度範圍"""
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.update()  # 觸發重繪
        
    def paintEvent(self, event):
        """繪製速度圖例"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 計算佈局（調整文字區域高度避免重疊）
        text_height = 50  # 增加文字區域高度：40 → 50
        bar_top = text_height
        bar_bottom = height - text_height
        bar_height = bar_bottom - bar_top
        
        if bar_height <= 0:
            return
        
        # 1. 繪製頂部文字（最高速度）
        painter.setPen(QPen(QColor(0, 0, 0)))  # ✅ 改用黑色
        font = QFont("Arial", 11, QFont.Bold)  # 字體稍微放大：10 → 11
        painter.setFont(font)
        painter.drawText(0, 5, width, 20, Qt.AlignCenter, f"{int(self.max_speed)}")  # 調整位置
        
        small_font = QFont("Arial", 8)
        painter.setFont(small_font)
        painter.drawText(0, 25, width, 20, Qt.AlignCenter, "km/h")  # 調整位置：15 → 25
        
        # 2. 繪製漸變色條（藍色 → 紅色，與 TrackMap 完全一致）
        gradient = QLinearGradient(0, bar_top, 0, bar_bottom)
        # ✅ 移除綠色過渡，只使用藍→紅線性漸變
        # 高速 = 藍色 (Material Blue 500) RGB(33, 150, 243)
        gradient.setColorAt(0.0, QColor(33, 150, 243))
        # 低速 = 紅色 (Material Red 500) RGB(244, 67, 54)
        gradient.setColorAt(1.0, QColor(244, 67, 54))
        
        # 繪製漸變矩形
        bar_margin = 10
        painter.fillRect(bar_margin, bar_top, width - 2*bar_margin, bar_height, gradient)
        
        # 繪製邊框
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(bar_margin, bar_top, width - 2*bar_margin, bar_height)
        
        # 3. 繪製底部文字（最低速度）
        painter.setPen(QPen(QColor(0, 0, 0)))  # ✅ 改用黑色
        painter.setFont(font)
        painter.drawText(0, bar_bottom + 5, width, 20, Qt.AlignCenter, f"{int(self.min_speed)}")  # 調整位置
        
        painter.setFont(small_font)
        painter.drawText(0, bar_bottom + 25, width, 20, Qt.AlignCenter, "km/h")  # 調整位置：20 → 25


class HistoricalTrackMapMDI(UniversalAnalysisMDI):
    """
    歷年賽道旗幟統計 MDI 視窗
    
    功能：
    - 賽道平面圖 (TrackMapWidget)
    - 高程剖面圖 (ElevationChartWidget)  
    - 年度旗幟統計表格
    - 彎道旗幟統計表格
    - 總計統計表格
    
    數據源：API-ONLY (Function 100)
    """
    
    # 類別層級註冊標記
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="historical_track_map",
                display_name=tr("historical_track_map", "Historical Track Map"),
                default_size=(1600, 900),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("historical_track_map", config)
            cls._REGISTERED = True
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="historical_track_map", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        self.session = None
        
        # 組件引用
        self.track_map = None
        self.elevation_chart = None
        self.speed_legend_widget = None  # ✅ 新增速度圖例
        self.yearly_table = None
        self.top3_drivers_table = None  # ✅ 新增：車手名次表格
        self.corner_table = None
        self.total_table = None
        self.info_label = None  # ❌ 已隱藏
        self.speed_gradient_checkbox = None
        self.speed_distribution_checkbox = None  # ✅ 新增速度分布勾選框
        
        # 狀態變數
        self._is_data_loaded = False
        self._current_flags_data = None
        
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 基類初始化完成")
    
    def create_data_manager(self) -> HistoricalTrackMapDataLoader:
        """創建數據管理器"""
        return HistoricalTrackMapDataLoader(self)
    
    def create_chart_widget(self) -> QWidget:
        """
        創建圖表組件
        
        此模組使用自定義佈局（TrackMap + ElevationChart + Tables），
        不使用單一圖表組件
        """
        return None  # 不使用單一圖表組件
    
    def create_control_widget(self) -> QWidget:
        """
        創建控制面板
        
        此模組使用內嵌控制按鈕，不使用獨立控制面板
        """
        return None  # 不使用獨立控制面板
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組組件
        
        創建完整的 UI 佈局：
        - 頂部：資訊標籤 + 控制按鈕
        - 左側：賽道地圖 + 高程圖表 (垂直分割)
        - 右側：旗幟統計表格
        
        Args:
            parent_widget: 父容器
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        logger.debug("[HISTORICAL_TRACK_MAP_MDI] initialize_module 開始...")
        
        try:
            # ✅ 驗證必要屬性（完全複製 Ideal Lap Ranking）
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error(f"[HISTORICAL_TRACK_MAP_MDI] ❌ 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error(f"[HISTORICAL_TRACK_MAP_MDI] ❌ 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error(f"[HISTORICAL_TRACK_MAP_MDI] ❌ 缺少 current_session 屬性")
                return False
            
            # ✅ 設置參數（完全複製 Ideal Lap Ranking）
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 參數已設置: {self.year} {self.race} {self.session}")
            
            # ✅ 關鍵修復：創建 data_manager（基類會在 initialize_module 中創建）
            if not hasattr(self, 'data_manager') or self.data_manager is None:
                logger.debug("[HISTORICAL_TRACK_MAP_MDI] 創建 data_manager...")
                self.data_manager = self.create_data_manager()
                if not self.data_manager:
                    logger.error("[HISTORICAL_TRACK_MAP_MDI] ❌ data_manager 創建失敗")
                    return False
                logger.info("[HISTORICAL_TRACK_MAP_MDI] ✅ data_manager 創建成功")
            else:
                logger.debug("[HISTORICAL_TRACK_MAP_MDI] data_manager 已存在，跳過創建")
            
            # 檢查必要組件是否可用
            if TrackMapWidget is None or ElevationChartWidget is None:
                error_msg = tr("required_components_unavailable", "必要組件不可用 (TrackMapWidget/ElevationChartWidget)")
                logger.error(f"[HISTORICAL_TRACK_MAP_MDI] {error_msg}")
                return False
            
            # 創建主容器
            if not hasattr(self, 'main_widget') or self.main_widget is None:
                self.main_widget = QWidget()
                main_layout = QVBoxLayout(self.main_widget)
                main_layout.setContentsMargins(0, 0, 0, 0)
                main_layout.setSpacing(0)
            else:
                main_layout = self.main_widget.layout()
                if main_layout is None:
                    main_layout = QVBoxLayout(self.main_widget)
                    main_layout.setContentsMargins(10, 10, 10, 10)
                    main_layout.setSpacing(5)
            
            # === 1. 創建頂部資訊與控制區 ===
            info_container = QWidget()
            info_layout = self._create_info_control_bar()
            info_container.setLayout(info_layout)
            info_container.setMaximumHeight(40)
            info_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            main_layout.addWidget(info_container)
            
            # === 2. 創建水平分割器 (左側圖表 + 右側表格) ===
            horizontal_splitter = QSplitter(Qt.Horizontal)
            
            # === 2.1 左側：垂直分割器 (賽道地圖 + 高程圖表) ===
            left_splitter = QSplitter(Qt.Vertical)
            
            # 賽道地圖區域（TrackMap + SpeedLegend）
            track_container = QWidget()
            track_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # ✅ 確保容器可擴展
            track_layout = QHBoxLayout(track_container)
            track_layout.setContentsMargins(0, 0, 0, 0)
            track_layout.setSpacing(0)
            
            # 賽道地圖
            self.track_map = TrackMapWidget()
            self.track_map.show_official_corners = True
            self.track_map.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # ✅ 確保 TrackMap 可擴展
            self.track_map.setMinimumSize(400, 300)  # ✅ 設置最小尺寸，確保始終可見
            track_layout.addWidget(self.track_map, stretch=1)
            
            # 速度圖例（初始隱藏）
            self.speed_legend_widget = SpeedLegendWidget()
            self.speed_legend_widget.setVisible(False)
            track_layout.addWidget(self.speed_legend_widget, stretch=0)
            
            left_splitter.addWidget(track_container)
            
            # 高程圖表
            self.elevation_chart = ElevationChartWidget()
            left_splitter.addWidget(self.elevation_chart)
            
            # 設定左側比例 (TrackMap 70%, Elevation 30%)
            left_splitter.setStretchFactor(0, 7)
            left_splitter.setStretchFactor(1, 3)
            
            horizontal_splitter.addWidget(left_splitter)
            
            # === 2.2 右側：旗幟統計表格面板 ===
            right_panel = self._create_flags_statistics_panel()
            horizontal_splitter.addWidget(right_panel)
            
            # 設定水平比例 (左側圖表 60%, 右側表格 40%) - 調整以容納 Total 表格
            horizontal_splitter.setStretchFactor(0, 60)
            horizontal_splitter.setStretchFactor(1, 40)
            
            main_layout.addWidget(horizontal_splitter)
            
            # 連接數據載入信號
            if self.data_manager:
                self.data_manager.data_loaded.connect(self._on_data_loaded)
                self.data_manager.load_error.connect(self._on_data_load_error)
                self.data_manager.status_changed.connect(self._on_status_changed)
            
            # ✅ 統一載入方式：使用 data_manager.load_data()
            # ❌ 移除 load_initial_data() - 避免與 _load_data_with_current_parameters() 雙重載入
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] 跳過 load_initial_data()，等待 _load_data_with_current_parameters() 調用")
            
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] initialize_module 完成")
            return True
            
        except Exception as e:
            logger.error(f"[HISTORICAL_TRACK_MAP_MDI] initialize_module 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ❌ 已禁用：統一使用通用載入模式，移除自定義載入方法
    # def load_initial_data(self):
    #     """
    #     [已移除] 載入初始資料 - 改用統一的 _load_data_with_current_parameters()
    #     
    #     ⚠️ 此方法導致雙重載入問題：
    #     - initialize_module() → load_initial_data() → API 請求 (第一次)
    #     - update_parameters() → _load_data_with_current_parameters() → API 請求 (第二次)
    #     
    #     ✅ 解決方案：完全移除此方法，統一使用基類的載入流程
    #     """
    #     pass
    
    # ========== 已移除的自定義載入方法 ==========
    # 以下方法已被統一載入模式取代：
    # - load_initial_data() → 改用 _load_data_with_current_parameters()
    # - _on_api_progress() → 改用 data_manager 的信號
    # - _on_api_success() → 改用 data_manager 的信號
    # - _on_api_failure() → 改用 data_manager 的信號
    # - _transform_api_data_to_gui_format() → 改用 data_manager 的處理
        
        # ✅ 直接使用已驗證的參數（完全複製 Ideal Lap Ranking）
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 📋 參數: {self.year} {self.race} {self.session}")
        
        # 驗證參數
        if not self.race:
            error_msg = "缺少 race 參數！無法載入數據。"
            logger.error(f"[HISTORICAL_TRACK_MAP_MDI] ❌ {error_msg}")
            if self.info_label:  # ❌ 已隱藏 - 檢查是否為 None
                self.info_label.setText(tr("missing_race_parameter", "Missing Race Parameter"))
            self._show_error(
                tr("parameter_error", "Parameter Error"),
                tr("missing_race_parameter_message", "Race parameter is required but not set.")
            )
            return
        
        # 更新狀態
        if self.info_label:  # ❌ 已隱藏 - 檢查是否為 None
            self.info_label.setText(tr("loading_from_api", "Loading from API..."))
        
        # 創建 API Worker
        api_params = {
            "year": self.year,  # ✅ 已在 initialize_module 驗證
            "race": self.race,
            "session": self.session,
            "force_refresh": False
        }
        
        logger.debug("[HISTORICAL_TRACK_MAP_MDI] 創建 API Worker...")
        self.api_worker = HistoricalTrackMapApiWorker(
            params=api_params,  # ✅ 第一個參數（匹配 Ideal Lap Ranking）
            base_url="https://api.f1telemetrystationpro.org",
            timeout=60.0
        )
        
        # 連接信號
        self.api_worker.progress.connect(self._on_api_progress)
        self.api_worker.success.connect(self._on_api_success)
        self.api_worker.failure.connect(self._on_api_failure)
        
        # 啟動 API 請求
        logger.debug("[HISTORICAL_TRACK_MAP_MDI] 啟動 API 請求...")
        self.api_worker.start()
    
    @pyqtSlot(int)
    def _on_api_progress(self, progress: int):
        """API 請求進度更新"""
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] API 進度: {progress}%")
        if self.info_label:  # ❌ 已隱藏 - 檢查是否為 None
            self.info_label.setText(f"{tr('api_loading', 'API Loading')}... {progress}%")
    
    @pyqtSlot(dict)
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        try:
            logger.debug("\n" + "="*80)
            logger.debug("🟢 _on_api_success() 被調用")
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] API 調用成功")
            logger.debug("="*80 + "\n")
            
            # 提取數據和元數據
            api_data = result.get("data", {})
            meta = result.get("meta", {})
            
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 數據源: {meta.get('source')}")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 延遲: {meta.get('latency_ms')}ms")
            
            # ⚠️ API 返回雙重嵌套結構！需要再提取一層 data
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 第一層 api_data 鍵: {list(api_data.keys()) if isinstance(api_data, dict) else 'NOT A DICT'}")
            
            # 檢查是否有雙重嵌套（JSON 包裝格式）
            if isinstance(api_data, dict) and "data" in api_data and "function_id" in api_data:
                logger.warning(f"[HISTORICAL_TRACK_MAP_MDI] ⚠️  檢測到雙重嵌套！提取內層 data...")
                api_data = api_data.get("data", {})
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 第二層 api_data 鍵: {list(api_data.keys()) if isinstance(api_data, dict) else 'NOT A DICT'}")
            
            # 驗證數據結構
            if not isinstance(api_data, dict):
                raise ValueError(tr("api_data_format_error", "API returned data format error"))
            
            # ✅ 轉換 API 數據格式為 GUI 期望的格式
            gui_data = self._transform_api_data_to_gui_format(api_data)
            
            # ✅ 檢查轉換結果
            if gui_data is None:
                raise ValueError(tr("data_transformation_failed", "Data transformation failed - returned None"))
            
            if not isinstance(gui_data, dict):
                raise ValueError(tr("gui_data_format_error", "Transformed data format error - must be dict"))
            
            logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 數據轉換成功，GUI 數據鍵: {list(gui_data.keys())}")
            
            # 處理數據（觸發現有的 _on_data_loaded 處理邏輯）
            self._on_data_loaded(gui_data)
            
            # 更新狀態
            if self.info_label:  # ❌ 已隱藏 - 檢查是否為 None
                source_label = "API" if meta.get('source') == 'api' else meta.get('source', 'Unknown')
                self.info_label.setText(f"{tr('loaded_from', 'Loaded from')} {source_label}")
            
        except Exception as e:
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] API 數據處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self._on_api_failure(str(e))
    
    def _transform_api_data_to_gui_format(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換 API 數據格式為 GUI 期望的格式
        
        API 格式：
        {
            "metadata": {...},
            "yearly_summary": {              # ✅ 字典: {year: stats}
                "2022": {...},
                "2023": {...}
            },
            "corner_analysis": {...},
            "detailed_position_records": [   # ✅ 包含 X, Y, elevation/z, speed
                {
                    "position_x": ...,
                    "position_y": ...,
                    "elevation": ...,        # FastF1 Z 軸原始值（GUI 會除以 10）
                    "z": ...,                # 同上
                    "distance_m": ...,
                    "speed": ...
                }
            ],
            "track_bounds": {...},
            "elevation_profile": {           # ✅ 高程統計
                "available": true,
                "min_elevation": ...,
                "max_elevation": ...,
                "elevation_change": ...
            }
        }
        
        GUI 格式：
        {
            "track_data": {
                "detailed_position_records": [...],
                "track_bounds": {...},
                "official_corners": {...}
            },
            "chart_data": {
                "track_outline": [...],      # 含 elevation/z 的完整數據
                "corners": [1, 2, 3, ...]    # 彎道編號列表
            },
            "yearly_summary": {...},
            "corner_analysis": {...},
            "elevation_profile": {...},      # ✅ 高程統計
            "metadata": {...}
        }
        """
        try:
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] 轉換 API 數據格式...")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] API 數據類型: {type(api_data)}")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] API 數據鍵: {list(api_data.keys()) if isinstance(api_data, dict) else 'NOT A DICT'}")
            
            # ✅ 驗證數據結構
            if not isinstance(api_data, dict):
                raise ValueError(f"API 數據必須是字典，實際類型: {type(api_data)}")
            
            # 提取原始數據
            position_records = api_data.get("detailed_position_records", [])
            track_bounds = api_data.get("track_bounds", {})
            metadata = api_data.get("metadata", {})
            
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 提取到 {len(position_records)} 個位置點")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] track_bounds: {track_bounds}")
            
            # 構建 track_data（賽道地圖用）
            # ✅ 使用 TrackMapWidget 期望的鍵名
            
            # ✅ 修復：official_corners 在 api_data 頂層（與 detailed_position_records 同級）
            official_corners_data = api_data.get("official_corners", {
                "available": False,
                "count": 0,
                "corners": []
            })
            
            logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 從 API 數據載入 {official_corners_data.get('count', 0)} 個官方彎道")
            if official_corners_data.get("corners"):
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 第 1 個彎道: {official_corners_data['corners'][0]}")
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 最後彎道: {official_corners_data['corners'][-1]}")
            
            # 🏁 提取 sector_boundaries（Function 100 包含此數據）
            sector_boundaries_data = api_data.get("sector_boundaries", [])
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 🏁 從 API 數據載入 {len(sector_boundaries_data)} 個 Sector 邊界")
            if sector_boundaries_data:
                for sb in sector_boundaries_data:
                    logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] - {sb.get('name')}: {sb.get('distance_m'):.1f}m")
            
            track_data = {
                "detailed_position_records": position_records,  # ✅ 正確鍵名
                "track_bounds": track_bounds,                   # ✅ 正確鍵名
                "official_corners": official_corners_data,      # ✅ 使用 FastF1 官方數據
                "sector_boundaries": sector_boundaries_data     # 🏁 新增：Sector 邊界數據
            }
            
            # ⚠️ Function 100 的 position_records 包含高程數據（elevation/z 欄位）
            # 現在可以構建 chart_data 用於高程圖表
            # ⚠️ Function 100 的 position_records 包含高程數據（elevation/z 欄位）
            # 現在可以構建 chart_data 用於高程圖表
            
            chart_data = {
                "track_outline": position_records,  # 完整數據（含 X, Y, elevation, speed）
                "official_corners": official_corners_data  # ✅ 使用 FastF1 官方數據
            }
            
            logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 已構建 chart_data（含高程數據 + {official_corners_data.get('count', 0)} 個彎道）")
            
            # 組合 GUI 格式數據
            gui_data = {
                "track_data": track_data,
                "chart_data": chart_data,
                "yearly_summary": api_data.get("yearly_summary", {}),  # ✅ 字典格式，不是列表
                "corner_analysis": api_data.get("corner_analysis", {}),
                "trends": api_data.get("trends", {}),
                "elevation_profile": api_data.get("elevation_profile"),  # ✅ 高程統計
                "race_top3_drivers_2022_2023": api_data.get("race_top3_drivers_2022_2023", {}),  # ✅ 新增：車手名次統計
                "metadata": metadata
            }
            
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 轉換完成: {len(position_records)} 個位置點")
            if gui_data.get("elevation_profile") and isinstance(gui_data.get("elevation_profile"), dict) and gui_data["elevation_profile"].get("available"):
                elev = gui_data["elevation_profile"]
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 高程範圍: {elev['min_elevation']:.1f}m ~ {elev['max_elevation']:.1f}m")
            
            logger.info("[HISTORICAL_TRACK_MAP_MDI] ✅ GUI 數據轉換成功")
            return gui_data
        
        except Exception as e:
            logger.error(f"[HISTORICAL_TRACK_MAP_MDI] ❌ 數據轉換失敗: {e}")
            import traceback
            traceback.print_exc()
            # ✅ 發生異常時返回 None，讓調用者處理
            return None
    
    @pyqtSlot(str)
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗"""
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] API 調用失敗: {error_msg}")
        
        if self.info_label:  # ❌ 已隱藏 - 檢查是否為 None
            self.info_label.setText(tr("api_failure", "API Request Failed"))
        
        # 顯示錯誤訊息
        self._show_error(
            tr("loading_failed", "Loading Failed"),
            tr(
                "historical_track_map_api_failure_message",
                "Historical Track Map data can only be loaded via API. Please ensure the API service is available or try again later.\n\nError details:\n{error}",
            ).format(error=error_msg)
        )
        logger.debug("[HISTORICAL_TRACK_MAP_MDI] API-ONLY 模式：不使用本地 JSON 後備")
    
    def _show_error(self, title: str, message: str):
        """
        顯示錯誤對話框
        
        Args:
            title: 對話框標題
            message: 錯誤訊息
        """
        # MDI 不是 QWidget，需要找到可用的 parent
        parent = None
        if hasattr(self, 'track_map') and self.track_map:
            parent = self.track_map
        elif hasattr(self, 'main_widget') and self.main_widget:
            parent = self.main_widget
        
        QMessageBox.critical(parent, title, message)
    
    def _create_info_control_bar(self) -> QHBoxLayout:
        """創建頂部資訊與控制列 - 包含 Speed Gradient 和 Speed Distribution checkboxes"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)  # 減少間距（8 → 4）
        
        from PyQt5.QtWidgets import QCheckBox
        
        # Speed Gradient 勾選框
        self.speed_gradient_checkbox = QCheckBox(tr("speed_gradient", "Speed Gradient"))
        self.speed_gradient_checkbox.setChecked(False)  # 預設不勾選
        self.speed_gradient_checkbox.setFixedHeight(28)
        self.speed_gradient_checkbox.setMaximumWidth(180)
        self.speed_gradient_checkbox.setStyleSheet(
            "font-size: 11px; padding: 4px 8px; "
            "background: #f0f0f0; border-radius: 4px; border: 1px solid #ccc;"
        )
        self.speed_gradient_checkbox.stateChanged.connect(self._toggle_speed_gradient)
        
        # Speed Distribution 勾選框
        self.speed_distribution_checkbox = QCheckBox(tr("speed_distribution", "Speed Distribution"))
        self.speed_distribution_checkbox.setChecked(True)  # 預設勾選
        self.speed_distribution_checkbox.setFixedHeight(28)
        self.speed_distribution_checkbox.setMaximumWidth(200)
        self.speed_distribution_checkbox.setStyleSheet(
            "font-size: 11px; padding: 4px 8px; "
            "background: #f0f0f0; border-radius: 4px; border: 1px solid #ccc;"
        )
        self.speed_distribution_checkbox.stateChanged.connect(self._toggle_speed_distribution)
        
        layout.addWidget(self.speed_gradient_checkbox, stretch=0)
        layout.addWidget(self.speed_distribution_checkbox, stretch=0)
        
        return layout
    
    def _create_flags_statistics_panel(self) -> QWidget:
        """創建右側旗幟統計面板"""
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        from PyQt5.QtGui import QFont, QColor
        
        panel = QWidget()
        # ✅ 調整寬度範圍，讓面板能更靈活適應
        panel.setMaximumWidth(800)  # 增加最大寬度
        panel.setMinimumWidth(350)  # 降低最小寬度
        # ✅ 移除高度限制，讓面板自動擴展填滿空間
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        # ✅ 移除 SetFixedSize，允許動態調整
        # layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        
        # === 標題 ===
        title_label = QLabel(tr("yearly_flags_statistics_2022_2025", "Yearly Flags Statistics (2022-2025)"))
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(
            "background: #F5F5F5; color: #333; padding: 8px; "
            "border: 1px solid #E0E0E0; border-radius: 3px;"
        )
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # === 年度統計表格 ===
        yearly_group = QGroupBox(tr("yearly_statistics", "Yearly Statistics"))
        yearly_group.setMaximumHeight(220)  # ✅ 再增加 15px：205 → 220
        yearly_layout = QVBoxLayout(yearly_group)
        yearly_layout.setContentsMargins(5, 5, 5, 5)
        yearly_layout.setSpacing(2)
        
        self.yearly_table = QTableWidget()
        self.yearly_table.setRowCount(4)
        self.yearly_table.setColumnCount(6)  # ✅ 增加到 6 列（添加 Max Speed）
        # ✅ 移除固定寬度，允許表格自適應容器寬度
        # self.yearly_table.setFixedWidth(660)
        # ✅ 移除高度限制，讓表格根據內容自動調整
        self.yearly_table.setVerticalHeaderLabels(['2022', '2023', '2024', '2025'])
        self.yearly_table.setHorizontalHeaderLabels([
            tr("yellow", "Yellow"), 
            tr("d_yellow", "D-Yellow"), 
            tr("red", "Red"), 
            tr("safety", "Safety"),
            tr("position_delta", "Position Δ"),
            tr("max_speed", "Max Speed")  # ✅ 新增 Max Speed 欄位
        ])
        
        # ✅ 使用 Stretch 模式讓列自動調整寬度
        self.yearly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.yearly_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.yearly_table.setAlternatingRowColors(True)
        
        # ✅ 設定表格字體（8pt，不粗體）
        table_font = QFont()
        table_font.setPointSize(8)
        self.yearly_table.setFont(table_font)
        
        # 設定標題欄位顏色
        header_colors = [
            QColor('#FFF9C4'),  # Yellow
            QColor('#FFE082'),  # D-Yellow
            QColor('#FFCDD2'),  # Red
            QColor('#E1BEE7'),  # Safety
            QColor('#C5E1A5'),  # Position Δ
            QColor('#B3E5FC')   # ✅ Max Speed (淺藍色)
        ]
        for col, color in enumerate(header_colors):
            header_item = self.yearly_table.horizontalHeaderItem(col)
            if header_item:
                header_item.setBackground(color)
        
        self.yearly_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                padding: 4px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        yearly_layout.addWidget(self.yearly_table)
        layout.addWidget(yearly_group, stretch=0)  # ✅ 固定大小，不擴展
        
        # === 彎道統計表格 ===
        corner_group = QGroupBox(tr("corner_flags_statistics_2022_2025", "Corner Flags Statistics (2022-2025)"))
        # ✅ 允許彎道表格擴展填滿剩餘空間（不設最大高度）
        corner_layout = QVBoxLayout(corner_group)
        corner_layout.setContentsMargins(5, 5, 5, 5)
        corner_layout.setSpacing(2)
        
        self.corner_table = QTableWidget()
        self.corner_table.setColumnCount(5)
        self.corner_table.setRowCount(0)
        # ✅ 移除最大寬度限制，讓表格自適應
        # self.corner_table.setMaximumWidth(540)
        # ✅ 移除高度限制
        self.corner_table.setHorizontalHeaderLabels([
            tr("turn", "Turn"), 
            tr("yellow", "Yellow"), 
            tr("d_yellow", "D-Yellow"), 
            tr("red", "Red"), 
            tr("safety", "Safety")
        ])
        
        # ✅ 使用 Stretch 模式讓列自動調整寬度
        self.corner_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.corner_table.verticalHeader().setVisible(False)
        self.corner_table.setAlternatingRowColors(True)
        
        # ✅ 設定表格字體（8pt，不粗體）
        corner_font = QFont()
        corner_font.setPointSize(8)
        self.corner_table.setFont(corner_font)
        
        self.corner_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 4px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        corner_layout.addWidget(self.corner_table)
        layout.addWidget(corner_group, stretch=1)  # ✅ 允許擴展，佔據剩餘空間
        
        # === 總計統計表格 ===
        total_group = QGroupBox(tr("total_2022_2025", "Total (2022-2025)"))
        total_group.setMaximumHeight(100)  # ✅ 固定最大高度
        total_layout = QVBoxLayout(total_group)
        total_layout.setContentsMargins(1, 1, 1, 1)
        total_layout.setSpacing(1)
        
        self.total_table = QTableWidget()
        self.total_table.setRowCount(2)
        self.total_table.setColumnCount(5)
        # ✅ 移除固定寬度，允許表格自適應容器寬度
        # self.total_table.setFixedWidth(660)
        # ✅ 移除固定高度
        self.total_table.setVerticalHeaderLabels([tr("type", "Type"), tr("total", "Total")])
        self.total_table.setHorizontalHeaderLabels([
            tr("yellow", "Yellow"), 
            tr("d_yellow", "D-Yellow"), 
            tr("red", "Red"), 
            tr("safety", "Safety"),
            tr("position_delta", "Position Δ")
        ])
        
        # 初始化類型行
        flag_types = [
            tr("yellow", "Yellow"), 
            tr("d_yellow", "D-Yellow"), 
            tr("red", "Red"), 
            tr("safety", "Safety"),
            tr("position_delta", "Position Δ")
        ]
        flag_colors = header_colors  # 使用與年度表格相同的顏色
        
        for col, (flag_type, flag_color) in enumerate(zip(flag_types, flag_colors)):
            type_item = QTableWidgetItem(flag_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setBackground(flag_color)
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            type_item.setFont(font)
            self.total_table.setItem(0, col, type_item)
            
            # 初始化數量行
            count_item = QTableWidgetItem("0")
            count_item.setTextAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(8)
            count_item.setFont(font)
            self.total_table.setItem(1, col, count_item)
        
        # ✅ 修復：使用 Stretch 模式，與 Yearly Statistics 一致 (2025-11-13)
        # 移除固定列寬設定，改用自動調整
        # for col in range(5):
        #     self.total_table.setColumnWidth(col, 120)
        
        # ✅ 改為 Stretch 模式，讓表格自動調整欄位寬度
        self.total_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.total_table.horizontalHeader().setVisible(False)
        self.total_table.verticalHeader().setVisible(True)
        self.total_table.setAlternatingRowColors(False)
        self.total_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                font-size: 8px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 4px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
                font-size: 9px;
            }
        """)
        
        total_layout.addWidget(self.total_table)
        layout.addWidget(total_group, stretch=0)  # ✅ 固定大小，不擴展
        
        # === 車手名次表格 (2022-2025 Top 3 Drivers) ===
        top3_group = QGroupBox(tr("race_top3_drivers_2022_2025", "Race Top 3 Drivers (2022-2025)"))
        top3_group.setMaximumHeight(250)  # ✅ 增加高度：200px → 250px
        top3_layout = QVBoxLayout(top3_group)
        top3_layout.setContentsMargins(5, 5, 5, 5)
        top3_layout.setSpacing(2)
        
        self.top3_drivers_table = QTableWidget()
        self.top3_drivers_table.setRowCount(4)  # ✅ 改為 4 行：2022, 2023, 2024, 2025
        self.top3_drivers_table.setColumnCount(3)  # P1, P2, P3
        self.top3_drivers_table.setVerticalHeaderLabels(['2022', '2023', '2024', '2025'])  # ✅ 添加 2024, 2025
        self.top3_drivers_table.setHorizontalHeaderLabels([
            tr("p1", "P1"),
            tr("p2", "P2"),
            tr("p3", "P3")
        ])
        
        # ✅ 使用 Stretch 模式讓列自動調整寬度
        self.top3_drivers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.top3_drivers_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.top3_drivers_table.setAlternatingRowColors(True)
        
        # ✅ 設定表格字體（8pt）
        top3_font = QFont()
        top3_font.setPointSize(8)
        self.top3_drivers_table.setFont(top3_font)
        
        # 設定標題欄位顏色（金銀銅）
        header_colors_top3 = [
            QColor('#FFD700'),  # Gold - P1
            QColor('#C0C0C0'),  # Silver - P2
            QColor('#CD7F32')   # Bronze - P3
        ]
        for col, color in enumerate(header_colors_top3):
            header_item = self.top3_drivers_table.horizontalHeaderItem(col)
            if header_item:
                header_item.setBackground(color)
        
        self.top3_drivers_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                padding: 4px;
                border: 1px solid #E0E0E0;
            }
        """)
        
        top3_layout.addWidget(self.top3_drivers_table)
        layout.addWidget(top3_group, stretch=0)  # ✅ 固定大小，不擴展
        
        # === 數據來源說明 ===
        # ❌ 已隱藏：用戶要求移除此標籤 (2025-11-13)
        # source_label = QLabel(tr("data_source_function_100", "Data Source: Function 100"))
        # source_label.setStyleSheet(
        #     "font-size: 9px; color: #999; padding: 3px; "
        #     "background: #FAFAFA; border: 1px solid #E0E0E0; border-radius: 2px;"
        # )
        # source_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(source_label)
        
        return panel
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        數據載入成功處理
        
        ⚠️ 簡化版本（賽道切換時重建 MDI，無需複雜狀態管理）
        - 移除賽道變更檢測（已在 update_lap_parameters 中處理）
        - 移除舊數據保留邏輯（全新初始化，無舊數據）
        - 直接使用 API 返回的數據
        """
        import traceback
        logger.debug("\n" + "="*70)
        logger.debug("[HISTORICAL_TRACK_MAP_MDI] 🚨 _on_data_loaded 觸發")
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 當前賽道: {self.year} {self.race} {self.session}")
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 🔍 調用堆棧:")
        for line in traceback.format_stack()[-5:-1]:
            logger.debug(f"{line.strip()}")
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 🔑 數據鍵: {list(data.keys())}")
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 🏆 race_top3 存在: {'race_top3_drivers_2022_2023' in data}")
        logger.debug("="*70)
        
        try:
            # 儲存旗幟數據
            self._current_flags_data = data
            self._is_data_loaded = True
            
            logger.debug(f"data 頂層鍵: {list(data.keys())}")
            
            # 🔍 提取賽道數據（優先使用 data.track_data，否則從 data 構建）
            track_data = data.get("track_data", {})
            
            # 如果 track_data 為空或缺少關鍵數據，從 data 重新構建
            if not track_data or "position_records" not in track_data:
                logger.warning(f"⚠️  track_data 為空或缺少 position_records，從 data 構建...")
                
                # ✅ 修正：使用正確的鍵名（position_records 而非 detailed_position_records）
                position_records = track_data.get("position_records") if track_data else None
                if not position_records:
                    # 從 data 層提取（使用 detailed_position_records）
                    detailed_records = data.get("detailed_position_records", [])
                    if detailed_records:
                        # 轉換為 position_records 格式
                        position_records = [{
                            "position_x": r.get("position_x", 0.0),
                            "position_y": r.get("position_y", 0.0),
                            "distance_m": r.get("distance_m", 0.0),
                            "elevation": r.get("z", 0.0),
                            "z": r.get("z", 0.0),
                            "speed": r.get("speed", 0.0)
                        } for r in detailed_records]
                
                track_data = {
                    "position_records": position_records or [],  # ✅ 修正鍵名
                    "track_bounds": data.get("track_bounds", {}),
                    "official_corners": data.get("official_corners", {}),
                    "sector_boundaries": data.get("sector_boundaries", []),
                    "speed_distribution": data.get("speed_distribution"),  # ✅ 速度分布
                }
                logger.info(f"✅ 重建 track_data，position_records 數量: {len(track_data['position_records'])}")
            
            # 🏁 確保 sector_boundaries 存在（直接從 data 或 track_data）
            if "sector_boundaries" not in track_data or not track_data.get("sector_boundaries"):
                if "sector_boundaries" in data and data.get("sector_boundaries"):
                    track_data["sector_boundaries"] = data.get("sector_boundaries", [])
                    logger.info(f"✅ 從 data 補充 sector_boundaries: {len(track_data['sector_boundaries'])} 個")
                else:
                    track_data["sector_boundaries"] = []
                    logger.warning(f"⚠️  無 sector_boundaries 數據")
            
            # 🎯 確保 speed_distribution 存在（無論 track_data 來源）
            if "speed_distribution" not in track_data or not track_data.get("speed_distribution"):
                if "speed_distribution" in data and data.get("speed_distribution"):
                    track_data["speed_distribution"] = data.get("speed_distribution")
                    sd = track_data["speed_distribution"]
                    logger.info(f"✅ 從 data 補充 speed_distribution: Low={sd.get('low_speed_percentage', 0):.1f}%, Mid={sd.get('mid_speed_percentage', 0):.1f}%, High={sd.get('high_speed_percentage', 0):.1f}%")
                else:
                    logger.warning(f"⚠️  無 speed_distribution 數據")
            
            logger.debug(f"\n[DEBUG] === 賽道地圖數據最終檢查 ===")
            logger.debug(f"track_data 存在: {bool(track_data)}")
            logger.debug(f"track_data 鍵: {list(track_data.keys())}")
            
            if "sector_boundaries" in track_data:
                sb_count = len(track_data['sector_boundaries'])
                logger.info(f"✅ sector_boundaries 數量: {sb_count}")
                if sb_count > 0:
                    for sb in track_data['sector_boundaries']:
                        logger.debug(f"- {sb.get('name')}: {sb.get('distance_m'):.1f}m at ({sb.get('position_x'):.1f}, {sb.get('position_y'):.1f})")
            
            # 更新賽道地圖
            if track_data and self.track_map:
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 準備更新賽道地圖...")
                
                success = self.track_map.load_track_data(track_data)
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 賽道地圖更新結果: {success}")
                
                # ✅ 強制啟用彎道顯示
                self.track_map.show_official_corners = True
                logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 已設置 show_official_corners=True")
                
                # ✅ 強制重繪
                self.track_map.update()
                logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 已調用 track_map.update() 強制重繪")
                
                # 🎨 傳遞彎道旗幟數據
                corner_analysis = data.get("corner_analysis", {})
                if corner_analysis and hasattr(self.track_map, 'set_corner_flags'):
                    self.track_map.set_corner_flags(corner_analysis)
                    logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 已傳遞 {len(corner_analysis)} 個彎道的旗幟數據")
                
                # 🏁 傳遞 Sector 邊界數據（從 track_data 取得）
                sector_boundaries = track_data.get("sector_boundaries", [])
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 🔍 準備設置 Sector 邊界: {len(sector_boundaries)} 個")
                
                if sector_boundaries and hasattr(self.track_map, 'set_sector_boundaries'):
                    self.track_map.set_sector_boundaries(sector_boundaries)
                    logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 已傳遞 {len(sector_boundaries)} 個 Sector 邊界給 TrackMapWidget")
                    
                    # ✅ 強制啟用 Sector 邊界顯示
                    if hasattr(self.track_map, 'show_sector_boundaries'):
                        self.track_map.show_sector_boundaries = True
                        logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 已設置 show_sector_boundaries=True")
                else:
                    logger.warning(f"[HISTORICAL_TRACK_MAP_MDI] ⚠️  sector_boundaries 為空或 TrackMapWidget 不支援")
            else:
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 跳過賽道地圖更新（無數據或 widget 不存在）")
            
            # 更新高程圖表
            chart_data = data.get("chart_data")
            logger.debug(f"\n[DEBUG] === 高程圖表數據檢查 ===")
            logger.debug(f"chart_data 存在: {bool(chart_data)}")
            
            if chart_data and self.elevation_chart:
                logger.debug(f"chart_data 鍵: {list(chart_data.keys())}")
                
                track_outline = chart_data.get("track_outline", [])
                # 🔧 修復：正確提取 corners 數據（參考 demo Line 721）
                official_corners = chart_data.get("official_corners", {})
                corners = official_corners.get("corners", [])
                
                logger.debug(f"track_outline 數量: {len(track_outline)}")
                logger.debug(f"official_corners 類型: {type(official_corners)}")
                logger.debug(f"corners 類型: {type(corners)}, 長度: {len(corners)}")
                
                if corners:
                    logger.debug(f"第 1 個彎道: {corners[0]}")
                    logger.debug(f"最後 1 個彎道: {corners[-1]}")
                else:
                    logger.warning(f"⚠️  corners 為空！")
                
                # 檢查是否有高程數據
                has_elevation = any('elevation' in p or 'z' in p for p in track_outline)
                
                if has_elevation and track_outline:
                    logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 準備繪製高程圖表（{len(track_outline)} 點，{len(corners)} 彎道）...")
                    self.elevation_chart.plot_elevation(track_outline, corners)
                    logger.info("[HISTORICAL_TRACK_MAP_MDI] ✅ 高程圖表已更新")
                else:
                    logger.warning("[HISTORICAL_TRACK_MAP_MDI] ⚠️  track_outline 無高程數據")
                    self.elevation_chart.plot_elevation([], [])
            else:
                logger.warning("[HISTORICAL_TRACK_MAP_MDI] ⚠️  無 chart_data，等高圖保持空白")
                if self.elevation_chart:
                    self.elevation_chart.plot_elevation([], [])  # 清空圖表
            
            # 更新旗幟統計表格
            self._update_flags_tables(data)
            
            # 更新資訊標籤
            self._update_info_label(data)
            
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] 所有組件已更新")
            
        except Exception as e:
            logger.error(f"[HISTORICAL_TRACK_MAP_MDI] _on_data_loaded 處理失敗: {e}")
            import traceback
            traceback.print_exc()
    
    @pyqtSlot(str)
    def _on_data_load_error(self, error_msg: str):
        """數據載入失敗處理"""
        logger.error(f"[HISTORICAL_TRACK_MAP_MDI] _on_data_load_error: {error_msg}")
        
        if self.info_label:
            self.info_label.setText(f"{tr('error', 'Error')}: {error_msg}")
        
        # ✅ 修正：使用 main_widget 作為 parent（self 不是 QWidget）
        parent = self.main_widget if hasattr(self, 'main_widget') else None
        QMessageBox.critical(
            parent, 
            tr("data_load_failed", "Data Load Failed"), 
            error_msg
        )
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """狀態變更處理"""
        if self.info_label:
            self.info_label.setText(status)
    
    def _update_info_label(self, data: Dict[str, Any]):
        """更新資訊標籤"""
        if not self.info_label:
            return
        
        metadata = data.get("metadata", {})
        circuit_name = metadata.get("circuit_name", "Circuit")
        years_analyzed = metadata.get("years_analyzed", [])
        
        summary = self.data_manager.get_flags_summary() if self.data_manager else {}
        
        info_html = f"""
        <b>{circuit_name}</b> | 
        {tr("years", "Years")}: {len(years_analyzed)} ({min(years_analyzed) if years_analyzed else 'N/A'}-{max(years_analyzed) if years_analyzed else 'N/A'}) | 
        <b>{tr("total_incidents", "Total Incidents")}: {summary.get('total_incidents', 0)}</b> | 
        <span style='color: #2196F3; font-weight: bold;'>{tr("data_source_api_function_100", "Data Source: API (Function 100)")}</span>
        """
        
        self.info_label.setText(info_html)
    
    def _update_flags_tables(self, data: Dict[str, Any]):
        """更新旗幟統計表格"""
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtGui import QFont, QColor, QLinearGradient, QBrush
        
        logger.debug(f"\n[DEBUG] 🚩 _update_flags_tables 被調用")
        logger.debug(f"data 鍵: {list(data.keys())[:10]}")  # 只顯示前 10 個
        
        yearly_summary = data.get("yearly_summary", {})
        corner_analysis = data.get("corner_analysis", {})
        
        # 載入每年度的名次變更數據（從 Function 15 的 JSON）
        position_changes_data = self._load_position_changes_data()
        logger.info(f"✅ Position Changes Data: {position_changes_data}")
        
        # 更新年度表格
        years = ['2022', '2023', '2024', '2025']
        flag_keys = ['yellow_flags', 'double_yellow_flags', 'red_flags', 'safety_cars']
        
        # 定義與 Total 表格一致的顏色配置
        flag_colors = [
            QColor('#FFF9C4'),  # Yellow
            QColor('#FFE082'),  # D-Yellow (Double Yellow)
            QColor('#FFCDD2'),  # Red
            QColor('#E1BEE7'),  # Safety
            QColor('#C5E1A5'),  # Position Δ
            QColor('#B3E5FC')   # ✅ Max Speed (淺藍色)
        ]
        
        for row, year in enumerate(years):
            year_data = yearly_summary.get(year, {})
            
            # 填充旗幟數據（列 0-3）
            for col, key in enumerate(flag_keys):
                count = year_data.get(key, 0)
                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignCenter)
                
                # ✅ 有數值時：粗體 + 背景色（與 Total 一致）
                if count > 0:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(flag_colors[col])  # 設定背景色
                
                self.yearly_table.setItem(row, col, item)
            
            # 填充名次變更數據（列 4）
            position_changes = position_changes_data.get(year, 0)
            pos_item = QTableWidgetItem(str(position_changes))
            pos_item.setTextAlignment(Qt.AlignCenter)
            
            # ✅ 有數值時：粗體 + 背景色（與 Total 一致）
            if position_changes > 0:
                font = QFont()
                font.setBold(True)
                pos_item.setFont(font)
                pos_item.setBackground(flag_colors[4])  # Position Δ 顏色
            
            self.yearly_table.setItem(row, 4, pos_item)
            
            # ✅ 填充最高時速數據（列 5）
            max_speed = year_data.get('max_speed', 0.0)
            speed_item = QTableWidgetItem(f"{max_speed:.1f}" if max_speed > 0 else "-")
            speed_item.setTextAlignment(Qt.AlignCenter)
            
            # ✅ 有數值時：粗體 + 背景色
            if max_speed > 0:
                font = QFont()
                font.setBold(True)
                speed_item.setFont(font)
                speed_item.setBackground(flag_colors[5])  # Max Speed 顏色
            
            self.yearly_table.setItem(row, 5, speed_item)
        
        # 更新總計表格
        total_yellow = sum(yearly_summary.get(y, {}).get('yellow_flags', 0) for y in years)
        total_double_yellow = sum(yearly_summary.get(y, {}).get('double_yellow_flags', 0) for y in years)
        total_red = sum(yearly_summary.get(y, {}).get('red_flags', 0) for y in years)
        total_safety_car = sum(yearly_summary.get(y, {}).get('safety_cars', 0) for y in years)
        total_position_changes = sum(position_changes_data.get(y, 0) for y in years)
        
        totals = [total_yellow, total_double_yellow, total_red, total_safety_car, total_position_changes]
        
        for col, count in enumerate(totals):
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(8)
            item.setFont(font)
            self.total_table.setItem(1, col, item)
        
        # 更新彎道統計表格
        self._update_corner_table(corner_analysis)
        
        # ✅ 更新車手名次表格 (2022-2023 Top 3 Drivers)
        self._update_top3_drivers_table(data)
        
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 旗幟統計表格已更新")
    
    def _update_corner_table(self, corner_analysis: Dict[str, Any]):
        """更新彎道旗幟統計表格"""
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtGui import QFont, QColor, QLinearGradient, QBrush
        
        if not corner_analysis:
            logger.warning(f"[HISTORICAL_TRACK_MAP_MDI] ⚠️ corner_analysis 為空，無法更新彎道表格")
            return
        
        # 按彎道編號排序
        sorted_corners = sorted(
            corner_analysis.items(),
            key=lambda x: int(x[0].replace('T', ''))
        )
        
        # 設定行數
        self.corner_table.setRowCount(len(sorted_corners))
        
        for row, (corner_key, corner_data) in enumerate(sorted_corners):
            corner_num = corner_data.get('corner_number', corner_key.replace('T', ''))
            yearly_breakdown = corner_data.get('yearly_breakdown', {})
            
            # 計算 2022-2025 年的總和
            total_yellow = 0
            total_double_yellow = 0
            total_red = 0
            total_safety_car = 0
            
            for year in ['2022', '2023', '2024', '2025']:
                year_data = yearly_breakdown.get(year, {})
                yellow_val = year_data.get('yellow', 0)
                double_val = year_data.get('double_yellow', 0)
                red_val = year_data.get('red_flag', 0)
                safety_val = year_data.get('safety_car', 0)
                
                total_yellow += 1 if yellow_val > 0 else 0
                total_double_yellow += 1 if double_val > 0 else 0
                total_red += 1 if red_val > 0 else 0
                total_safety_car += 1 if safety_val > 0 else 0
            
            # 填充表格
            # 列 0: Turn 編號（根據旗幟類型設定背景色）
            turn_item = QTableWidgetItem(f"T{corner_num}")
            turn_item.setTextAlignment(Qt.AlignCenter)
            turn_font = QFont()
            turn_font.setBold(True)
            turn_item.setFont(turn_font)
            
            # 根據旗幟類型設定 Turn 欄位顏色
            has_yellow = (total_yellow > 0) or (total_double_yellow > 0)
            has_safety = total_safety_car > 0
            
            if has_yellow and has_safety:
                # 同時有黃旗和安全車：使用漸層
                gradient = QLinearGradient(0, 0, 1, 0)
                gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
                gradient.setColorAt(0.0, QColor('#FFF9C4'))
                gradient.setColorAt(1.0, QColor('#E1BEE7'))
                turn_item.setBackground(QBrush(gradient))
            elif has_yellow:
                turn_item.setBackground(QColor('#FFF9C4'))
            elif has_safety:
                turn_item.setBackground(QColor('#E1BEE7'))
            
            self.corner_table.setItem(row, 0, turn_item)
            
            # 列 1-4: 旗幟數量
            counts = [total_yellow, total_double_yellow, total_red, total_safety_car]
            
            for col, count in enumerate(counts, start=1):
                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignCenter)
                
                if count > 0:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                
                self.corner_table.setItem(row, col, item)
        
        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 彎道統計表格已更新 ({len(sorted_corners)} 個彎道)")
    
    def _update_top3_drivers_table(self, data: Dict[str, Any]):
        """更新 2022-2025 車手名次表格"""
        from PyQt5.QtWidgets import QTableWidgetItem
        from PyQt5.QtGui import QFont, QColor
        from modules.gui.themes.color_palette_provider import color_palette_provider
        
        logger.debug(f"\n[DEBUG] 🏆 _update_top3_drivers_table 被調用")
        logger.debug(f"data 頂層鍵: {list(data.keys())}")
        
        # 獲取 race_top3_drivers_2022_2023 數據
        top3_data = data.get("race_top3_drivers_2022_2023", {})
        logger.debug(f"race_top3_drivers_2022_2023 存在: {bool(top3_data)}")
        
        if not top3_data or not top3_data.get("available"):
            logger.warning(f"[HISTORICAL_TRACK_MAP_MDI] ⚠️  race_top3_drivers_2022_2023 數據不可用")
            # 清空表格（4 年）
            for row in range(4):  # ✅ 改為 4 行
                for col in range(3):
                    self.top3_drivers_table.setItem(row, col, QTableWidgetItem("-"))
            return
        
        years_data = top3_data.get("years_data", [])
        
        if not years_data:
            logger.warning(f"[HISTORICAL_TRACK_MAP_MDI] ⚠️  years_data 為空")
            return
        
        # 填充表格（支援 2022-2025）
        for year_entry in years_data:
            year = year_entry.get("year")
            top3_drivers = year_entry.get("top3", [])
            
            # ✅ 確定行號（2022=0, 2023=1, 2024=2, 2025=3）
            if year == 2022:
                row = 0
            elif year == 2023:
                row = 1
            elif year == 2024:
                row = 2
            elif year == 2025:
                row = 3
            else:
                continue  # 跳過其他年份
            
            # 填充 P1, P2, P3
            for col, driver_data in enumerate(top3_drivers[:3]):  # 只取前三名
                driver_code = driver_data.get("driver_code", "UNK")
                team = driver_data.get("team", "Unknown")
                fastest_lap_seconds = driver_data.get("fastest_lap_seconds")
                
                # 格式化顯示：車手代碼 (最速圈時間)
                if fastest_lap_seconds:
                    # 轉換為 mm:ss.sss 格式
                    minutes = int(fastest_lap_seconds // 60)
                    seconds = fastest_lap_seconds % 60
                    time_str = f"{minutes}:{seconds:06.3f}"
                    display_text = f"{driver_code}\n({time_str})"
                else:
                    display_text = f"{driver_code}\n(N/A)"
                
                item = QTableWidgetItem(display_text)
                item.setTextAlignment(Qt.AlignCenter)
                
                # ✅ 設定車隊背景色
                team_color = color_palette_provider.get_team_color(team)
                if team_color:
                    item.setBackground(team_color)
                    # 根據背景色調整文字顏色
                    if team_color.lightness() < 128:
                        item.setForeground(QColor(Qt.white))
                    else:
                        item.setForeground(QColor(Qt.black))
                
                # 設定字體
                font = QFont()
                font.setPointSize(8)
                font.setBold(True)
                item.setFont(font)
                
                self.top3_drivers_table.setItem(row, col, item)
        
        logger.info(f"[HISTORICAL_TRACK_MAP_MDI] ✅ 車手名次表格已更新")
    
    def _toggle_corners(self):
        """切換彎道顯示"""
        if self.track_map:
            self.track_map.show_official_corners = not self.track_map.show_official_corners
            self.track_map.update()
            status = tr("enabled", "Enabled") if self.track_map.show_official_corners else tr("disabled", "Disabled")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] {tr('corner_display', 'Corner Display')}: {status}")
    
    def _toggle_speed_gradient(self, state):
        """切換速度漸層模式"""
        if self.track_map:
            enabled = (state == Qt.Checked)
            self.track_map.set_speed_gradient_enabled(enabled)
            
            # 顯示/隱藏速度圖例
            if self.speed_legend_widget:
                self.speed_legend_widget.setVisible(enabled)
                
                # 如果啟用，更新速度範圍
                if enabled and hasattr(self.track_map, 'position_data') and self.track_map.position_data:
                    speeds = [record.get('speed', 0) for record in self.track_map.position_data]
                    if speeds:
                        min_speed = min(speeds)
                        max_speed = max(speeds)
                        self.speed_legend_widget.set_speed_range(min_speed, max_speed)
                        logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] Speed Range: {min_speed:.1f} - {max_speed:.1f} km/h")
            
            mode = tr("speed_gradient_mode", "Speed Gradient Mode") if enabled else tr("normal_blue_mode", "Normal Blue Mode")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] {tr('track_display', 'Track Display')}: {mode}")
    
    def _toggle_speed_distribution(self, state):
        """切換速度分布圓餅圖顯示"""
        if self.track_map:
            enabled = (state == Qt.Checked)
            self.track_map.set_speed_distribution_enabled(enabled)
            
            status = tr("shown", "Shown") if enabled else tr("hidden", "Hidden")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] {tr('speed_distribution_display', 'Speed Distribution')}: {status}")
    
    def _fit_view(self):
        """重置視圖"""
        if self.track_map:
            self.track_map.fit_to_view()
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] {tr('view_reset', 'View Reset')}")
    
    def _refresh_charts(self):
        """重新繪製圖表"""
        if not self._is_data_loaded or not self._current_flags_data:
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] {tr('no_data_to_refresh', 'No Data to Refresh')}")
            return
        
        chart_data = self._current_flags_data.get("chart_data", {})
        if chart_data and self.elevation_chart:
            track_outline = chart_data.get("track_outline", [])
            # 🔧 修復：正確提取 corners 數據（參考 demo Line 721）
            official_corners = chart_data.get("official_corners", {})
            corners = official_corners.get("corners", [])
            self.elevation_chart.plot_elevation(track_outline, corners)
            logger.debug("[HISTORICAL_TRACK_MAP_MDI] {tr('charts_redrawn', 'Charts Redrawn')}")
    
    def _load_data_with_current_parameters(self):
        """
        使用當前參數載入數據 - UniversalAnalysisMDI 需要此方法
        
        這個方法被基類的 update_parameters() 調用，確保參數變更時自動重新載入數據
        """
        try:
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] _load_data_with_current_parameters 被調用")
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 當前參數: {self.current_year} {self.current_race} {self.current_session}")
            
            # ✅ 同步實例變量（非常重要！）
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 實例變量已同步: self.year={self.year}, self.race={self.race}, self.session={self.session}")
            
            if self.data_manager:
                # 同步數據管理器的參數
                # ⚠️ Function 100 只需要 race 參數（year 和 session 都是可選的）
                self.data_manager.race = self.current_race
                
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 數據管理器參數已同步")
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 開始載入數據...")
                
                # 載入數據 - Function 100 只需要 race 參數
                result = self.data_manager.load_data(
                    race=self.current_race
                )
                logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] 數據載入結果: {result}")
                return result
            else:
                logger.error(f"[HISTORICAL_TRACK_MAP_MDI] data_manager 不存在！")
            
            return False
            
        except Exception as e:
            logger.error(f"[HISTORICAL_TRACK_MAP_MDI] _load_data_with_current_parameters 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """
        更新分析參數（舊版方法，保留以支援舊代碼）
        
        ⚠️ 簡化策略：直接調用基類，移除複雜邏輯
        
        Args:
            year: 年份
            race: 比賽
            session: 賽段
            **kwargs: 額外參數
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.debug(f"[HISTORICAL_TRACK_MAP_MDI] update_lap_parameters: {year} {race} {session}")
            
            # 直接調用基類的 update_parameters() 方法，確保使用統一的更新流程
            return super().update_parameters(year=year, race=race, session=session, **kwargs)
            
        except Exception as e:
            logger.error(f"[HISTORICAL_TRACK_MAP_MDI] update_lap_parameters 失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_position_changes_data(self) -> Dict[str, int]:
        """
        載入每年度的名次變更總次數（從 API 的 yearly_summary）
        
        ✅ 硬編碼策略：如果 API 只返回 2025 年，則為 2022-2024 計算 position_changes
        
        Returns:
            Dict[str, int]: {年份: 名次變更總次數}
        """
        try:
            logger.debug(f"\n[HISTORICAL_TRACK_MAP_MDI] 📊 載入名次變更數據 (從 API yearly_summary) - Race: {self.race}")
            
            years = ['2022', '2023', '2024', '2025']
            position_changes = {}
            
            # ✅ 從已載入的數據 (_current_flags_data) 的 yearly_summary 中讀取
            if not hasattr(self, '_current_flags_data') or not self._current_flags_data:
                logger.warning("   ⚠️  _current_flags_data 不存在，無法載入 position changes")
                return {year: 0 for year in years}
            
            if 'yearly_summary' not in self._current_flags_data:
                logger.warning("   ⚠️  _current_flags_data 缺少 yearly_summary")
                return {year: 0 for year in years}
            
            yearly_summary = self._current_flags_data['yearly_summary']
            
            # ✅ 檢查是否只有 2025 年數據（GUI 只查詢 2025）
            if len(yearly_summary) == 1 and '2025' in yearly_summary:
                logger.debug("   🔧 檢測到只有 2025 年數據，開始為 2022-2024 計算 position_changes...")
                
                # 從 2025 年數據中提取 position_changes
                if '2025' in yearly_summary and 'position_changes' in yearly_summary['2025']:
                    position_changes['2025'] = yearly_summary['2025']['position_changes']
                    logger.info(f"   ✅ 2025: {position_changes['2025']} 次名次變更")
                else:
                    position_changes['2025'] = 0
                
                # 為 2022-2024 計算 position_changes
                for year in ['2022', '2023', '2024']:
                    try:
                        from CLI_modules.cli.analyzer.historical_flags_analysis import _calculate_position_changes_for_year
                        changes = _calculate_position_changes_for_year(int(year), self.race, self.session)
                        position_changes[year] = changes
                        logger.info(f"   ✅ {year}: {changes} 次名次變更 (即時計算)")
                    except Exception as e:
                        logger.warning(f"   ⚠️  {year}: 計算失敗 - {e}")
                        position_changes[year] = 0
            else:
                # 標準模式：從 yearly_summary 讀取所有年份
                for year in years:
                    if year in yearly_summary:
                        year_data = yearly_summary[year]
                        
                        if isinstance(year_data, dict) and 'position_changes' in year_data:
                            changes = year_data['position_changes']
                            position_changes[year] = changes
                            logger.info(f"   ✅ {year}: {changes} 次名次變更")
                        else:
                            position_changes[year] = 0
                            logger.warning(f"   ⚠️  {year}: yearly_summary 缺少 position_changes 欄位")
                    else:
                        position_changes[year] = 0
                        logger.warning(f"   ⚠️  {year}: yearly_summary 中找不到該年份數據")
            
            return position_changes
            
        except Exception as e:
            logger.error(f"載入名次變更數據失敗: {e}")
            import traceback

            traceback.print_exc()
            return {'2022': 0, '2023': 0, '2024': 0, '2025': 0}
    
    def get_module_info(self) -> Dict[str, Any]:
        """獲取模組資訊"""
        return {
            "name": tr("historical_track_map", "Historical Track Map"),
            "type": "historical_flags_analysis",
            "version": "1.0.0",
            "description": tr("historical_track_map_description", "F1 Historical Flags Analysis with Track Map"),
            "author": "F1T Team",
            "supports_realtime": False,
            "data_sources": ["API"],
            "chart_types": [tr("track_map", "Track Map"), tr("elevation_profile", "Elevation Profile"), tr("flags_tables", "Flags Tables")],
            "parameters": {
                "requires_year": True,
                "requires_race": True,
                "requires_session": True,
                "requires_driver": False,
                "requires_lap": False
            }
        }
