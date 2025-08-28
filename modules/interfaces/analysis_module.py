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
from typing import Dict, Any, Optional
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
    def update_parameters(self, year: int, race: str, session: str) -> None:
        """
        更新分析參數
        
        當 PopoutSubWindow 的參數提供者更新時會調用此方法
        
        Args:
            year: 年份
            race: 賽事名稱  
            session: 賽段 (FP1, FP2, FP3, Q, R, S)
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
