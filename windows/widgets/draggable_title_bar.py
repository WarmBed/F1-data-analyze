# -*- coding: utf-8 -*-
"""
F1T GUI - DraggableTitleBar
============================

可拖拽的自定義標題欄，支援 Snap 預覽、同步控制、連動功能。

從 f1t_gui_main.py 提取 (原始行號: 2797-3452, 656 行)
提取日期: 2025-06-14
"""

import logging
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMenu

# 引入翻譯函數
try:
    from core.gui_i18n import tr
except ImportError:
    def tr(key, *args, **kwargs):
        return key

# 設定日誌
logger = logging.getLogger(__name__)


# SnapZone 枚舉佔位符 - 實際使用時從主程式引入
class SnapZone:
    """Snap 區域枚舉佔位符"""
    NONE = 0
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
    TOP_LEFT = 5
    TOP_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_RIGHT = 8


class DraggableTitleBar(QWidget):
    """可拖拽的自定義標題欄"""
    
    def __init__(self, parent_window, title=""):
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(20)
        self.dragging = False
        self.drag_position = QPoint()
        
        # 創建標題欄布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        
        # 標題標籤
        self.title_label = QLabel(title)
        self.title_label.setObjectName("SubWindowTitle")
        layout.addWidget(self.title_label)
        
        # [LINK] 接收同步控制按鈕
        self.sync_btn = QPushButton("S")
        self.sync_btn.setObjectName("SyncButton")
        self.sync_btn.setFixedSize(16, 16)
        self.sync_btn.setToolTip(tr('sync_button_tooltip_enabled', 'Receive sync from main: Enabled (S) / Disabled (X)'))
        self.sync_btn.setCheckable(True)
        self.sync_btn.setChecked(True)  # 預設啟用
        self.sync_btn.clicked.connect(self.toggle_x_sync)
        layout.addWidget(self.sync_btn)
        
        # [LINKAGE] 個別連動控制按鈕
        self.linkage_btn = QPushButton("L")
        self.linkage_btn.setObjectName("LinkageButton")
        self.linkage_btn.setFixedSize(16, 16)
        self.linkage_btn.setToolTip(tr('linkage_button_tooltip_enabled', 'Individual linkage: Enabled (L) / Disabled (X)'))
        self.linkage_btn.setCheckable(True)
        self.linkage_btn.setChecked(True)  # 預設啟用
        self.linkage_btn.clicked.connect(self.toggle_individual_linkage)
        layout.addWidget(self.linkage_btn)
        
        # [DRIVER_LAP_SYNC] 車手與圈數同步控制按鈕（僅遙測模組）
        self.driver_lap_sync_btn = QPushButton("D")
        self.driver_lap_sync_btn.setObjectName("DriverLapSyncButton")
        self.driver_lap_sync_btn.setFixedSize(16, 16)
        self.driver_lap_sync_btn.setToolTip(tr('driver_lap_sync_tooltip_enabled', 'Sync driver & lap with main window: Enabled (D) / Disabled (X)'))
        self.driver_lap_sync_btn.setCheckable(True)
        self.driver_lap_sync_btn.setChecked(True)  # 預設啟用
        self.driver_lap_sync_btn.clicked.connect(self.toggle_driver_lap_sync)
        # 只有遙測模組才顯示此按鈕
        self.driver_lap_sync_btn.setVisible(False)  # 預設隱藏，由模組控制
        layout.addWidget(self.driver_lap_sync_btn)
        
        # 初始化顏色狀態 - 確保預設綠色正確顯示
        logger.debug(f"[GREEN] 接收同步初始化為啟動狀態")
        
        layout.addStretch()
        
        # [HOT] 恢復按鈕（針對極小視窗）
        restore_btn = QPushButton("⟲")
        restore_btn.setObjectName("RestoreButton")
        restore_btn.setFixedSize(16, 16)
        restore_btn.setToolTip(tr('restore_normal_size', 'Restore Normal Size'))
        restore_btn.clicked.connect(self.restore_normal_size)
        layout.addWidget(restore_btn)
        
        # 設定按鈕（放在最小化按鈕左邊）
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.setFixedSize(16, 16)
        settings_btn.setToolTip(tr('window_settings', 'Window Settings'))
        settings_btn.clicked.connect(self.parent_window.show_settings_dialog)
        layout.addWidget(settings_btn)
        
        # 標準視窗控制按鈕
        minimize_btn = QPushButton("─")
        minimize_btn.setObjectName("WindowControlButton")
        minimize_btn.setFixedSize(16, 16)
        minimize_btn.setToolTip(tr('minimize', 'Minimize'))
        minimize_btn.clicked.connect(self.parent_window.custom_minimize)
        layout.addWidget(minimize_btn)
        
        maximize_btn = QPushButton("□")
        maximize_btn.setObjectName("WindowControlButton")
        maximize_btn.setFixedSize(16, 16)
        maximize_btn.setToolTip(tr('maximize_restore', 'Maximize/Restore'))
        maximize_btn.clicked.connect(self.parent_window.toggle_maximize)
        layout.addWidget(maximize_btn)
        
        # 彈出按鈕
        self.popout_btn = QPushButton("⧉")
        self.popout_btn.setObjectName("PopoutButton")
        self.popout_btn.setFixedSize(16, 16)
        self.popout_btn.setToolTip(tr('popout_tooltip'))
        self.popout_btn.clicked.connect(self.parent_window.toggle_popout)
        layout.addWidget(self.popout_btn)
        
        # 關閉按鈕
        close_btn = QPushButton("✕")
        close_btn.setObjectName("WindowControlButton")
        close_btn.setFixedSize(16, 16)
        close_btn.setToolTip(tr('close_tooltip'))
        close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(close_btn)
        
    def restore_normal_size(self):
        """恢復視窗到正常大小"""
        if hasattr(self.parent_window, 'content_widget') and self.parent_window.content_widget:
            # 根據內容類型設置合適的大小
            if hasattr(self.parent_window.content_widget, 'chart_type'):
                # 圖表視窗
                self.parent_window.resize(500, 350)
            else:
                # 其他視窗
                self.parent_window.resize(400, 300)
        else:
            # 默認大小
            self.parent_window.resize(400, 300)
        
        # 確保視窗在可見區域內
        if self.parent_window.parent():
            parent_rect = self.parent_window.parent().rect()
            current_pos = self.parent_window.pos()
            new_x = max(10, min(current_pos.x(), parent_rect.width() - 420))
            new_y = max(10, min(current_pos.y(), parent_rect.height() - 320))
            self.parent_window.move(new_x, new_y)
        
    def mouseDoubleClickEvent(self, event):
        """雙擊恢復視窗大小"""
        if event.button() == Qt.LeftButton:
            self.restore_normal_size()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event):
        """右鍵選單"""
        menu = QMenu(self)
        restore_action = menu.addAction("[REFRESH] 恢復正常大小")
        restore_action.triggered.connect(self.restore_normal_size)
        
        maximize_action = menu.addAction("🔳 最大化")
        maximize_action.triggered.connect(self.parent_window.toggle_maximize)
        
        menu.exec_(event.globalPos())
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 開始拖拽，但不干擾調整大小"""
        if event.button() == Qt.LeftButton:
            # 檢查是否在父視窗的調整邊緣區域
            parent_pos = self.parent_window.mapFromGlobal(event.globalPos())
            if self.parent_window.get_resize_direction(parent_pos):
                # 如果在調整區域，讓父視窗處理
                event.ignore()
                return
                
            self.dragging = True
            self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 執行拖拽，但不干擾調整大小，並支援 Snap 預覽"""
        # 檢查是否在調整模式
        if hasattr(self.parent_window, 'resizing') and self.parent_window.resizing:
            event.ignore()
            return
            
        # 檢查是否在調整區域，如果是就讓父視窗處理游標
        parent_pos = self.parent_window.mapFromGlobal(event.globalPos())
        if hasattr(self.parent_window, 'get_resize_direction') and self.parent_window.get_resize_direction(parent_pos):
            event.ignore()
            return
            
        if event.buttons() == Qt.LeftButton and self.dragging:
            new_pos = event.globalPos() - self.drag_position
            self.parent_window.move(new_pos)
            
            # ========== Snap 預覽（支援 Smart Width + 動態剩餘空間）==========
            # 檢查是否有 MDI 區域並支援 Snap
            mdi_area = self._get_mdi_area()
            if mdi_area and hasattr(mdi_area, 'detect_snap_zone'):
                # 傳遞正在拖動的視窗以支援視窗邊緣檢測
                snap_zone = mdi_area.detect_snap_zone(event.globalPos(), self.parent_window)
                # 獲取模組名稱用於 Smart Width
                module_name = self._get_module_name()
                # 傳遞正在拖動的視窗以排除計算
                mdi_area.show_snap_preview(snap_zone, module_name, self.parent_window)
            
            event.accept()
        else:
            # 沒有拖拽時，讓父視窗處理事件
            event.ignore()
            
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拽，並執行 Snap"""
        if event.button() == Qt.LeftButton:
            # ========== 執行 Snap ==========
            if self.dragging:
                mdi_area = self._get_mdi_area()
                if mdi_area and hasattr(mdi_area, 'detect_snap_zone'):
                    snap_zone = mdi_area.detect_snap_zone(event.globalPos(), self.parent_window)
                    mdi_area.hide_snap_preview()
                    
                    # 如果有有效的 Snap 區域，執行 Snap
                    if snap_zone != SnapZone.NONE:
                        mdi_area.snap_window_to_zone(self.parent_window, snap_zone)
            
            self.dragging = False
            event.accept()
    
    def _get_mdi_area(self):
        """獲取父層的 MDI 區域"""
        if hasattr(self.parent_window, 'parent_mdi') and self.parent_window.parent_mdi:
            return self.parent_window.parent_mdi
        return None
    
    def _get_module_name(self) -> str:
        """獲取模組名稱用於 Smart Width"""
        if hasattr(self.parent_window, 'analysis_module') and self.parent_window.analysis_module:
            if hasattr(self.parent_window.analysis_module, 'analysis_type'):
                return self.parent_window.analysis_module.analysis_type
        # 嘗試從視窗標題推斷模組類型
        title = self.parent_window.windowTitle().lower()
        # 注意：匹配順序很重要，更具體的要放前面
        if 'lap time' in title or 'distribution' in title:
            return 'lap_time_distribution'
        elif 'circle' in title:
            return 'circle_map'
        elif 'ranking' in title or 'tower' in title:
            return 'ranking_tower'
        elif 'strategy' in title:
            return 'driver_strategy'
        elif 'speed' in title:
            return 'speed_trace'
        elif 'calendar' in title:
            return 'race_calendar'
        elif 'rain' in title or 'temp' in title or 'temperature' in title:
            return 'temp_analysis'
        elif 'track' in title and 'map' in title:
            return 'circle_map'  # Track Map 使用相同設定
        elif 'telemetry' in title or 'comparison' in title:
            return 'telemetry_comparison'
        elif 'position' in title:
            return 'position_analysis'
        return 'default'
    
    def paintEvent(self, event):
        """繪製事件 - 手動繪製背景色以確保顯示"""
        # 手動繪製 #F0F0F0 背景色以確保顯示
        painter = QPainter(self)
        # 繪製稍微大一點的矩形，確保填滿所有可能的間隙
        extended_rect = self.rect()
        extended_rect.setTop(extended_rect.top() - 5)  # 向上延伸5像素
        extended_rect.setLeft(extended_rect.left() - 5)  # 向左延伸5像素 
        extended_rect.setRight(extended_rect.right() + 5)  # 向右延伸5像素
        painter.fillRect(extended_rect, QColor("#F0F0F0"))
        
        super().paintEvent(event)
    
    def update_title(self, title):
        """更新標題"""
        self.title_label.setText(title)
    
    def toggle_x_sync(self):
        """切換接收同步狀態 - S=接收主程式同步，X=獨立運作"""
        is_enabled = self.sync_btn.isChecked()
        
        # 更新按鈕外觀和提示
        if is_enabled:
            self.sync_btn.setText("S")
            self.sync_btn.setToolTip(tr('sync_button_tooltip_enabled', 'Receive sync from main: Enabled (S)'))
            logger.debug(f"[SYNC] 接收同步已啟動 (S) - 將接收主程式參數")
        else:
            self.sync_btn.setText("X")
            self.sync_btn.setToolTip(tr('sync_button_tooltip_disabled', 'Receive sync from main: Disabled (X)'))
            logger.debug(f"[SYNC] 接收同步已停用 (X) - 獨立運作模式")
        
        # 強制重新應用樣式確保顏色更新
        self.sync_btn.style().unpolish(self.sync_btn)
        self.sync_btn.style().polish(self.sync_btn)
        self.sync_btn.update()
        
        # 更新父視窗的同步狀態
        if hasattr(self.parent_window, 'sync_enabled'):
            self.parent_window.sync_enabled = is_enabled
            logger.debug(f"[REFRESH] 視窗 '{self.parent_window.windowTitle()}' 同步接收狀態已更新: {is_enabled}")
            
            # [TOOL] 新增：立即更新標題（同步狀態改變時）
            if hasattr(self.parent_window, 'update_window_title'):
                self.parent_window.update_window_title()
    
    def toggle_individual_linkage(self):
        """切換個別連動狀態"""
        is_enabled = self.linkage_btn.isChecked()
        
        # 更新按鈕外觀和提示
        if is_enabled:
            self.linkage_btn.setText("L")
            self.linkage_btn.setToolTip(tr('linkage_button_tooltip_enabled', 'Individual linkage: Enabled (L)'))
            logger.debug(f"[LINKAGE] 個別連動已啟用 (L)")
        else:
            self.linkage_btn.setText("X")
            self.linkage_btn.setToolTip(tr('linkage_button_tooltip_disabled', 'Individual linkage: Disabled (X)'))
            logger.debug(f"[LINKAGE] 個別連動已停用 (X)")
        
        # 強制重新應用樣式確保顏色更新
        self.linkage_btn.style().unpolish(self.linkage_btn)
        self.linkage_btn.style().polish(self.linkage_btn)
        self.linkage_btn.update()
        
        # 通知分析模組更新連動狀態
        if hasattr(self.parent_window, 'set_linkage_enabled'):
            self.parent_window.set_linkage_enabled(is_enabled)
            logger.debug(f"[LINKAGE] 視窗 '{self.parent_window.windowTitle()}' 個別連動狀態已更新: {is_enabled}")
    
    def toggle_driver_lap_sync(self):
        """切換車手與圈數同步狀態（僅遙測模組）"""
        is_enabled = self.driver_lap_sync_btn.isChecked()
        
        # 更新按鈕外觀和提示
        if is_enabled:
            self.driver_lap_sync_btn.setText("D")
            self.driver_lap_sync_btn.setToolTip(tr('driver_lap_sync_tooltip_enabled', 'Sync driver & lap with main window: Enabled (D)'))
            logger.debug(f"[DRIVER_LAP_SYNC] 車手與圈數同步已啟用 (D)")
        else:
            self.driver_lap_sync_btn.setText("X")
            self.driver_lap_sync_btn.setToolTip(tr('driver_lap_sync_tooltip_disabled', 'Sync driver & lap with main window: Disabled (X)'))
            logger.debug(f"[DRIVER_LAP_SYNC] 車手與圈數同步已停用 (X)")
        
        # 強制重新應用樣式確保顏色更新
        self.driver_lap_sync_btn.style().unpolish(self.driver_lap_sync_btn)
        self.driver_lap_sync_btn.style().polish(self.driver_lap_sync_btn)
        self.driver_lap_sync_btn.update()
        
        # 通知分析模組更新同步狀態
        if hasattr(self.parent_window, 'analysis_module'):
            analysis_module = self.parent_window.analysis_module
            if hasattr(analysis_module, 'sync_driver_lap_enabled'):
                analysis_module.sync_driver_lap_enabled = is_enabled
                logger.info(f"[DRIVER_LAP_SYNC] 分析模組同步狀態已更新: {is_enabled}")
                
                # 如果有設定對話框，同步更新 checkbox 狀態
                if hasattr(self.parent_window, 'settings_dialog') and self.parent_window.settings_dialog:
                    if hasattr(self.parent_window.settings_dialog, 'sync_driver_lap_checkbox'):
                        # 阻止信號避免遞迴
                        self.parent_window.settings_dialog.sync_driver_lap_checkbox.blockSignals(True)
                        self.parent_window.settings_dialog.sync_driver_lap_checkbox.setChecked(is_enabled)
                        self.parent_window.settings_dialog.sync_driver_lap_checkbox.blockSignals(False)
                        logger.info(f"[DRIVER_LAP_SYNC] 設定對話框 checkbox 已同步更新")
                        
                        # 如果 Settings 對話框打開，更新控制項的可編輯性
                        if hasattr(self.parent_window.settings_dialog, '_update_driver_lap_controls_editability'):
                            self.parent_window.settings_dialog._update_driver_lap_controls_editability()
                
                # 根據同步狀態載入對應的資料（無論 Settings 對話框是否打開）
                if not is_enabled:
                    logger.info(f"[DRIVER_LAP_SYNC] 同步已停用，載入全域參數池")
                    # 如果 Settings 對話框打開，通過它載入參數（只更新 UI）
                    if hasattr(self.parent_window, 'settings_dialog') and self.parent_window.settings_dialog:
                        if hasattr(self.parent_window.settings_dialog, '_load_shared_params_to_ui'):
                            logger.info(f"[DRIVER_LAP_SYNC] Settings 對話框打開，更新 UI 控制項")
                            self.parent_window.settings_dialog._load_shared_params_to_ui()
                    
                    # 無論 Settings 對話框是否打開，都要載入資料
                    logger.info(f"[DRIVER_LAP_SYNC] 載入全域參數池資料")
                    self._reload_data_with_shared_params()
                else:
                    logger.info(f"[DRIVER_LAP_SYNC] 同步已啟用，載入主視窗資料")
                    # 觸發資料重新載入（使用主視窗參數）
                    self._reload_data_with_main_window_params()
    
    def _reload_data_with_main_window_params(self):
        """重新載入資料（使用主視窗參數）"""
        try:
            logger.info(f"[RELOAD_DATA] 開始重新載入資料（同步模式）")
            
            # 檢查是否有 Settings 對話框且是遙測模組
            if not hasattr(self.parent_window, 'main_window'):
                logger.warning(f"[RELOAD_DATA] 找不到 main_window")
                return
            
            main_window = self.parent_window.main_window
            
            # 從主視窗讀取所有參數
            main_driver1 = main_window.driver1_combo.currentText()
            main_driver2_data = main_window.driver2_combo.currentData()
            main_driver2 = main_window.driver2_combo.currentText() if main_driver2_data is not None else None
            main_lap1 = main_window.lap1_spinbox.value()
            main_lap2 = main_window.lap2_spinbox.value()
            main_is_fastest = main_window.fastest_lap_checkbox.isChecked()
            
            logger.info(f"[RELOAD_DATA] 主視窗參數:")
            logger.info(f"[RELOAD_DATA]   車手 1: {main_driver1}")
            logger.info(f"[RELOAD_DATA]   車手 2: {main_driver2}")
            logger.info(f"[RELOAD_DATA]   圈數 1: {main_lap1}")
            logger.info(f"[RELOAD_DATA]   圈數 2: {main_lap2}")
            logger.info(f"[RELOAD_DATA]   最速圈: {main_is_fastest}")
            
            # 檢查是否有打開的 Settings 對話框
            if hasattr(self.parent_window, 'settings_dialog') and self.parent_window.settings_dialog:
                # 如果 Settings 對話框打開，使用它的 _apply_driver_lap_settings 方法
                logger.info(f"[RELOAD_DATA] 使用 Settings 對話框的 _apply_driver_lap_settings()")
                self.parent_window.settings_dialog._apply_driver_lap_settings(
                    main_driver1, main_driver2, main_lap1, main_lap2, main_is_fastest
                )
            else:
                # Settings 對話框未打開，直接調用分析模組的載入方法
                logger.info(f"[RELOAD_DATA] Settings 對話框未打開，直接調用分析模組")
                
                if hasattr(self.parent_window, 'analysis_module'):
                    analysis_module = self.parent_window.analysis_module
                    
                    # 獲取主視窗的 year, race, session
                    year = main_window.year_combo.currentText()
                    race_display = main_window.race_combo.currentText()
                    race = main_window._get_race_key_from_display(race_display)
                    session = main_window.session_combo.currentText()
                    
                    # 獲取時間軸設定
                    use_time_axis = getattr(analysis_module, 'use_time_axis', False)
                    
                    logger.info(f"[RELOAD_DATA] 賽事參數: {year} {race} {session}")
                    logger.info(f"[RELOAD_DATA] 時間軸: {use_time_axis}")
                    
                    # 優先使用 update_lap_parameters 方法（完整的參數更新 + 資料載入）
                    if hasattr(analysis_module, 'update_lap_parameters'):
                        logger.info(f"[RELOAD_DATA] 調用 update_lap_parameters()")
                        success = analysis_module.update_lap_parameters(
                            year=year,
                            race=race,
                            session=session,
                            driver1=main_driver1,
                            driver2=main_driver2,
                            lap1=main_lap1,
                            lap2=main_lap2,
                            is_fastest=main_is_fastest,
                            use_time_axis=use_time_axis
                        )
                        if success:
                            logger.info(f"[RELOAD_DATA] update_lap_parameters 執行成功")
                        else:
                            logger.warning(f"[RELOAD_DATA] update_lap_parameters 執行失敗")
                    # 備用方案：使用 load_speed_data 或 load_data
                    elif hasattr(analysis_module, 'load_speed_data'):
                        logger.info(f"[RELOAD_DATA] 調用 load_speed_data()")
                        analysis_module.load_speed_data(
                            year=year, race=race, session=session,
                            driver1=main_driver1, driver2=main_driver2, lap_number=main_lap1
                        )
                    elif hasattr(analysis_module, 'load_data'):
                        logger.info(f"[RELOAD_DATA] 調用 load_data()")
                        analysis_module.load_data(
                            year=year, race=race, session=session,
                            driver1=main_driver1, driver2=main_driver2, lap_number=main_lap1
                        )
                    else:
                        logger.warning(f"[RELOAD_DATA] 分析模組沒有 load_data 方法")
                else:
                    logger.warning(f"[RELOAD_DATA] 找不到 analysis_module")
                
        except Exception as e:
            logger.error(f"[RELOAD_DATA] 重新載入資料失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _reload_data_with_shared_params(self):
        """重新載入資料（使用全域參數池）"""
        try:
            logger.info(f"[RELOAD_SHARED] 開始重新載入資料（獨立模式）")
            
            # 獲取主視窗以存取全域參數池
            if not hasattr(self.parent_window, 'main_window'):
                logger.warning(f"[RELOAD_SHARED] 找不到 main_window")
                return
            
            main_window = self.parent_window.main_window
            
            # 檢查全域參數池是否存在
            if not hasattr(main_window, 'shared_independent_params'):
                logger.warning(f"[RELOAD_SHARED] 主視窗沒有 shared_independent_params")
                return
            
            shared_params = main_window.shared_independent_params
            
            logger.info(f"[RELOAD_SHARED] 全域參數池內容:")
            for key, value in shared_params.items():
                logger.info(f"[RELOAD_SHARED]   {key}: {value}")
            
            # 檢查是否為空（所有值都是 None）
            if all(v is None for k, v in shared_params.items() if k != 'use_time_axis'):
                logger.warning(f"[RELOAD_SHARED] 全域參數池為空，無法載入資料")
                return
            
            # 讀取參數
            year1 = shared_params.get('year1')
            race1 = shared_params.get('race1')
            session1 = shared_params.get('session1')
            driver1 = shared_params.get('driver1')
            lap1 = shared_params.get('lap1', 1)
            
            year2 = shared_params.get('year2')
            race2 = shared_params.get('race2')
            session2 = shared_params.get('session2')
            driver2 = shared_params.get('driver2')
            lap2 = shared_params.get('lap2', 1)
            
            use_time_axis = shared_params.get('use_time_axis', False)
            
            logger.info(f"[RELOAD_SHARED] 參數: {year1} {race1} {session1}")
            logger.info(f"[RELOAD_SHARED] 車手 1: {driver1} (Lap {lap1})")
            logger.info(f"[RELOAD_SHARED] 車手 2: {driver2} (Lap {lap2}) - {year2} {race2} {session2}")
            
            # 檢測是否為跨賽段/跨賽事比較
            is_cross_event = (year1 != year2) or (race1 != race2) or (session1 != session2)
            logger.info(f"[RELOAD_SHARED] 跨賽段/賽事比較: {is_cross_event}")
            
            # 調用分析模組的載入方法
            if hasattr(self.parent_window, 'analysis_module'):
                analysis_module = self.parent_window.analysis_module
                
                # 如果是跨賽段比較，使用 update_cross_event_comparison
                if is_cross_event and hasattr(analysis_module, 'update_cross_event_comparison'):
                    logger.info(f"[RELOAD_SHARED] 調用 update_cross_event_comparison() 處理跨賽段比較")
                    is_fastest = (lap1 == 99 or lap2 == 99)
                    success = analysis_module.update_cross_event_comparison(
                        year1=str(year1), race1=race1, session1=session1, driver1=driver1, lap1=lap1,
                        year2=str(year2), race2=race2, session2=session2, driver2=driver2, lap2=lap2,
                        is_fastest=is_fastest,
                        use_time_axis=use_time_axis
                    )
                    if success:
                        logger.info(f"[RELOAD_SHARED] 跨賽段比較載入成功")
                    else:
                        logger.warning(f"[RELOAD_SHARED] 跨賽段比較載入失敗")
                # 單一賽段比較，使用 update_lap_parameters
                elif hasattr(analysis_module, 'update_lap_parameters'):
                    logger.info(f"[RELOAD_SHARED] 調用 update_lap_parameters() 處理單一賽段比較")
                    is_fastest = (lap1 == 99 or lap2 == 99)
                    success = analysis_module.update_lap_parameters(
                        year=str(year1),
                        race=race1,
                        session=session1,
                        driver1=driver1,
                        driver2=driver2,
                        lap1=lap1,
                        lap2=lap2,
                        is_fastest=is_fastest,
                        use_time_axis=use_time_axis
                    )
                    if success:
                        logger.info(f"[RELOAD_SHARED] update_lap_parameters 執行成功")
                    else:
                        logger.warning(f"[RELOAD_SHARED] update_lap_parameters 執行失敗")
                # 備用方案：使用 load_speed_data 或 load_data
                elif hasattr(analysis_module, 'load_speed_data'):
                    logger.info(f"[RELOAD_SHARED] 調用 load_speed_data()")
                    analysis_module.load_speed_data(
                        year=str(year1), race=race1, session=session1,
                        driver1=driver1, driver2=driver2, lap_number=lap1
                    )
                elif hasattr(analysis_module, 'load_data'):
                    logger.info(f"[RELOAD_SHARED] 調用 load_data()")
                    analysis_module.load_data(
                        year=str(year1), race=race1, session=session1,
                        driver1=driver1, driver2=driver2, lap_number=lap1
                    )
                else:
                    logger.warning(f"[RELOAD_SHARED] 分析模組沒有 load_data 方法")
            else:
                logger.warning(f"[RELOAD_SHARED] 找不到 analysis_module")
                
        except Exception as e:
            logger.error(f"[RELOAD_SHARED] 重新載入資料失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())

    
    def set_linkage_button_state(self, enabled: bool):
        """設置連動按鈕狀態（由主視窗總開關調用）"""
        self.linkage_btn.setChecked(enabled)
        self.toggle_individual_linkage()  # 觸發狀態更新
    
    def get_sync_status(self):
        """取得當前X軸連動狀態"""
        return self.sync_btn.isChecked()
    
    def cleanup(self):
        """
        清理資源和信號連接
        
        資源洩漏修復: 在視窗關閉時斷開所有信號，防止循環引用導致內存洩漏
        
        清理項目:
        - 所有按鈕信號連接（包括實例屬性和局部變數）
        - parent_window 循環引用
        - 所有 Qt 對象引用
        
        技術細節:
        - DraggableTitleBar 有3個實例屬性按鈕 + 5個局部變數按鈕
        - 遍歷所有子 QPushButton 以斷開所有 clicked 信號
        """
        try:
            logger.debug(f"[CLEANUP] 開始清理 DraggableTitleBar 資源...")
            
            # 步驟1: 遍歷所有子 QPushButton 並斷開 clicked 信號
            # 這樣可以處理實例屬性按鈕和局部變數按鈕
            button_count = 0
            for child in self.findChildren(QPushButton):
                try:
                    child.clicked.disconnect()
                    button_count += 1
                    logger.debug(f"[CLEANUP]   斷開按鈕信號: {child.objectName() or '未命名按鈕'}")
                except TypeError:
                    # 信號已經斷開或無連接
                    pass
            
            logger.debug(f"[CLEANUP]   共斷開 {button_count} 個按鈕信號")
            
            # 步驟2: 清除 parent_window 循環引用
            if hasattr(self, 'parent_window'):
                logger.debug(f"[CLEANUP]   清除 parent_window 引用")
                self.parent_window = None
            
            # 步驟3: 清除其他對象引用
            self.title_label = None
            self.sync_btn = None
            self.linkage_btn = None
            self.popout_btn = None
            
            logger.debug(f"[CLEANUP] DraggableTitleBar 資源清理完成")
            
        except Exception as e:
            logger.warning(f"[WARNING] DraggableTitleBar cleanup 失敗: {e}")
            import traceback
            traceback.print_exc()
