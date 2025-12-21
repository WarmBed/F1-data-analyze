# -*- coding: utf-8 -*-
"""
TabPopOuter - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from core.gui_i18n import tr
from core.logger import get_logger
from windows.widgets.standalone_windows import TabStandaloneWindow
from config.version import APP_FULL_TITLE

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class TabPopOuter:
    """從 f1t_gui_main.py 提取的 pop_out_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def pop_out_tab(self, tab_index):
        """彈出指定分頁為獨立視窗"""
        try:
            # 檢查是否為 HOME 主頁
            if tab_index == 0:
                logger.debug(f"[TAB_POPOUT] {tr('home_tab_no_popout')}")
                return
            
            # 檢查是否已經彈出
            if tab_index in self.main_window.popped_out_tabs:
                logger.debug(f"[TAB_POPOUT] {tr('tab_already_popped')}")
                return
            
            # 獲取分頁內容和名稱
            tab_widget = self.main_window.tab_widget.widget(tab_index)
            tab_name = self.main_window.tab_widget.tabText(tab_index)
            
            if not tab_widget:
                logger.debug(f"[TAB_POPOUT] Cannot get tab {tab_index} content")
                return
            
            # 檢查是否為 CustomMdiArea
            if not isinstance(tab_widget, CustomMdiArea):
                logger.debug(f"[TAB_POPOUT] Tab {tab_index} is not MDI area")
                return
            
            logger.debug(f"[TAB_POPOUT] {tr('tab_starting_popout').format(index=tab_index, name=tab_name)}")
            logger.debug(f"[TAB_POPOUT] 📊 MDI 子視窗數量: {len(tab_widget.subWindowList())}")
            
            # 創建佔位符 widget（保持分頁索引不變）
            placeholder = QWidget()
            placeholder.setObjectName("PopoutPlaceholder")
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_label = QLabel(tr('tab_placeholder_label').format(name=tab_name))
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setStyleSheet("font-size: 16px; color: #666666;")
            placeholder_layout.addWidget(placeholder_label)
            
            # 創建獨立視窗（複用 ResizableStandaloneWindow）
            standalone_window = TabStandaloneWindow(
                tab_name=tab_name,
                mdi_area=tab_widget,
                tab_index=tab_index,
                main_window=self.main_window
            )
            
            # 計算視窗大小（主視窗的 80%）
            main_size = self.main_window.size()
            window_width = int(main_size.width() * 0.8)
            window_height = int(main_size.height() * 0.8)
            standalone_window.resize(window_width, window_height)
            
            # 設置視窗標題
            standalone_window.setWindowTitle(f"{tab_name} - {APP_FULL_TITLE}")
            
            # ✅ 關鍵修復：先從 QTabWidget 移除，再設置到獨立視窗
            # 這樣可以保持 MDI 區域的 parent 關係正確
            self.main_window.tab_widget.removeTab(tab_index)
            self.main_window.tab_widget.insertTab(tab_index, placeholder, tab_name)
            
            # 移植 MDI 工作區到獨立視窗
            standalone_window.setCentralWidget(tab_widget)
            
            # ✅ 關鍵修復：強制 MDI 區域顯示和更新
            tab_widget.setVisible(True)
            tab_widget.show()
            tab_widget.update()
            
            # 強制更新所有 MDI 子視窗
            for sub_win in tab_widget.subWindowList():
                sub_win.setVisible(True)
                sub_win.show()
                sub_win.update()
            
            logger.debug(f"[TAB_POPOUT] 🔄 已強制更新 MDI 區域和 {len(tab_widget.subWindowList())} 個子視窗")
            
            # 顯示獨立視窗
            standalone_window.show()
            
            # 再次確認 MDI 區域可見性
            QTimer.singleShot(100, lambda: self.main_window._ensure_mdi_visible(tab_widget))
            logger.debug(f"[TAB_POPOUT] 🔍 已設置延遲檢查 MDI 可見性")
            
            # 更新分頁標籤為灰色 + 🔗 圖標
            self.main_window._update_tab_appearance(tab_index, is_popped_out=True)
            
            # 記錄到追蹤字典
            self.main_window.popped_out_tabs[tab_index] = {
                'standalone_window': standalone_window,
                'original_widget': tab_widget,
                'placeholder': placeholder,
                'tab_name': tab_name
            }
            
            logger.debug(f"[TAB_POPOUT] {tr('tab_popout_success').format(index=tab_index)}")
            logger.debug(f"[TAB_POPOUT] Current popped out tabs: {len(self.main_window.popped_out_tabs)}")
            
        except Exception as e:
            logger.debug(f"[TAB_POPOUT] Pop out failed: {e}")
            import traceback
            traceback.print_exc()
