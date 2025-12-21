#!/usr/bin/env python3
"""
全車手最高速度分析模組
All Drivers Max Speed Module

實作 IAnalysisModule 介面，提供統一的模組介面給主 GUI 使用
使用 F121 (Straight Line All Laps Analysis) API 獲取數據

作者: F1T Team
日期: 2025-10-20
版本: 1.0.0
"""

import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget
from core.logger import get_logger

# 導入介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    from modules.gui.interfaces.analysis_module import IAnalysisModule

# 導入 MDI
try:
    from .all_drivers_max_speed_mdi import AllDriversMaxSpeedMDI
except ImportError:
    from modules.gui.all_drivers.max_speed.all_drivers_max_speed_mdi import (
        AllDriversMaxSpeedMDI
    )


logger = get_logger(__name__)


class AllDriversMaxSpeedModule(IAnalysisModule):
    """
    全車手最高速度分析模組 - 實作 IAnalysisModule 介面
    
    提供統一的模組介面給主 GUI 使用，管理 AllDriversMaxSpeedMDI 的生命週期
    使用 F121 API 獲取全車手直線速度統計數據
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
        
        # analysis_type 屬性
        self.analysis_type = 'all_drivers_max_speed'
        
        # 模組基本資訊
        self._module_name = "AllDriversMaxSpeed"
        self._display_name = "All Drivers Max Speed"
        self._version = "1.0.0"
        self._description = "All Drivers Maximum Speed Analysis (All Laps Statistics - F121)"
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 內部核心實例
        self._max_speed_core: Optional[AllDriversMaxSpeedMDI] = None
        
        # 主要元件
        self._main_widget: Optional[QWidget] = None
        
        # 狀態
        self._is_initialized = False
        
        logger.info("[MAX_SPEED_MODULE] 模組已創建: %s %s %s", year, race, session)
    
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
        """模組描述"""
        return self._description
    
    # ========== IAnalysisModule 介面實作 ==========
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            parent_widget: 父元件
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("[MAX_SPEED_MODULE] 開始初始化模組...")
            
            if self._is_initialized:
                logger.info("[MAX_SPEED_MODULE] 模組已初始化，跳過")
                return True
            
            # 檢查參數
            if not self.current_year or not self.current_race or not self.current_session:
                logger.error("[MAX_SPEED_MODULE] 缺少必要參數 (year/race/session)")
                return False
            
            # 創建 MDI 核心實例
            if not self._max_speed_core:
                logger.info("[MAX_SPEED_MODULE] 創建 MDI 核心（延遲初始化模式）")
                self._max_speed_core = AllDriversMaxSpeedMDI(parent=parent_widget)
                
                # 設置參數
                self._max_speed_core.current_year = self.current_year
                self._max_speed_core.current_race = self.current_race
                self._max_speed_core.current_session = self.current_session
                
                logger.info(
                    "[MAX_SPEED_MODULE] 已設置參數: %s %s %s",
                    self.current_year,
                    self.current_race,
                    self.current_session,
                )
                
                # 初始化 MDI 核心
                logger.info("[MAX_SPEED_MODULE] 初始化 MDI 核心...")
                if not self._max_speed_core.initialize_module():
                    logger.error("[MAX_SPEED_MODULE] MDI 核心初始化失敗")
                    return False
                logger.info("[MAX_SPEED_MODULE] MDI 核心初始化成功")
            
            # 獲取主要元件
            self._main_widget = self._max_speed_core.get_widget()
            
            if not self._main_widget:
                logger.error("[MAX_SPEED_MODULE] 無法獲取主要元件")
                return False
            
            self._is_initialized = True
            logger.info("[MAX_SPEED_MODULE] 模組初始化成功")
            return True
            
        except Exception as e:
            logger.exception("[MAX_SPEED_MODULE] 模組初始化失敗: %s", e)
            return False
    
    def get_widget(self) -> Optional[QWidget]:
        """
        獲取主要元件
        
        Returns:
            QWidget: 主要顯示元件
        """
        if not self._is_initialized:
            logger.warning("[MAX_SPEED_MODULE] 模組未初始化")
            return None
        return self._main_widget
    
    def update_parameters(self, year=None, race=None, session=None, **kwargs) -> bool:
        """
        更新分析參數並重新載入數據
        
        Args:
            year: 賽季年份
            race: 賽事名稱
            session: 賽段類型
            **kwargs: 額外參數
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.info("[MAX_SPEED_MODULE] 更新參數...")
            
            # 更新參數
            if year is not None:
                self.current_year = str(year)
            if race is not None:
                self.current_race = race
            if session is not None:
                self.current_session = session
            
            # 如果核心已創建，同步更新
            if self._max_speed_core:
                self._max_speed_core.year = self.current_year
                self._max_speed_core.race = self.current_race
                self._max_speed_core.session = self.current_session
                
                # 重新載入數據
                if hasattr(self._max_speed_core, 'load_initial_data'):
                    self._max_speed_core.load_initial_data()
            
            logger.info(
                "[MAX_SPEED_MODULE] 參數已更新: %s %s %s",
                self.current_year,
                self.current_race,
                self.current_session
            )
            return True
            
        except Exception as e:
            logger.exception("[MAX_SPEED_MODULE] 更新參數失敗: %s", e)
            return False
    
    def load_data(self, **kwargs) -> bool:
        """
        載入分析數據
        
        Args:
            **kwargs: 載入參數
            
        Returns:
            bool: 載入是否成功
        """
        try:
            if not self._max_speed_core or not hasattr(self._max_speed_core, 'load_initial_data'):
                logger.error("[MAX_SPEED_MODULE] 核心未初始化或不支援數據載入")
                return False
            
            self._max_speed_core.load_initial_data()
            return True
            
        except Exception as e:
            logger.exception("[MAX_SPEED_MODULE] 載入數據失敗: %s", e)
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        try:
            if self._max_speed_core and hasattr(self._max_speed_core, 'load_initial_data'):
                self._max_speed_core.load_initial_data()
                logger.info("[MAX_SPEED_MODULE] 分析已刷新")
        except Exception as e:
            logger.exception("[MAX_SPEED_MODULE] 刷新分析失敗: %s", e)
    
    def clear_data(self) -> None:
        """清除所有數據"""
        try:
            if self._max_speed_core:
                self._max_speed_core._current_data = None
                self._max_speed_core._is_data_loaded = False
                logger.info("[MAX_SPEED_MODULE] 數據已清除")
        except Exception as e:
            logger.exception("[MAX_SPEED_MODULE] 清除數據失敗: %s", e)
    
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """
        匯出分析數據
        
        Args:
            export_path: 匯出路徑
            export_format: 匯出格式
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            if not self._max_speed_core or not self._max_speed_core._current_data:
                logger.warning("[MAX_SPEED_MODULE] 無數據可匯出")
                return False
            
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self._max_speed_core._current_data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str
                )
            
            logger.info("[MAX_SPEED_MODULE] 數據已匯出至: %s", export_path)
            return True
            
        except Exception as e:
            logger.exception("[MAX_SPEED_MODULE] 匯出數據失敗: %s", e)
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取當前分析數據
        
        Returns:
            Dict[str, Any]: 當前的分析數據
        """
        if self._max_speed_core:
            return self._max_speed_core._current_data
        return None
    
    def cleanup(self):
        """清理資源"""
        try:
            logger.info("[MAX_SPEED_MODULE] 清理資源...")
            
            if self._max_speed_core:
                # 清理 MDI 核心
                if hasattr(self._max_speed_core, 'cleanup'):
                    self._max_speed_core.cleanup()
                self._max_speed_core = None
            
            self._main_widget = None
            self._is_initialized = False
            
            logger.info("[MAX_SPEED_MODULE] 資源清理完成")
            
        except Exception as e:
            logger.exception("[MAX_SPEED_MODULE] 清理資源失敗: %s", e)


__all__ = ["AllDriversMaxSpeedModule"]
