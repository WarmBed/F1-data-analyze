"""
參數同步管理器
統一管理年份/賽事/場次參數的同步功能

提供的功能：
- 參數變更廣播到所有 MDI 子視窗
- 獨立視窗參數池管理
- 參數同步狀態追蹤

從 f1t_gui_main.py 中提取的方法：
- sync_to_all_mdi_subwindows()
- sync_to_mdi_area()
- sync_all_independent_windows()
- register_mdi_area()
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger
from typing import List
from typing import Optional
from PyQt5.QtWidgets import QMdiSubWindow
from PyQt5.QtWidgets import QMdiArea
from typing import Any

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow, QMdiArea, QMdiSubWindow

logger = get_logger(__name__)


class ParameterSyncManager:
    """
    參數同步管理器
    
    負責管理所有參數同步操作，包括：
    - 參數變更廣播到所有 MDI 子視窗
    - 獨立視窗參數池管理
    - 參數同步狀態追蹤
    
    Attributes:
        main_window: 主視窗實例
        mdi_areas: 已註冊的 MDI 區域列表
        shared_independent_params: 共享的獨立參數池
    """
    
    def __init__(self, main_window: 'QMainWindow'):
        """
        初始化參數同步管理器
        
        Args:
            main_window: 主視窗實例（StyleHMainWindow）
        """
        self.main_window = main_window
        
        # 使用主視窗的 mdi_areas 列表（向後兼容）
        # self._mdi_areas: List['QMdiArea'] = []
        
        # 共享的獨立參數池
        self._shared_independent_params: Dict[str, Any] = {}
        
        logger.debug("[ParameterSyncManager] Initialized")
    
    @property
    def mdi_areas(self) -> List['QMdiArea']:
        """取得主視窗的 mdi_areas 列表"""
        return getattr(self.main_window, 'mdi_areas', [])
    
    @property
    def shared_independent_params(self) -> Dict[str, Any]:
        """取得共享的獨立參數池"""
        # 優先使用主視窗的，確保向後兼容
        if hasattr(self.main_window, 'shared_independent_params'):
            return self.main_window.shared_independent_params
        return self._shared_independent_params
    
    # ==================== MDI 區域註冊 ====================
    
    def register_mdi_area(self, mdi_area: 'QMdiArea') -> None:
        """
        註冊 MDI 區域到管理器
        
        Args:
            mdi_area: 要註冊的 MDI 區域
        """
        if mdi_area is None:
            logger.warning("[ParameterSyncManager] Cannot register None MDI area")
            return
        
        mdi_areas = self.mdi_areas
        if mdi_area not in mdi_areas:
            mdi_areas.append(mdi_area)
            logger.debug(f"[ParameterSyncManager] Registered MDI area: {mdi_area.objectName()}")
            logger.debug(f"[ParameterSyncManager] Total registered: {len(mdi_areas)}")
        else:
            logger.debug(f"[ParameterSyncManager] MDI area already registered: {mdi_area.objectName()}")
    
    def unregister_mdi_area(self, mdi_area: 'QMdiArea') -> None:
        """
        取消註冊 MDI 區域
        
        Args:
            mdi_area: 要取消註冊的 MDI 區域
        """
        mdi_areas = self.mdi_areas
        if mdi_area in mdi_areas:
            mdi_areas.remove(mdi_area)
            logger.debug(f"[ParameterSyncManager] Unregistered MDI area: {mdi_area.objectName()}")
    
    # ==================== 參數同步 ====================
    
    def sync_to_all_mdi_subwindows(self, param_type: str, value: Any) -> int:
        """
        同步參數到所有 MDI 子視窗
        
        Args:
            param_type: 參數類型（'year', 'race', 'session' 等）
            value: 參數值
            
        Returns:
            更新的子視窗數量
        """
        logger.debug(f"[ParameterSyncManager] Syncing {param_type}={value} to all MDI subwindows")
        logger.debug(f"[ParameterSyncManager] Registered MDI areas: {len(self.mdi_areas)}")
        
        synced_count = 0
        for i, mdi_area in enumerate(self.mdi_areas):
            logger.debug(f"[ParameterSyncManager] Checking MDI area {i+1}/{len(self.mdi_areas)}: {mdi_area.objectName()}")
            synced_count += self.sync_to_mdi_area(mdi_area, param_type, value)
        
        logger.debug(f"[ParameterSyncManager] Sync complete, updated {synced_count} subwindows")
        return synced_count
    
    def sync_to_mdi_area(self, mdi_area: 'QMdiArea', param_type: str, value: Any) -> int:
        """
        同步參數到指定 MDI 區域的所有子視窗
        
        Args:
            mdi_area: MDI 區域
            param_type: 參數類型
            value: 參數值
            
        Returns:
            更新的子視窗數量
        """
        if mdi_area is None:
            logger.warning("[ParameterSyncManager] MDI area is None, skipping sync")
            return 0
        
        notified_count = 0
        subwindow_list = mdi_area.subWindowList()
        logger.debug(f"[ParameterSyncManager] Syncing to {len(subwindow_list)} subwindows in {mdi_area.objectName()}")
        
        for subwindow in subwindow_list:
            window_title = subwindow.windowTitle() if subwindow else "Unknown"
            
            # 發送通知，讓子視窗自己決定是否響應
            if hasattr(subwindow, 'receive_main_window_update_notification'):
                try:
                    subwindow.receive_main_window_update_notification(param_type, value)
                    notified_count += 1
                    logger.debug(f"[ParameterSyncManager] Notified: {window_title}")
                except Exception as e:
                    logger.error(f"[ParameterSyncManager] Failed to notify {window_title}: {e}")
            else:
                logger.debug(f"[ParameterSyncManager] {window_title} does not support notifications")
        
        return notified_count
    
    def sync_all_independent_windows(self, updated_params: Dict[str, Any]) -> int:
        """
        同步所有停用同步的視窗（全域共享參數池功能）
        
        當任一視窗取消勾選"與主視窗同步車手與圈數"時觸發，
        更新全域共享參數池並同步所有停用同步的視窗。
        
        Args:
            updated_params: 更新後的參數字典
            
        Returns:
            同步的視窗數量
        """
        logger.debug("[ParameterSyncManager] Syncing all independent windows")
        logger.debug(f"[ParameterSyncManager] Updated params: {updated_params}")
        
        # 更新全域共享參數池
        self.shared_independent_params.update(updated_params)
        logger.debug("[ParameterSyncManager] Global param pool updated")
        
        # 遍歷所有 MDI 子視窗
        synchronized_count = 0
        total_windows = 0
        
        for mdi_area in self.mdi_areas:
            for sub_window in mdi_area.subWindowList():
                total_windows += 1
                
                # 檢查是否有 analysis_module
                if not hasattr(sub_window, 'analysis_module'):
                    continue
                
                analysis_module = sub_window.analysis_module
                if analysis_module is None:
                    continue
                
                # 檢查是否停用同步
                sync_enabled = getattr(analysis_module, 'sync_driver_lap_enabled', True)
                if sync_enabled:
                    continue
                
                # 同步參數
                if hasattr(analysis_module, 'update_from_shared_params'):
                    try:
                        analysis_module.update_from_shared_params(updated_params)
                        synchronized_count += 1
                        logger.debug(f"[ParameterSyncManager] Synced: {sub_window.windowTitle()}")
                    except Exception as e:
                        logger.error(f"[ParameterSyncManager] Sync failed: {e}")
        
        logger.debug(f"[ParameterSyncManager] Synced {synchronized_count}/{total_windows} windows")
        return synchronized_count
    
    # ==================== 參數廣播 ====================
    
    def broadcast_year_change(self, year: int) -> None:
        """
        廣播年份變更
        
        Args:
            year: 新的年份
        """
        self.sync_to_all_mdi_subwindows('year', year)
    
    def broadcast_race_change(self, race: str) -> None:
        """
        廣播賽事變更
        
        Args:
            race: 新的賽事名稱
        """
        self.sync_to_all_mdi_subwindows('race', race)
    
    def broadcast_session_change(self, session: str) -> None:
        """
        廣播場次變更
        
        Args:
            session: 新的場次（R, Q, FP1 等）
        """
        self.sync_to_all_mdi_subwindows('session', session)
    
    def broadcast_driver_change(self, driver: str, driver_num: int = 1) -> None:
        """
        廣播車手變更
        
        Args:
            driver: 車手代碼
            driver_num: 車手編號（1 或 2）
        """
        param_type = f'driver{driver_num}' if driver_num > 1 else 'driver'
        self.sync_to_all_mdi_subwindows(param_type, driver)
    
    def broadcast_lap_change(self, lap: int, driver_num: int = 1) -> None:
        """
        廣播圈數變更
        
        Args:
            lap: 圈數
            driver_num: 車手編號（1 或 2）
        """
        param_type = f'lap{driver_num}' if driver_num > 1 else 'lap'
        self.sync_to_all_mdi_subwindows(param_type, lap)
    
    # ==================== 參數獲取 ====================
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """
        獲取當前參數（從主視窗）
        
        Returns:
            包含年份、賽事、場次等參數的字典
        """
        if hasattr(self.main_window, 'get_current_parameters'):
            return self.main_window.get_current_parameters()
        
        # 備用方案：直接從控件讀取
        params = {
            'year': None,
            'race': None,
            'session': None,
            'driver1': None,
            'driver2': None,
            'lap1': None,
            'lap2': None,
        }
        
        try:
            if hasattr(self.main_window, 'control_dock'):
                dock = self.main_window.control_dock
                if hasattr(dock, 'year_combo'):
                    params['year'] = dock.year_combo.currentText()
                if hasattr(dock, 'race_combo'):
                    params['race'] = dock.race_combo.currentText()
                if hasattr(dock, 'session_combo'):
                    params['session'] = dock.session_combo.currentText()
        except Exception as e:
            logger.error(f"[ParameterSyncManager] Failed to get parameters: {e}")
        
        return params
    
    # ==================== 統計資訊 ====================
    
    def get_sync_stats(self) -> Dict[str, int]:
        """
        獲取同步統計資訊
        
        Returns:
            包含各類統計數據的字典
        """
        total_mdi_areas = len(self.mdi_areas)
        total_subwindows = 0
        syncable_subwindows = 0
        independent_subwindows = 0
        
        for mdi_area in self.mdi_areas:
            for sub_window in mdi_area.subWindowList():
                total_subwindows += 1
                
                if hasattr(sub_window, 'receive_main_window_update_notification'):
                    syncable_subwindows += 1
                
                if hasattr(sub_window, 'analysis_module'):
                    module = sub_window.analysis_module
                    if module and not getattr(module, 'sync_driver_lap_enabled', True):
                        independent_subwindows += 1
        
        return {
            'mdi_areas': total_mdi_areas,
            'total_subwindows': total_subwindows,
            'syncable_subwindows': syncable_subwindows,
            'independent_subwindows': independent_subwindows,
        }
