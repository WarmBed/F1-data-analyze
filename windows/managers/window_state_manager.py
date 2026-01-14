# -*- coding: utf-8 -*-
"""
WindowStateManager - 視窗狀態管理器
===================================

實現 Ctrl+Z 撤銷功能，支援：
1. 視窗關閉恢復
2. 視窗位置/大小恢復
3. Tab 關閉恢復
4. 拖動位置恢復

歷史記錄限制：10 步

Author: F1T Team
Date: 2026-01-14
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum, auto

from PyQt5.QtCore import QObject, pyqtSignal, QRect

from core.logger import get_logger

logger = get_logger(__name__)


class StateType(Enum):
    """狀態類型枚舉"""
    WINDOW_CLOSE = auto()    # 視窗關閉
    WINDOW_MOVE = auto()     # 視窗移動
    WINDOW_RESIZE = auto()   # 視窗調整大小
    TAB_CLOSE = auto()       # Tab 關閉


@dataclass
class WindowState:
    """
    視窗狀態快照
    
    儲存視窗在某一時刻的完整狀態，用於撤銷操作
    """
    state_type: StateType
    timestamp: float = field(default_factory=time.time)
    
    # 視窗識別
    window_id: int = 0                    # 視窗唯一 ID
    window_title: str = ""                # 視窗標題
    module_type: str = ""                 # 模組類型 (例如 "lap_analysis")
    
    # 位置/大小 (使用元組便於序列化)
    geometry: tuple = (0, 0, 400, 300)    # (x, y, width, height)
    old_geometry: tuple = None            # 移動/調整前的幾何形狀
    
    # 模組參數（用於重建視窗）
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Tab 資訊
    tab_index: int = -1
    tab_name: str = ""
    tab_windows: List[Dict] = field(default_factory=list)  # Tab 中的視窗列表
    
    # 同步狀態
    sync_enabled: bool = True             # X 軸同步狀態
    
    # MDI 區域參考 (不序列化)
    mdi_area_index: int = -1              # 所屬的 MDI 區域索引
    
    def to_qrect(self) -> QRect:
        """轉換 geometry 為 QRect"""
        return QRect(*self.geometry)
    
    def old_to_qrect(self) -> Optional[QRect]:
        """轉換 old_geometry 為 QRect"""
        if self.old_geometry:
            return QRect(*self.old_geometry)
        return None


class WindowStateManager(QObject):
    """
    視窗狀態管理器
    
    管理視窗狀態歷史，提供撤銷/重做功能
    
    使用方式：
    1. 在視窗關閉/移動/調整大小前調用 push_state()
    2. 用戶按 Ctrl+Z 時調用 undo()
    3. 用戶按 Ctrl+Y 時調用 redo()
    """
    
    # 信號
    state_restored = pyqtSignal(object)   # 狀態恢復後發射
    undo_available = pyqtSignal(bool)     # 是否可撤銷
    redo_available = pyqtSignal(bool)     # 是否可重做
    
    MAX_HISTORY = 10  # 最大歷史記錄數
    
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        
        self.main_window = main_window
        
        # 歷史堆疊
        self._undo_stack: List[WindowState] = []
        self._redo_stack: List[WindowState] = []
        
        # 暫停記錄標誌（在恢復操作時使用）
        self._recording_paused = False
        
        logger.info("[UNDO] WindowStateManager 初始化完成")
    
    @property
    def can_undo(self) -> bool:
        """是否可以撤銷"""
        return len(self._undo_stack) > 0
    
    @property
    def can_redo(self) -> bool:
        """是否可以重做"""
        return len(self._redo_stack) > 0
    
    def push_state(self, state: WindowState) -> None:
        """
        記錄新狀態
        
        Args:
            state: 要記錄的視窗狀態
        """
        if self._recording_paused:
            logger.debug("[UNDO] 記錄已暫停，跳過")
            return
        
        # 添加到撤銷堆疊
        self._undo_stack.append(state)
        
        # 清空重做堆疊（新操作會使重做失效）
        self._redo_stack.clear()
        
        # 保持堆疊大小在限制內
        while len(self._undo_stack) > self.MAX_HISTORY:
            self._undo_stack.pop(0)
        
        # 發射信號
        self.undo_available.emit(self.can_undo)
        self.redo_available.emit(self.can_redo)
        
        logger.info(f"[UNDO] 記錄狀態: {state.state_type.name} - {state.window_title}")
        logger.debug(f"[UNDO] 堆疊大小: undo={len(self._undo_stack)}, redo={len(self._redo_stack)}")
    
    def undo(self) -> Optional[WindowState]:
        """
        撤銷上一個操作
        
        Returns:
            被恢復的狀態，如果沒有可撤銷的操作則返回 None
        """
        if not self.can_undo:
            logger.warning("[UNDO] 沒有可撤銷的操作")
            return None
        
        # 暫停記錄，避免恢復操作被記錄
        self._recording_paused = True
        
        try:
            state = self._undo_stack.pop()
            
            # 恢復狀態
            self._restore_state(state)
            
            # 添加到重做堆疊
            self._redo_stack.append(state)
            
            # 發射信號
            self.undo_available.emit(self.can_undo)
            self.redo_available.emit(self.can_redo)
            self.state_restored.emit(state)
            
            logger.info(f"[UNDO] ✅ 撤銷成功: {state.state_type.name} - {state.window_title}")
            
            return state
            
        except Exception as e:
            logger.error(f"[UNDO] ❌ 撤銷失敗: {e}")
            return None
        finally:
            self._recording_paused = False
    
    def redo(self) -> Optional[WindowState]:
        """
        重做上一個撤銷的操作
        
        Returns:
            被重做的狀態，如果沒有可重做的操作則返回 None
        """
        if not self.can_redo:
            logger.warning("[UNDO] 沒有可重做的操作")
            return None
        
        self._recording_paused = True
        
        try:
            state = self._redo_stack.pop()
            
            # 對於視窗關閉，重做意味著再次關閉
            if state.state_type == StateType.WINDOW_CLOSE:
                self._close_window_by_id(state.window_id)
            elif state.state_type == StateType.WINDOW_MOVE:
                # 重做移動：使用新位置
                self._move_window(state.window_id, state.to_qrect())
            elif state.state_type == StateType.WINDOW_RESIZE:
                # 重做調整大小：使用新尺寸
                self._resize_window(state.window_id, state.to_qrect())
            
            # 返回撤銷堆疊
            self._undo_stack.append(state)
            
            self.undo_available.emit(self.can_undo)
            self.redo_available.emit(self.can_redo)
            
            logger.info(f"[UNDO] ✅ 重做成功: {state.state_type.name}")
            
            return state
            
        except Exception as e:
            logger.error(f"[UNDO] ❌ 重做失敗: {e}")
            return None
        finally:
            self._recording_paused = False
    
    def _restore_state(self, state: WindowState) -> None:
        """
        根據狀態類型恢復視窗
        
        Args:
            state: 要恢復的狀態
        """
        if state.state_type == StateType.WINDOW_CLOSE:
            self._restore_closed_window(state)
        elif state.state_type == StateType.WINDOW_MOVE:
            self._restore_window_position(state)
        elif state.state_type == StateType.WINDOW_RESIZE:
            self._restore_window_size(state)
        elif state.state_type == StateType.TAB_CLOSE:
            self._restore_closed_tab(state)
    
    def _restore_closed_window(self, state: WindowState) -> None:
        """恢復已關閉的視窗"""
        if not self.main_window:
            logger.error("[UNDO] main_window 未設置")
            return
        
        logger.info(f"[UNDO] 恢復視窗: {state.window_title} ({state.module_type})")
        
        # 使用 AnalysisWindowCreator 重建視窗
        from windows.managers.analysis_window_creator import AnalysisWindowCreator
        
        try:
            creator = AnalysisWindowCreator(self.main_window)
            
            # 根據模組類型重建視窗
            params = state.parameters
            
            # 嘗試找到對應的 Tab
            if state.tab_index >= 0:
                tab_widget = getattr(self.main_window, 'tab_widget', None)
                if not tab_widget:
                    tab_widget = getattr(self.main_window, 'main_tab_widget', None)
                if tab_widget and state.tab_index < tab_widget.count():
                    tab_widget.setCurrentIndex(state.tab_index)
            
            # 使用模組工廠創建視窗
            window = creator.create_analysis_window_with_params(
                module_type=state.module_type,
                title=state.window_title,
                parameters=params,
                geometry=state.to_qrect(),
                sync_enabled=state.sync_enabled
            )
            
            if window:
                logger.info(f"[UNDO] ✅ 視窗恢復成功: {state.window_title}")
            else:
                logger.warning(f"[UNDO] ⚠️ 視窗恢復失敗: {state.window_title}")
                
        except Exception as e:
            logger.error(f"[UNDO] ❌ 恢復視窗時發生錯誤: {e}")
    
    def _restore_window_position(self, state: WindowState) -> None:
        """恢復視窗位置"""
        old_rect = state.old_to_qrect()
        if old_rect:
            self._move_window(state.window_id, old_rect)
            logger.info(f"[UNDO] 恢復位置: ({old_rect.x()}, {old_rect.y()})")
    
    def _restore_window_size(self, state: WindowState) -> None:
        """恢復視窗大小"""
        old_rect = state.old_to_qrect()
        if old_rect:
            self._resize_window(state.window_id, old_rect)
            logger.info(f"[UNDO] 恢復大小: {old_rect.width()}x{old_rect.height()}")
    
    def _restore_closed_tab(self, state: WindowState) -> None:
        """恢復已關閉的 Tab"""
        if not self.main_window:
            return
        
        logger.info(f"[UNDO] 恢復 Tab: {state.tab_name}")
        
        try:
            # 使用 NewTabAdder 重建 Tab
            from windows.managers.new_tab_adder import NewTabAdder
            
            adder = NewTabAdder(self.main_window)
            new_index = adder.add_new_tab(state.tab_name)
            
            if new_index >= 0:
                # 恢復 Tab 中的視窗
                for window_info in state.tab_windows:
                    self._restore_closed_window(WindowState(
                        state_type=StateType.WINDOW_CLOSE,
                        window_title=window_info.get('title', ''),
                        module_type=window_info.get('module_type', ''),
                        geometry=window_info.get('geometry', (0, 0, 400, 300)),
                        parameters=window_info.get('parameters', {}),
                        tab_index=new_index,
                        sync_enabled=window_info.get('sync_enabled', True)
                    ))
                
                logger.info(f"[UNDO] ✅ Tab 恢復成功: {state.tab_name}")
            else:
                logger.warning(f"[UNDO] ⚠️ Tab 恢復失敗: {state.tab_name}")
                
        except Exception as e:
            logger.error(f"[UNDO] ❌ 恢復 Tab 時發生錯誤: {e}")
    
    def _move_window(self, window_id: int, rect: QRect) -> None:
        """移動視窗到指定位置"""
        window = self._find_window_by_id(window_id)
        if window:
            window.move(rect.x(), rect.y())
            logger.info(f"[UNDO] ✅ 視窗已移動到 ({rect.x()}, {rect.y()})")
        else:
            logger.warning(f"[UNDO] ⚠️ 找不到視窗 (id={window_id})，無法移動")
    
    def _resize_window(self, window_id: int, rect: QRect) -> None:
        """調整視窗大小"""
        window = self._find_window_by_id(window_id)
        if window:
            window.setGeometry(rect)
            logger.info(f"[UNDO] ✅ 視窗大小已調整到 {rect.width()}x{rect.height()}")
        else:
            logger.warning(f"[UNDO] ⚠️ 找不到視窗 (id={window_id})，無法調整大小")
    
    def _close_window_by_id(self, window_id: int) -> None:
        """關閉指定 ID 的視窗"""
        window = self._find_window_by_id(window_id)
        if window:
            window.close()
            logger.info(f"[UNDO] ✅ 視窗已關閉")
        else:
            logger.warning(f"[UNDO] ⚠️ 找不到視窗 (id={window_id})，無法關閉")
    
    def _find_window_by_id(self, window_id: int):
        """根據 ID 查找視窗"""
        if not self.main_window:
            logger.debug("[UNDO] main_window 未設置")
            return None
        
        # 嘗試多個可能的 tab widget 屬性名稱
        tab_widget = getattr(self.main_window, 'tab_widget', None)
        if not tab_widget:
            tab_widget = getattr(self.main_window, 'main_tab_widget', None)
        if not tab_widget:
            logger.debug("[UNDO] 找不到 tab_widget")
            return None
        
        # 遍歷所有 Tab 的 MDI 區域
        for i in range(tab_widget.count()):
            tab = tab_widget.widget(i)
            if hasattr(tab, 'subWindowList'):
                for window in tab.subWindowList():
                    if id(window) == window_id:
                        logger.debug(f"[UNDO] ✅ 在 Tab {i} 找到視窗")
                        return window
            # 檢查嵌套的 MDI 區域
            for child in tab.findChildren(object):
                if hasattr(child, 'subWindowList'):
                    for window in child.subWindowList():
                        if id(window) == window_id:
                            logger.debug(f"[UNDO] ✅ 在 Tab {i} 的嵌套 MDI 找到視窗")
                            return window
        
        logger.debug(f"[UNDO] ⚠️ 遍歷所有 Tab 後仍找不到視窗 (id={window_id})")
        return None
    
    def clear_history(self) -> None:
        """清空所有歷史記錄"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.undo_available.emit(False)
        self.redo_available.emit(False)
        logger.info("[UNDO] 歷史記錄已清空")
    
    def get_undo_description(self) -> str:
        """獲取下一個撤銷操作的描述"""
        if not self.can_undo:
            return ""
        state = self._undo_stack[-1]
        return f"撤銷 {state.state_type.name}: {state.window_title}"
    
    def get_redo_description(self) -> str:
        """獲取下一個重做操作的描述"""
        if not self.can_redo:
            return ""
        state = self._redo_stack[-1]
        return f"重做 {state.state_type.name}: {state.window_title}"


# ============================================================================
# 輔助函數 - 用於從視窗創建狀態快照
# ============================================================================

def capture_window_state(window, state_type: StateType, 
                         old_geometry: tuple = None) -> WindowState:
    """
    從視窗捕獲狀態快照
    
    Args:
        window: PopoutSubWindow 或 QMdiSubWindow
        state_type: 狀態類型
        old_geometry: 移動/調整前的幾何形狀（可選）
        
    Returns:
        WindowState 快照
    """
    # 獲取基本信息
    title = window.windowTitle() if hasattr(window, 'windowTitle') else ""
    geom = window.geometry() if hasattr(window, 'geometry') else None
    
    # 獲取模組類型
    module_type = ""
    if hasattr(window, 'module_name'):
        module_type = window.module_name
    elif hasattr(window, 'analysis_module') and window.analysis_module:
        module_type = type(window.analysis_module).__name__
    
    # 獲取參數
    parameters = {}
    if hasattr(window, 'get_current_parameters'):
        try:
            parameters = window.get_current_parameters() or {}
        except:
            pass
    
    # 獲取同步狀態
    sync_enabled = True
    if hasattr(window, 'sync_enabled'):
        sync_enabled = window.sync_enabled
    
    # 獲取 Tab 索引
    tab_index = -1
    mdi_area_index = -1
    parent = window.parent()
    if parent:
        # 嘗試找到所屬的 Tab
        tab_widget = None
        current = parent
        while current:
            if hasattr(current, 'indexOf'):
                tab_widget = current
                break
            current = current.parent() if hasattr(current, 'parent') else None
        
        if tab_widget and hasattr(tab_widget, 'currentIndex'):
            tab_index = tab_widget.currentIndex()
    
    return WindowState(
        state_type=state_type,
        window_id=id(window),
        window_title=title,
        module_type=module_type,
        geometry=(geom.x(), geom.y(), geom.width(), geom.height()) if geom else (0, 0, 400, 300),
        old_geometry=old_geometry,
        parameters=parameters,
        tab_index=tab_index,
        sync_enabled=sync_enabled,
        mdi_area_index=mdi_area_index
    )


def capture_tab_state(tab_widget, tab_index: int) -> WindowState:
    """
    從 Tab 捕獲狀態快照
    
    Args:
        tab_widget: QTabWidget
        tab_index: Tab 索引
        
    Returns:
        WindowState 快照
    """
    tab_name = tab_widget.tabText(tab_index) if tab_widget else ""
    tab = tab_widget.widget(tab_index) if tab_widget else None
    
    # 收集 Tab 中的所有視窗信息
    tab_windows = []
    if tab:
        # 找到 Tab 中的 MDI 區域
        mdi_area = None
        if hasattr(tab, 'subWindowList'):
            mdi_area = tab
        else:
            for child in tab.findChildren(object):
                if hasattr(child, 'subWindowList'):
                    mdi_area = child
                    break
        
        if mdi_area:
            for window in mdi_area.subWindowList():
                state = capture_window_state(window, StateType.WINDOW_CLOSE)
                tab_windows.append({
                    'title': state.window_title,
                    'module_type': state.module_type,
                    'geometry': state.geometry,
                    'parameters': state.parameters,
                    'sync_enabled': state.sync_enabled
                })
    
    return WindowState(
        state_type=StateType.TAB_CLOSE,
        window_title=f"Tab: {tab_name}",
        tab_index=tab_index,
        tab_name=tab_name,
        tab_windows=tab_windows
    )
