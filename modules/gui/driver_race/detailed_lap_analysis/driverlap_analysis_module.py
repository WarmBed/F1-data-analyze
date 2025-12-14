#!/usr/bin/env python3
"""
driverLapAnalysisModule - F1T Detailed Lap Analysis Module
========================================================

Comprehensive detailed lap analysis module based on universal architecture.

Features:
- Detailed lap time trend analysis (per lap second display)
- Driver selection control area (up to 5 drivers simultaneous comparison)
- Intelligent marking system (accident A, rain R, pitstop P, fastest lap F, etc.)
- Tire strategy timeline (bottom shows each driver's tire usage)
- Line chart visualization analysis
- Calls CLI -f28 for data generation

Author: F1T Team
Date: 2025-09-12
Version: 2.0.0 (Detailed Lap Analysis Version)
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from core.logger import get_logger
logger = get_logger(__name__)

# 導入介面和基類
try:
    from ...interfaces.analysis_module import IAnalysisModule
except ImportError:  # pragma: no cover - fallback for standalone execution
    from modules.gui.interfaces.analysis_module import IAnalysisModule

# 導入通用詳細圈速分析模組
try:
    from .driverlap_analysis_mdi import driverLapAnalysisMDI
except ImportError:  # pragma: no cover - fallback when package not installed
    from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi import (
        driverLapAnalysisMDI,
    )


class driverLapAnalysisModule(IAnalysisModule):
    """
    Detailed Lap Analysis Module Main Class - Implements IAnalysisModule Interface
    
    Provides consistent interface with telemetry analysis module to ensure
    seamless integration with existing PopoutSubWindow system.
    """
    
    def __init__(self, parent=None, year=None, race=None, session=None, driver=None):
        """Initialize detailed lap analysis module"""
        super().__init__(parent)
        
        # Module basic information
        self._module_name = "detailed_laptime_analysis"
        self._display_name = "⏱️ Detailed Lap Analysis"
        self._version = "2.0.0"
        self._description = "F1 Detailed Lap Time Analysis Module - Lap trends, smart markers and tire strategy timeline"
        
        # 狀態追蹤
        self._is_initialized = False
        
        # 參數存儲
        self.current_year = str(year) if year else "2025"
        self.current_race = race if race else "Japan"
        self.current_session = session if session else "R"
        self.current_driver = driver if driver else None
        
        # 組件實例
        self._detailed_laptime_analysis_core = None
        self._main_widget: Optional[QWidget] = None
        self._data_loader = None
        
        # 參數提供者 (由外部設置)
        self.parameter_provider = None
        
    # 實現抽象屬性
    @property
    def module_name(self) -> str:
        """返回模組名稱"""
        return self._module_name
        
    @property 
    def display_name(self) -> str:
        """返回顯示名稱"""
        return self._display_name
        
    @property
    def version(self) -> str:
        """返回模組版本"""
        return self._version
        
    @property
    def description(self) -> str:
        """返回模組描述"""
        return self._description
        
    # 實現抽象方法
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組"""
        try:
            logger.debug(f"[LAPTIME_MODULE] 開始初始化詳細圈速分析模組...")
            
            if self._is_initialized:
                logger.debug(f"ℹ️ [LAPTIME_MODULE] 模組已經初始化，跳過重複初始化")
                return True
            
            # 初始化 MDI 數據管理器
            if not self._detailed_laptime_analysis_core:
                logger.debug(f"🔧 [LAPTIME_MODULE] 創建 MDI 實例...")
                self._detailed_laptime_analysis_core = driverLapAnalysisMDI(parent=parent_widget)
                
                # ✅ 啟用 Workspace 模式（防止 initialize_module() 觸發數據載入）
                if hasattr(self._detailed_laptime_analysis_core, '_workspace_loading_mode'):
                    self._detailed_laptime_analysis_core._workspace_loading_mode = True
                    logger.debug(f"🔧 [LAPTIME_MODULE] Workspace 模式已啟用")
                
                # ✅ 只設置參數屬性，不調用 update_parameters()（避免啟動執行緒）
                # 模仿 Rain Analysis 的安全模式
                if hasattr(self._detailed_laptime_analysis_core, 'current_year'):
                    self._detailed_laptime_analysis_core.current_year = str(self.current_year)
                if hasattr(self._detailed_laptime_analysis_core, 'current_race'):
                    self._detailed_laptime_analysis_core.current_race = self.current_race
                if hasattr(self._detailed_laptime_analysis_core, 'current_session'):
                    self._detailed_laptime_analysis_core.current_session = self.current_session
                logger.debug(f"🔧 [LAPTIME_MODULE] 參數已設置（未觸發數據載入）: {self.current_year} {self.current_race} {self.current_session}")
                
                # ✅ 禁用 Workspace 模式（恢復正常）
                if hasattr(self._detailed_laptime_analysis_core, '_workspace_loading_mode'):
                    self._detailed_laptime_analysis_core._workspace_loading_mode = False
                    logger.debug(f"🔧 [LAPTIME_MODULE] Workspace 模式已禁用")
            
            # 創建主要 Widget
            if not self._main_widget:
                # ✅ 修復：應該獲取 MDI 的內部 Widget，不是 MDI 對象本身
                if hasattr(self._detailed_laptime_analysis_core, 'get_widget'):
                    self._main_widget = self._detailed_laptime_analysis_core.get_widget()
                else:
                    # 回退：直接使用 MDI 的 main_widget 屬性
                    self._main_widget = getattr(self._detailed_laptime_analysis_core, 'main_widget', self._detailed_laptime_analysis_core)
                logger.debug(f"🔧 [LAPTIME_MODULE] Widget 已創建: {type(self._main_widget)}")
            
            self._is_initialized = True
            logger.info(f"[LAPTIME_MODULE] 模組已初始化")
            return True
            
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 初始化失敗: {e}")
            return False
        
    def get_widget(self):
        """返回模組的主要 Widget"""
        if not self._main_widget:
            self.initialize_module()
        return self._main_widget
        
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """更新分析參數"""
        try:
            logger.debug(f"[LAPTIME_MODULE] update_parameters 被調用: {year}, {race}, {session}")
            
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # 更新內部實例的參數
            if self._detailed_laptime_analysis_core and hasattr(self._detailed_laptime_analysis_core, 'update_parameters'):
                success = self._detailed_laptime_analysis_core.update_parameters(
                    str(year), race, session
                )
                if success:
                    logger.info(f"[LAPTIME_MODULE] 參數更新成功")
                    return True
                else:
                    logger.warning(f"[LAPTIME_MODULE] MDI 參數更新失敗")
            else:
                logger.warning(f"[LAPTIME_MODULE] MDI 實例不存在或沒有 update_parameters 方法")
            
            return False
            
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] update_parameters 錯誤: {e}")
            return False
        
    def load_data(self, **kwargs) -> bool:
        """載入分析數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.load_data(**kwargs)
            return False
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 載入數據失敗: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        try:
            if self._detailed_laptime_analysis_core:
                self._detailed_laptime_analysis_core.refresh_analysis()
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 重新執行分析失敗: {e}")
    
    def clear_data(self) -> None:
        """清除所有數據"""
        try:
            if self._detailed_laptime_analysis_core:
                self._detailed_laptime_analysis_core.clear_data()
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 清除數據失敗: {e}")
    
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出分析數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.export_data(export_path, export_format)
            return False
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 匯出數據失敗: {e}")
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前分析數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.get_current_data()
            return None
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 獲取當前數據失敗: {e}")
            return None
        
    # 支援方法（保持與原版相容）
    def get_cache_key(self, year: int, race: str, session: str) -> str:
        """Generate cache key"""
        return f"Detailed Lap Analysis_{year}_{race}_{session}"
        
    def get_window_title(self, year: int, race: str, session: str) -> str:
        """Generate window title - 只顯示模組名稱"""
        from core.gui_i18n import tr, get_gui_language

        language = get_gui_language()
        if language == 'zh':
            return f"{tr('detailed_lap_analysis', '詳細圈速分析')}"
        else:
            return f"Detailed Lap Analysis"
        
    def is_data_available(self, year: int, race: str, session: str) -> bool:
        """Check if data is available"""
        try:
            if self._detailed_laptime_analysis_core:
                # Check if detailed lap analysis data is available
                has_data = self._detailed_laptime_analysis_core.check_data_availability(
                    year=str(year), race=race, session=session
                )
                if has_data:
                    self._debug(f"成功載入詳細圈速分析數據: {year} {race} {session}")
                    return True
                else:
                    self._debug(f"無法載入詳細圈速分析數據: {year} {race} {session}")
                    return False
            return False
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 檢查數據可用性失敗: {e}")
            return False
    
    def refresh_data(self) -> bool:
        """重新整理數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.refresh_data()
            return False
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 重新整理數據失敗: {e}")
            return False
    
    def cleanup(self):
        """清理資源"""
        try:
            if self._detailed_laptime_analysis_core:
                self._detailed_laptime_analysis_core.cleanup()
                self._detailed_laptime_analysis_core = None
            
            if self._main_widget:
                self._main_widget.deleteLater()
                self._main_widget = None
                
            self._is_initialized = False
            logger.info(f"[LAPTIME_MODULE] 模組清理完成")
        except Exception as e:
            logger.error(f"[LAPTIME_MODULE] 模組清理失敗: {e}")
    
    # 向後相容性方法
    def get_title(self) -> str:
        """獲取標題（向後相容）"""
        return self._display_name
    
    def get_default_size(self) -> tuple:
        """獲取預設尺寸"""
        return (1200, 800)
    
    def supports_driver_parameter(self) -> bool:
        """檢查是否支援車手參數"""
        return True
    
    def get_supported_sessions(self) -> list:
        """獲取支援的節次"""
        return ['R', 'Q', 'P1', 'P2', 'P3', 'SQ']  # 支援所有節次
    
    def get_analysis_capabilities(self) -> Dict[str, bool]:
        """獲取分析能力"""
        return {
            'detailed_laptime_trends': True,      # 詳細圈速趨勢
            'smart_markers': True,                # 智能標記
            'driver_comparison': True,            # 車手比較
            'tire_timeline': True,                # 輪胎時間軸
            'interactive_charts': True,           # 互動圖表
            'data_export': True,                  # 數據匯出
            'real_time_updates': False            # 即時更新
        }
    
    def get_required_cli_function(self) -> int:
        """獲取所需的 CLI 功能號"""
        return 28  # Function 28: 詳細圈速分析
    
    def validate_parameters(self, **kwargs) -> bool:
        """驗證參數"""
        required_params = ['year', 'race', 'session']
        return all(param in kwargs for param in required_params)
    
    # 輔助方法
    def _debug(self, message: str):
        """調試信息輸出"""
        logger.debug(f"[LAPTIME_MODULE] {message}")
    
    def _error(self, message: str):
        """錯誤信息輸出"""
        logger.error(f"[LAPTIME_MODULE] ❌ {message}")
    
    def _info(self, message: str):
        """資訊輸出"""
        logger.debug(f"[LAPTIME_MODULE] ℹ️ {message}")


def create_detailed_laptime_analysis_module(parent=None, **kwargs) -> driverLapAnalysisModule:
    """
    工廠函數：創建詳細圈速分析模組實例
    
    Args:
        parent: 父對象
        **kwargs: 其他參數
        
    Returns:
        driverLapAnalysisModule: 詳細圈速分析模組實例
    """
    return driverLapAnalysisModule(parent=parent, **kwargs)


# 模組註冊資訊
MODULE_INFO = {
    'name': 'detailed_laptime_analysis',
    'display_name': '⏱️ Detailed Lap Analysis',
    'version': '2.0.0',
    'description': 'F1 Detailed Lap Time Analysis Module',
    'author': 'F1T Team',
    'category': 'telemetry',
    'cli_function': 28,
    'supports_driver_selection': True,
    'supports_session_types': ['R', 'Q', 'P1', 'P2', 'P3', 'SQ'],
    'data_types': ['detailed_laptime', 'smart_markers', 'tire_timeline'],
    'chart_types': ['line_chart', 'timeline', 'interactive']
}


# 預設導出
__all__ = [
    'driverLapAnalysisModule',
    'driverLapAnalysisModuleAdapter',
    'create_detailed_laptime_analysis_module',
    'MODULE_INFO'
]


# ============================================================================
# Adapter 類別（模仿 Rain Analysis）
# ============================================================================

class driverLapAnalysisModuleAdapter(driverLapAnalysisModule):
    """
    詳細圈速分析模組適配器
    
    為了與主 GUI 的工廠模式和 Workspace 系統兼容而提供的適配器類別。
    完全模仿 RainAnalysisModuleAdapter 的三層隔離架構。
    
    架構模式：
        Adapter → Module → MDI (UniversalAnalysisMDI)
        
    安全特性：
        - 只接受參數並傳遞給父類
        - 不調用 update_parameters()（避免執行緒啟動）
        - 適用於 Workspace 快速重建場景
    """
    
    def __init__(self, parent=None, **kwargs):
        """
        初始化適配器
        
        Args:
            parent: 父級 QObject
            **kwargs: 關鍵字參數，支援：
                - year: 賽季年份
                - race: 賽事名稱
                - session: 賽段類型
                - driver: 車手代碼（可選）
        """
        # 提取工廠模式可能傳遞的參數
        year = kwargs.get('year')
        race = kwargs.get('race')
        session = kwargs.get('session')
        driver = kwargs.get('driver')
        
        # 呼叫父類建構函數
        super().__init__(parent, year, race, session, driver)
        
        # 適配器特定設定
        self.adapter_version = "1.0.0"
        
        logger.info(f"[LAPTIME_ADAPTER] driverLapAnalysisModuleAdapter 初始化完成")


if __name__ == "__main__":
    """測試用例"""
    logger.debug("詳細圈速分析模組測試")
    
    # 創建模組實例
    module = create_detailed_laptime_analysis_module()
    
    # 測試基本功能
    logger.debug(f"模組名稱: {module.display_name}")
    logger.debug(f"版本: {module.version}")
    logger.debug(f"描述: {module.description}")
    logger.debug(f"CLI 功能: {module.get_required_cli_function()}")
    logger.debug(f"分析能力: {module.get_analysis_capabilities()}")
    logger.debug(f"支援節次: {module.get_supported_sessions()}")
    
    # 測試參數驗證
    test_params = {'year': 2025, 'race': 'Japan', 'session': 'R'}
    is_valid = module.validate_parameters(**test_params)
    logger.debug(f"參數驗證結果: {is_valid}")
    
    # 清理
    module.cleanup()
    
    logger.debug("詳細圈速分析模組測試完成")
