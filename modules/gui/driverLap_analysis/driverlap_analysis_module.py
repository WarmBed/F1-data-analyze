#!/usr/bin/env python3
"""
driverLapAnalysisModule - F1T 詳細圈速分析模組
=======================================

基於通用架構的詳細圈速分析模組，提供完整的圈速數據分析功能。

功能特色：
- 詳細圈速趨勢分析（每圈秒數顯示）
- 車手選擇控制區（最多5位車手同時比較）
- 智能標記系統（事故A、降雨R、進站P、最快圈F等）
- 輪胎策略時間軸（底部顯示各車手輪胎使用情況）
- 折線圖視覺化分析
- 呼叫 CLI -f28 生成數據

Author: F1T Team
Date: 2025-09-12
Version: 2.0.0 (詳細圈速分析版本)
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

# 導入介面和基類
try:
    from ..interfaces.analysis_module import IAnalysisModule
except ImportError:
    from modules.gui.interfaces.analysis_module import IAnalysisModule

# 導入通用詳細圈速分析模組
try:
    from .driverlap_analysis_mdi import driverLapAnalysisMDI
except ImportError:
    from modules.gui.driverLap_analysis.driverlap_analysis_mdi import driverLapAnalysisMDI


class driverLapAnalysisModule(IAnalysisModule):
    """
    詳細圈速分析模組主類 - 實現 IAnalysisModule 介面
    
    提供與遙測分析模組一致的介面，確保可以完美整合到
    現有的 PopoutSubWindow 系統中。
    """
    
    def __init__(self, parent=None, year=None, race=None, session=None, driver=None):
        """初始化詳細圈速分析模組"""
        super().__init__(parent)
        
        # 模組基本資訊
        self._module_name = "detailed_laptime_analysis"
        self._display_name = "⏱️ 詳細圈速分析"
        self._version = "2.0.0"
        self._description = "F1 比賽詳細圈速分析模組，提供圈速趨勢分析、智能標記和輪胎策略時間軸"
        
        # 狀態追蹤
        self._is_initialized = False
        
        # 參數存儲
        self.current_year = str(year) if year else "2025"
        self.current_race = race if race else "Japan"
        self.current_session = session if session else "R"
        self.current_driver = driver if driver else None
        
        # 組件實例
        self._detailed_laptime_analysis_core = None
        self._main_widget = None
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
            print(f"🚀 [LAPTIME_MODULE] 開始初始化詳細圈速分析模組...")
            
            if self._is_initialized:
                print(f"ℹ️ [LAPTIME_MODULE] 模組已經初始化，跳過重複初始化")
                return True
            
            # 初始化 MDI 數據管理器
            if not self._detailed_laptime_analysis_core:
                print(f"🔧 [LAPTIME_MODULE] 創建 MDI 實例...")
                self._detailed_laptime_analysis_core = driverLapAnalysisMDI(parent=parent_widget)
                
                # 設置初始參數
                if hasattr(self._detailed_laptime_analysis_core, 'update_parameters'):
                    print(f"🔧 [LAPTIME_MODULE] 設置初始參數: {self.current_year} {self.current_race} {self.current_session}")
                    self._detailed_laptime_analysis_core.update_parameters(
                        self.current_year, self.current_race, self.current_session
                    )
            
            # 創建主要 Widget
            if not self._main_widget:
                self._main_widget = self._detailed_laptime_analysis_core
            
            self._is_initialized = True
            print(f"✅ [LAPTIME_MODULE] 模組已初始化")
            return True
            
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 初始化失敗: {e}")
            return False
        
    def get_widget(self):
        """返回模組的主要 Widget"""
        if not self._main_widget:
            self.initialize_module()
        return self._main_widget
        
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """更新分析參數"""
        try:
            print(f"🔄 [LAPTIME_MODULE] update_parameters 被調用: {year}, {race}, {session}")
            
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # 更新內部實例的參數
            if self._detailed_laptime_analysis_core and hasattr(self._detailed_laptime_analysis_core, 'update_parameters'):
                success = self._detailed_laptime_analysis_core.update_parameters(
                    str(year), race, session
                )
                if success:
                    print(f"✅ [LAPTIME_MODULE] 參數更新成功")
                    return True
                else:
                    print(f"⚠️ [LAPTIME_MODULE] MDI 參數更新失敗")
            else:
                print(f"⚠️ [LAPTIME_MODULE] MDI 實例不存在或沒有 update_parameters 方法")
            
            return False
            
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] update_parameters 錯誤: {e}")
            return False
        
    def load_data(self, **kwargs) -> bool:
        """載入分析數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.load_data(**kwargs)
            return False
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 載入數據失敗: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        try:
            if self._detailed_laptime_analysis_core:
                self._detailed_laptime_analysis_core.refresh_analysis()
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 重新執行分析失敗: {e}")
    
    def clear_data(self) -> None:
        """清除所有數據"""
        try:
            if self._detailed_laptime_analysis_core:
                self._detailed_laptime_analysis_core.clear_data()
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 清除數據失敗: {e}")
    
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出分析數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.export_data(export_path, export_format)
            return False
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 匯出數據失敗: {e}")
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前分析數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.get_current_data()
            return None
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 獲取當前數據失敗: {e}")
            return None
        
    # 支援方法（保持與原版相容）
    def get_cache_key(self, year: int, race: str, session: str) -> str:
        """生成快取鍵值"""
        return f"詳細圈速分析_{year}_{race}_{session}"
        
    def get_window_title(self, year: int, race: str, session: str) -> str:
        """生成視窗標題"""
        return f"詳細圈速分析_{year}_{race}_{session}"
        
    def is_data_available(self, year: int, race: str, session: str) -> bool:
        """檢查數據是否可用"""
        try:
            if self._detailed_laptime_analysis_core:
                # 檢查是否有相關的詳細圈速分析數據
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
            print(f"❌ [LAPTIME_MODULE] 檢查數據可用性失敗: {e}")
            return False
    
    def refresh_data(self) -> bool:
        """重新整理數據"""
        try:
            if self._detailed_laptime_analysis_core:
                return self._detailed_laptime_analysis_core.refresh_data()
            return False
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 重新整理數據失敗: {e}")
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
            print(f"✅ [LAPTIME_MODULE] 模組清理完成")
        except Exception as e:
            print(f"❌ [LAPTIME_MODULE] 模組清理失敗: {e}")
    
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
        print(f"[LAPTIME_MODULE] {message}")
    
    def _error(self, message: str):
        """錯誤信息輸出"""
        print(f"[LAPTIME_MODULE] ❌ {message}")
    
    def _info(self, message: str):
        """資訊輸出"""
        print(f"[LAPTIME_MODULE] ℹ️ {message}")


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
    'display_name': '⏱️ 詳細圈速分析',
    'version': '2.0.0',
    'description': 'F1 比賽詳細圈速分析模組',
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
    'create_detailed_laptime_analysis_module',
    'MODULE_INFO'
]


if __name__ == "__main__":
    """測試用例"""
    print("詳細圈速分析模組測試")
    
    # 創建模組實例
    module = create_detailed_laptime_analysis_module()
    
    # 測試基本功能
    print(f"模組名稱: {module.display_name}")
    print(f"版本: {module.version}")
    print(f"描述: {module.description}")
    print(f"CLI 功能: {module.get_required_cli_function()}")
    print(f"分析能力: {module.get_analysis_capabilities()}")
    print(f"支援節次: {module.get_supported_sessions()}")
    
    # 測試參數驗證
    test_params = {'year': 2025, 'race': 'Japan', 'session': 'R'}
    is_valid = module.validate_parameters(**test_params)
    print(f"參數驗證結果: {is_valid}")
    
    # 清理
    module.cleanup()
    
    print("詳細圈速分析模組測試完成")
