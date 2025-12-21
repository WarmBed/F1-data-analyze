#!/usr/bin/env python3
"""
連動管理器
統一管理所有圈速分析模組的連動狀態和信號分發
"""

from typing import List, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal

from core.logger import get_logger
logger = get_logger(__name__)


class LinkageManager(QObject):
    """
    連動管理器
    
    職責：
    - 管理所有註冊的連動模組
    - 統一分發連動信號
    - 處理主開關狀態變更
    - 提供連動狀態查詢
    """
    
    # 信號定義
    master_linkage_changed = pyqtSignal(bool)  # 主開關狀態變更
    time_axis_mode_changed = pyqtSignal(bool)  # 時間軸模式變更 (True=時間軸, False=距離軸)
    x_linkage_signal = pyqtSignal(float, float)  # X軸連動信號 (distance/time, y_relative)
    x_linkage_clear = pyqtSignal()  # X軸連動清除
    click_linkage_signal = pyqtSignal(float)  # 點擊連動信號 (distance/time)
    click_linkage_clear = pyqtSignal()  # 點擊連動清除
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 連動狀態
        self.master_linkage_enabled = True
        self.time_axis_mode = False  # 時間軸模式（False=距離軸, True=時間軸）
        
        # 註冊的連動模組
        self.registered_modules: List[Any] = []
        
        # 模組類型統計
        self.module_types: Dict[str, int] = {}
    
    def register_module(self, module, module_type: str = "unknown"):
        """
        註冊連動模組
        
        Args:
            module: 實現了連動混合類的模組實例
            module_type: 模組類型（speed/rpm/throttle等）
        """
        if module not in self.registered_modules:
            self.registered_modules.append(module)
            
            # 統計模組類型
            self.module_types[module_type] = self.module_types.get(module_type, 0) + 1
            
            # 連接模組的信號到管理器
            self._connect_module_signals(module)
            
            # 設置模組的當前主開關狀態
            if hasattr(module, 'set_master_linkage_enabled'):
                module.set_master_linkage_enabled(self.master_linkage_enabled)
            
            logger.debug(f"[LINKAGE_MANAGER] 已註冊 {module_type} 連動模組，目前共 {len(self.registered_modules)} 個模組")
    
    def unregister_module(self, module):
        """取消註冊連動模組"""
        logger.debug(f"[LINKAGE_MANAGER] [UNREGISTER_DEBUG] unregister 前: list 長度 = {len(self.registered_modules)}")
        logger.debug(f"[LINKAGE_MANAGER] [UNREGISTER_DEBUG] module 在 list 中: {module in self.registered_modules}")
        logger.debug(f"[LINKAGE_MANAGER] [UNREGISTER_DEBUG] module ID: {id(module)}")
        logger.debug(f"[LINKAGE_MANAGER] [UNREGISTER_DEBUG] list 中的 ID: {[id(m) for m in self.registered_modules]}")
        
        if module in self.registered_modules:
            self.registered_modules.remove(module)
            self._disconnect_module_signals(module)
            logger.debug(f"[LINKAGE_MANAGER] [UNREGISTER_DEBUG] 已從 list 移除")
            logger.debug(f"[LINKAGE_MANAGER] [UNREGISTER_DEBUG] unregister 後: list 長度 = {len(self.registered_modules)}")
            logger.debug(f"[LINKAGE_MANAGER] 已取消註冊連動模組，目前共 {len(self.registered_modules)} 個模組")
        else:
            logger.debug(f"[LINKAGE_MANAGER] [UNREGISTER_DEBUG] module 不在 list 中，無法移除")
    
    def set_master_linkage_enabled(self, enabled: bool):
        """設置主連動開關狀態"""
        if self.master_linkage_enabled != enabled:
            self.master_linkage_enabled = enabled
            
            # 通知所有註冊的模組
            for module in self.registered_modules:
                try:
                    if hasattr(module, 'on_master_linkage_changed'):
                        module.on_master_linkage_changed(enabled)
                    elif hasattr(module, 'set_master_linkage_enabled'):
                        module.set_master_linkage_enabled(enabled)
                except Exception as e:
                    logger.error(f"[LINKAGE_MANAGER] 通知模組主開關變更失敗: {e}")
            
            # 發送信號
            self.master_linkage_changed.emit(enabled)
            logger.debug(f"[LINKAGE_MANAGER] 主連動開關: {'啟用' if enabled else '停用'}，已通知 {len(self.registered_modules)} 個模組")
    
    def is_master_linkage_enabled(self) -> bool:
        """獲取主連動開關狀態"""
        return self.master_linkage_enabled
    
    def set_time_axis_mode(self, use_time_axis: bool):
        """
        設置時間軸模式並廣播給所有模組
        
        Args:
            use_time_axis: True=使用時間軸, False=使用距離軸
        """
        if self.time_axis_mode != use_time_axis:
            self.time_axis_mode = use_time_axis
            
            # 通知所有註冊的模組
            for module in self.registered_modules:
                try:
                    if hasattr(module, 'set_time_axis_mode'):
                        module.set_time_axis_mode(use_time_axis)
                except Exception as e:
                    logger.error(f"[LINKAGE_MANAGER] 通知模組時間軸模式變更失敗: {e}")
            
            # 發送信號
            self.time_axis_mode_changed.emit(use_time_axis)
            
            logger.debug(f"[LINKAGE_MANAGER] 時間軸模式: {'啟用（時間軸）' if use_time_axis else '停用（距離軸）'}，已通知 {len(self.registered_modules)} 個模組")
    
    def is_time_axis_mode(self) -> bool:
        """獲取當前時間軸模式狀態"""
        return self.time_axis_mode
    
    def send_x_linkage(self, distance_value: float, y_relative: float, sender=None):
        """發送X軸連動信號"""
        if not self.master_linkage_enabled:
            return
        
        # 發送給所有模組（除了發送者）
        for module in self.registered_modules:
            if module != sender and hasattr(module, 'on_x_linkage_received'):
                try:
                    module.on_x_linkage_received(distance_value, y_relative)
                except Exception as e:
                    logger.error(f"[LINKAGE_MANAGER] X軸連動信號發送失敗: {e}")
        
        # 發送全域信號
        self.x_linkage_signal.emit(distance_value, y_relative)
    
    def send_x_linkage_clear(self, sender=None):
        """發送X軸連動清除信號"""
        if not self.master_linkage_enabled:
            return
        
        # 發送給所有模組（除了發送者）
        for module in self.registered_modules:
            if module != sender and hasattr(module, 'on_x_linkage_clear'):
                try:
                    module.on_x_linkage_clear()
                except Exception as e:
                    logger.error(f"[LINKAGE_MANAGER] X軸連動清除信號發送失敗: {e}")
        
        # 發送全域信號
        self.x_linkage_clear.emit()
    
    def send_click_linkage(self, distance_value: float, sender=None):
        """發送點擊連動信號"""
        if not self.master_linkage_enabled:
            return
        
        # 發送給所有模組（除了發送者）
        for module in self.registered_modules:
            if module != sender and hasattr(module, 'on_click_linkage_received'):
                try:
                    module.on_click_linkage_received(distance_value)
                except Exception as e:
                    logger.error(f"[LINKAGE_MANAGER] 點擊連動信號發送失敗: {e}")
        
        # 發送全域信號
        self.click_linkage_signal.emit(distance_value)
    
    def send_click_linkage_clear(self, sender=None):
        """發送點擊連動清除信號"""
        if not self.master_linkage_enabled:
            return
        
        # 發送給所有模組（除了發送者）
        for module in self.registered_modules:
            if module != sender and hasattr(module, 'on_click_linkage_clear'):
                try:
                    module.on_click_linkage_clear()
                except Exception as e:
                    logger.error(f"[LINKAGE_MANAGER] 點擊連動清除信號發送失敗: {e}")
        
        # 發送全域信號
        self.click_linkage_clear.emit()
    
    def get_module_stats(self) -> Dict[str, Any]:
        """獲取模組統計信息"""
        return {
            'total_modules': len(self.registered_modules),
            'module_types': self.module_types.copy(),
            'master_linkage_enabled': self.master_linkage_enabled
        }
    
    def get_registered_modules(self) -> Dict[str, Any]:
        """獲取已註冊的模組"""
        result = {}
        for i, module in enumerate(self.registered_modules):
            module_name = f"module_{i}"
            if hasattr(module, '__class__'):
                module_name = module.__class__.__name__
            result[module_name] = module
        return result
    
    def is_linkage_enabled(self) -> bool:
        """檢查連動是否啟用（別名方法）"""
        return self.is_master_linkage_enabled()
    
    def set_linkage_enabled(self, enabled: bool):
        """設置連動狀態（別名方法）"""
        self.set_master_linkage_enabled(enabled)
    
    def broadcast_signal(self, signal_name: str, data: Any):
        """廣播信號到所有模組"""
        logger.debug(f"[LINKAGE_MANAGER] 廣播信號: {signal_name}, 數據: {data}")
        # 這裡可以根據需要實現特定的信號廣播邏輯
    
    def _connect_module_signals(self, module):
        """連接模組信號到管理器"""
        # 這裡可以根據需要連接模組的特定信號
        pass
    
    def _disconnect_module_signals(self, module):
        """斷開模組信號連接"""
        # 這裡可以根據需要斷開模組的信號連接
        pass
    
    def clear_all_linkage(self):
        """清除所有連動狀態"""
        self.send_x_linkage_clear()
        self.send_click_linkage_clear()
        logger.debug(f"[LINKAGE_MANAGER] 已清除所有連動狀態")


# 全域連動管理器實例
linkage_manager = LinkageManager()
