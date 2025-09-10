#!/usr/bin/env python3
"""
TireAnalysisModule - F1T 輪胎策略分析模組
=======================================

基於通用架構的輪胎策略分析模組，提供完整的輪胎數據分析功能。

功能特色：
- 輪胎配方策略分析（SOFT/MEDIUM/HARD）
- Stint 時間分析和比較
- 輪胎衰退曲線追蹤
- 最佳換胎窗口計算
- 橫向長條圖視覺化
- 呼叫 CLI -f26 生成數據

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

# 導入介面和基類
try:
    from ..interfaces.analysis_module import IAnalysisModule
except ImportError:
    from modules.gui.interfaces.analysis_module import IAnalysisModule

# 導入通用輪胎策略分析模組
try:
    from .tire_analysis_mdi import TireAnalysisUniversal
except ImportError:
    from modules.gui.tire_analysis.tire_analysis_mdi import TireAnalysisUniversal


class TireAnalysisModule(IAnalysisModule):
    """
    輪胎策略分析模組主類 - 實現 IAnalysisModule 介面
    
    提供與遙測分析模組一致的介面，確保可以完美整合到
    現有的 PopoutSubWindow 系統中。
    """
    
    def __init__(self, parent=None, year=None, race=None, session=None, driver=None):
        """初始化輪胎策略分析模組"""
        super().__init__(parent)
        
        # 模組基本資訊
        self._module_name = "TireAnalysis"
        self._display_name = "🛞 輪胎策略分析"
        self._version = "1.0.0"
        self._description = "F1 比賽輪胎策略分析模組"
        
        # 參數
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        self.current_driver = driver  # 新增車手參數
        
        # 同步設定
        self.sync_enabled = True
        
        # UI 組件
        self._main_widget = None
        self._is_initialized = False
        
        # 創建內部的通用輪胎策略分析實例
        self._tire_analysis_core = None
        
        # 初始化模組（創建 UI 組件）
        init_success = self.initialize_module(parent)
        if not init_success:
            self._debug("模組初始化失敗")
        
        # 初始化完成標記
        self._is_initialized = True
    
    # ===== 實現 IAnalysisModule 抽象方法 =====
    
    @property
    def module_name(self) -> str:
        """返回模組名稱"""
        return self._module_name
        
    @property 
    def display_name(self) -> str:
        """返回顯示名稱 (用於UI)"""
        return self._display_name
        
    @property
    def version(self) -> str:
        """返回模組版本"""
        return self._version
        
    @property
    def description(self) -> str:
        """返回模組描述"""
        return self._description
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組"""
        try:
            if parent_widget:
                self._parent_widget = parent_widget
            
            # 創建內部的通用輪胎策略分析實例
            if not self._tire_analysis_core:
                self._tire_analysis_core = TireAnalysisUniversal(parent_widget)
            
            # 創建主要 Widget
            if not self._main_widget:
                self._main_widget = self._tire_analysis_core.get_widget()
            
            self._is_initialized = True
            print(f"✅ [tire_MODULE] 模組已初始化")
            return True
            
        except Exception as e:
            print(f"❌ [tire_MODULE] 初始化失敗: {e}")
            return False
        
    def get_widget(self):
        """返回模組的主要 Widget"""
        if not self._main_widget:
            self.initialize_module()
        return self._main_widget
        
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """更新分析參數"""
        try:
            print(f"🔄 [tire_MODULE] update_parameters 被調用: {year}, {race}, {session}")
            
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # 更新內部實例的參數
            if self._tire_analysis_core:
                success = self._tire_analysis_core.update_analysis_parameters(
                    year=str(year), race=race, session=session
                )
                if success:
                    print(f"✅ [tire_MODULE] 參數更新成功")
                    return True
            
            print(f"⚠️ [tire_MODULE] 參數更新失敗")
            return False
            
        except Exception as e:
            print(f"❌ [tire_MODULE] 參數更新錯誤: {e}")
            return False
            
    def validate_parameters(self, year: int, race: str, session: str) -> bool:
        """驗證分析參數"""
        if not year or year < 2018 or year > 2030:
            return False
        if not race or not isinstance(race, str):
            return False
        if session not in ['FP1', 'FP2', 'FP3', 'Q', 'R', 'S']:
            return False
        return True
        
    def get_title(self) -> str:
        """返回模組標題"""
        year = self.current_year or "2025"
        race = self.current_race or "Unknown"
        session = self.current_session or "R"
        return f"降雨分析_{year}_{race}_{session}"
    
    def get_window_title(self, year: str, race: str, session: str) -> str:
        """生成視窗標題"""
        return f"🌧️ 降雨分析_{year}_{race}_{session}"
    
    def get_default_size(self):
        """獲取預設視窗大小"""
        return (1400, 900)  # 與通用配置一致
        
    def load_race_data(self, year, race, session):
        """載入特定賽事的降雨數據"""
        try:
            self._debug(f"正在載入賽事數據: {year} {race} {session}")
            
            # 檢查數據管理器是否已初始化
            if hasattr(self, 'data_manager') and self.data_manager is not None:
                success = self.data_manager.load_data(year=year, race=race, session=session)
                
                if success:
                    self._debug(f"成功載入降雨分析數據: {year} {race} {session}")
                    # 更新 UI 參數
                    self.update_parameters(str(year), race, session)
                else:
                    self._debug(f"無法載入降雨分析數據: {year} {race} {session}")
            else:
                self._debug("數據管理器尚未初始化，將延遲載入數據")
                # 保存參數供後續載入
                self._pending_load_params = (year, race, session)
            
        except Exception as e:
            self._debug(f"載入賽事數據時發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # get_widget 方法由基類提供，直接返回 self.main_widget
        
    def get_display_name(self) -> str:
        """獲取模組顯示名稱"""
        return "下雨分析"
        
    def get_module_type(self) -> str:
        """獲取模組類型"""
        return "tire"
        
    def is_ready(self) -> bool:
        """檢查模組是否準備就緒"""
        return (hasattr(self, 'initialization_completed') and 
                self.initialization_completed and
                self.data_manager is not None)
                
    def cleanup(self):
        """清理模組資源"""
        try:
            # 停止任何執行中的操作
            if self.data_manager:
                self.data_manager.stop_loading()
                
            # 清理 UI 組件
            if hasattr(self, '_main_widget') and self._main_widget:
                self._main_widget.deleteLater()
                self._main_widget = None
                
            # 清理數據
            if self.data_manager:
                self.data_manager.clear_cache()
                
            self._debug("下雨分析模組清理完成")
            
        except Exception as e:
            self._debug(f"模組清理時發生錯誤: {str(e)}")
            
    def export_analysis_data(self, file_path: str = None) -> bool:
        """
        匯出分析數據
        
        Args:
            file_path: 匯出檔案路徑（可選）
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            if not self.data_manager or not self.data_manager.current_data:
                self._debug("沒有可匯出的數據")
                return False
                
            # 準備匯出數據
            export_data = {
                "module_info": self.get_module_info(),
                "analysis_summary": self.get_analysis_summary(),
                "chart_data": getattr(self.data_manager, 'charts_data', {}),
                "raw_data": self.data_manager.current_data
            }
            
            # 如果沒有指定路徑，使用預設路徑
            if not file_path:
                timestamp = self.get_current_timestamp().replace(":", "-")
                file_path = f"tire_analysis_export_{timestamp}.json"
                
            # 執行匯出（這裡可以擴展為不同格式）
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            self._debug(f"數據已匯出至: {file_path}")
            return True
            
        except Exception as e:
            self._debug(f"匯出數據失敗: {str(e)}")
            return False

    # ===== 實現缺少的抽象方法 =====
    
    def load_data(self, **kwargs) -> bool:
        """
        載入分析數據
        
        Args:
            **kwargs: 載入參數
            
        Returns:
            bool: 載入是否成功
        """
        try:
            if self._tire_analysis_core:
                # 從 kwargs 或當前參數獲取載入參數
                year = kwargs.get('year', self.current_year)
                race = kwargs.get('race', self.current_race)
                session = kwargs.get('session', self.current_session)
                
                if year and race and session:
                    success = self._tire_analysis_core.update_analysis_parameters(
                        year=str(year), race=race, session=session
                    )
                    if success:
                        print(f"✅ [tire_MODULE] load_data 成功: {year} {race} {session}")
                        self.data_loaded.emit({'year': year, 'race': race, 'session': session})
                        return True
            
            print(f"⚠️ [tire_MODULE] load_data 失敗")
            return False
            
        except Exception as e:
            print(f"❌ [tire_MODULE] load_data 錯誤: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        try:
            if self._tire_analysis_core and hasattr(self._tire_analysis_core, 'refresh_data'):
                self._tire_analysis_core.refresh_data()
                print(f"✅ [tire_MODULE] refresh_analysis 完成")
            elif self.current_year and self.current_race and self.current_session:
                # 重新載入當前參數的數據
                self.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
                print(f"✅ [tire_MODULE] refresh_analysis 通過重新載入完成")
            else:
                print(f"⚠️ [tire_MODULE] refresh_analysis 無法執行：缺少參數")
                
        except Exception as e:
            print(f"❌ [tire_MODULE] refresh_analysis 錯誤: {e}")
    
    def clear_data(self) -> None:
        """清除所有數據"""
        try:
            if self._tire_analysis_core and hasattr(self._tire_analysis_core, 'clear_all_data'):
                self._tire_analysis_core.clear_all_data()
            
            # 重置參數
            self.current_year = None
            self.current_race = None
            self.current_session = None
            
            print(f"✅ [tire_MODULE] clear_data 完成")
            
        except Exception as e:
            print(f"❌ [tire_MODULE] clear_data 錯誤: {e}")
    
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """
        匯出分析數據
        
        Args:
            export_path: 匯出路徑
            export_format: 匯出格式 ("json", "csv", "png" 等)
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            if export_format.lower() == "json":
                return self.export_analysis_data(export_path)
            else:
                print(f"⚠️ [tire_MODULE] 不支援的匯出格式: {export_format}")
                return False
                
        except Exception as e:
            print(f"❌ [tire_MODULE] export_data 錯誤: {e}")
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取當前分析數據
        
        Returns:
            Dict[str, Any]: 當前的分析數據，如果沒有數據則返回 None
        """
        try:
            if self._tire_analysis_core and hasattr(self._tire_analysis_core, 'get_analysis_data'):
                return self._tire_analysis_core.get_analysis_data()
            
            # 如果沒有核心數據，返回基本信息
            if self.current_year and self.current_race and self.current_session:
                return {
                    'year': self.current_year,
                    'race': self.current_race,
                    'session': self.current_session,
                    'module_type': 'tire_analysis',
                    'timestamp': self.get_current_timestamp() if hasattr(self, 'get_current_timestamp') else None
                }
            
            return None
            
        except Exception as e:
            print(f"❌ [tire_MODULE] get_current_data 錯誤: {e}")
            return None

    # ===== 輔助方法 =====
    
    def _debug(self, message: str):
        """調試訊息輸出"""
        print(f"[tire_MODULE] {message}")
        
    def get_current_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# 便利函數
def create_tire_analysis_module(parent=None) -> TireAnalysisModule:
    """
    創建輪胎策略分析模組實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        TireAnalysisModule: 輪胎策略分析模組實例
    """
    return TireAnalysisModule(parent)


def get_module_info() -> Dict[str, Any]:
    """
    獲取模組信息（靜態方法）
    
    Returns:
        Dict[str, Any]: 模組信息字典
    """
    return {
        "name": "下雨分析模組",
        "class_name": "tireAnalysisModule",
        "type": "tire",
        "version": "1.0.0",
        "description": "F1 比賽降雨天氣分析模組，支援多種天氣數據的視覺化和分析",
        "author": "F1T Team",
        "date": "2025-09-10",
        "supported_data_formats": ["JSON", "CSV"],
        "supported_chart_types": [
            "雙Y軸折線圖 (降雨+氣溫)",
            "溫度對比圖 (氣溫vs賽道溫度)",
            "濕度風速圖 (濕度+風速)",
            "氣壓變化圖"
        ],
        "features": [
            "降雨狀態分析",
            "溫度變化追蹤",
            "濕度監測",
            "風速分析",
            "氣壓變化",
            "數據匯出功能",
            "即時圖表更新"
        ],
        "dependencies": [
            "PyQt5",
            "modules.gui.base.universal_analysis_mdi_base",
            "modules.gui.base.universal_data_loader_base", 
            "modules.gui.base.universal_chart_widget_base"
        ]
    }


# 模組測試函數
def test_tire_analysis_module():
    """測試下雨分析模組基本功能"""
    try:
        # 創建模組實例
        module = create_tire_analysis_module()
        
        # 測試基本屬性
        print(f"模組名稱: {module.get_display_name()}")
        print(f"模組類型: {module.get_module_type()}")
        print(f"是否準備就緒: {module.is_ready()}")
        
        # 測試模組信息
        info = module.get_module_info()
        print(f"支援的圖表類型: {info.get('chart_types', [])}")
        
        print("下雨分析模組測試通過!")
        return True
        
    except Exception as e:
        print(f"下雨分析模組測試失敗: {str(e)}")
        return False


class TireAnalysisModuleAdapter(TireAnalysisModule):
    """
    輪胎策略分析模組適配器
    
    為了與主 GUI 的工廠模式兼容而提供的適配器類別
    """
    
    def __init__(self, parent=None, **kwargs):
        """初始化適配器"""
        # 提取工廠模式可能傳遞的參數
        year = kwargs.get('year')
        race = kwargs.get('race') 
        session = kwargs.get('session')
        
        # 呼叫父類建構函數
        super().__init__(parent, year, race, session)
        
        # 適配器特定設定
        self.adapter_version = "1.0.0"
        
        self._debug(f"TireAnalysisModuleAdapter 初始化完成")


if __name__ == "__main__":
    # 模組測試
    test_tire_analysis_module()
