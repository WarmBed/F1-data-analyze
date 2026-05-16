#!/usr/bin/env python3
"""
TireAnalysisModule - F1T Tire Strategy Analysis Module
======================================================

Comprehensive tire strategy analysis module based on universal architecture.

Features:
- Tire compound strategy analysis (SOFT/MEDIUM/HARD)
- Stint time analysis and comparison
- Tire degradation curve tracking
- Optimal pit window calculation
- Horizontal bar chart visualization
- Calls CLI -f26 for data generation

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
from core.logger import get_logger

# 導入介面和基類
try:
    from modules.gui.interfaces.analysis_module import IAnalysisModule
except ImportError:
    from modules.gui.interfaces.analysis_module import IAnalysisModule

# 導入通用輪胎策略分析模組
try:
    from .tire_analysis_mdi import TireAnalysisUniversal
except ImportError:
    from modules.gui.tire_analysis.tire_analysis_mdi import TireAnalysisUniversal


logger = get_logger("tire_analysis_module", component="gui")


class TireAnalysisModule(IAnalysisModule):
    """
    Tire Strategy Analysis Module Main Class - Implements IAnalysisModule Interface
    
    Provides consistent interface with telemetry analysis module to ensure
    seamless integration with existing PopoutSubWindow system.
    """
    
    def __init__(self, parent=None, year=None, race=None, session=None, driver=None):
        """Initialize tire strategy analysis module"""
        super().__init__(parent)
        
        # ✅ 添加 analysis_type 屬性以支援批次更新
        self.analysis_type = 'tire'
        
        # Module basic information
        self._module_name = "TireAnalysis"
        self._display_name = "🛞 Tire Strategy Analysis"
        self._version = "1.0.0"
        self._description = "F1 Race Tire Strategy Analysis Module"
        
        # Parameters
        self.current_year = str(year) if year else None
        self.current_race = race
        self.current_session = session
        self.current_driver = driver  # Added driver parameter
        
        # Sync settings
        self.sync_enabled = True
        
        # UI components
        self._main_widget = None
        self._is_initialized = False
        
        # Create internal universal tire strategy analysis instance
        self._tire_analysis_core = None
        
        # Initialize module (create UI components)
        init_success = self.initialize_module(parent)
        if not init_success:
            self._debug("Module initialization failed")
        
        # Initialization complete flag
        self._is_initialized = True
    
    # ===== Implement IAnalysisModule Abstract Methods =====
    
    @property
    def module_name(self) -> str:
        """Return module name"""
        return self._module_name
        
    @property 
    def display_name(self) -> str:
        """Return display name (for UI)"""
        return self._display_name
        
    @property
    def version(self) -> str:
        """Return module version"""
        return self._version
        
    @property
    def description(self) -> str:
        """Return module description"""
        return self._description
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """Initialize module"""
        try:
            if parent_widget:
                self._parent_widget = parent_widget
            
            # Create internal universal tire strategy analysis instance
            if not self._tire_analysis_core:
                self._tire_analysis_core = TireAnalysisUniversal(parent_widget)
            
            # Create main Widget
            if not self._main_widget:
                self._main_widget = self._tire_analysis_core.get_widget()
            
            self._is_initialized = True
            logger.info("✅ [tire_MODULE] Module initialized")
            return True
            
        except Exception as e:
            logger.exception("❌ [tire_MODULE] Initialization failed: %s", e)
            return False
        
    def get_widget(self):
        """Return module's main Widget"""
        if not self._main_widget:
            self.initialize_module()
        return self._main_widget
        
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """Update analysis parameters"""
        try:
            logger.info("🔄 [tire_MODULE] update_parameters called: %s, %s, %s", year, race, session)
            
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            
            # Update internal instance parameters
            if self._tire_analysis_core:
                success = self._tire_analysis_core.update_analysis_parameters(
                    year=str(year), race=race, session=session
                )
                if success is False:
                    logger.warning("Parameter update failed in core module")
                    return False
                logger.info("[tire_MODULE] Parameters updated successfully")
                return True
            
            logger.warning("⚠️ [tire_MODULE] Parameter update failed")
            return False
            
        except Exception as e:
            logger.exception("❌ [tire_MODULE] Parameter update error: %s", e)
            return False
            
    def validate_parameters(self, year: int, race: str, session: str) -> bool:
        """Validate analysis parameters"""
        if not year or year < 2018 or year > 2030:
            return False
        if not race or not isinstance(race, str):
            return False
        if session not in ['FP1', 'FP2', 'FP3', 'Q', 'R', 'S']:
            return False
        return True
        
    def get_title(self) -> str:
        """Return module title"""
        year = self.current_year or "2025"
        race = self.current_race or "Unknown"
        session = self.current_session or "R"
        return f"Tire Strategy Analysis_{year}_{race}_{session}"
    
    def get_window_title(self, year: str, race: str, session: str) -> str:
        """Generate window title - 只顯示模組名稱"""
        from core.gui_i18n import tr, get_gui_language
        language = get_gui_language()
        if language == 'zh':
            return f"{tr('tire_strategy_analysis')}"
        else:
            return f"Tire Strategy Analysis"
    
    def get_default_size(self):
        """Get default window size"""
        return (1400, 900)  # Consistent with universal configuration
        
    def load_race_data(self, year, race, session):
        """Load race data for specific event"""
        try:
            self._debug(f"Loading race data: {year} {race} {session}")
            
            # Check if data manager is initialized
            if hasattr(self, 'data_manager') and self.data_manager is not None:
                success = self.data_manager.load_data(year=year, race=race, session=session)
                
                if success:
                    self._debug(f"Successfully loaded tire strategy analysis data: {year} {race} {session}")
                    # Update UI parameters
                    self.update_parameters(str(year), race, session)
                else:
                    self._debug(f"Failed to load tire strategy analysis data: {year} {race} {session}")
            else:
                self._debug("Data manager not yet initialized, will defer data loading")
                # Save parameters for later loading
                self._pending_load_params = (year, race, session)
            
        except Exception as e:
            self._debug(f"Error occurred while loading race data: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # get_widget method provided by base class, directly returns self.main_widget
        
    def get_display_name(self) -> str:
        """Get module display name"""
        return "Tire Analysis"
        
    def get_module_type(self) -> str:
        """Get module type"""
        return "tire"
        
    def is_ready(self) -> bool:
        """Check if module is ready"""
        return (hasattr(self, 'initialization_completed') and 
                self.initialization_completed and
                self.data_manager is not None)
                
    def cleanup(self):
        """
        Clean up module resources - IAnalysisModule required method
        
        Properly cleans up API workers to prevent QThread crash.
        """
        try:
            # Clean up core analysis component and its API worker
            if hasattr(self, '_tire_analysis_core') and self._tire_analysis_core:
                # Try to stop any ongoing operations
                if hasattr(self._tire_analysis_core, 'stop_loading'):
                    self._tire_analysis_core.stop_loading()
                
                # Clean up data_manager's API worker (critical!)
                if hasattr(self._tire_analysis_core, 'data_manager'):
                    core_manager = self._tire_analysis_core.data_manager
                    if core_manager:
                        # Call _cleanup_api_worker directly with sync_wait
                        if hasattr(core_manager, '_cleanup_api_worker'):
                            core_manager._cleanup_api_worker(sync_wait=True)
                        elif hasattr(core_manager, 'cleanup'):
                            core_manager.cleanup()
                
                # Try to clear cache
                if hasattr(self._tire_analysis_core, 'clear_cache'):
                    self._tire_analysis_core.clear_cache()
                
                self._tire_analysis_core = None
                
            # Clean up UI components
            if hasattr(self, '_main_widget') and self._main_widget:
                self._main_widget.deleteLater()
                self._main_widget = None
                
            self._debug("Tire analysis module cleanup completed")
            
        except Exception as e:
            self._debug(f"Error occurred during module cleanup: {str(e)}")
            
    def export_analysis_data(self, file_path: str = None) -> bool:
        """
        Export analysis data
        
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
                        logger.info("✅ [tire_MODULE] load_data 成功: %s %s %s", year, race, session)
                        self.data_loaded.emit({'year': year, 'race': race, 'session': session})
                        return True
            
            logger.warning("⚠️ [tire_MODULE] load_data 失敗")
            return False
            
        except Exception as e:
            logger.exception("❌ [tire_MODULE] load_data 錯誤: %s", e)
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        try:
            if self._tire_analysis_core and hasattr(self._tire_analysis_core, 'refresh_data'):
                self._tire_analysis_core.refresh_data()
                logger.info("✅ [tire_MODULE] refresh_analysis 完成")
            elif self.current_year and self.current_race and self.current_session:
                # 重新載入當前參數的數據
                self.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
                logger.info("✅ [tire_MODULE] refresh_analysis 通過重新載入完成")
            else:
                logger.warning("⚠️ [tire_MODULE] refresh_analysis 無法執行：缺少參數")
                
        except Exception as e:
            logger.exception("❌ [tire_MODULE] refresh_analysis 錯誤: %s", e)
    
    def clear_data(self) -> None:
        """清除所有數據"""
        try:
            if self._tire_analysis_core and hasattr(self._tire_analysis_core, 'clear_all_data'):
                self._tire_analysis_core.clear_all_data()
            
            # 重置參數
            self.current_year = None
            self.current_race = None
            self.current_session = None
            
            logger.info("✅ [tire_MODULE] clear_data 完成")
            
        except Exception as e:
            logger.exception("❌ [tire_MODULE] clear_data 錯誤: %s", e)
    
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
                logger.warning("⚠️ [tire_MODULE] 不支援的匯出格式: %s", export_format)
                return False
                
        except Exception as e:
            logger.exception("❌ [tire_MODULE] export_data 錯誤: %s", e)
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
            logger.exception("❌ [tire_MODULE] get_current_data 錯誤: %s", e)
            return None

    # ===== 輔助方法 =====
    
    def _debug(self, message: str):
        """調試訊息輸出"""
        logger.info("[tire_MODULE] %s", message)
        
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
        logger.info("模組名稱: %s", module.get_display_name())
        logger.info("模組類型: %s", module.get_module_type())
        logger.info("是否準備就緒: %s", module.is_ready())
        
        # 測試模組信息
        info = module.get_module_info()
        logger.info("支援的圖表類型: %s", info.get('chart_types', []))
        
        logger.info("下雨分析模組測試通過!")
        return True
        
    except Exception as e:
        logger.exception("下雨分析模組測試失敗: %s", str(e))
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
