"""
TabManager - 分頁管理器

此管理器負責管理所有分頁相關操作，從 f1t_gui_main.py 中提取
約 18 個分頁相關方法，提供統一的分頁管理介面。

重構效果：
- 重構前：18 個方法散落在 StyleHMainWindow 中
- 重構後：統一的 TabManager 類別
- 職責分離：分頁操作與主視窗邏輯解耦

使用方式：
    # 在 StyleHMainWindow.__init__ 中初始化
    from windows.managers import TabManager
    self.tab_manager = TabManager(self)
    
    # 設置分頁功能
    self.tab_manager.setup_tab_widget(self.tab_widget)

Author: F1T Development Team
Date: 2025-12-16
"""

import logging
from typing import TYPE_CHECKING, Dict, Any, Optional, Set

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMenu, QInputDialog, 
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from core.logger import get_logger
from typing import Dict
from typing import Optional
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QMenu
from windows.widgets.custom_mdi_area import CustomMdiArea
from PyQt5.QtWidgets import QLineEdit
from typing import Any
from PyQt5.QtWidgets import QTabWidget

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow, QTabWidget

logger = logging.getLogger(__name__)


def tr(key: str, default: str = '') -> str:
    """多語言翻譯函數"""
    try:
        from core.gui_i18n import tr as gui_tr
        return gui_tr(key, default)
    except ImportError:
        return default


def get_gui_language() -> str:
    """取得當前 GUI 語言"""
    try:
        from core.gui_i18n import get_gui_language as get_lang
        return get_lang()
    except ImportError:
        return 'en'


class TabManager:
    """
    分頁管理器
    
    統一管理所有分頁相關操作，包括：
    - 新增、關閉、重新命名分頁
    - 彈出/返回獨立視窗
    - 分頁右鍵選單
    - 分頁外觀管理
    
    Attributes:
        main_window: 主視窗實例
        tab_widget: QTabWidget 實例
        popped_out_tabs: 彈出分頁追蹤字典
        mdi_areas: MDI 區域列表
    """
    
    def __init__(self, main_window: 'QMainWindow'):
        """
        初始化分頁管理器
        
        Args:
            main_window: 主視窗實例（StyleHMainWindow）
        """
        self.main_window = main_window
        self.tab_widget: Optional['QTabWidget'] = None
        # 🆕 使用主視窗的 popped_out_tabs 而非獨立維護
        # self.popped_out_tabs: Dict[int, Dict[str, Any]] = {}
        self.mdi_areas: list = []
        self._tab_count_label = None
        
        logger.debug("[TabManager] Initialized")
    
    @property
    def popped_out_tabs(self) -> Dict[int, Dict[str, Any]]:
        """取得主視窗的 popped_out_tabs（向後兼容）"""
        return getattr(self.main_window, 'popped_out_tabs', {})
    
    def setup_tab_widget(self, tab_widget: 'QTabWidget', tab_count_label=None) -> None:
        """
        設置分頁元件
        
        Args:
            tab_widget: QTabWidget 實例
            tab_count_label: 分頁數量標籤（可選）
        """
        self.tab_widget = tab_widget
        self._tab_count_label = tab_count_label
        
        # 設置右鍵選單
        self._setup_context_menu()
        
        # 連接分頁切換信號
        if self.tab_widget:
            self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        logger.debug("[TabManager] Tab widget setup completed")
    
    def _setup_context_menu(self) -> None:
        """為 QTabWidget 設定右鍵選單"""
        if self.tab_widget is None:
            return
        
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        tab_bar.customContextMenuRequested.connect(self._show_context_menu)
        
        logger.debug("[TabManager] Context menu setup completed")
    
    def _show_context_menu(self, pos) -> None:
        """顯示分頁右鍵選單"""
        if self.tab_widget is None:
            return
            
        tab_bar = self.tab_widget.tabBar()
        tab_index = tab_bar.tabAt(pos)
        
        if tab_index == -1:
            return
        
        # HOME 主頁不顯示選單
        if tab_index == 0:
            return
        
        is_popped_out = (tab_index in self.popped_out_tabs)
        
        menu = QMenu(self.main_window)
        
        if is_popped_out:
            return_action = menu.addAction(tr('tab_return_menu', 'Return to Main Window'))
            # 使用主視窗的方法（向後兼容）
            return_action.triggered.connect(lambda: self.main_window.pop_back_in_tab(tab_index))
            menu.addSeparator()
            rename_action = menu.addAction(tr('tab_rename_menu', 'Rename Tab'))
            rename_action.triggered.connect(lambda: self.main_window.rename_tab(tab_index))
        else:
            popout_action = menu.addAction(tr('tab_popout_menu', 'Pop Out as Window'))
            # 使用主視窗的方法（向後兼容）
            popout_action.triggered.connect(lambda: self.main_window.pop_out_tab(tab_index))
            menu.addSeparator()
            rename_action = menu.addAction(tr('tab_rename_menu', 'Rename Tab'))
            rename_action.triggered.connect(lambda: self.main_window.rename_tab(tab_index))
        
        global_pos = tab_bar.mapToGlobal(pos)
        menu.exec_(global_pos)
        logger.debug(f"[TabManager] Show tab {tab_index} context menu (popped_out={is_popped_out})")
    
    def add_new_tab(self) -> int:
        """
        新增分頁
        
        Returns:
            新分頁的索引
        """
        if self.tab_widget is None:
            return -1
        
        # 延遲導入避免循環依賴
        from f1t_gui_main import CustomMdiArea
        
        tab_count = self.tab_widget.count()
        
        # 根據語言生成標籤名稱
        current_lang = get_gui_language()
        if current_lang == "zh":
            number_str = self._convert_to_chinese_number(tab_count)
        else:
            number_str = str(tab_count)
        tab_name = tr("tab_page", "Tab {number}").format(number=number_str)
        
        # 創建空白 MDI 工作區
        new_mdi_area = CustomMdiArea()
        new_mdi_area.setObjectName(f"MdiArea_{tab_count}")
        
        index = self.tab_widget.addTab(new_mdi_area, tab_name)
        self.tab_widget.setCurrentIndex(index)
        
        self.mdi_areas.append(new_mdi_area)
        
        logger.debug(f"[TabManager] Created new tab: {tab_name}")
        self.update_tab_count()
        
        return index
    
    def create_tab_for_workspace(self, tab_name: str) -> 'CustomMdiArea':
        """
        專門用於 Workspace 載入的分頁創建方法
        
        Args:
            tab_name: 分頁名稱
            
        Returns:
            CustomMdiArea: 新創建的 MDI 區域
        """
        if self.tab_widget is None:
            return None
        
        from f1t_gui_main import CustomMdiArea
        
        tab_count = self.tab_widget.count()
        
        new_mdi_area = CustomMdiArea()
        new_mdi_area.setObjectName(f"MdiArea_{tab_count}")
        
        index = self.tab_widget.addTab(new_mdi_area, tab_name)
        self.mdi_areas.append(new_mdi_area)
        
        logger.debug(f"[TabManager] Created tab for workspace: '{tab_name}' (index={index})")
        return new_mdi_area
    
    def close_tab(self, index: int) -> None:
        """
        關閉指定索引的分頁
        
        Args:
            index: 分頁索引
        """
        if self.tab_widget is None:
            return
        
        # 最後一個分頁時，創建歡迎頁
        if self.tab_widget.count() <= 1:
            logger.debug("[TabManager] Closing last tab, creating welcome page")
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            if widget:
                widget.deleteLater()
            
            # 創建新的歡迎頁
            welcome_tab = self.main_window.create_welcome_tab()
            welcome_tab.setObjectName("welcome_tab")
            self.tab_widget.addTab(welcome_tab, tr("home_page", "Home"))
            self.tab_widget.setCurrentIndex(0)
            
            logger.debug("[TabManager] Created new welcome page")
            self.update_tab_count()
            return
        
        # 正常關閉分頁
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        
        if widget:
            widget.deleteLater()
        
        logger.debug(f"[TabManager] Closed tab #{index}")
        self.update_tab_count()
    
    def close_current_tab(self) -> None:
        """關閉當前分頁"""
        if self.tab_widget is None:
            return
            
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)
    
    def rename_tab(self, tab_index: int) -> None:
        """
        重新命名分頁
        
        Args:
            tab_index: 分頁索引
        """
        if self.tab_widget is None:
            return
        
        # 禁止重命名主頁
        if tab_index == 0:
            logger.debug(f"[TabManager] Cannot rename home tab")
            return
        
        current_name = self.tab_widget.tabText(tab_index).replace("🔗 ", "")
        
        new_name, ok = QInputDialog.getText(
            self.main_window,
            tr('tab_rename_dialog_title', 'Rename Tab'),
            tr('tab_rename_dialog_label', 'Enter new name:'),
            QLineEdit.Normal,
            current_name
        )
        
        if not ok or not new_name:
            logger.debug(f"[TabManager] User cancelled rename")
            return
        
        new_name = new_name.strip()
        
        if new_name == current_name:
            logger.debug(f"[TabManager] Tab name unchanged")
            return
        
        final_name = self._get_unique_tab_name(new_name)
        is_popped_out = (tab_index in self.popped_out_tabs)
        
        if is_popped_out:
            self.tab_widget.setTabText(tab_index, f"🔗 {final_name}")
            
            # 同步更新獨立視窗標題
            popout_info = self.popped_out_tabs[tab_index]
            standalone_window = popout_info['standalone_window']
            from f1t_gui_main import APP_FULL_TITLE
            standalone_window.setWindowTitle(f"{final_name} - {APP_FULL_TITLE}")
            popout_info['tab_name'] = final_name
            
            logger.debug(f"[TabManager] Renamed popped out tab {tab_index} to '{final_name}'")
        else:
            self.tab_widget.setTabText(tab_index, final_name)
            logger.debug(f"[TabManager] Renamed tab {tab_index} to '{final_name}'")
    
    def pop_out_tab(self, tab_index: int) -> None:
        """
        彈出指定分頁為獨立視窗
        
        Args:
            tab_index: 分頁索引
        """
        if self.tab_widget is None:
            return
        
        # 檢查是否為 HOME 主頁
        if tab_index == 0:
            logger.debug(f"[TabManager] Cannot pop out home tab")
            return
        
        # 檢查是否已經彈出
        if tab_index in self.popped_out_tabs:
            logger.debug(f"[TabManager] Tab {tab_index} already popped out")
            return
        
        from f1t_gui_main import CustomMdiArea, TabStandaloneWindow, APP_FULL_TITLE
        
        tab_widget = self.tab_widget.widget(tab_index)
        tab_name = self.tab_widget.tabText(tab_index)
        
        if not tab_widget or not isinstance(tab_widget, CustomMdiArea):
            logger.debug(f"[TabManager] Tab {tab_index} is not MDI area")
            return
        
        logger.debug(f"[TabManager] Starting pop out tab {tab_index}: {tab_name}")
        logger.debug(f"[TabManager] MDI sub-windows: {len(tab_widget.subWindowList())}")
        
        # 創建佔位符
        placeholder = QWidget()
        placeholder.setObjectName("PopoutPlaceholder")
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_label = QLabel(tr('tab_placeholder_label', 'Tab "{name}" is in a separate window').format(name=tab_name))
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("font-size: 16px; color: #666666;")
        placeholder_layout.addWidget(placeholder_label)
        
        # 創建獨立視窗
        standalone_window = TabStandaloneWindow(
            tab_name=tab_name,
            mdi_area=tab_widget,
            tab_index=tab_index,
            main_window=self.main_window
        )
        
        # 計算視窗大小
        main_size = self.main_window.size()
        window_width = int(main_size.width() * 0.8)
        window_height = int(main_size.height() * 0.8)
        standalone_window.resize(window_width, window_height)
        standalone_window.setWindowTitle(f"{tab_name} - {APP_FULL_TITLE}")
        
        # 移植 MDI 工作區
        self.tab_widget.removeTab(tab_index)
        self.tab_widget.insertTab(tab_index, placeholder, tab_name)
        standalone_window.setCentralWidget(tab_widget)
        
        # 強制顯示
        tab_widget.setVisible(True)
        tab_widget.show()
        tab_widget.update()
        
        for sub_win in tab_widget.subWindowList():
            sub_win.setVisible(True)
            sub_win.show()
            sub_win.update()
        
        standalone_window.show()
        
        # 延遲檢查 MDI 可見性
        QTimer.singleShot(100, lambda: self._ensure_mdi_visible(tab_widget))
        
        # 更新分頁標籤外觀
        self._update_tab_appearance(tab_index, is_popped_out=True)
        
        # 記錄到主視窗的追蹤字典
        self.main_window.popped_out_tabs[tab_index] = {
            'standalone_window': standalone_window,
            'original_widget': tab_widget,
            'placeholder': placeholder,
            'tab_name': tab_name
        }
        
        logger.debug(f"[TabManager] Pop out success: tab {tab_index}")
    
    def pop_back_in_tab(self, tab_index: int) -> None:
        """
        將彈出的分頁返回主視窗
        
        Args:
            tab_index: 分頁索引
        """
        try:
            if tab_index not in self.popped_out_tabs:
                logger.debug(f"[TabManager] Tab {tab_index} is not popped out")
                return
            
            logger.debug(f"[TabManager] Starting return tab {tab_index}")
            
            popout_info = self.popped_out_tabs[tab_index]
            standalone_window = popout_info['standalone_window']
            mdi_area = popout_info['original_widget']
            placeholder = popout_info['placeholder']
            tab_name = popout_info['tab_name']
            
            logger.debug(f"[TabManager] MDI sub-windows: {len(mdi_area.subWindowList())}")
            
            # 先從主視窗的字典移除
            del self.main_window.popped_out_tabs[tab_index]
            logger.debug(f"[TabManager] Removed tab {tab_index} from tracking")
            
            # 從獨立視窗取出 MDI 區域
            standalone_window.takeCentralWidget()
            
            # 移除佔位符，恢復 MDI 工作區
            self.tab_widget.removeTab(tab_index)
            self.tab_widget.insertTab(tab_index, mdi_area, tab_name)
            self.tab_widget.setCurrentIndex(tab_index)
            
            placeholder.deleteLater()
            
            # 恢復分頁標籤正常樣式
            self._update_tab_appearance(tab_index, is_popped_out=False)
            
            standalone_window.close()
            
            logger.debug(f"[TabManager] Return success: tab {tab_index}")
            
        except KeyError:
            logger.debug(f"[TabManager] Tab {tab_index} already returned")
        except Exception as e:
            logger.debug(f"[TabManager] Return failed: {type(e).__name__}: {e}")
    
    def _update_tab_appearance(self, tab_index: int, is_popped_out: bool) -> None:
        """更新分頁標籤外觀"""
        try:
            if self.tab_widget is None:
                return
                
            tab_name = self.tab_widget.tabText(tab_index)
            tab_name_clean = tab_name.replace("🔗 ", "")
            
            if is_popped_out:
                new_tab_text = f"🔗 {tab_name_clean}"
                self.tab_widget.setTabText(tab_index, new_tab_text)
                
                tab_bar = self.tab_widget.tabBar()
                tab_bar.setTabTextColor(tab_index, QColor(102, 102, 102))
                
                logger.debug(f"[TabManager] Tab {tab_index} appearance set to popped out")
            else:
                self.tab_widget.setTabText(tab_index, tab_name_clean)
                
                tab_bar = self.tab_widget.tabBar()
                tab_bar.setTabTextColor(tab_index, QColor(0, 0, 0))
                
                logger.debug(f"[TabManager] Tab {tab_index} appearance restored")
                
        except Exception as e:
            logger.debug(f"[TabManager] Update appearance failed: {e}")
    
    def _ensure_mdi_visible(self, mdi_area) -> None:
        """確保 MDI 區域可見"""
        try:
            if not mdi_area:
                return
            
            is_visible = mdi_area.isVisible()
            geometry = mdi_area.geometry()
            sub_count = len(mdi_area.subWindowList())
            
            logger.debug(f"[TabManager] MDI visibility check: visible={is_visible}, "
                        f"size={geometry.width()}x{geometry.height()}, subs={sub_count}")
            
            if not is_visible or geometry.width() == 0 or geometry.height() == 0:
                logger.debug(f"[TabManager] MDI abnormal, fixing...")
                mdi_area.setVisible(True)
                mdi_area.show()
                mdi_area.update()
                
                if geometry.width() == 0 or geometry.height() == 0:
                    mdi_area.resize(800, 600)
                    logger.debug(f"[TabManager] Set MDI size to 800x600")
            
            for sub_win in mdi_area.subWindowList():
                if not sub_win.isVisible():
                    logger.debug(f"[TabManager] Showing hidden sub-window: {sub_win.windowTitle()}")
                    sub_win.setVisible(True)
                    sub_win.show()
                    
        except Exception as e:
            logger.debug(f"[TabManager] MDI visibility check failed: {e}")
    
    def _on_tab_changed(self, index: int) -> None:
        """分頁切換事件處理"""
        try:
            # 調用主視窗的工具欄更新方法
            if hasattr(self.main_window, '_check_and_update_toolbar_status'):
                self.main_window._check_and_update_toolbar_status()
            
            # 切換到 Home 頁面時，重新排列視窗
            if index == 0 and self.tab_widget:
                tab_widget = self.tab_widget.widget(index)
                if tab_widget:
                    from f1t_gui_main import CustomMdiArea
                    
                    def find_and_arrange():
                        mdi_areas = tab_widget.findChildren(CustomMdiArea)
                        if mdi_areas:
                            mdi_area = mdi_areas[0]
                            if hasattr(mdi_area, 'arrange_welcome_windows'):
                                logger.debug(f"[TabManager] Switching to Home, rearranging windows")
                                mdi_area.arrange_welcome_windows()
                    
                    QTimer.singleShot(200, find_and_arrange)
        except Exception as e:
            logger.error(f"[TabManager] Tab changed handler failed: {e}")
    
    def update_tab_count(self) -> None:
        """更新分頁數量顯示"""
        if self.tab_widget is None:
            return
            
        count = self.tab_widget.count()
        
        if self._tab_count_label:
            self._tab_count_label.setText(f"Tab: {count}")
        
        # 同步更新主視窗的 tab_count_label
        if hasattr(self.main_window, 'tab_count_label'):
            self.main_window.tab_count_label.setText(f"Tab: {count}")
    
    def _get_unique_tab_name(self, base_name: str) -> str:
        """獲取唯一的分頁名稱"""
        if self.tab_widget is None:
            return base_name
        
        existing_names = []
        for i in range(self.tab_widget.count()):
            name = self.tab_widget.tabText(i).replace("🔗 ", "")
            existing_names.append(name)
        
        if base_name not in existing_names:
            return base_name
        
        counter = 1
        while True:
            new_name = f"{base_name} ({counter})"
            if new_name not in existing_names:
                return new_name
            counter += 1
    
    def _convert_to_chinese_number(self, num: int) -> str:
        """將數字轉換為中文數字"""
        chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]
        if 1 <= num <= 20:
            return chinese_nums[num - 1]
        else:
            return str(num)
    
    def get_current_mdi_area(self, auto_create_tab: bool = False):
        """
        獲取當前分頁的 MDI 區域
        
        Args:
            auto_create_tab: 是否在沒有 MDI 時自動創建分頁
            
        Returns:
            CustomMdiArea 或 None
        """
        if self.tab_widget is None:
            return None
        
        from f1t_gui_main import CustomMdiArea
        
        current_index = self.tab_widget.currentIndex()
        current_widget = self.tab_widget.widget(current_index)
        
        if isinstance(current_widget, CustomMdiArea):
            return current_widget
        
        # 在當前分頁中查找 MDI 區域
        if current_widget:
            mdi_areas = current_widget.findChildren(CustomMdiArea)
            if mdi_areas:
                return mdi_areas[0]
        
        # 自動創建分頁
        if auto_create_tab:
            logger.debug("[TabManager] No MDI area, creating new tab")
            self.add_new_tab()
            new_index = self.tab_widget.currentIndex()
            new_widget = self.tab_widget.widget(new_index)
            if isinstance(new_widget, CustomMdiArea):
                return new_widget
        
        return None
    
    def check_and_hide_tabs(self) -> None:
        """檢查標籤欄狀態（確保可見）"""
        if self.tab_widget is None:
            return
            
        logger.debug("[TabManager] Checking tab bar status...")
        logger.debug(f"[TabManager] TabBar visible: {self.tab_widget.tabBar().isVisible()}")
        logger.debug(f"[TabManager] TabBar height: {self.tab_widget.tabBar().height()}")
        
        # 確保標籤欄顯示
        self.tab_widget.tabBar().setVisible(True)
        logger.debug(f"[TabManager] Tab bar enabled")
