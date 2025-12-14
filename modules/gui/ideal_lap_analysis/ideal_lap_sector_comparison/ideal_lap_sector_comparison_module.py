#!/usr/bin/env python3
"""
理想圈分段對比模組
Ideal Lap Sector Comparison Module

實作 IAnalysisModule 介面，提供統一的模組介面給主 GUI 使用
使用水平棒狀圖展示全車手的理想圈與最快圈分段對比

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger
logger = get_logger(__name__)

# 導入介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    from ...interfaces.analysis_module import IAnalysisModule

# 導入 MDI
try:
    from .ideal_lap_sector_comparison_mdi import IdealLapSectorComparisonMDI
except ImportError:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi import IdealLapSectorComparisonMDI


class IdealLapSectorComparisonModule(IAnalysisModule):
    """
    理想圈分段對比模組 - 實作 IAnalysisModule 介面
    
    提供統一的模組介面給主 GUI 使用，管理 IdealLapSectorComparisonMDI 的生命週期
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
        
        # ✅ 添加 analysis_type 屬性以支援批次更新
        self.analysis_type = 'ideal_lap'
        
        # 模組基本資訊
        self._module_name = "IdealLapSectorComparison"
        self._display_name = "Ideal Lap Sector Comparison"
        self._version = "1.0.0"
        self._description = "Ideal vs Fastest Lap Sector Breakdown (All Drivers)"
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 內部核心實例
        self._comparison_core: Optional[IdealLapSectorComparisonMDI] = None
        
        # 主要元件
        self._main_widget: Optional[QWidget] = None
        
        # 狀態
        self._is_initialized = False
        
        logger.debug(f"[SECTOR_COMPARISON_MODULE] 模組已創建: {year} {race} {session}")
    
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
            logger.debug("[SECTOR_COMPARISON_MODULE] 開始初始化模組...")
            
            if self._is_initialized:
                logger.debug("[SECTOR_COMPARISON_MODULE] 模組已初始化，跳過")
                return True
            
            # 檢查參數
            if not self.current_year or not self.current_race or not self.current_session:
                logger.error("[SECTOR_COMPARISON_MODULE] 缺少必要參數 (year/race/session)")
                return False
            
            # 創建 MDI 核心實例（不傳遞參數，使用延遲初始化）
            if not self._comparison_core:
                logger.debug(f"[SECTOR_COMPARISON_MODULE] 創建 MDI 核心（延遲初始化模式）")
                self._comparison_core = IdealLapSectorComparisonMDI(parent=parent_widget)
                
                # 設置參數（通過基類屬性）
                self._comparison_core.current_year = self.current_year
                self._comparison_core.current_race = self.current_race
                self._comparison_core.current_session = self.current_session
                
                logger.debug(f"[SECTOR_COMPARISON_MODULE] 已設置參數: {self.current_year} {self.current_race} {self.current_session}")
                
                # ✅ 初始化 MDI 核心（觸發參數讀取和組件創建）
                logger.debug("[SECTOR_COMPARISON_MODULE] 初始化 MDI 核心...")
                if not self._comparison_core.initialize_module():
                    logger.error("[SECTOR_COMPARISON_MODULE] MDI 核心初始化失敗")
                    return False
                logger.info("[SECTOR_COMPARISON_MODULE] MDI 核心初始化成功")
            
            # 獲取主要元件
            self._main_widget = self._comparison_core.get_widget()
            
            if not self._main_widget:
                logger.error("[SECTOR_COMPARISON_MODULE] 無法獲取主要元件")
                return False
            
            self._is_initialized = True
            logger.info("[SECTOR_COMPARISON_MODULE] 模組初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_widget(self) -> Optional[QWidget]:
        """
        獲取主要 Widget
        
        Returns:
            Optional[QWidget]: 主要元件，若未初始化則返回 None
        """
        if not self._is_initialized:
            logger.warning("[SECTOR_COMPARISON_MODULE] 模組尚未初始化")
            return None
        
        return self._main_widget
    
    def refresh_data(self, **kwargs) -> bool:
        """
        刷新數據
        
        Args:
            **kwargs: 刷新參數
            
        Returns:
            bool: 刷新是否成功
        """
        try:
            logger.debug("[SECTOR_COMPARISON_MODULE] 刷新數據...")
            
            if not self._is_initialized or not self._comparison_core:
                logger.error("[SECTOR_COMPARISON_MODULE] 模組未初始化，無法刷新")
                return False
            
            # 委派給 MDI 核心
            self._comparison_core.reload_data()
            logger.info("[SECTOR_COMPARISON_MODULE] 數據刷新成功")
            return True
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 刷新失敗: {e}")
            return False
    
    def load_data(self, **kwargs) -> bool:
        """
        載入資料 (IAnalysisModule 必須方法)
        
        Args:
            **kwargs: 載入參數
            
        Returns:
            bool: 載入是否成功
        """
        try:
            logger.debug("[SECTOR_COMPARISON_MODULE] 載入資料...")
            
            if not self._is_initialized:
                logger.error("[SECTOR_COMPARISON_MODULE] 模組未初始化")
                return False
            
            if not self._comparison_core:
                logger.error("[SECTOR_COMPARISON_MODULE] MDI 核心未創建")
                return False
            
            # 觸發 MDI 載入資料
            self._comparison_core.load_initial_data()
            
            logger.info("[SECTOR_COMPARISON_MODULE] 資料載入已觸發")
            return True
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 載入資料失敗: {e}")
            import traceback

            traceback.print_exc()
            return False
    
    def refresh_analysis(self) -> bool:
        """
        刷新分析 (IAnalysisModule 必須方法)
        
        Returns:
            bool: 刷新是否成功
        """
        # 委派給 refresh_data
        return self.refresh_data()
    
    def clear_data(self) -> bool:
        """
        清空資料 (IAnalysisModule 必須方法)
        
        Returns:
            bool: 清空是否成功
        """
        try:
            logger.debug("[SECTOR_COMPARISON_MODULE] 清空資料...")
            
            if self._comparison_core and hasattr(self._comparison_core, 'chart_widget'):
                # 清空圖表
                if hasattr(self._comparison_core.chart_widget, 'clear'):
                    self._comparison_core.chart_widget.clear()
                logger.info("[SECTOR_COMPARISON_MODULE] 資料已清空")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 清空資料失敗: {e}")
            return False
    
    def export_data(self, export_path: str, export_format: str = "csv") -> bool:
        """
        匯出資料 (IAnalysisModule 必須方法)
        
        Args:
            export_path: 匯出路徑
            export_format: 匯出格式
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            logger.debug(f"[SECTOR_COMPARISON_MODULE] 匯出資料到: {export_path} (格式: {export_format})")
            
            # 委派給圖表匯出方法
            if export_format in ["png", "jpg", "svg"]:
                return self.export_chart(export_path)
            
            # TODO: 實作 CSV/JSON 匯出功能
            logger.warning("[SECTOR_COMPARISON_MODULE] CSV/JSON 匯出功能尚未實作")
            return False
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 匯出失敗: {e}")
            return False
    
    def update_parameters(self, **params) -> bool:
        """
        更新參數
        
        Args:
            **params: 新參數 (year, race, session 等)
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.debug(f"[SECTOR_COMPARISON_MODULE] 更新參數: {params}")
            
            # 更新內部參數
            if 'year' in params:
                self.current_year = str(params['year'])
            if 'race' in params:
                self.current_race = params['race']
            if 'session' in params:
                self.current_session = params['session']
            
            # 如果 MDI 核心已初始化，更新其參數
            if self._comparison_core:
                self._comparison_core.update_parameters(**params)
            
            logger.info("[SECTOR_COMPARISON_MODULE] 參數更新成功")
            return True
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 參數更新失敗: {e}")
            return False
    
    def cleanup(self):
        """清理資源"""
        try:
            logger.debug("[SECTOR_COMPARISON_MODULE] 開始清理資源...")
            
            # 清理 MDI 核心
            if self._comparison_core:
                if hasattr(self._comparison_core, 'cleanup'):
                    self._comparison_core.cleanup()
                self._comparison_core = None
            
            # 清理主要元件
            self._main_widget = None
            
            # 重置狀態
            self._is_initialized = False
            
            logger.info("[SECTOR_COMPARISON_MODULE] 資源清理完成")
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 清理失敗: {e}")
    
    def get_module_info(self) -> Dict[str, Any]:
        """
        獲取模組資訊
        
        Returns:
            Dict: 模組資訊字典
        """
        return {
            "name": self._module_name,
            "display_name": self._display_name,
            "version": self._version,
            "description": self._description,
            "is_initialized": self._is_initialized,
            "parameters": {
                "year": self.current_year,
                "race": self.current_race,
                "session": self.current_session
            }
        }
    
    def is_ready(self) -> bool:
        """
        檢查模組是否就緒
        
        Returns:
            bool: 模組是否已初始化且就緒
        """
        return self._is_initialized and self._comparison_core is not None
    
    # ========== 模組特定方法 ==========
    
    def get_current_data(self) -> Optional[Dict]:
        """
        獲取當前數據
        
        Returns:
            Optional[Dict]: 當前數據，若無則返回 None
        """
        if not self._comparison_core:
            return None
        
        return self._comparison_core.get_current_data()
    
    def export_chart(self, file_path: str) -> bool:
        """
        匯出圖表
        
        Args:
            file_path: 匯出檔案路徑
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            if not self._comparison_core:
                return False
            
            return self._comparison_core.export_chart(file_path)
            
        except Exception as e:
            logger.error(f"[SECTOR_COMPARISON_MODULE] 匯出失敗: {e}")
            return False
