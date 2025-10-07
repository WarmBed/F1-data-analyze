"""
IAnalysisModule - F1T 分析模組標準介面
========================================

這個模組定義了所有 F1T 分析模組必須實現的標準介面，
確保所有模組都能與現有的 PopoutSubWindow 系統完美整合。

設計原則：
1. 與現有 PopoutSubWindow 架構完全兼容
2. 支援同步/非同步參數模式 
3. 統一的信號管理機制
4. 標準化的錯誤處理

Author: F1T Team
Date: 2025-08-28
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from PyQt5.QtCore import QObject, pyqtSignal, QMetaObject


class AnalysisModuleMeta(type(QObject), type(ABC)):
    """解決 QObject 和 ABC 的 metaclass 衝突"""
    pass


class IAnalysisModule(QObject, ABC, metaclass=AnalysisModuleMeta):
    """
    F1T 分析模組標準介面
    
    所有分析模組都必須繼承這個介面，以確保能夠與現有的
    PopoutSubWindow 系統完美整合。
    """
    
    # 標準信號定義 (與現有 PopoutSubWindow 兼容)
    module_error = pyqtSignal(str)  # 錯誤信號
    parameters_updated = pyqtSignal(dict)  # 參數更新信號
    data_loaded = pyqtSignal(dict)  # 數據載入完成信號
    analysis_completed = pyqtSignal(dict)  # 分析完成信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._module_name = self.__class__.__name__
        self._version = "1.0.0"
        self._is_initialized = False
        
    @property
    @abstractmethod
    def module_name(self) -> str:
        """返回模組名稱"""
        pass
        
    @property 
    @abstractmethod
    def display_name(self) -> str:
        """返回顯示名稱 (用於UI)"""
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        """返回模組版本"""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """返回模組描述"""
        pass
        
    @abstractmethod
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            parent_widget: 父級 widget (通常是 PopoutSubWindow)
            **kwargs: 額外的初始化參數
            
        Returns:
            bool: 初始化是否成功
        """
        pass
        
    @abstractmethod
    def get_widget(self):
        """
        返回模組的主要 Widget
        
        這個 Widget 將被嵌入到 PopoutSubWindow 中
        
        Returns:
            QWidget: 模組的主要界面 Widget
        """
        pass
        
    @abstractmethod
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """
        更新分析參數
        
        當 PopoutSubWindow 的參數提供者更新時會調用此方法
        
        Args:
            year: 年份
            race: 賽事名稱  
            session: 賽段 (FP1, FP2, FP3, Q, R, S)
            
        Returns:
            bool: 參數更新是否成功
        """
        pass
        
    @abstractmethod
    def load_data(self, **kwargs) -> bool:
        """
        載入分析數據
        
        Args:
            **kwargs: 載入參數
            
        Returns:
            bool: 載入是否成功
        """
        pass
        
    @abstractmethod
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        pass
        
    @abstractmethod
    def clear_data(self) -> None:
        """清除所有數據"""
        pass
        
    @abstractmethod
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """
        匯出分析數據
        
        Args:
            export_path: 匯出路徑
            export_format: 匯出格式 ("json", "csv", "png" 等)
            
        Returns:
            bool: 匯出是否成功
        """
        pass
        
    @abstractmethod
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        獲取當前分析數據
        
        Returns:
            Dict[str, Any]: 當前的分析數據，如果沒有數據則返回 None
        """
        pass
    
    def set_statistics_visibility(self, visible: bool) -> bool:
        """
        設置統計面板顯示狀態 (可選實現)
        
        子類可以選擇實現此方法來支援統計面板的顯示/隱藏控制
        
        Args:
            visible: True=顯示統計面板, False=隱藏統計面板
            
        Returns:
            bool: 操作是否成功
        """
        # 預設實現：查找圖表組件並嘗試設置統計面板顯示狀態
        try:
            widget = self.get_widget()
            if hasattr(widget, 'set_statistics_visibility'):
                return widget.set_statistics_visibility(visible)
            
            # 如果主 widget 沒有統計面板控制方法，嘗試查找子組件
            for child in widget.findChildren(QObject):
                if hasattr(child, 'set_statistics_visibility'):
                    return child.set_statistics_visibility(visible)
            
            print(f"[ANALYSIS_MODULE] ⚠️ {self.display_name} 不支援統計面板控制")
            return False
            
        except Exception as e:
            print(f"[ERROR] [ANALYSIS_MODULE] 設置統計面板顯示狀態失敗: {e}")
            return False
        
    def validate_parameters(self, year: int, race: str, session: str) -> bool:
        """
        驗證參數有效性
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段
            
        Returns:
            bool: 參數是否有效
        """
        try:
            # 基本參數驗證
            if not (2018 <= year <= 2025):
                return False
            if not race or len(race.strip()) == 0:
                return False
            if session not in ['FP1', 'FP2', 'FP3', 'Q', 'R', 'S']:
                return False
            return True
        except Exception:
            return False
            
    def get_window_title(self, year: int, race: str, session: str) -> str:
        """
        生成視窗標題
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段
            
        Returns:
            str: 標準化的視窗標題
        """
        return f"{self.display_name}_{year}_{race}_{session}"
        
    def emit_error(self, error_message: str) -> None:
        """
        發出錯誤信號
        
        Args:
            error_message: 錯誤訊息
        """
        self.module_error.emit(f"[{self.module_name}] {error_message}")
        
    def emit_parameters_updated(self, parameters: Dict[str, Any]) -> None:
        """
        發出參數更新信號
        
        Args:
            parameters: 更新的參數
        """
        self.parameters_updated.emit(parameters)
        
    def is_initialized(self) -> bool:
        """返回模組是否已初始化"""
        return self._is_initialized
        
    def set_initialized(self, status: bool) -> None:
        """設置模組初始化狀態"""
        self._is_initialized = status


# ========== 模組管理基礎設施 ==========

class ModuleFactory:
    """模組工廠 - 負責創建和管理模組實例"""
    
    _registry = {}
    
    @classmethod
    def register_module(cls, module_type: str, module_class: type):
        """註冊模組類別"""
        cls._registry[module_type] = module_class
    
    @classmethod
    def create_module(cls, module_type: str, **kwargs) -> Optional['IAnalysisModule']:
        """創建模組實例"""
        module_class = cls._registry.get(module_type)
        if module_class:
            return module_class(**kwargs)
        return None
    
    @classmethod
    def get_available_modules(cls) -> List[str]:
        """獲取可用模組列表"""
        return list(cls._registry.keys())
    
    @classmethod
    def module_exists(cls, module_type: str) -> bool:
        """檢查模組是否存在"""
        return module_type in cls._registry


class ModuleTypes:
    """模組類型定義"""
    RAIN_ANALYSIS = "rain_analysis"                    # 雨天分析
    TELEMETRY_SPEED = "telemetry_speed"                # 遙測分析 - 速度分析
    TELEMETRY_BRAKE = "telemetry_brake"                # 遙測分析 - 煞車分析
    TELEMETRY_THROTTLE = "telemetry_throttle"          # 遙測分析 - 油門分析
    TELEMETRY_STEERING = "telemetry_steering"          # 遙測分析 - 方向盤分析
    TELEMETRY_RPM = "telemetry_rpm"                    # 遙測分析 - 轉速分析
    TELEMETRY_GEAR = "telemetry_gear"                  # 遙測分析 - 檔位分析
    TELEMETRY_ACCELERATION = "telemetry_acceleration"  # 遙測分析 - 加速度分析
    TELEMETRY_DISTANCEDIFF = "telemetry_distancediff"  # 遙測分析 - 距離差異分析
    TELEMETRY_SPEEDDIFF = "telemetry_speeddiff"        # 遙測分析 - 速度差異分析
    TELEMETRY_ANALYSIS = "telemetry_analysis"          # 遙測分析 - 綜合分析
    THROTTLE_BOX_PLOT = "throttle_box_plot"            # 油門箱型圖分析
    TRACK_MAP = "track_map"                            # 賽道地圖
    LAP_ANALYSIS = "lap_analysis"                      # 單圈分析
    PITSTOP_ANALYSIS = "pitstop_analysis"              # 進站分析
    STATISTICS = "statistics"                          # 統計分析
    ACCIDENT_ANALYSIS = "accident_analysis"            # 事故分析
    TRACK_ANALYSIS = "track_analysis"                  # 賽道分析
