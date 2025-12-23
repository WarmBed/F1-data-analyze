#!/usr/bin/env python3
"""
基礎分析模組介面 - 通用子模組視窗架構
Base Analysis Module Interface - Universal Sub-module Window Architecture
"""

from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, QObject
from typing import Dict, Any, Optional, List


class IAnalysisModule(ABC):
    """分析模組標準介面"""
    
    @abstractmethod
    def get_widget(self) -> QWidget:
        """返回模組的主要UI Widget"""
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """返回模組標題"""
        pass
    
    @abstractmethod
    def update_parameters(self, **params) -> bool:
        """更新分析參數"""
        pass
    
    @abstractmethod
    def supports_sync(self) -> bool:
        """是否支援主程式同步"""
        pass
    
    @abstractmethod
    def get_parameter_interface(self) -> Optional[QWidget]:
        """返回參數設定介面（用於設定對話框）"""
        pass
    
    @abstractmethod
    def get_default_size(self) -> tuple:
        """返回預設視窗大小 (width, height)"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理資源"""
        pass


class IParameterProvider(ABC):
    """參數提供者介面 - 用於從主程式獲取參數"""
    
    @abstractmethod
    def get_current_year(self) -> str:
        pass
    
    @abstractmethod  
    def get_current_race(self) -> str:
        pass
    
    @abstractmethod
    def get_current_session(self) -> str:
        pass


class ModuleSignals(QObject):
    """模組通用信號"""
    
    # 參數更新信號
    parameters_updated = pyqtSignal(dict)
    
    # 同步狀態變更信號
    sync_state_changed = pyqtSignal(bool)
    
    # 模組狀態信號
    module_ready = pyqtSignal()
    module_error = pyqtSignal(str)
    
    # 數據更新信號
    data_updated = pyqtSignal()


class BaseAnalysisModule(IAnalysisModule):
    """基礎分析模組實現 - 提供通用功能"""
    
    def __init__(self, title: str, parameter_provider: Optional[IParameterProvider] = None):
        self.title = title
        self.parameter_provider = parameter_provider
        self.signals = ModuleSignals()
        self._widget = None
        self._sync_enabled = True
        self._current_params = {}
        
    def get_title(self) -> str:
        return self.title
    
    def supports_sync(self) -> bool:
        return True  # 大部分模組都支援同步
    
    def get_default_size(self) -> tuple:
        return (450, 280)  # 預設大小
    
    def cleanup(self):
        """基礎清理實現"""
        if self._widget:
            self._widget.deleteLater()
            self._widget = None
    
    def set_sync_enabled(self, enabled: bool):
        """設定同步狀態"""
        self._sync_enabled = enabled
        self.signals.sync_state_changed.emit(enabled)
    
    def is_sync_enabled(self) -> bool:
        return self._sync_enabled
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """獲取當前參數"""
        if self.parameter_provider:
            return {
                'year': self.parameter_provider.get_current_year(),
                'race': self.parameter_provider.get_current_race(), 
                'session': self.parameter_provider.get_current_session()
            }
        return self._current_params.copy()
    
    def update_parameters(self, **params) -> bool:
        """更新參數的基礎實現"""
        try:
            self._current_params.update(params)
            self.signals.parameters_updated.emit(self._current_params.copy())
            return True
        except Exception as e:
            self.signals.module_error.emit(f"參數更新失敗: {e}")
            return False


class ModuleFactory:
    """模組工廠 - 負責創建和管理模組實例"""
    
    _registry = {}
    
    @classmethod
    def register_module(cls, module_type: str, module_class: type):
        """註冊模組類別"""
        cls._registry[module_type] = module_class
    
    @classmethod
    def create_module(cls, module_type: str, parameter_provider: Optional[IParameterProvider] = None, **kwargs) -> Optional[IAnalysisModule]:
        """創建模組實例"""
        module_class = cls._registry.get(module_type)
        if module_class:
            return module_class(parameter_provider=parameter_provider, **kwargs)
        return None
    
    @classmethod
    def get_available_modules(cls) -> List[str]:
        """獲取可用模組列表"""
        return list(cls._registry.keys())
    
    @classmethod
    def module_exists(cls, module_type: str) -> bool:
        """檢查模組是否存在"""
        return module_type in cls._registry


# 模組類型常數
class ModuleTypes:
    """模組類型定義"""
    RAIN_ANALYSIS = "rain_analysis"
    TELEMETRY_SPEED = "telemetry_speed"
    TELEMETRY_BRAKE = "telemetry_brake"
    TELEMETRY_THROTTLE = "telemetry_throttle"
    TELEMETRY_STEERING = "telemetry_steering"
    TRACK_MAP = "track_map"
    LAP_ANALYSIS = "lap_analysis"
    STATISTICS = "statistics"
