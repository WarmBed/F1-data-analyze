# -*- coding: utf-8 -*-
"""
F1T GUI - Standalone Windows
=============================

可調整大小的獨立視窗類別。

從 f1t_gui_main.py 提取 (原始行號: 5782-6336, 555 行)
提取日期: 2025-06-14
"""

import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QApplication
)

# 引入翻譯函數
try:
    from core.gui_i18n import tr
except ImportError:
    def tr(key, default=None, *args, **kwargs):
        return default if default else key

# 設定日誌
logger = logging.getLogger(__name__)


class ResizableStandaloneWindow(QMainWindow):
    """可調整大小的獨立視窗"""
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.resize_margin = 10  # 調整邊框的寬度
        self.resizing = False
        self.resize_direction = None
        
        # 創建可視的調整邊框
        self.setStyleSheet("""
            QMainWindow {
                border: 2px solid #CCCCCC;
                background-color: #FFFFFF;
            }
            QMainWindow:hover {
                border: 2px solid #999999;
            }
        """)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件"""
        if event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            event.accept()
            return
            
        # 更新游標
        direction = self.get_resize_direction(event.pos())
        if direction:
            # 取消上方調整大小功能，移除 'top' 相關游標
            if direction in ['bottom']:  # 只保留 bottom，移除 top
                self.setCursor(Qt.SizeVerCursor)
            elif direction in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif direction in ['bottom-right']:  # 移除 top-left
                self.setCursor(Qt.SizeFDiagCursor)
            elif direction in ['bottom-left']:  # 移除 top-right
                self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件"""
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
        
    def get_resize_direction(self, pos):
        """判斷調整方向 (取消上方調整) - ResizableStandaloneWindow"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        margin = self.resize_margin
        
        # 角落區域 (優先判斷) - 取消上方相關的角落調整
        # if x <= margin and y <= margin:
        #     return 'top-left'
        # elif x >= w - margin and y <= margin:
        #     return 'top-right'
        if x <= margin and y >= h - margin:
            return 'bottom-left'
        elif x >= w - margin and y >= h - margin:
            return 'bottom-right'
        # 邊緣區域 - 取消上方調整，保留左、右、下
        # elif y <= margin:
        #     return 'top'
        elif y >= h - margin:
            return 'bottom'
        elif x <= margin:
            return 'left'
        elif x >= w - margin:
            return 'right'
        
        return None
        
    def perform_resize(self, global_pos):
        """執行調整大小"""
        if not self.resize_direction:
            return
            
        delta = global_pos - self.resize_start_pos
        old_geometry = self.resize_start_geometry
        
        new_x = old_geometry.x()
        new_y = old_geometry.y()
        new_width = old_geometry.width()
        new_height = old_geometry.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geometry.x() + delta.x()
            new_width = old_geometry.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geometry.width() + delta.x()
            
        # 取消 top 調整，只保留 bottom (ResizableStandaloneWindow)
        # if 'top' in self.resize_direction:
        #     new_y = old_geometry.y() + delta.y()
        #     new_height = old_geometry.height() - delta.y()
        if 'bottom' in self.resize_direction:
            new_height = old_geometry.height() + delta.y()
            
        # 限制最小大小
        min_size = self.minimumSize()
        if new_width < min_size.width():
            if 'left' in self.resize_direction:
                new_x = old_geometry.x() + old_geometry.width() - min_size.width()
            new_width = min_size.width()
            
        if new_height < min_size.height():
            # 取消 top 調整功能 (ResizableStandaloneWindow)
            # if 'top' in self.resize_direction:
            #     new_y = old_geometry.y() + old_geometry.height() - min_size.height()
            new_height = min_size.height()
            
        # 應用新的幾何形狀
        self.setGeometry(new_x, new_y, new_width, new_height)
        
    def paintEvent(self, event):
        """繪製事件 - 添加可視邊框提示"""
        super().paintEvent(event)
        
        # 在視窗邊緣繪製調整提示
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 右下角調整提示
        corner_size = 15
        corner_color = QColor(100, 100, 100, 150)
        painter.fillRect(
            self.width() - corner_size, 
            self.height() - corner_size, 
            corner_size, 
            corner_size, 
            corner_color
        )
        
        # 繪製調整線條
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        for i in range(3):
            offset = 3 + i * 3
            painter.drawLine(
                self.width() - offset, self.height() - 3,
                self.width() - 3, self.height() - offset
            )


class TabStandaloneWindow(ResizableStandaloneWindow):
    """分頁彈出的獨立視窗，繼承自 ResizableStandaloneWindow"""
    
    def __init__(self, tab_name, mdi_area, tab_index, main_window):
        """
        初始化分頁獨立視窗
        
        Args:
            tab_name: 分頁名稱
            mdi_area: CustomMdiArea 實例
            tab_index: 分頁索引
            main_window: 主視窗引用
        """
        super().__init__()
        
        self.tab_name = tab_name
        self.mdi_area = mdi_area
        self.tab_index = tab_index
        self.main_window = main_window
        self.sync_enabled = True  # 預設啟用參數同步
        
        # 設置工具列
        self.setup_toolbar()
        
        # 連接主視窗參數變更信號（如果需要同步）
        self._connect_parameter_signals()
        
        logger.debug(f"[TAB_STANDALONE] 獨立視窗已創建: '{tab_name}'")
    
    def setup_toolbar(self):
        """設定工具列（6 個按鈕）"""
        toolbar = self.addToolBar("控制")
        toolbar.setObjectName("TabStandaloneToolbar")
        toolbar.setMovable(False)
        
        # 按鈕 1: 返回主畫面
        return_action = toolbar.addAction(tr("return_to_main", "返回主畫面"))
        return_action.setToolTip(tr("return_tab_to_main", "返回分頁到主視窗"))
        return_action.triggered.connect(self._on_return_to_main)
        
        toolbar.addSeparator()
        
        # 按鈕 2: 同步開關
        self.sync_action = toolbar.addAction(tr("sync_on", "同步: ON"))
        self.sync_action.setToolTip(tr("toggle_param_sync", "切換參數同步（年份/賽事/賽段）"))
        self.sync_action.triggered.connect(self.toggle_sync)
        
        toolbar.addSeparator()
        
        # 按鈕 3: Show All Data
        show_all_action = toolbar.addAction(tr("show_all_data", "Show All Data"))
        show_all_action.setToolTip(tr("reset_all_mdi_views", "重置所有 MDI 子視窗的 XY 軸視圖"))
        show_all_action.triggered.connect(self.show_all_data)
        
        # 按鈕 4: Close All Windows
        close_all_action = toolbar.addAction(tr("close_all_windows", "Close All Windows"))
        close_all_action.setToolTip(tr("close_all_mdi_subwindows", "關閉所有 MDI 子視窗"))
        close_all_action.triggered.connect(self.close_all_windows)
        
        toolbar.addSeparator()
        
        # 按鈕 5: Tile Windows
        tile_action = toolbar.addAction(tr("tile_windows", "Tile Windows"))
        tile_action.setToolTip(tr("tile_all_subwindows", "平鋪所有子視窗"))
        tile_action.triggered.connect(self.tile_windows)
        
        # 按鈕 6: Cascade Windows
        cascade_action = toolbar.addAction(tr("cascade_windows", "Cascade Windows"))
        cascade_action.setToolTip(tr("cascade_all_subwindows", "層疊所有子視窗"))
        cascade_action.triggered.connect(self.cascade_windows)
        
        logger.debug(f"[TAB_STANDALONE] 工具列已設置（6 個按鈕）")
    
    def _connect_parameter_signals(self):
        """連接主視窗參數變更信號"""
        try:
            if hasattr(self.main_window, 'year_combo'):
                self.main_window.year_combo.currentIndexChanged.connect(self._on_main_parameter_changed)
            if hasattr(self.main_window, 'race_combo'):
                self.main_window.race_combo.currentIndexChanged.connect(self._on_main_parameter_changed)
            if hasattr(self.main_window, 'session_combo'):
                self.main_window.session_combo.currentIndexChanged.connect(self._on_main_parameter_changed)
            logger.debug(f"[TAB_STANDALONE] 已連接主視窗參數變更信號")
        except Exception as e:
            logger.debug(f"[TAB_STANDALONE] 連接參數信號失敗: {e}")
    
    def _disconnect_parameter_signals(self):
        """斷開主視窗參數變更信號"""
        try:
            if hasattr(self.main_window, 'year_combo'):
                self.main_window.year_combo.currentIndexChanged.disconnect(self._on_main_parameter_changed)
            if hasattr(self.main_window, 'race_combo'):
                self.main_window.race_combo.currentIndexChanged.disconnect(self._on_main_parameter_changed)
            if hasattr(self.main_window, 'session_combo'):
                self.main_window.session_combo.currentIndexChanged.disconnect(self._on_main_parameter_changed)
            logger.debug(f"[TAB_STANDALONE] 已斷開主視窗參數變更信號")
        except Exception as e:
            logger.debug(f"[TAB_STANDALONE] 斷開參數信號失敗: {e}")
    
    def toggle_sync(self):
        """切換參數同步狀態"""
        self.sync_enabled = not self.sync_enabled
        new_text = tr("sync_on", "同步: ON") if self.sync_enabled else tr("sync_off", "同步: OFF")
        self.sync_action.setText(new_text)
        status = tr("enabled", "啟用") if self.sync_enabled else tr("disabled", "禁用")
        logger.debug(f"[TAB_STANDALONE] 參數同步已{status}")
    
    def _on_main_parameter_changed(self):
        """主視窗參數變更時的處理"""
        if not self.sync_enabled:
            logger.debug(f"[TAB_STANDALONE] 同步已禁用，忽略參數變更")
            return
        
        logger.debug(f"[TAB_STANDALONE] 檢測到主視窗參數變更，準備更新子視窗...")
        
        # 獲取當前參數
        try:
            year = int(self.main_window.year_combo.currentText()) if hasattr(self.main_window, 'year_combo') else 2025
            race = self.main_window.race_combo.currentText() if hasattr(self.main_window, 'race_combo') else "Japan"
            session = self.main_window.session_combo.currentText() if hasattr(self.main_window, 'session_combo') else "R"
            
            logger.debug(f"[TAB_STANDALONE] 新參數: {year} {race} {session}")
            
            # 更新所有 MDI 子視窗
            self._update_all_subwindows(year, race, session)
            
        except Exception as e:
            logger.debug(f"[TAB_STANDALONE] 更新子視窗失敗: {e}")
    
    def _update_all_subwindows(self, year, race, session):
        """更新所有 MDI 子視窗的參數"""
        if not self.mdi_area:
            return
        
        subwindows = self.mdi_area.subWindowList()
        updated_count = 0
        
        for sub_win in subwindows:
            try:
                # 嘗試調用子視窗的 update_current_window 方法
                if hasattr(sub_win, 'update_current_window'):
                    sub_win.update_current_window()
                    updated_count += 1
            except Exception as e:
                logger.debug(f"[TAB_STANDALONE] 更新子視窗失敗: {e}")
        
        logger.debug(f"[TAB_STANDALONE] 已更新 {updated_count}/{len(subwindows)} 個子視窗")
    
    def show_all_data(self):
        """重置所有子視窗視圖"""
        if not self.mdi_area:
            logger.debug(f"[TAB_STANDALONE] MDI 區域不存在")
            return
        
        subwindows = self.mdi_area.subWindowList()
        reset_count = 0
        
        for sub_win in subwindows:
            try:
                widget = sub_win.widget()
                if hasattr(widget, 'reset_chart_view'):
                    widget.reset_chart_view()
                    reset_count += 1
                elif hasattr(widget, 'chart_widget') and hasattr(widget.chart_widget, 'reset_view'):
                    widget.chart_widget.reset_view()
                    reset_count += 1
            except Exception as e:
                logger.debug(f"[TAB_STANDALONE] 重置視圖失敗: {e}")
        
        logger.debug(f"[TAB_STANDALONE] 已重置 {reset_count}/{len(subwindows)} 個視窗")
    
    def close_all_windows(self):
        """關閉所有子視窗"""
        if not self.mdi_area:
            logger.debug(f"[TAB_STANDALONE] MDI 區域不存在")
            return
        
        self.mdi_area.closeAllSubWindows()
        logger.debug(f"[TAB_STANDALONE] 已關閉所有子視窗")
    
    def tile_windows(self):
        """重新排列視窗 - 智能平鋪獨立視窗中的所有子視窗（與主 GUI 邏輯一致）"""
        if not self.mdi_area:
            logger.debug(f"[TAB_STANDALONE] MDI 區域不存在")
            return
        
        try:
            # 步驟 1: 獲取所有子視窗並過濾出可見的視窗
            all_subwindows = self.mdi_area.subWindowList()
            # 只包含可見且未關閉的視窗，並排除固定的歡迎頁面視窗
            subwindows = [
                sw for sw in all_subwindows 
                if sw.isVisible() 
                and not sw.isWindowModified() 
                and not sw.property("is_welcome_fixed")  # 排除固定視窗
            ]
            logger.debug(f"[TAB_STANDALONE] 找到 {len(all_subwindows)} 個子視窗，其中 {len(subwindows)} 個可見且非固定")
            
            if not subwindows:
                logger.debug(f"[TAB_STANDALONE] 沒有可見的非固定子視窗需要排列")
                return
            
            logger.debug(f"[TAB_STANDALONE] 準備排列 {len(subwindows)} 個視窗")
            
            # 步驟 2: 計算可用空間（無邊距，完全填滿）
            available_width = self.mdi_area.width()
            available_height = self.mdi_area.height()
            logger.debug(f"[TAB_STANDALONE] MDI 區域大小: {self.mdi_area.width()}x{self.mdi_area.height()}")
            logger.debug(f"[TAB_STANDALONE] 可用空間: {available_width}x{available_height}")
            
            # 步驟 3: 計算最佳的行列配置
            num_windows = len(subwindows)
            logger.debug(f"[TAB_STANDALONE] 視窗數量: {num_windows}")
            
            if num_windows == 0:
                logger.debug(f"[TAB_STANDALONE] 視窗數量為 0，退出")
                return
            
            # 計算列數（基於平方根）
            cols = int(num_windows ** 0.5)
            logger.debug(f"[TAB_STANDALONE] 初始計算 cols: {cols}")
            
            if cols == 0:  # 防止除零錯誤
                cols = 1
                logger.debug(f"[TAB_STANDALONE] cols 修正為 1")
            
            if cols * cols < num_windows:
                cols += 1
                logger.debug(f"[TAB_STANDALONE] cols 調整為: {cols}")
            
            # 計算行數
            rows = (num_windows + cols - 1) // cols
            logger.debug(f"[TAB_STANDALONE] 計算得到 rows: {rows}")
            
            if rows == 0:  # 額外保護
                rows = 1
                logger.debug(f"[TAB_STANDALONE] rows 修正為 1")
            
            # 步驟 4: 計算每個視窗的尺寸
            window_width = available_width // cols if cols > 0 else available_width
            window_height = available_height // rows if rows > 0 else available_height
            logger.debug(f"[TAB_STANDALONE] 每個視窗尺寸: {window_width}x{window_height}")
            
            # 步驟 5: 確保最小尺寸
            min_width, min_height = 250, 150
            window_width = max(window_width, min_width)
            window_height = max(window_height, min_height)
            logger.debug(f"[TAB_STANDALONE] 調整後視窗尺寸: {window_width}x{window_height}")
            
            # 步驟 6: 開始排列視窗
            logger.debug(f"[TAB_STANDALONE] 開始排列 {len(subwindows)} 個視窗，配置: {rows}行 x {cols}列")
            
            # 預檢查：確保所有視窗的基本設定一致
            logger.debug(f"[TAB_STANDALONE] ========== 預檢查視窗設定 ==========")
            for i, subwindow in enumerate(subwindows):
                widget = subwindow.widget()
                if widget:
                    min_size = widget.minimumSize()
                    size_policy = widget.sizePolicy()
                    logger.debug(f"[TAB_STANDALONE] 視窗 {i}: 最小尺寸({min_size.width()}x{min_size.height()}), 尺寸策略({size_policy.horizontalPolicy()}x{size_policy.verticalPolicy()})")
                    
                    # 檢查是否有調試方法可以調用
                    if hasattr(widget, 'debug_window_status'):
                        logger.debug(f"[TAB_STANDALONE] 調用視窗 {i} 的狀態報告:")
                        widget.debug_window_status()
            logger.debug(f"[TAB_STANDALONE] ========== 預檢查完成 ==========")
            
            # 步驟 7: 逐個設置視窗位置和尺寸
            for i, subwindow in enumerate(subwindows):
                row = i // cols
                col = i % cols
                
                x = col * window_width
                y = row * window_height
                
                logger.debug(f"[TAB_STANDALONE] 視窗 {i}: 位置({x}, {y}) 尺寸({window_width}, {window_height})")
                
                # 設置視窗位置和尺寸
                subwindow.setGeometry(x, y, window_width, window_height)
                
                # 確保視窗可見和正常化
                subwindow.showNormal()
                subwindow.raise_()
                
                # 強制處理事件，確保尺寸更新完成
                QApplication.processEvents()
                
                # 檢查實際尺寸並調試
                actual_size = subwindow.size()
                logger.debug(f"[TAB_STANDALONE] 視窗 {i} 實際尺寸: {actual_size.width()}x{actual_size.height()}")
                
                if actual_size.width() != window_width or actual_size.height() != window_height:
                    logger.debug(f"[TAB_STANDALONE] 視窗 {i} 尺寸不匹配！目標: {window_width}x{window_height}, 實際: {actual_size.width()}x{actual_size.height()}")
                    
                    # 嘗試重新設置
                    subwindow.resize(window_width, window_height)
                    QApplication.processEvents()
                    final_size = subwindow.size()
                    logger.debug(f"[TAB_STANDALONE] 視窗 {i} 重設後尺寸: {final_size.width()}x{final_size.height()}")
            
            # 步驟 8: 最終同步步驟 - 確保所有視窗尺寸一致
            logger.debug(f"[TAB_STANDALONE] ========== 開始最終尺寸同步 ==========")
            
            # 收集所有視窗的實際尺寸
            actual_sizes = []
            for i, subwindow in enumerate(subwindows):
                size = subwindow.size()
                actual_sizes.append((size.width(), size.height()))
                logger.debug(f"[TAB_STANDALONE] 視窗 {i} 當前尺寸: {size.width()}x{size.height()}")
            
            # 找到最小的共同尺寸（確保所有視窗都能適應）
            if actual_sizes:
                min_common_width = min(size[0] for size in actual_sizes)
                min_common_height = min(size[1] for size in actual_sizes)
                logger.debug(f"[TAB_STANDALONE] 統一目標尺寸: {min_common_width}x{min_common_height}")
                
                # 將所有視窗設置為相同尺寸
                for i, subwindow in enumerate(subwindows):
                    current_pos = subwindow.pos()
                    subwindow.setGeometry(current_pos.x(), current_pos.y(), min_common_width, min_common_height)
                    QApplication.processEvents()
                    
                    final_size = subwindow.size()
                    logger.debug(f"[TAB_STANDALONE] 視窗 {i} 最終尺寸: {final_size.width()}x{final_size.height()}")
            
            logger.debug(f"[TAB_STANDALONE] ========== 尺寸同步完成 ==========")
            
            # 步驟 9: 調試 - 檢查每個子視窗的邊距設定
            logger.debug(f"[TAB_STANDALONE] ========== 子視窗邊距檢查 ==========")
            for i, subwindow in enumerate(subwindows):
                widget = subwindow.widget()
                logger.debug(f"[TAB_STANDALONE] 子視窗 {i}: {subwindow.windowTitle()}")
                
                # 檢查 MDI 子視窗的邊距
                margins = subwindow.contentsMargins()
                logger.debug(f"[TAB_STANDALONE]   MDI 邊距: left={margins.left()}, top={margins.top()}, right={margins.right()}, bottom={margins.bottom()}")
                
                # 檢查子視窗的 frameGeometry vs geometry
                frame_geo = subwindow.frameGeometry()
                geo = subwindow.geometry()
                logger.debug(f"[TAB_STANDALONE]   frameGeometry: {frame_geo.width()}x{frame_geo.height()}")
                logger.debug(f"[TAB_STANDALONE]   geometry: {geo.width()}x{geo.height()}")
                logger.debug(f"[TAB_STANDALONE]   邊框差異: width={frame_geo.width()-geo.width()}, height={frame_geo.height()-geo.height()}")
                
                if widget:
                    widget_size = widget.size()
                    logger.debug(f"[TAB_STANDALONE]   內部 widget 尺寸: {widget_size.width()}x{widget_size.height()}")
            
            logger.debug(f"[TAB_STANDALONE] ========== 邊距檢查完成 ==========")
            logger.debug(f"[TAB_STANDALONE] 已平鋪 {num_windows} 個子視窗")
            
        except Exception as e:
            logger.debug(f"[TAB_STANDALONE] 平鋪失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def cascade_windows(self):
        """層疊子視窗"""
        if not self.mdi_area:
            logger.debug(f"[TAB_STANDALONE] MDI 區域不存在")
            return
        
        self.mdi_area.cascadeSubWindows()
        logger.debug(f"[TAB_STANDALONE] 已層疊所有子視窗")
    
    def _on_return_to_main(self):
        """返回主畫面按鈕處理"""
        logger.debug(f"[TAB_STANDALONE] 用戶點擊返回按鈕")
        if self.main_window and hasattr(self.main_window, 'pop_back_in_tab'):
            self.main_window.pop_back_in_tab(self.tab_index)
    
    def closeEvent(self, event):
        """關閉事件：自動返回主視窗"""
        logger.debug(f"[TAB_STANDALONE] 獨立視窗正在關閉...")
        
        # 斷開參數信號
        self._disconnect_parameter_signals()
        
        # 修復：檢查是否仍在彈出列表中（避免重複調用 pop_back_in_tab）
        if self.main_window and hasattr(self.main_window, 'pop_back_in_tab'):
            if self.tab_index in self.main_window.popped_out_tabs:
                logger.debug(f"[TAB_STANDALONE] 自動返回主視窗（closeEvent 觸發）")
                self.main_window.pop_back_in_tab(self.tab_index)
            else:
                logger.debug(f"[TAB_STANDALONE] 分頁 {self.tab_index} 已經返回（跳過重複返回）")
        
        event.accept()
        logger.debug(f"[TAB_STANDALONE] 獨立視窗已關閉")
