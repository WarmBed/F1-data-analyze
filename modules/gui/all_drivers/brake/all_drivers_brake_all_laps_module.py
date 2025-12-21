#!/usr/bin/env python3
"""
全車手煞車全圈數分析模組
All Drivers Brake All Laps Module

實作 IAnalysisModule 介面，提供統一的模組介面給主 GUI 使用

作者: F1T Team
日期: 2025-12-14
版本: 1.0.0
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget

# 導入 i18n
from core.gui_i18n import tr

# 導入 logger
from core.logger import get_logger
logger = get_logger(__name__)

# 導入介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    from modules.gui.interfaces.analysis_module import IAnalysisModule

# 導入 MDI
try:
    from .all_drivers_brake_all_laps_mdi import AllDriversBrakeAllLapsMDI
except ImportError:
    from modules.gui.all_drivers.brake.all_drivers_brake_all_laps_mdi import (
        AllDriversBrakeAllLapsMDI
    )


class AllDriversBrakeAllLapsModule(IAnalysisModule):
    """
    全車手煞車全圈數分析模組 - 實作 IAnalysisModule 介面
    
    提供統一的模組介面給主 GUI 使用，管理 AllDriversBrakeAllLapsMDI 的生命週期
    """
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        """
        初始化模組
        
        Args:
            parent: 父元件
            year: 賽季年份
            race: 賽事名稱
            session: 賽段類型
        """
        super().__init__(parent)
        
        # 添加 analysis_type 屬性
        self.analysis_type = 'brake_all_laps'
        
        # 模組基本資訊
        self._module_name = "AllDriversBrakeAllLaps"
        self._display_name = tr("all_drivers_brake_all_laps_analysis", "All Drivers Brake All Laps Analysis")
        self._version = "1.0.0"
        self._description = tr("brake_all_laps_desc", "Brake Performance Statistics Analysis (All Drivers, All Laps)")
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 內部核心實例
        self._brake_core: Optional[AllDriversBrakeAllLapsMDI] = None
        
        # 主要元件
        self._main_widget: Optional[QWidget] = None
        
        # 狀態
        self._is_initialized = False
        
        logger.debug(f"[BRAKE_ALL_LAPS_MODULE] Module created: {year} {race} {session}")
    
    # ========== IAnalysisModule 屬性實作 ==========
    
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return self._module_name
    
    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return self._display_name
    
    @property
    def version(self) -> str:
        """版本號"""
        return self._version
    
    @property
    def description(self) -> str:
        """描述"""
        return self._description
    
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._is_initialized
    
    # ========== IAnalysisModule 方法實作 ==========
    
    def initialize(self, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            if self._is_initialized:
                logger.debug("[BRAKE_ALL_LAPS_MODULE] Already initialized")
                return True
            
            logger.info("[BRAKE_ALL_LAPS_MODULE] Initializing module...")
            
            # 創建 MDI 核心
            self._brake_core = AllDriversBrakeAllLapsMDI(parent=None)
            
            # 設置參數
            self._brake_core.current_year = self.current_year
            self._brake_core.current_race = self.current_race
            self._brake_core.current_session = self.current_session
            
            # 初始化 MDI
            if not self._brake_core.initialize_module(**kwargs):
                logger.error("[BRAKE_ALL_LAPS_MODULE] MDI initialization failed")
                return False
            
            # 獲取主要元件
            self._main_widget = self._brake_core.get_main_widget()
            
            self._is_initialized = True
            logger.info("[BRAKE_ALL_LAPS_MODULE] Initialization complete")
            
            return True
            
        except Exception as e:
            logger.exception("[BRAKE_ALL_LAPS_MODULE] Initialization failed", exc_info=e)
            return False
    
    def get_widget(self) -> Optional[QWidget]:
        """
        獲取模組的主要 Widget
        
        Returns:
            QWidget: 主要 Widget，如果未初始化則返回 None
        """
        if not self._is_initialized:
            logger.warning("[BRAKE_ALL_LAPS_MODULE] Module not initialized")
            return None
        
        return self._main_widget
    
    def update_parameters(self, **kwargs) -> bool:
        """
        更新模組參數
        
        Args:
            **kwargs: 參數字典（year, race, session）
            
        Returns:
            bool: 更新是否成功
        """
        try:
            year = kwargs.get('year', self.current_year)
            race = kwargs.get('race', self.current_race)
            session = kwargs.get('session', self.current_session)
            
            self.current_year = str(year) if year else None
            self.current_race = race
            self.current_session = session
            
            if self._brake_core:
                self._brake_core.current_year = self.current_year
                self._brake_core.current_race = self.current_race
                self._brake_core.current_session = self.current_session
                self._brake_core.year = self.current_year
                self._brake_core.race = self.current_race
                self._brake_core.session = self.current_session
            
            logger.debug(f"[BRAKE_ALL_LAPS_MODULE] Parameters updated: {year} {race} {session}")
            return True
            
        except Exception as e:
            logger.exception("[BRAKE_ALL_LAPS_MODULE] Failed to update parameters", exc_info=e)
            return False
    
    def refresh_data(self) -> bool:
        """
        刷新數據
        
        Returns:
            bool: 刷新是否成功
        """
        try:
            if not self._is_initialized or not self._brake_core:
                logger.warning("[BRAKE_ALL_LAPS_MODULE] Cannot refresh, not initialized")
                return False
            
            self._brake_core.reload_data()
            return True
            
        except Exception as e:
            logger.exception("[BRAKE_ALL_LAPS_MODULE] Failed to refresh data", exc_info=e)
            return False
    
    def cleanup(self):
        """清理資源"""
        try:
            logger.debug("[BRAKE_ALL_LAPS_MODULE] Cleaning up...")
            
            if self._brake_core:
                self._brake_core.cleanup()
                self._brake_core = None
            
            self._main_widget = None
            self._is_initialized = False
            
            logger.debug("[BRAKE_ALL_LAPS_MODULE] Cleanup complete")
            
        except Exception as e:
            logger.exception("[BRAKE_ALL_LAPS_MODULE] Cleanup failed", exc_info=e)
    
    def get_status(self) -> Dict[str, Any]:
        """
        獲取模組狀態
        
        Returns:
            Dict: 狀態信息
        """
        return {
            "module_name": self._module_name,
            "version": self._version,
            "is_initialized": self._is_initialized,
            "year": self.current_year,
            "race": self.current_race,
            "session": self.current_session,
        }
