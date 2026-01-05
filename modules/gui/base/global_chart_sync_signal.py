# -*- coding: utf-8 -*-
"""
GlobalChartSyncSignal - 跨模組圖表同步信號機制

用於同步 Detailed Lap Analysis 和 Throttle Line Chart 之間的：
1. 車手選擇（5 位車手）
2. X 軸縮放範圍（圈數）
3. 重置視圖

設計為單例模式，確保所有模組使用同一個信號實例。
"""

from __future__ import annotations

from typing import List, Optional, Set, Tuple
from PyQt5.QtCore import QObject, pyqtSignal

from core.logger import get_logger

logger = get_logger(__name__)


class GlobalChartSyncSignal(QObject):
    """
    全局圖表同步信號管理器（單例模式）
    
    Signals:
        drivers_changed: 當車手選擇改變時發出，參數為選中的車手列表
        x_range_changed: 當 X 軸範圍改變時發出，參數為 (min_lap, max_lap)
        reset_view: 重置視圖信號
        module_registered: 模組註冊時發出
        module_unregistered: 模組取消註冊時發出
    """
    
    # 單例實例
    _instance: Optional['GlobalChartSyncSignal'] = None
    
    # 信號定義
    drivers_changed = pyqtSignal(list, str)  # (selected_drivers, source_module)
    x_range_changed = pyqtSignal(float, float, str)  # (min_lap, max_lap, source_module)
    reset_view = pyqtSignal(str)  # source_module
    module_registered = pyqtSignal(str)  # module_name
    module_unregistered = pyqtSignal(str)  # module_name
    
    # 支援的模組標識
    MODULE_DETAILED_LAP = "detailed_lap_analysis"
    MODULE_THROTTLE_LINE = "throttle_line_chart"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 已註冊的模組
        self._registered_modules: Set[str] = set()
        
        # 當前同步狀態
        self._current_drivers: List[str] = []
        self._current_x_range: Optional[Tuple[float, float]] = None
        self._is_zoomed: bool = False
        
        logger.debug("[GLOBAL_SYNC] GlobalChartSyncSignal 初始化完成")
    
    @classmethod
    def get_instance(cls) -> 'GlobalChartSyncSignal':
        """獲取單例實例"""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("[GLOBAL_SYNC] 創建 GlobalChartSyncSignal 單例實例")
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置單例實例（主要用於測試）"""
        if cls._instance is not None:
            cls._instance._registered_modules.clear()
            cls._instance._current_drivers.clear()
            cls._instance._current_x_range = None
            cls._instance._is_zoomed = False
            cls._instance = None
            logger.debug("[GLOBAL_SYNC] 單例實例已重置")
    
    # ========== 模組註冊管理 ==========
    
    def register_module(self, module_name: str) -> None:
        """
        註冊模組
        
        Args:
            module_name: 模組標識（使用類常量）
        """
        if module_name not in self._registered_modules:
            self._registered_modules.add(module_name)
            self.module_registered.emit(module_name)
            logger.debug(f"[GLOBAL_SYNC] 模組已註冊: {module_name}")
            logger.debug(f"[GLOBAL_SYNC] 當前註冊模組: {self._registered_modules}")
    
    def unregister_module(self, module_name: str) -> None:
        """
        取消註冊模組
        
        Args:
            module_name: 模組標識
        """
        if module_name in self._registered_modules:
            self._registered_modules.discard(module_name)
            self.module_unregistered.emit(module_name)
            logger.debug(f"[GLOBAL_SYNC] 模組已取消註冊: {module_name}")
            
            # 如果所有模組都關閉，清除同步狀態
            if not self._registered_modules:
                self._clear_sync_state()
    
    def is_module_registered(self, module_name: str) -> bool:
        """檢查模組是否已註冊"""
        return module_name in self._registered_modules
    
    def get_registered_modules(self) -> Set[str]:
        """獲取已註冊的模組列表"""
        return self._registered_modules.copy()
    
    # ========== 車手同步 ==========
    
    def emit_drivers_changed(self, drivers: List[str], source: str) -> None:
        """
        發出車手選擇改變信號
        
        Args:
            drivers: 選中的車手列表（最多 5 位）
            source: 發出信號的模組標識
        """
        # 過濾空值
        drivers = [d for d in drivers if d and d.strip()]
        
        self._current_drivers = drivers.copy()
        self.drivers_changed.emit(drivers, source)
        logger.debug(f"[GLOBAL_SYNC] 車手選擇改變: {drivers} (來源: {source})")
    
    def get_current_drivers(self) -> List[str]:
        """獲取當前選中的車手列表"""
        return self._current_drivers.copy()
    
    # ========== X 軸縮放同步 ==========
    
    def emit_x_range_changed(self, min_lap: float, max_lap: float, source: str) -> None:
        """
        發出 X 軸範圍改變信號
        
        Args:
            min_lap: 最小圈數
            max_lap: 最大圈數
            source: 發出信號的模組標識
        """
        self._current_x_range = (min_lap, max_lap)
        self._is_zoomed = True
        self.x_range_changed.emit(min_lap, max_lap, source)
        logger.debug(f"[GLOBAL_SYNC] X 軸範圍改變: Lap {min_lap:.1f} - {max_lap:.1f} (來源: {source})")
    
    def get_current_x_range(self) -> Optional[Tuple[float, float]]:
        """獲取當前 X 軸範圍"""
        return self._current_x_range
    
    def is_zoomed(self) -> bool:
        """檢查是否有縮放"""
        return self._is_zoomed
    
    # ========== 重置視圖 ==========
    
    def emit_reset_view(self, source: str) -> None:
        """
        發出重置視圖信號
        
        Args:
            source: 發出信號的模組標識
        """
        self._current_x_range = None
        self._is_zoomed = False
        self.reset_view.emit(source)
        logger.debug(f"[GLOBAL_SYNC] 重置視圖 (來源: {source})")
    
    # ========== 內部方法 ==========
    
    def _clear_sync_state(self) -> None:
        """清除所有同步狀態（當所有模組關閉時調用）"""
        self._current_drivers.clear()
        self._current_x_range = None
        self._is_zoomed = False
        logger.debug("[GLOBAL_SYNC] 同步狀態已清除（所有模組已關閉）")


# 便捷函數：獲取全局同步信號實例
def get_global_chart_sync() -> GlobalChartSyncSignal:
    """獲取全局圖表同步信號實例"""
    return GlobalChartSyncSignal.get_instance()
