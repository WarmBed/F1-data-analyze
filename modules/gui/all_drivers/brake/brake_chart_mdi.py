#!/usr/bin/env python3
"""
全車手煞車性能圖表 MDI 視窗
All Drivers Brake Chart MDI

負責管理 MDI 視窗，整合資料載入器和圖表元件
呼叫 F122 API 獲取全圈數煞車統計並繪製煞車前速度-減速度散點圖

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import pyqtSlot

# 導入基類
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入資料載入器
from .brake_chart_data_loader import BrakeChartDataLoader

# 導入圖表元件
from .brake_chart_widget import BrakeChartWidget

# 導入國際化
from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger("brake_chart_mdi", component="gui")


class AllDriversBrakeChartMDI(UniversalAnalysisMDI):
    """
    全車手煞車性能圖表 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 BrakeChartDataLoader 和 BrakeChartWidget
    
    視覺化:
    - X軸: 煞車前速度 (km/h)
    - Y軸: 減速度 (m/s^2) - 使用絕對值
    - 每車手一個散點，車隊顏色標記
    """
    
    # 模組類型註冊標記
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="all_drivers_brake_chart",
                display_name="All Drivers Brake Chart",
                default_size=(1100, 800),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("all_drivers_brake_chart", config)
            cls._REGISTERED = True
            logger.info("[BRAKE_CHART_MDI] Module type registered")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.info("[BRAKE_CHART_MDI] AllDriversBrakeChartMDI initializing...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="all_drivers_brake_chart", parent=parent)
        
        # 初始化參數
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        logger.info("[BRAKE_CHART_MDI] Base init done, waiting for params...")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組（設置參數並載入初始數據）
        
        Args:
            parent_widget: 父級 widget
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("[BRAKE_CHART_MDI] Starting module initialization...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error("[BRAKE_CHART_MDI] Missing current_year attribute")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error("[BRAKE_CHART_MDI] Missing current_race attribute")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error("[BRAKE_CHART_MDI] Missing current_session attribute")
                return False
            
            # 設置參數
            self.year = int(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info("[BRAKE_CHART_MDI] Params set: %s %s %s", self.year, self.race, self.session)
            
            # 調用基類的 initialize_module
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.error("[BRAKE_CHART_MDI] Base init failed")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                logger.error("[BRAKE_CHART_MDI] chart_widget not created")
                return False
            
            if not self.data_manager:
                logger.error("[BRAKE_CHART_MDI] data_manager not created")
                return False
            
            logger.info("[BRAKE_CHART_MDI] Components created successfully")
            
            # 自動載入初始數據
            logger.info("[BRAKE_CHART_MDI] Loading initial data...")
            self.load_initial_data()
            
            return True
            
        except Exception as e:
            logger.exception("[BRAKE_CHART_MDI] Initialization failed: %s", e)
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料管理器（資料載入器）
        
        Returns:
            BrakeChartDataLoader: 資料載入器實例
        """
        logger.info("[BRAKE_CHART_MDI] Creating data manager...")
        
        loader = BrakeChartDataLoader(parent=self)
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        logger.info("[BRAKE_CHART_MDI] Data manager created")
        return loader
    
    def create_chart_widget(self):
        """
        創建圖表元件
        
        Returns:
            BrakeChartWidget: 圖表元件實例
        """
        logger.info("[BRAKE_CHART_MDI] Creating chart widget...")
        
        widget = BrakeChartWidget(parent=None)
        
        logger.info("[BRAKE_CHART_MDI] Chart widget created")
        return widget
    
    def create_additional_widgets(self) -> list:
        """
        創建額外的 Widget 組件
        
        Returns:
            list: 額外的 Widget 列表（空）
        """
        # 純圖表顯示，不需要額外組件
        return []
    
    # ========== 數據處理回調 ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        數據載入完成回調
        
        Args:
            data: 載入的資料
        """
        try:
            logger.info("[BRAKE_CHART_MDI] Data loaded signal received")
            
            if not data:
                self._on_load_error(tr("Data is empty"))
                return
            
            self._current_data = data
            self._is_data_loaded = True
            
            # 更新圖表
            if self.chart_widget:
                self.chart_widget.set_data(data)
            
            logger.info("[BRAKE_CHART_MDI] Data processing completed")
            
        except Exception as e:
            logger.exception("[BRAKE_CHART_MDI] Data processing failed: %s", e)
            self._on_load_error(f"{tr('Data processing error')}: {str(e)}")
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.error("[BRAKE_CHART_MDI] Data load error: %s", error_msg)
        QMessageBox.critical(None, tr("Load Error"), error_msg)
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """狀態變更回調"""
        logger.info("[BRAKE_CHART_MDI] Status: %s", status)
    
    def load_initial_data(self):
        """載入初始數據"""
        try:
            logger.info("[BRAKE_CHART_MDI] Loading initial data...")
            
            if not self.data_manager:
                logger.error("[BRAKE_CHART_MDI] data_manager not exists")
                return
            
            # 呼叫資料載入器
            self.data_manager.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
                
        except Exception as e:
            logger.exception("[BRAKE_CHART_MDI] Failed to load initial data: %s", e)
    
    # ========== 覆寫基類方法 ==========
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        生成視窗標題
        
        Returns:
            str: 模組名稱標題
        """
        module_name = tr('all_drivers_brake_chart', 'All Drivers Brake Chart')
        return module_name


__all__ = ["AllDriversBrakeChartMDI"]
