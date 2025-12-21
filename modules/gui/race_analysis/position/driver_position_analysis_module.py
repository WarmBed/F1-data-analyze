#!/usr/bin/env python3
"""
車手比賽排名分析模組
Driver Position Analysis Module

實作 IAnalysisModule 介面，提供統一的模組介面給主 GUI 使用

作者: F1T Team
日期: 2025-10-28
版本: 1.0.0
"""

from typing import Optional
from PyQt5.QtWidgets import QWidget
from core.logger import get_logger

# 導入介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    from modules.gui.interfaces.analysis_module import IAnalysisModule

# 導入 MDI
try:
    from .driver_position_analysis_mdi import DriverPositionAnalysisMDI
except ImportError:
    from modules.gui.driver_position_analysis.driver_position_analysis_mdi import DriverPositionAnalysisMDI


logger = get_logger("gui.driver_position_analysis_module", component="gui")


class DriverPositionAnalysisModule(IAnalysisModule):
    """
    車手比賽排名分析模組 - 實作 IAnalysisModule 介面
    
    提供統一的模組介面給主 GUI 使用，管理 DriverPositionAnalysisMDI 的生命週期
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
        
        # 添加 analysis_type 屬性以支援批次更新
        self.analysis_type = 'driver_position'
        
        # 模組基本資訊
        self._module_name = "DriverPositionAnalysis"
        self._display_name = "Driver Race Position Analysis"
        self._version = "1.0.0"
        self._description = "All Drivers Race Position Analysis"
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 內部核心實例
        self._position_core: Optional[DriverPositionAnalysisMDI] = None
        
        # 主要元件
        self._main_widget: Optional[QWidget] = None
        
        # 狀態
        self._is_initialized = False
        
        logger.info(
            "[POSITION_MODULE] 模組已創建: %s %s %s",
            year,
            race,
            session,
        )
    
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
            logger.info("[POSITION_MODULE] 開始初始化模組...")
            
            if self._is_initialized:
                logger.info("[POSITION_MODULE] 模組已初始化，跳過")
                return True
            
            # 檢查參數
            if not self.current_year or not self.current_race or not self.current_session:
                logger.error("❌ [POSITION_MODULE] 缺少必要參數 (year/race/session)")
                return False
            
            # 創建 MDI 核心實例
            if not self._position_core:
                logger.info(
                    "[POSITION_MODULE] 創建 MDI 核心: %s %s %s",
                    self.current_year,
                    self.current_race,
                    self.current_session,
                )
                # MDI 構造函數只接受 parent 參數
                self._position_core = DriverPositionAnalysisMDI(parent=parent_widget)
                
                # 在初始化前設置必要的屬性
                self._position_core.current_year = self.current_year
                self._position_core.current_race = self.current_race
                self._position_core.current_session = self.current_session
                
                # 初始化 MDI 核心
                logger.info("[POSITION_MODULE] 初始化 MDI 核心...")
                if not self._position_core.initialize_module():
                    logger.error("❌ [POSITION_MODULE] MDI 核心初始化失敗")
                    return False
                logger.info("✅ [POSITION_MODULE] MDI 核心初始化成功")
            
            # 獲取主要元件
            self._main_widget = self._position_core.get_widget()
            
            if not self._main_widget:
                logger.error("❌ [POSITION_MODULE] 無法獲取主要元件")
                return False
            
            self._is_initialized = True
            logger.info("✅ [POSITION_MODULE] 模組初始化成功")
            return True
            
        except Exception as e:
            logger.exception("❌ [POSITION_MODULE] 初始化失敗")
            return False
    
    def load_data(self, **kwargs) -> bool:
        """
        載入資料
        
        Args:
            **kwargs: 載入參數
            
        Returns:
            bool: 載入是否成功
        """
        try:
            logger.info("[POSITION_MODULE] 載入資料...")
            
            if not self._is_initialized:
                logger.error("❌ [POSITION_MODULE] 模組未初始化")
                return False
            
            if not self._position_core:
                logger.error("❌ [POSITION_MODULE] MDI 核心未創建")
                return False
            
            # 觸發 MDI 載入資料
            self._position_core.load_initial_data()
            
            logger.info("✅ [POSITION_MODULE] 資料載入已觸發")
            return True
            
        except Exception as e:
            logger.exception("❌ [POSITION_MODULE] 載入資料失敗")
            return False
    
    def update_parameters(self, year: int, race: str, session: str, **kwargs) -> bool:
        """
        更新分析參數
        
        Args:
            year: 年份
            race: 賽事
            session: 賽段
            **kwargs: 額外參數
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.info("[POSITION_MODULE] 更新參數: %s %s %s", year, race, session)
            
            # 更新模組參數
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # 更新 MDI 核心參數
            if self._position_core:
                return self._position_core.update_analysis_parameters(str(year), race, session)
            
            logger.warning("⚠️  [POSITION_MODULE] MDI 核心未初始化，只更新模組參數")
            return True
            
        except Exception:
            logger.exception("❌ [POSITION_MODULE] 參數更新失敗")
            return False
    
    def get_widget(self) -> Optional[QWidget]:
        """
        獲取主要顯示元件
        
        Returns:
            Optional[QWidget]: 主要元件，如果未初始化則返回 None
        """
        return self._main_widget
    
    def cleanup(self):
        """清理資源"""
        try:
            logger.info("[POSITION_MODULE] 清理資源...")
            
            if self._position_core:
                if hasattr(self._position_core, 'cleanup'):
                    self._position_core.cleanup()
                self._position_core = None
            
            self._main_widget = None
            self._is_initialized = False
            
            logger.info("✅ [POSITION_MODULE] 資源已清理")
            
        except Exception:
            logger.exception("❌ [POSITION_MODULE] 清理失敗")
    
    def get_current_state(self) -> dict:
        """
        獲取當前模組狀態
        
        Returns:
            dict: 狀態字典
        """
        return {
            "module_name": self._module_name,
            "year": self.current_year,
            "race": self.current_race,
            "session": self.current_session,
            "is_initialized": self._is_initialized,
        }
