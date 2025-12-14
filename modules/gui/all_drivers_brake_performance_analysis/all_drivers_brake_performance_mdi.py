#!/usr/bin/env python3
"""
全車手煞車性能分析 MDI 視窗
All Drivers Brake Performance MDI

負責管理 MDI 視窗，整合資料載入器和表格元件

作者: F1T Team
日期: 2025-10-18
版本: 1.0.0
"""

import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSlot

# 導入基類
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from ...base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入資料載入器
try:
    from .brake_performance_loader import BrakePerformanceDataLoader
except ImportError:
    from modules.gui.all_drivers_brake_performance_analysis.brake_performance_loader import (
        BrakePerformanceDataLoader
    )

# ✅ 導入表格元件
try:
    from .all_drivers_brake_performance_table_widget import AllDriversBrakePerformanceTableWidget
except ImportError:
    from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_table_widget import (
        AllDriversBrakePerformanceTableWidget
    )

# 導入國際化與日誌
from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger(component="AllDriversBrakePerformanceMDI")


class AllDriversBrakePerformanceMDI(UniversalAnalysisMDI):
    """
    全車手煞車性能分析 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 BrakePerformanceDataLoader 和 AllDriversBrakePerformanceTableWidget
    """
    
    # 模組類型註冊標記
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="all_drivers_brake_performance",
                display_name=tr("all_drivers_brake_performance", "All Drivers Brake Performance"),
                default_size=(1200, 900),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("all_drivers_brake_performance", config)
            cls._REGISTERED = True
            logger.debug("[BRAKE_MDI] 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.info("[BRAKE_MDI] AllDriversBrakePerformanceMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="all_drivers_brake_performance", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        logger.debug("[BRAKE_MDI] 基類初始化完成，等待參數設置...")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組（設置參數並載入初始數據）
        
        Args:
            parent_widget: 父級 widget（可選）
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("[BRAKE_MDI] 開始初始化模組...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error("[BRAKE_MDI] 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error("[BRAKE_MDI] 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error("[BRAKE_MDI] 缺少 current_session 屬性")
                return False
            
            # 設置參數
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info("[BRAKE_MDI] 參數已設置: %s %s %s", self.year, self.race, self.session)
            
            # 調用基類的 initialize_module
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.error("[BRAKE_MDI] 基類初始化失敗")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                logger.error("[BRAKE_MDI] chart_widget 未創建")
                return False
            
            if not self.data_manager:
                logger.error("[BRAKE_MDI] data_manager 未創建")
                return False
            
            logger.info("[BRAKE_MDI] 組件創建成功")
            
            # 自動載入初始數據
            logger.info("[BRAKE_MDI] 準備載入初始數據...")
            self.load_initial_data()
            
            return True
            
        except Exception as e:
            logger.exception("[BRAKE_MDI] 初始化失敗", exc_info=e)
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料管理器（資料載入器）
        
        Returns:
            BrakePerformanceDataLoader: 資料載入器實例
        """
        logger.debug("[BRAKE_MDI] 創建資料管理器...")
        
        # ✅ 使用 BrakePerformanceDataLoader
        loader = BrakePerformanceDataLoader(parent=self)
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        logger.debug("[BRAKE_MDI] 資料管理器已創建")
        return loader
    
    def create_chart_widget(self):
        """
        創建表格元件（QTableWidget 版本）
        
        Returns:
            AllDriversBrakePerformanceTableWidget: 表格元件實例
        """
        logger.debug("[BRAKE_MDI] 創建表格元件（QTableWidget 版本）...")
        
        widget = AllDriversBrakePerformanceTableWidget(parent=None)
        
        logger.debug("[BRAKE_MDI] 表格元件已創建")
        return widget
    
    def create_additional_widgets(self) -> list:
        """
        創建額外的 Widget 組件
        
        Returns:
            list: 額外的 Widget 列表（空）
        """
        logger.debug("[BRAKE_MDI] 不創建額外組件")
        
        # ✅ 不創建統計面板，返回空列表
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
            logger.info("[BRAKE_MDI] 收到資料載入完成信號")
            
            if not data:
                self._on_load_error(tr("data_empty", "資料為空"))
                return
            
            self._current_data = data
            self._is_data_loaded = True
            
            # 更新圖表
            if self.chart_widget:
                self.chart_widget.update_data(data)
            
            logger.info("[BRAKE_MDI] 資料處理完成")
            
        except Exception as e:
            logger.exception("[BRAKE_MDI] 資料處理失敗", exc_info=e)
            self._on_load_error(f"{tr('data_processing_error', '資料處理錯誤')}: {str(e)}")
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.error("[BRAKE_MDI] 資料載入錯誤: %s", error_msg)
        QMessageBox.critical(None, tr("load_error", "載入錯誤"), error_msg)
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """狀態變更回調"""
        logger.info("[BRAKE_MDI] 狀態: %s", status)
    
    def load_initial_data(self):
        """載入初始數據"""
        try:
            logger.info("[BRAKE_MDI] 開始載入初始數據...")
            
            if not self.data_manager:
                logger.error("[BRAKE_MDI] data_manager 不存在")
                return
            
            # 呼叫資料載入器
            success = self.data_manager.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
            
            if not success:
                logger.error("[BRAKE_MDI] 資料載入失敗")
                
        except Exception as e:
            logger.exception("[BRAKE_MDI] 載入初始數據失敗", exc_info=e)
    
    # ========== 覆寫基類方法 ==========
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        生成視窗標題（覆寫基類方法）- 只顯示模組名稱
        
        Args:
            year: 年份（忽略）
            race: 賽事（忽略）
            session: 場次（忽略）
            
        Returns:
            str: 模組名稱標題
        """
        from core.gui_i18n import tr
        module_name = tr('all_drivers_brake_performance', 'All Drivers Brake Performance')
        return module_name
    
    # ========== 事件處理 ==========
    
    @pyqtSlot(str)
    def _on_driver_clicked(self, driver_code: str):
        """車手點擊事件"""
        logger.info("[BRAKE_MDI] 車手被點擊: %s", driver_code)


__all__ = ["AllDriversBrakePerformanceMDI"]
