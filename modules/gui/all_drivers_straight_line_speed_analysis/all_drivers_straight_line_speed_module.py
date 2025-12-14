#!/usr/bin/env python3
"""
全車手直線速度與加速性能模組
All Drivers Straight Line Speed Module

實作 IAnalysisModule 介面，提供統一的模組介面給主 GUI 使用

作者: F1T Team
日期: 2025-10-14
版本: 1.0.0
"""

import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget

# 導入介面
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    from ...interfaces.analysis_module import IAnalysisModule

# 導入 MDI
try:
    from .all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
except ImportError:
    from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import (
        AllDriversStraightLineSpeedMDI
    )


class AllDriversStraightLineSpeedModule(IAnalysisModule):
    """
    全車手直線速度與加速性能模組 - 實作 IAnalysisModule 介面
    
    提供統一的模組介面給主 GUI 使用，管理 AllDriversStraightLineSpeedMDI 的生命週期
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
        self.analysis_type = 'straight_line_speed'
        
        # 模組基本資訊
        self._module_name = "AllDriversStraightLineSpeed"
        self._display_name = "All Drivers Straight Line Speed"
        self._version = "1.0.0"
        self._description = "Maximum Speed and 100-300km/h Acceleration Analysis (All Drivers)"
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        
        # 內部核心實例
        self._speed_core: Optional[AllDriversStraightLineSpeedMDI] = None
        
        # 主要元件
        self._main_widget: Optional[QWidget] = None
        
        # 狀態
        self._is_initialized = False
    
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
            if self._is_initialized:
                return True
            
            # 檢查參數
            if not self.current_year or not self.current_race or not self.current_session:
                return False
            
            # 創建 MDI 核心實例
            if not self._speed_core:
                self._speed_core = AllDriversStraightLineSpeedMDI(parent=parent_widget)
                
                # 設置參數
                self._speed_core.current_year = self.current_year
                self._speed_core.current_race = self.current_race
                self._speed_core.current_session = self.current_session
                
                # 初始化 MDI 核心
                if not self._speed_core.initialize_module():
                    return False
            
            # 獲取主要元件
            self._main_widget = self._speed_core.get_widget()
            
            if not self._main_widget:
                print("❌ [SPEED_MODULE] 無法獲取主要元件")
                return False
            
            self._is_initialized = True
            print("✅ [SPEED_MODULE] 模組初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ [SPEED_MODULE] 模組初始化失敗: {e}")
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
            # 更新參數
            if year is not None:
                self.current_year = str(year)
            if race is not None:
                self.current_race = race
            if session is not None:
                self.current_session = session
            
            # 如果核心已創建，同步更新
            if self._speed_core:
                self._speed_core.year = self.current_year
                self._speed_core.race = self.current_race
                self._speed_core.session = self.current_session
                
                # 重新載入數據
                if hasattr(self._speed_core, 'load_initial_data'):
                    self._speed_core.load_initial_data()
            
            print(f"✅ [SPEED_MODULE] 參數已更新: {self.current_year} {self.current_race} {self.current_session}")
            return True
            
        except Exception as e:
            print(f"❌ [SPEED_MODULE] 更新參數失敗: {e}")
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
            if not self._speed_core or not hasattr(self._speed_core, 'load_initial_data'):
                return False
            
            self._speed_core.load_initial_data()
            return True
            
        except Exception as e:
            print(f"❌ [SPEED_MODULE] 載入數據失敗: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        try:
            if self._speed_core and hasattr(self._speed_core, 'load_initial_data'):
                self._speed_core.load_initial_data()
                print("✅ [SPEED_MODULE] 分析已刷新")
        except Exception as e:
            print(f"❌ [SPEED_MODULE] 刷新分析失敗: {e}")
    
    def clear_data(self) -> None:
        """清除所有數據"""
        try:
            if self._speed_core:
                self._speed_core._current_data = None
                self._speed_core._is_data_loaded = False
                print("✅ [SPEED_MODULE] 數據已清除")
        except Exception as e:
            print(f"❌ [SPEED_MODULE] 清除數據失敗: {e}")
    
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
            if not self._speed_core or not self._speed_core._current_data:
                return False
            
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._speed_core._current_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
            
        except Exception as e:
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取當前分析數據
        
        Returns:
            Dict[str, Any]: 當前的分析數據
        """
        if self._speed_core:
            return self._speed_core._current_data
        return None
    
    def cleanup(self):
        """清理資源"""
        try:
            if self._speed_core:
                # 清理 MDI 核心
                if hasattr(self._speed_core, 'cleanup'):
                    self._speed_core.cleanup()
                self._speed_core = None
            
            self._main_widget = None
            self._is_initialized = False
            
            print("✅ [SPEED_MODULE] 資源清理完成")
            
        except Exception as e:
            print(f"❌ [SPEED_MODULE] 清理資源失敗: {e}")
            import traceback
            traceback.print_exc()


__all__ = ["AllDriversStraightLineSpeedModule"]
