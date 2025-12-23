"""
MDI 視窗管理器
統一管理所有 MDI 區域和子視窗操作

提供的功能：
- 視窗排列（平鋪、層疊）
- 視窗狀態控制（最小化、還原、關閉）
- MDI 區域查找
- 視窗統計

從 f1t_gui_main.py 中提取的方法：
- tile_windows()
- cascade_windows()
- minimize_all_windows()
- restore_all_windows()
- close_all_windows()
- close_all_mdi_windows()
- close_all_mdi_windows_in_current_tab()
- get_current_mdi_area()
"""

from typing import Optional, List, TYPE_CHECKING
from PyQt5.QtWidgets import QApplication, QWidget, QMdiSubWindow
from PyQt5.QtCore import QRect

from core.logger import get_logger
from typing import List
from PyQt5.QtWidgets import QMdiSubWindow
from windows.widgets.custom_mdi_area import CustomMdiArea
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtWidgets import QTabWidget

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow, QMdiArea, QTabWidget

logger = get_logger(__name__)


class MDIManager:
    """
    MDI 視窗管理器
    
    負責管理所有 MDI 區域和子視窗操作，包括：
    - 視窗排列（平鋪、層疊）
    - 視窗狀態控制（最小化、還原、關閉）
    - MDI 區域查找
    - 視窗統計
    
    Attributes:
        main_window: 主視窗實例
        tab_widget: QTabWidget 實例（用於分頁切換）
    """
    
    def __init__(self, main_window: 'QMainWindow'):
        """
        初始化 MDI 管理器
        
        Args:
            main_window: 主視窗實例（StyleHMainWindow）
        """
        self.main_window = main_window
        self._tab_widget: Optional['QTabWidget'] = None
        self._custom_mdi_area_class = None  # 延遲載入避免循環依賴
        
        logger.debug("[MDIManager] Initialized")
    
    @property
    def tab_widget(self) -> Optional['QTabWidget']:
        """取得分頁元件"""
        if self._tab_widget is None:
            self._tab_widget = getattr(self.main_window, 'tab_widget', None)
        return self._tab_widget
    
    @tab_widget.setter
    def tab_widget(self, value: 'QTabWidget') -> None:
        """設置分頁元件"""
        self._tab_widget = value
    
    def _get_custom_mdi_area_class(self):
        """延遲載入 CustomMdiArea 類別避免循環依賴"""
        if self._custom_mdi_area_class is None:
            from f1t_gui_main import CustomMdiArea
            self._custom_mdi_area_class = CustomMdiArea
        return self._custom_mdi_area_class
    
    # ==================== MDI 區域查找 ====================
    
    def get_current_mdi_area(self, auto_create_tab: bool = False) -> Optional['QMdiArea']:
        """
        獲取當前分頁的 MDI 區域
        
        Args:
            auto_create_tab: 是否在主頁時自動創建分頁（默認 False）
                            只有在用戶主動操作（如點擊模組）時才應設為 True
        
        Returns:
            CustomMdiArea 實例或 None
        """
        try:
            if self.tab_widget is None:
                logger.error("[MDIManager] tab_widget is None")
                return None
            
            # 獲取當前分頁
            current_tab = self.tab_widget.currentWidget()
            if not current_tab:
                logger.error("[MDIManager] Cannot get current tab")
                return None
            
            current_index = self.tab_widget.currentIndex()
            CustomMdiArea = self._get_custom_mdi_area_class()
            
            logger.debug(f"[MDIManager] Current tab index: {current_index}, "
                        f"objectName: {current_tab.objectName()}")
            
            # 檢查是否為主頁（歡迎頁）
            is_welcome_tab = (current_index == 0 and 
                             current_tab.objectName() == "welcome_tab")
            
            if is_welcome_tab and auto_create_tab:
                logger.debug("[MDIManager] On welcome tab, auto creating new tab")
                self.main_window.add_new_tab()
                current_tab = self.tab_widget.currentWidget()
            elif is_welcome_tab:
                logger.debug("[MDIManager] On welcome tab, no MDI area")
                return None
            
            # 檢查當前分頁是否就是 MDI 區域
            if isinstance(current_tab, CustomMdiArea):
                logger.debug(f"[MDIManager] Current tab is CustomMdiArea: {current_tab.objectName()}")
                return current_tab
            
            # 遞歸查找 MDI 區域
            mdi_area = self._find_mdi_area_recursive(current_tab, CustomMdiArea)
            
            if mdi_area:
                logger.debug(f"[MDIManager] Found MDI area: {mdi_area.objectName()}")
            else:
                logger.debug(f"[MDIManager] No MDI area found in tab: {current_tab.objectName()}")
            
            return mdi_area
            
        except Exception as e:
            logger.error(f"[MDIManager] Failed to get current MDI area: {e}")
            return None
    
    def _find_mdi_area_recursive(self, widget: QWidget, mdi_class) -> Optional['QMdiArea']:
        """遞歸查找 MDI 區域"""
        if isinstance(widget, mdi_class):
            return widget
        
        if hasattr(widget, 'children'):
            for child in widget.children():
                if isinstance(child, QWidget):
                    result = self._find_mdi_area_recursive(child, mdi_class)
                    if result:
                        return result
        return None
    
    def find_mdi_area_in_tab(self, tab_widget: QWidget) -> Optional['QMdiArea']:
        """
        在指定分頁中查找 MDI 區域
        
        Args:
            tab_widget: 分頁元件
            
        Returns:
            MDI 區域或 None
        """
        CustomMdiArea = self._get_custom_mdi_area_class()
        
        if isinstance(tab_widget, CustomMdiArea):
            return tab_widget
        
        # 使用 findChildren 查找
        children = tab_widget.findChildren(CustomMdiArea)
        return children[0] if children else None
    
    # ==================== 視窗排列 ====================
    
    def tile_windows(self, mdi_area: Optional['QMdiArea'] = None) -> None:
        """
        平鋪視窗 - 智能平鋪 MDI 區域中的所有子視窗
        
        Args:
            mdi_area: 指定的 MDI 區域，若為 None 則使用當前活動的 MDI 區域
        """
        if mdi_area is None:
            mdi_area = self.get_current_mdi_area()
        
        if mdi_area is None:
            logger.debug("[MDIManager] No MDI area for tile_windows")
            return
        
        try:
            # 獲取可見且非固定的子視窗
            subwindows = self._get_tileable_subwindows(mdi_area)
            
            if not subwindows:
                logger.debug("[MDIManager] No visible subwindows to tile")
                return
            
            logger.debug(f"[MDIManager] Tiling {len(subwindows)} windows")
            
            # 計算可用空間（右邊和下方保留 10px）
            margin = 10
            available_width = mdi_area.width() - margin
            available_height = mdi_area.height() - margin
            
            # 計算最佳的行列配置
            num_windows = len(subwindows)
            cols = max(1, int(num_windows ** 0.5))
            if cols * cols < num_windows:
                cols += 1
            rows = max(1, (num_windows + cols - 1) // cols)
            
            # 計算每個視窗的尺寸
            window_width = available_width // cols
            window_height = available_height // rows
            
            # 套用最小尺寸限制（如果不會超出範圍）
            min_w, min_h = 250, 150
            if max(window_width, min_w) * cols <= available_width:
                window_width = max(window_width, min_w)
            if max(window_height, min_h) * rows <= available_height:
                window_height = max(window_height, min_h)
            
            logger.debug(f"[MDIManager] Grid: {rows}x{cols}, Window size: {window_width}x{window_height}")
            
            # 排列視窗
            for i, subwindow in enumerate(subwindows):
                row = i // cols
                col = i % cols
                x = col * window_width
                y = row * window_height
                
                subwindow.setGeometry(x, y, window_width, window_height)
                subwindow.showNormal()
                subwindow.raise_()
                QApplication.processEvents()
            
            # 最終同步：統一所有視窗尺寸
            self._sync_window_sizes(subwindows)
            
            mdi_area.update()
            logger.debug(f"[MDIManager] Tiled {num_windows} windows successfully")
            
        except Exception as e:
            logger.error(f"[MDIManager] Tile windows failed: {e}")
    
    def cascade_windows(self, mdi_area: Optional['QMdiArea'] = None) -> None:
        """
        層疊視窗 - 將 MDI 區域中的所有子視窗以階梯式排列
        
        Args:
            mdi_area: 指定的 MDI 區域，若為 None 則使用當前活動的 MDI 區域
        """
        if mdi_area is None:
            mdi_area = self.get_current_mdi_area()
        
        if mdi_area is None:
            logger.debug("[MDIManager] No MDI area for cascade_windows")
            return
        
        try:
            # 獲取可見且非固定的子視窗
            subwindows = self._get_tileable_subwindows(mdi_area)
            
            if not subwindows:
                logger.debug("[MDIManager] No visible subwindows to cascade")
                return
            
            logger.debug(f"[MDIManager] Cascading {len(subwindows)} windows")
            
            # 層疊參數
            cascade_offset = 30
            base_width = 500
            base_height = 350
            start_x = 20
            start_y = 20
            
            # 計算最大可層疊的視窗數
            max_windows = min(
                len(subwindows),
                (mdi_area.width() - base_width) // cascade_offset + 1,
                (mdi_area.height() - base_height) // cascade_offset + 1
            )
            max_windows = max(1, max_windows)
            
            # 層疊排列視窗
            for i, subwindow in enumerate(subwindows):
                offset_multiplier = i % max_windows
                x = start_x + offset_multiplier * cascade_offset
                y = start_y + offset_multiplier * cascade_offset
                
                subwindow.setGeometry(x, y, base_width, base_height)
                subwindow.showNormal()
                subwindow.raise_()
            
            # 將最後一個視窗帶到前面
            if subwindows:
                subwindows[-1].activateWindow()
                subwindows[-1].raise_()
            
            mdi_area.update()
            logger.debug(f"[MDIManager] Cascaded {len(subwindows)} windows successfully")
            
        except Exception as e:
            logger.error(f"[MDIManager] Cascade windows failed: {e}")
    
    # ==================== 視窗狀態控制 ====================
    
    def minimize_all_windows(self, mdi_area: Optional['QMdiArea'] = None) -> None:
        """
        最小化所有視窗
        
        Args:
            mdi_area: 指定的 MDI 區域，若為 None 則使用當前活動的 MDI 區域
        """
        if mdi_area is None:
            mdi_area = self.get_current_mdi_area()
        
        if mdi_area is None:
            return
        
        try:
            subwindows = self._get_tileable_subwindows(mdi_area)
            
            for subwindow in subwindows:
                subwindow.showMinimized()
            
            mdi_area.update()
            logger.debug(f"[MDIManager] Minimized {len(subwindows)} windows")
            
        except Exception as e:
            logger.error(f"[MDIManager] Minimize all windows failed: {e}")
    
    def restore_all_windows(self, mdi_area: Optional['QMdiArea'] = None) -> None:
        """
        還原所有視窗
        
        Args:
            mdi_area: 指定的 MDI 區域，若為 None 則使用當前活動的 MDI 區域
        """
        if mdi_area is None:
            mdi_area = self.get_current_mdi_area()
        
        if mdi_area is None:
            return
        
        try:
            for subwindow in mdi_area.subWindowList():
                if not subwindow.property("is_welcome_fixed"):
                    subwindow.showNormal()
            
            mdi_area.update()
            logger.debug("[MDIManager] Restored all windows")
            
        except Exception as e:
            logger.error(f"[MDIManager] Restore all windows failed: {e}")
    
    def close_all_windows(self, mdi_area: Optional['QMdiArea'] = None) -> None:
        """
        關閉所有視窗
        
        Args:
            mdi_area: 指定的 MDI 區域，若為 None 則使用當前活動的 MDI 區域
        """
        if mdi_area is None:
            mdi_area = self.get_current_mdi_area()
        
        if mdi_area is None:
            return
        
        try:
            subwindows = self._get_tileable_subwindows(mdi_area)
            
            for subwindow in subwindows:
                subwindow.close()
            
            mdi_area.update()
            logger.debug(f"[MDIManager] Closed {len(subwindows)} windows")
            
        except Exception as e:
            logger.error(f"[MDIManager] Close all windows failed: {e}")
    
    def close_all_mdi_windows_in_current_tab(self) -> None:
        """關閉當前分頁中的所有 MDI 視窗"""
        mdi_area = self.get_current_mdi_area()
        if mdi_area:
            self.close_all_windows(mdi_area)
    
    # ==================== 輔助方法 ====================
    
    def _get_tileable_subwindows(self, mdi_area: 'QMdiArea') -> List[QMdiSubWindow]:
        """
        獲取可排列的子視窗（可見且非固定）
        
        Args:
            mdi_area: MDI 區域
            
        Returns:
            可排列的子視窗列表
        """
        all_subwindows = mdi_area.subWindowList()
        return [
            sw for sw in all_subwindows
            if sw.isVisible()
            and not sw.isWindowModified()
            and not sw.property("is_welcome_fixed")
        ]
    
    def _sync_window_sizes(self, subwindows: List[QMdiSubWindow]) -> None:
        """
        同步所有視窗尺寸（使用最小共同尺寸）
        
        Args:
            subwindows: 子視窗列表
        """
        if not subwindows:
            return
        
        try:
            # 收集所有視窗的實際尺寸
            actual_sizes = [(sw.size().width(), sw.size().height()) for sw in subwindows]
            
            # 找到最小的共同尺寸
            min_width = min(size[0] for size in actual_sizes)
            min_height = min(size[1] for size in actual_sizes)
            
            # 將所有視窗設置為相同尺寸
            for subwindow in subwindows:
                current_pos = subwindow.pos()
                subwindow.setGeometry(current_pos.x(), current_pos.y(), min_width, min_height)
                QApplication.processEvents()
                
        except Exception as e:
            logger.debug(f"[MDIManager] Sync window sizes failed: {e}")
    
    def get_window_count(self, mdi_area: Optional['QMdiArea'] = None) -> int:
        """
        獲取 MDI 區域中的視窗數量
        
        Args:
            mdi_area: 指定的 MDI 區域，若為 None 則使用當前活動的 MDI 區域
            
        Returns:
            視窗數量
        """
        if mdi_area is None:
            mdi_area = self.get_current_mdi_area()
        
        if mdi_area is None:
            return 0
        
        return len(self._get_tileable_subwindows(mdi_area))
    
    def get_all_mdi_areas(self) -> List['QMdiArea']:
        """
        獲取所有分頁中的 MDI 區域
        
        Returns:
            MDI 區域列表
        """
        mdi_areas = []
        
        if self.tab_widget is None:
            return mdi_areas
        
        CustomMdiArea = self._get_custom_mdi_area_class()
        
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                mdi_area = self.find_mdi_area_in_tab(tab)
                if mdi_area:
                    mdi_areas.append(mdi_area)
        
        return mdi_areas
