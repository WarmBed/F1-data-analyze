"""
Live Timing 模組全局同步信號管理器
===================================

提供所有 Trace 模組共享的同步信號，實現跨模組設定同步。

功能：
- 全局單例同步信號
- 支援車手選擇同步
- 支援顯示選項同步
- 支援 Hover 位置同步 (Linkage 功能)

Author: F1T Team
Date: 2025-12-11
Updated: 2025-12-21 - 添加 Hover 位置同步
"""

from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any


class GlobalTraceSettingsSyncSignal(QObject):
    """
    全局 Trace 設定同步信號
    
    所有 Trace 模組（Speed、Throttle、Brake、Gear、DRS、RPM）共享此信號
    """
    settings_changed = pyqtSignal(dict)
    
    # Hover 位置同步信號
    # 參數: dict = {'source_widget': int, 'x_value': float, 'is_hovering': bool}
    hover_position_changed = pyqtSignal(dict)


# 全局單例
_global_sync_signal = None


def get_global_sync_signal() -> GlobalTraceSettingsSyncSignal:
    """
    獲取全局同步信號單例
    
    Returns:
        GlobalTraceSettingsSyncSignal: 全局同步信號實例
    """
    global _global_sync_signal
    if _global_sync_signal is None:
        _global_sync_signal = GlobalTraceSettingsSyncSignal()
    return _global_sync_signal
