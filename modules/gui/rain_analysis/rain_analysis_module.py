#!/usr/bin/env python3
"""
RainAnalysisModule - F1T 下雨分析模組
=====================================

基於通用架構的下雨分析模組，提供完整的天氣數據分析功能。

功能特色：
- 降雨狀態分析（有雨/無雨）
- 溫度變化追蹤（氣溫、賽道溫度）
- 濕度和風速監測
- 氣壓變化分析
- 多種圖表類型支援
- 實時數據更新

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

# 導入通用下雨分析模組
try:
    from .rain_analysis_mdi import RainAnalysisUniversal
except ImportError:
    from modules.gui.rain_analysis.rain_analysis_mdi import RainAnalysisUniversal


class RainAnalysisModule(RainAnalysisUniversal):
    """
    下雨分析模組主類
    
    這是下雨分析模組的主要入口點，
    繼承自通用下雨分析類別，提供標準化的介面。
    """
    
    def __init__(self, parent=None, year=None, race=None, session=None):
        """初始化下雨分析模組"""
        super().__init__(parent)
        
        # 模組特定設定
        self.module_version = "1.0.0"
        
        # 賽事參數
        self.year = year
        self.race = race
        self.session = session
        
        # 初始化模組（創建 UI 組件）
        init_success = self.initialize_module(parent)
        if not init_success:
            self._debug("模組初始化失敗")
        
        # 如果提供了賽事參數，自動載入數據
        if year and race and session:
            self.load_race_data(year, race, session)
        
        # 初始化完成標記
        self.initialization_completed = True
        
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
        return "rain"
        
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
                file_path = f"rain_analysis_export_{timestamp}.json"
                
            # 執行匯出（這裡可以擴展為不同格式）
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            self._debug(f"數據已匯出至: {file_path}")
            return True
            
        except Exception as e:
            self._debug(f"匯出數據失敗: {str(e)}")
            return False


# 便利函數
def create_rain_analysis_module(parent=None) -> RainAnalysisModule:
    """
    創建下雨分析模組實例
    
    Args:
        parent: 父級 QObject
        
    Returns:
        RainAnalysisModule: 下雨分析模組實例
    """
    return RainAnalysisModule(parent)


def get_module_info() -> Dict[str, Any]:
    """
    獲取模組信息（靜態方法）
    
    Returns:
        Dict[str, Any]: 模組信息字典
    """
    return {
        "name": "下雨分析模組",
        "class_name": "RainAnalysisModule",
        "type": "rain",
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
def test_rain_analysis_module():
    """測試下雨分析模組基本功能"""
    try:
        # 創建模組實例
        module = create_rain_analysis_module()
        
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


class RainAnalysisModuleAdapter(RainAnalysisModule):
    """
    下雨分析模組適配器
    
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
        
        self._debug(f"RainAnalysisModuleAdapter 初始化完成")


if __name__ == "__main__":
    # 模組測試
    test_rain_analysis_module()
