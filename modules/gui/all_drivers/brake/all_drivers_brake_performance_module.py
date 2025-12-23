#!/usr/bin/env python3
"""
全車手煞車性能分析模組
All Drivers Brake Performance Module

實作 IAnalysisModule 介面，提供統一的模組介面給主 GUI 使用

作者: F1T Team
日期: 2025-10-18
版本: 1.0.0
"""

import sys
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
    from .all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
except ImportError:
    from modules.gui.all_drivers.brake.all_drivers_brake_performance_mdi import (
        AllDriversBrakePerformanceMDI
    )


class AllDriversBrakePerformanceModule(IAnalysisModule):
    """
    全車手煞車性能分析模組 - 實作 IAnalysisModule 介面
    
    提供統一的模組介面給主 GUI 使用，管理 AllDriversBrakePerformanceMDI 的生命週期
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
        
        # ✅ 添加 analysis_type 屬性
        self.analysis_type = 'brake_performance'
        
        # 模組基本資訊
        self._module_name = "AllDriversBrakePerformance"
        self._display_name = tr("all_drivers_brake_performance", "All Drivers Brake Performance")
        self._version = "1.0.0"
        self._description = tr("brake_performance_desc", "Maximum Deceleration, Brake Distance and Brake Time Analysis (All Drivers)")
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 內部核心實例
        self._brake_core: Optional[AllDriversBrakePerformanceMDI] = None
        
        # 主要元件
        self._main_widget: Optional[QWidget] = None
        
        # 狀態
        self._is_initialized = False
        
        logger.debug(f"[BRAKE_MODULE] 模組已創建: {year} {race} {session}")
    
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
            logger.debug("[BRAKE_MODULE] 開始初始化模組...")
            
            if self._is_initialized:
                logger.debug("[BRAKE_MODULE] 模組已初始化，跳過")
                return True
            
            # 檢查參數
            if not self.current_year or not self.current_race or not self.current_session:
                logger.debug("[BRAKE_MODULE] 缺少必要參數 (year/race/session)")
                return False
            
            # 創建 MDI 核心實例
            if not self._brake_core:
                logger.debug("[BRAKE_MODULE] 創建 MDI 核心（延遲初始化模式）")
                self._brake_core = AllDriversBrakePerformanceMDI(parent=parent_widget)
                
                # 設置參數
                self._brake_core.current_year = self.current_year
                self._brake_core.current_race = self.current_race
                self._brake_core.current_session = self.current_session
                
                logger.debug(f"[BRAKE_MODULE] 已設置參數: {self.current_year} {self.current_race} {self.current_session}")
                
                # 初始化 MDI 核心
                logger.debug("[BRAKE_MODULE] 初始化 MDI 核心...")
                if not self._brake_core.initialize_module():
                    logger.debug("[BRAKE_MODULE] MDI 核心初始化失敗")
                    return False
                logger.debug("[BRAKE_MODULE] MDI 核心初始化成功")
            
            # 獲取主要元件
            self._main_widget = self._brake_core.get_widget()
            
            if not self._main_widget:
                logger.debug("[BRAKE_MODULE] 無法獲取主要元件")
                return False
            
            self._is_initialized = True
            logger.debug("[BRAKE_MODULE] 模組初始化成功")
            return True
            
        except Exception as e:
            logger.debug(f"[BRAKE_MODULE] 模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_widget(self) -> Optional[QWidget]:
        """
        獲取主要元件
        
        Returns:
            QWidget: 主要顯示元件
        """
        if not self._is_initialized:
            logger.debug("[BRAKE_MODULE] 模組未初始化")
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
            logger.debug("[BRAKE_MODULE] 更新參數...")
            
            # 更新參數
            if year is not None:
                self.current_year = str(year)
            if race is not None:
                self.current_race = race
            if session is not None:
                self.current_session = session
            
            # 如果核心已創建，同步更新
            if self._brake_core:
                self._brake_core.year = self.current_year
                self._brake_core.race = self.current_race
                self._brake_core.session = self.current_session
                
                # 重新載入數據
                if hasattr(self._brake_core, 'load_initial_data'):
                    self._brake_core.load_initial_data()
            
            logger.debug(f"[BRAKE_MODULE] 參數已更新: {self.current_year} {self.current_race} {self.current_session}")
            return True
            
        except Exception as e:
            logger.debug(f"[BRAKE_MODULE] 更新參數失敗: {e}")
            import traceback
            traceback.print_exc()
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
            if not self._brake_core or not hasattr(self._brake_core, 'load_initial_data'):
                logger.debug("[BRAKE_MODULE] 核心未初始化或不支援數據載入")
                return False
            
            self._brake_core.load_initial_data()
            return True
            
        except Exception as e:
            logger.debug(f"[BRAKE_MODULE] 載入數據失敗: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        try:
            if self._brake_core and hasattr(self._brake_core, 'load_initial_data'):
                self._brake_core.load_initial_data()
                logger.debug("[BRAKE_MODULE] 分析已刷新")
        except Exception as e:
            logger.debug(f"[BRAKE_MODULE] 刷新分析失敗: {e}")
    
    def clear_data(self) -> None:
        """清除所有數據"""
        try:
            if self._brake_core:
                self._brake_core._current_data = None
                self._brake_core._is_data_loaded = False
                logger.debug("[BRAKE_MODULE] 數據已清除")
        except Exception as e:
            logger.debug(f"[BRAKE_MODULE] 清除數據失敗: {e}")
    
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
            if not self._brake_core or not self._brake_core._current_data:
                logger.debug("[BRAKE_MODULE] 無數據可匯出")
                return False
            
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._brake_core._current_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.debug(f"[BRAKE_MODULE] 數據已匯出至: {export_path}")
            return True
            
        except Exception as e:
            logger.debug(f"[BRAKE_MODULE] 匯出數據失敗: {e}")
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取當前分析數據
        
        Returns:
            Dict[str, Any]: 當前的分析數據
        """
        if self._brake_core:
            return self._brake_core._current_data
        return None
    
    def cleanup(self):
        """清理資源"""
        try:
            logger.debug("[BRAKE_MODULE] 清理資源...")
            
            if self._brake_core:
                # 清理 MDI 核心
                if hasattr(self._brake_core, 'cleanup'):
                    self._brake_core.cleanup()
                self._brake_core = None
            
            self._main_widget = None
            self._is_initialized = False
            
            logger.debug("[BRAKE_MODULE] 資源清理完成")
            
        except Exception as e:
            logger.debug(f"[BRAKE_MODULE] 清理資源失敗: {e}")
            import traceback
            traceback.print_exc()


__all__ = ["AllDriversBrakePerformanceModule"]
