#!/usr/bin/env python3
"""
全車手煞車全圈數分析 MDI 視窗
All Drivers Brake All Laps MDI

負責管理 MDI 視窗，整合資料載入器和表格元件
簡化版：只顯示表格（與 All Driver Max Speed 一致）

作者: F1T Team
日期: 2025-12-14
版本: 1.2.0 - 簡化為只顯示表格
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QMessageBox
)
from PyQt5.QtCore import pyqtSlot

# 導入基類
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入資料載入器
try:
    from .brake_all_laps_loader import BrakeAllLapsDataLoader
except ImportError:
    from modules.gui.all_drivers.brake.brake_all_laps_loader import (
        BrakeAllLapsDataLoader
    )

# 導入表格元件
try:
    from .all_drivers_brake_all_laps_table_widget import AllDriversBrakeAllLapsTableWidget
except ImportError:
    from modules.gui.all_drivers.brake.all_drivers_brake_all_laps_table_widget import (
        AllDriversBrakeAllLapsTableWidget
    )

# 導入國際化與日誌
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(component="AllDriversBrakeAllLapsMDI")


class AllDriversBrakeAllLapsMDI(UniversalAnalysisMDI):
    """
    全車手煞車全圈數分析 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 BrakeAllLapsDataLoader 和 AllDriversBrakeAllLapsTableWidget
    
    特色功能：
    - 10 個完整統計欄位表格
    - 簡化介面（僅顯示表格）
    """
    
    # 模組類型註冊標記
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="all_drivers_brake_all_laps",
                display_name=tr("all_drivers_brake_all_laps_analysis", "All Drivers Brake All Laps Analysis"),
                default_size=(1400, 900),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("all_drivers_brake_all_laps", config)
            cls._REGISTERED = True
            logger.debug("[BRAKE_ALL_LAPS_MDI] Module type registered")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.info("[BRAKE_ALL_LAPS_MDI] Initializing...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="all_drivers_brake_all_laps", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        # 表格元件
        self._table_widget: Optional[AllDriversBrakeAllLapsTableWidget] = None
        
        logger.debug("[BRAKE_ALL_LAPS_MDI] Base initialization complete")
    
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
            logger.info("[BRAKE_ALL_LAPS_MDI] Initializing module...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error("[BRAKE_ALL_LAPS_MDI] Missing current_year")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error("[BRAKE_ALL_LAPS_MDI] Missing current_race")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error("[BRAKE_ALL_LAPS_MDI] Missing current_session")
                return False
            
            # 設置參數
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info("[BRAKE_ALL_LAPS_MDI] Parameters set: %s %s %s", self.year, self.race, self.session)
            
            # 調用基類的 initialize_module
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.error("[BRAKE_ALL_LAPS_MDI] Base initialization failed")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                logger.error("[BRAKE_ALL_LAPS_MDI] chart_widget not created")
                return False
            
            if not self.data_manager:
                logger.error("[BRAKE_ALL_LAPS_MDI] data_manager not created")
                return False
            
            logger.info("[BRAKE_ALL_LAPS_MDI] Components created successfully")
            
            # 自動載入初始數據
            logger.info("[BRAKE_ALL_LAPS_MDI] Loading initial data...")
            self.load_initial_data()
            
            return True
            
        except Exception as e:
            logger.exception("[BRAKE_ALL_LAPS_MDI] Initialization failed", exc_info=e)
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料管理器（資料載入器）
        
        Returns:
            BrakeAllLapsDataLoader: 資料載入器實例
        """
        logger.debug("[BRAKE_ALL_LAPS_MDI] Creating data manager...")
        
        # 使用 BrakeAllLapsDataLoader
        loader = BrakeAllLapsDataLoader(parent=self)
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        logger.debug("[BRAKE_ALL_LAPS_MDI] Data manager created")
        return loader
    
    def create_chart_widget(self):
        """
        創建主視圖（只顯示表格，與 All Driver Max Speed 一致）
        
        Returns:
            QWidget: 表格元件
        """
        logger.debug("[BRAKE_ALL_LAPS_MDI] Creating table widget...")
        
        # 直接創建並返回表格元件
        self._table_widget = AllDriversBrakeAllLapsTableWidget(parent=None)
        
        logger.debug("[BRAKE_ALL_LAPS_MDI] Table widget created")
        return self._table_widget
    
    def create_additional_widgets(self) -> list:
        """
        創建額外的 Widget 組件（不需要額外組件）
        
        Returns:
            list: 空列表（與 All Driver Max Speed 一致）
        """
        logger.debug("[BRAKE_ALL_LAPS_MDI] No additional widgets needed")
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
            logger.info("[BRAKE_ALL_LAPS_MDI] Data loaded signal received")
            
            if not data:
                self._on_load_error(tr("data_empty", "Data is empty"))
                return
            
            self._current_data = data
            self._is_data_loaded = True
            
            # 更新表格 - 添加安全檢查防止 AttributeError
            if self._table_widget:
                self._table_widget.update_data(data)
            elif hasattr(self, 'chart_widget') and self.chart_widget:
                # 備用：使用基類的 chart_widget
                if hasattr(self.chart_widget, 'update_data'):
                    self.chart_widget.update_data(data)
            else:
                logger.warning("[BRAKE_ALL_LAPS_MDI] 表格元件尚未初始化，資料已快取以便稍後更新")
            
            logger.info("[BRAKE_ALL_LAPS_MDI] Data processing complete")
            
        except Exception as e:
            logger.exception("[BRAKE_ALL_LAPS_MDI] Data processing failed", exc_info=e)
            self._on_load_error(f"{tr('data_processing_error', 'Data processing error')}: {str(e)}")
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.error("[BRAKE_ALL_LAPS_MDI] Load error: %s", error_msg)
        self._is_data_loaded = False
        
        # 顯示錯誤訊息
        self._show_error(tr("load_error_title", "Load Error"), error_msg)
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """
        狀態變更回調
        
        Args:
            status: 狀態訊息
        """
        logger.debug("[BRAKE_ALL_LAPS_MDI] Status: %s", status)
        # 可以在這裡更新狀態欄
    
    def _show_error(self, title: str, message: str):
        """
        顯示錯誤訊息
        
        Args:
            title: 標題
            message: 訊息內容
        """
        parent_widget = self.chart_widget if hasattr(self, 'chart_widget') and self.chart_widget else None
        QMessageBox.critical(parent_widget, title, message)
    
    # ========== 數據載入 ==========
    
    def load_initial_data(self):
        """載入初始數據"""
        if not self.data_manager:
            logger.error("[BRAKE_ALL_LAPS_MDI] data_manager not available")
            return
        
        logger.info("[BRAKE_ALL_LAPS_MDI] Loading data: %s %s %s", self.year, self.race, self.session)
        
        self.data_manager.load_data(
            year=self.year,
            race=self.race,
            session=self.session
        )
    
    def reload_data(self):
        """重新載入數據"""
        logger.info("[BRAKE_ALL_LAPS_MDI] Reloading data...")
        self.load_initial_data()
    
    # ========== 清理 ==========
    
    def cleanup(self):
        """清理資源"""
        logger.debug("[BRAKE_ALL_LAPS_MDI] Cleaning up...")
        
        if self.data_manager:
            self.data_manager.cleanup()
        
        super().cleanup()
    
    def closeEvent(self, event):
        """
        清理 API worker 防止視窗關閉時崩潰
        
        防止 'QThread: Destroyed while thread is still running' 錯誤
        當視窗在 API 載入期間關閉時發生
        
        使用 sync_wait=True 確保 Worker 在視窗關閉前停止
        """
        try:
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager._cleanup_api_worker(sync_wait=True)
        except Exception as e:
            logger.debug(f"[BRAKE_ALL_LAPS_MDI] closeEvent cleanup error: {str(e)}")
        super().closeEvent(event)
