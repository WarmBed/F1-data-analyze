# -*- coding: utf-8 -*-
"""
F1T GUI - Global Signal Manager
================================

全域信號管理器 - 用於跨視窗同步。

從 f1t_gui_main.py 提取 (原始行號: 1378-1412, 35 行)
提取日期: 2025-06-14
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal
from core.logger import get_logger
from PyQt5.QtCore import pyqtSignal

# 設定日誌
logger = logging.getLogger(__name__)


class GlobalSignalManager(QObject):
    """全域信號管理器 - 用於跨視窗同步"""
    sync_x_position = pyqtSignal(int)  # X軸位置同步信號 (滑鼠位置)
    sync_x_range = pyqtSignal(float, float)  # X軸範圍同步信號 (偏移, 縮放)
    
    # 新增：遙測分析模組連動信號 (獨立於同步功能)
    lap_analysis_x_linkage = pyqtSignal(float, float)  # 遙測分析X軸連動信號 (距離值, Y軸相對位置)
    lap_analysis_x_clear = pyqtSignal()  # 遙測分析X軸清除信號
    
    # 新增：遙測分析點擊連動信號
    lap_analysis_click_linkage = pyqtSignal(float)  # 遙測分析點擊連動信號 (距離值)
    lap_analysis_click_clear = pyqtSignal()  # 遙測分析點擊清除信號
    
    # 新增：遙測分析連動控制信號
    lap_analysis_master_linkage_changed = pyqtSignal(bool)  # 總開關狀態變更信號
    
    def __init__(self):
        super().__init__()
        # 遙測分析連動總開關狀態
        self.lap_analysis_linkage_master_enabled = True
        
    def set_lap_linkage_enabled(self, enabled: bool):
        """設置遙測分析連動總開關狀態"""
        self.lap_analysis_linkage_master_enabled = enabled
        self.lap_analysis_master_linkage_changed.emit(enabled)
        logger.debug(f"[GLOBAL_SIGNALS] 遙測分析連動總開關: {'啟用' if enabled else '停用'}")
    
    def is_lap_linkage_enabled(self) -> bool:
        """檢查遙測分析連動總開關是否啟用"""
        return self.lap_analysis_linkage_master_enabled


# 創建全域信號管理器實例
global_signals = GlobalSignalManager()
