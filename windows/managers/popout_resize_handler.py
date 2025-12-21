"""
PopoutResizeHandler - 視窗調整大小處理器

從 PopoutSubWindow 中提取的調整大小邏輯。
負責處理視窗邊緣拖曳調整大小的功能。

Phase 5.3 重構 - 從 f1t_gui_main.py 提取
"""

import logging
from typing import TYPE_CHECKING, Optional, Tuple

from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QCursor
from core.logger import get_logger
from typing import Optional
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QRect
from typing import Tuple

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtGui import QMouseEvent

logger = logging.getLogger(__name__)


class PopoutResizeHandler:
    """
    視窗調整大小處理器
    
    負責處理 PopoutSubWindow 中的視窗調整大小操作，包括：
    - 偵測滑鼠位置對應的調整方向
    - 執行調整大小
    - 更新游標樣式
    - 限制最小/最大大小
    """
    
    # 調整大小的最小限制
    MIN_WIDTH = 200
    MIN_HEIGHT = 150
    
    # 游標樣式映射
    CURSOR_MAP = {
        'bottom': Qt.SizeVerCursor,
        'left': Qt.SizeHorCursor,
        'right': Qt.SizeHorCursor,
        'bottom-left': Qt.SizeBDiagCursor,
        'bottom-right': Qt.SizeFDiagCursor,
    }
    
    def __init__(self, popout_window: 'QWidget', detection_margin: int = 10):
        """
        初始化調整大小處理器
        
        Args:
            popout_window: PopoutSubWindow 實例
            detection_margin: 邊緣偵測區域寬度（像素）
        """
        self.window = popout_window
        self.detection_margin = detection_margin
        
        # 調整狀態
        self.resizing = False
        self.resize_direction: Optional[str] = None
        self.resize_start_pos: Optional[QPoint] = None
        self.resize_start_geometry: Optional[QRect] = None
        
        # 游標緩存
        self._cursor_cache = {}
        self._current_cursor: Optional[Qt.CursorShape] = None
        
    def get_resize_direction(self, pos: QPoint) -> Optional[str]:
        """
        判斷調整方向
        
        根據滑鼠位置判斷應該使用哪個方向調整大小。
        注意：已取消上方調整功能，只支援左、右、下方向。
        
        Args:
            pos: 滑鼠位置（相對於視窗）
            
        Returns:
            調整方向字串，如 'left', 'right', 'bottom', 'bottom-left', 'bottom-right'
            如果不在調整區域則返回 None
        """
        x, y = pos.x(), pos.y()
        w, h = self.window.width(), self.window.height()
        margin = self.detection_margin
        
        # 角落區域 (優先判斷) - 已取消上方相關的角落
        if x <= margin and y >= h - margin:
            return 'bottom-left'
        elif x >= w - margin and y >= h - margin:
            return 'bottom-right'
        # 邊緣區域 - 已取消上方調整
        elif y >= h - margin:
            return 'bottom'
        elif x <= margin:
            return 'left'
        elif x >= w - margin:
            return 'right'
        
        return None
    
    def start_resize(self, event: 'QMouseEvent') -> bool:
        """
        開始調整大小
        
        Args:
            event: 滑鼠按下事件
            
        Returns:
            如果成功開始調整則返回 True
        """
        if event.button() != Qt.LeftButton:
            return False
            
        direction = self.get_resize_direction(event.pos())
        if not direction:
            return False
            
        self.resizing = True
        self.resize_direction = direction
        self.resize_start_pos = event.globalPos()
        self.resize_start_geometry = self.window.geometry()
        
        return True
    
    def perform_resize(self, global_pos: QPoint) -> None:
        """
        執行調整大小
        
        Args:
            global_pos: 滑鼠全局位置
        """
        if not self.resize_direction or not self.resize_start_pos or not self.resize_start_geometry:
            return
            
        delta = global_pos - self.resize_start_pos
        old_geo = self.resize_start_geometry
        
        new_x = old_geo.x()
        new_y = old_geo.y()
        new_width = old_geo.width()
        new_height = old_geo.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geo.x() + delta.x()
            new_width = old_geo.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geo.width() + delta.x()
            
        if 'bottom' in self.resize_direction:
            new_height = old_geo.height() + delta.y()
            
        # 限制最小大小
        if new_width < self.MIN_WIDTH:
            if 'left' in self.resize_direction:
                new_x = old_geo.x() + old_geo.width() - self.MIN_WIDTH
            new_width = self.MIN_WIDTH
            
        if new_height < self.MIN_HEIGHT:
            new_height = self.MIN_HEIGHT
            
        # 限制在 MDI 區域內
        parent_mdi = getattr(self.window, 'parent_mdi', None)
        if parent_mdi:
            mdi_rect = parent_mdi.rect()
            
            if new_x < 0:
                new_x = 0
            if new_y < 0:
                new_y = 0
            if new_x + new_width > mdi_rect.width():
                if 'right' in self.resize_direction:
                    new_width = mdi_rect.width() - new_x
                else:
                    new_x = mdi_rect.width() - new_width
            if new_y + new_height > mdi_rect.height():
                if 'bottom' in self.resize_direction:
                    new_height = mdi_rect.height() - new_y
                else:
                    new_y = mdi_rect.height() - new_height
            
        # 應用新的幾何形狀
        self.window.setGeometry(new_x, new_y, new_width, new_height)
    
    def end_resize(self) -> None:
        """結束調整大小"""
        self.resizing = False
        self.resize_direction = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        
        # 恢復箭頭游標
        self._set_cursor(Qt.ArrowCursor)
    
    def update_cursor(self, pos: QPoint) -> bool:
        """
        根據滑鼠位置更新游標
        
        Args:
            pos: 滑鼠位置
            
        Returns:
            如果需要設置特殊游標則返回 True
        """
        direction = self.get_resize_direction(pos)
        
        if direction:
            cursor_shape = self.CURSOR_MAP.get(direction, Qt.ArrowCursor)
            self._set_cursor(cursor_shape)
            return True
        else:
            self._set_cursor(Qt.ArrowCursor)
            return False
    
    def _set_cursor(self, cursor_shape: Qt.CursorShape) -> None:
        """
        設置游標（帶緩存，避免重複設置）
        
        Args:
            cursor_shape: 游標形狀
        """
        if cursor_shape != self._current_cursor:
            self.window.setCursor(cursor_shape)
            self._current_cursor = cursor_shape
    
    def reset_cursor(self) -> None:
        """重置游標為箭頭"""
        self._set_cursor(Qt.ArrowCursor)
    
    @property
    def is_resizing(self) -> bool:
        """是否正在調整大小"""
        return self.resizing
    
    def handle_mouse_press(self, event: 'QMouseEvent') -> bool:
        """
        處理滑鼠按下事件
        
        Args:
            event: 滑鼠事件
            
        Returns:
            如果事件被處理則返回 True
        """
        return self.start_resize(event)
    
    def handle_mouse_move(self, event: 'QMouseEvent') -> bool:
        """
        處理滑鼠移動事件
        
        Args:
            event: 滑鼠事件
            
        Returns:
            如果事件被處理則返回 True
        """
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            return True
        
        # 即使沒有在調整，也要更新游標
        return self.update_cursor(event.pos())
    
    def handle_mouse_release(self, event: 'QMouseEvent') -> bool:
        """
        處理滑鼠釋放事件
        
        Args:
            event: 滑鼠事件
            
        Returns:
            如果事件被處理則返回 True
        """
        if event.button() == Qt.LeftButton and self.resizing:
            self.end_resize()
            return True
        return False
    
    def handle_leave(self) -> None:
        """處理滑鼠離開事件"""
        if not self.resizing:
            self.reset_cursor()
