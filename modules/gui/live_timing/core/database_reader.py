"""
Database Reader - 從 SQLite 資料庫讀取即時數據
==================================================

提供 QTimer 定時讀取資料庫的功能，供 GUI 模組使用。

使用方式:
1. 創建 DatabaseReaderWidget 並連接到父 widget
2. 調用 start_reading() 開始定時讀取
3. 連接 snapshot_updated 信號獲取數據
4. 調用 stop_reading() 停止讀取

Author: F1T Team
Date: 2025-12-07
"""

from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from core.logger import get_logger

from .realtime_database import get_realtime_db, RealtimeDatabase


class DatabaseReader(QObject):
    """
    資料庫讀取器
    
    定時從 SQLite 資料庫讀取最新數據並發出信號
    
    信號:
        snapshot_updated: 當讀取到新數據時發出
    """
    
    # 信號
    snapshot_updated = pyqtSignal(dict)  # 快照數據
    
    def __init__(self, parent=None, interval_ms: int = 100):
        """
        初始化資料庫讀取器
        
        Args:
            parent: 父物件
            interval_ms: 讀取間隔 (毫秒)，預設 100ms
        """
        super().__init__(parent)
        
        self._db: RealtimeDatabase = get_realtime_db()
        self._interval_ms = interval_ms
        self._is_reading = False
        
        # 定時器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._read_and_emit)
        
        # 計數器
        self._read_count = 0
        self._last_driver_count = 0

        self._logger = get_logger("live_timing.database_reader", component="gui")
        
    def start_reading(self):
        """開始定時讀取"""
        if self._is_reading:
            return
        
        self._db.connect()
        self._is_reading = True
        self._timer.start(self._interval_ms)
        self._logger.info("Started reading every %sms", self._interval_ms)
    
    def stop_reading(self):
        """停止定時讀取"""
        if not self._is_reading:
            return
        
        self._timer.stop()
        self._is_reading = False
        self._logger.info("Stopped reading (total reads: %s)", self._read_count)
    
    def is_reading(self) -> bool:
        """是否正在讀取"""
        return self._is_reading
    
    def read_once(self) -> Dict[str, Any]:
        """讀取一次並返回數據"""
        self._db.connect()
        return self._db.get_snapshot()
    
    def _read_and_emit(self):
        """讀取資料庫並發出信號"""
        try:
            snapshot = self._db.get_snapshot()
            self._read_count += 1
            
            # 調試輸出（每 100 次輸出一次）
            driver_count = len(snapshot.get('drivers', {}))
            if self._read_count % 100 == 1 or driver_count != self._last_driver_count:
                lap_info = f"Lap {snapshot.get('current_lap', 0)}/{snapshot.get('total_laps', 0)}"
                self._logger.debug(
                    "Read #%s: %s drivers | %s",
                    self._read_count,
                    driver_count,
                    lap_info,
                )
                self._last_driver_count = driver_count
            
            self.snapshot_updated.emit(snapshot)
            
        except Exception as e:
            self._logger.error("Read error: %s", e)
    
    def set_interval(self, interval_ms: int):
        """設置讀取間隔"""
        self._interval_ms = interval_ms
        if self._is_reading:
            self._timer.setInterval(interval_ms)


# 單例
_reader_instance: Optional[DatabaseReader] = None


def get_database_reader(parent=None, interval_ms: int = 100) -> DatabaseReader:
    """
    獲取 DatabaseReader 單例
    
    Args:
        parent: 父物件（僅在首次創建時使用）
        interval_ms: 讀取間隔
    
    Returns:
        DatabaseReader 實例
    """
    global _reader_instance
    
    if _reader_instance is None:
        _reader_instance = DatabaseReader(parent, interval_ms)
    
    return _reader_instance
