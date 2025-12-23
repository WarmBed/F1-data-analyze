"""
Live Timing MDI 基類
====================

所有 Live Timing MDI 子視窗的基類，
提供自動訂閱 LiveTimingDataManager 信號的功能。

Author: F1T Team
Date: 2025-12-03
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import pyqtSlot, Qt
from typing import Dict, Any, Optional

from core.logger import get_logger


logger = get_logger("live_timing.base_live_mdi", component="gui")


class BaseLiveTimingMDI(QWidget):
    """
    Live Timing MDI 子視窗基類
    
    所有 Live Timing 模組（如 TrackMap、TowerPanel 等）都應繼承此類。
    此類繼承自 QWidget，會被 QMdiArea.addSubWindow() 包裝成 QMdiSubWindow。
    
    特性：
    - 自動訂閱 LiveTimingDataManager 的信號
    - 提供標準化的生命週期管理
    - 統一的錯誤處理機制
    
    子類需要實現：
    - _setup_ui(): 設置 UI 組件
    - _on_snapshot_updated(snapshot): 處理數據更新
    - _on_race_loaded(race_info): 處理賽事載入
    - _on_race_unloaded(): 處理賽事卸載
    """
    
    def __init__(self, parent=None, data_manager=None):
        """
        初始化 MDI 子視窗
        
        Args:
            parent: 父視窗
            data_manager: LiveTimingDataManager 實例（可選，若不提供則使用單例）
        """
        super().__init__(parent)
        
        # 獲取 DataManager 實例
        if data_manager is None:
            from .data_manager import LiveTimingDataManager
            self._data_manager = LiveTimingDataManager.instance()
        else:
            self._data_manager = data_manager
        
        # 主佈局
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(4, 4, 4, 4)
        
        # 狀態追蹤
        self._is_subscribed = False
        self._race_loaded = False
        
        # 設置視窗屬性
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        # 設定 Live Timing 識別屬性 (供 force_white_background 排除使用)
        self.setProperty("is_live_timing_widget", True)
        
        # ★★★ 設置 objectName 以便 CSS 排除 ★★★
        # 格式: LiveTiming_{ClassName}
        self.setObjectName(f"LiveTiming_{self.__class__.__name__}")
        
        # ★★★ 設置深色背景 (所有 Live Timing 模組統一黑色底) ★★★
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
            }
        """)
        
        # 設置 UI
        self._setup_ui()
        
        # 訂閱信號
        self._subscribe_signals()
        
        logger.info("[%s] 初始化完成", self.__class__.__name__)
    
    def _setup_ui(self):
        """
        設置 UI 組件 - 子類應覆寫此方法
        """
        pass
    
    def _subscribe_signals(self):
        """訂閱 DataManager 的信號"""
        if self._is_subscribed:
            return
        
        try:
            dm = self._data_manager
            
            # 核心信號
            dm.snapshot_updated.connect(self._handle_snapshot_updated)
            dm.race_loaded.connect(self._handle_race_loaded)
            dm.race_unloaded.connect(self._handle_race_unloaded)
            
            # 插值信號 - 用於平滑動畫
            dm.interpolation_updated.connect(self._handle_interpolation_updated)
            
            # 可選信號 - 子類可以選擇性覆寫處理方法
            dm.playback_state_changed.connect(self._handle_playback_state_changed)
            dm.time_changed.connect(self._handle_time_changed)
            dm.progress_changed.connect(self._handle_progress_changed)
            
            self._is_subscribed = True
            logger.info("[%s] 已訂閱 DataManager 信號", self.__class__.__name__)
            
        except Exception as e:
            logger.exception("[%s] 訂閱信號失敗", self.__class__.__name__)
    
    def _unsubscribe_signals(self):
        """取消訂閱信號"""
        if not self._is_subscribed:
            return
        
        try:
            dm = self._data_manager
            
            dm.snapshot_updated.disconnect(self._handle_snapshot_updated)
            dm.race_loaded.disconnect(self._handle_race_loaded)
            dm.race_unloaded.disconnect(self._handle_race_unloaded)
            dm.interpolation_updated.disconnect(self._handle_interpolation_updated)
            dm.playback_state_changed.disconnect(self._handle_playback_state_changed)
            dm.time_changed.disconnect(self._handle_time_changed)
            dm.progress_changed.disconnect(self._handle_progress_changed)
            
            self._is_subscribed = False
            logger.info("[%s] 已取消訂閱 DataManager 信號", self.__class__.__name__)
            
        except Exception as e:
            logger.exception("[%s] 取消訂閱信號失敗", self.__class__.__name__)
    
    # ===========================================
    # 信號處理器 - 內部包裝
    # ===========================================
    @pyqtSlot(dict)
    def _handle_snapshot_updated(self, snapshot: Dict[str, Any]):
        """處理快照更新（內部包裝）"""
        try:
            self._on_snapshot_updated(snapshot)
        except Exception as e:
            logger.exception("[%s] 處理快照更新失敗", self.__class__.__name__)
    
    @pyqtSlot(dict)
    def _handle_race_loaded(self, race_info: Dict[str, Any]):
        """處理賽事載入（內部包裝）"""
        try:
            self._race_loaded = True
            self._on_race_loaded(race_info)
        except Exception as e:
            logger.exception("[%s] 處理賽事載入失敗", self.__class__.__name__)
    
    @pyqtSlot()
    def _handle_race_unloaded(self):
        """處理賽事卸載（內部包裝）"""
        try:
            self._race_loaded = False
            self._on_race_unloaded()
        except Exception as e:
            logger.exception("[%s] 處理賽事卸載失敗", self.__class__.__name__)
    
    @pyqtSlot(str)
    def _handle_playback_state_changed(self, state: str):
        """處理播放狀態改變（內部包裝）"""
        try:
            self._on_playback_state_changed(state)
        except Exception as e:
            logger.exception("[%s] 處理播放狀態改變失敗", self.__class__.__name__)
    
    @pyqtSlot(float)
    def _handle_time_changed(self, time_seconds: float):
        """處理時間改變（內部包裝）"""
        try:
            self._on_time_changed(time_seconds)
        except Exception as e:
            logger.exception("[%s] 處理時間改變失敗", self.__class__.__name__)
    
    @pyqtSlot(float)
    def _handle_progress_changed(self, progress: float):
        """處理進度改變（內部包裝）"""
        try:
            self._on_progress_changed(progress)
        except Exception as e:
            logger.exception("[%s] 處理進度改變失敗", self.__class__.__name__)
    
    @pyqtSlot(dict, dict, float, float)
    def _handle_interpolation_updated(self, current_snap: dict, next_snap: dict, 
                                       alpha: float, race_time_seconds: float):
        """處理插值更新（內部包裝）- 用於平滑動畫"""
        try:
            self._on_interpolation_updated(current_snap, next_snap, alpha, race_time_seconds)
        except Exception as e:
            logger.exception("[%s] 處理插值更新失敗", self.__class__.__name__)
    
    # ===========================================
    # 虛擬方法 - 子類應覆寫
    # ===========================================
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        處理數據快照更新
        
        Args:
            snapshot: 包含 'race_time', 'race_time_seconds', 'drivers' 的字典
        """
        pass
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """
        處理賽事載入
        
        Args:
            race_info: 賽事資訊字典
        """
        pass
    
    def _on_race_unloaded(self):
        """處理賽事卸載"""
        pass
    
    def _on_playback_state_changed(self, state: str):
        """
        處理播放狀態改變
        
        Args:
            state: 'playing', 'paused', 'stopped'
        """
        pass
    
    def _on_time_changed(self, time_seconds: float):
        """
        處理時間改變
        
        Args:
            time_seconds: 當前時間（秒）
        """
        pass
    
    def _on_progress_changed(self, progress: float):
        """
        處理進度改變
        
        Args:
            progress: 0.0 ~ 1.0
        """
        pass
    
    def _on_interpolation_updated(self, current_snap: Dict[str, Any], next_snap: Dict[str, Any],
                                   alpha: float, race_time_seconds: float):
        """
        處理插值更新 - 用於平滑動畫
        
        子類可覆寫此方法以實現平滑的位置過渡動畫。
        此方法在每次 playback tick 時都會被調用（約 20 FPS）。
        
        Args:
            current_snap: 當前快照
            next_snap: 下一個快照
            alpha: 插值因子 (0.0 ~ 1.0)，表示當前時間在兩個快照之間的位置
            race_time_seconds: 當前賽事時間（秒）
        """
        pass
    
    # ===========================================
    # 工具方法
    # ===========================================
    def _show_error(self, title: str, message: str):
        """顯示錯誤訊息"""
        QMessageBox.critical(self, title, message)
    
    def _show_warning(self, title: str, message: str):
        """顯示警告訊息"""
        QMessageBox.warning(self, title, message)
    
    def _show_info(self, title: str, message: str):
        """顯示資訊訊息"""
        QMessageBox.information(self, title, message)
    
    def get_data_manager(self):
        """獲取 DataManager 實例"""
        return self._data_manager
    
    def is_race_loaded(self) -> bool:
        """檢查是否已載入賽事"""
        return self._race_loaded
    
    # ===========================================
    # 生命週期管理
    # ===========================================
    def closeEvent(self, event):
        """視窗關閉時清理資源"""
        logger.info("[%s] 關閉視窗，清理資源...", self.__class__.__name__)
        
        # 取消訂閱信號
        self._unsubscribe_signals()
        
        # 呼叫清理方法（子類可覆寫）
        self._cleanup()
        
        super().closeEvent(event)
    
    def _cleanup(self):
        """
        清理資源 - 子類可覆寫此方法進行額外清理
        """
        pass
