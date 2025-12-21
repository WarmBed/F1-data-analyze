# -*- coding: utf-8 -*-
"""
LapControlsShower - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QAction
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LapControlsShower:
    """從 f1t_gui_main.py 提取的 show_lap_controls 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def show_lap_controls(self):
        """顯示遙測分析控件（動態添加到工具欄）"""
        logger.debug("[LAP_CONTROL] [DEBUG]   📊 開始顯示遙測分析控件（動態添加）")
        
        # 檢查是否已經添加到工具欄 - 修復：檢查 main_window 而不是 self
        if getattr(self.main_window, '_lap_controls_added', False):
            logger.debug("[LAP_CONTROL] [DEBUG]   ⚠️ 遙測分析控件已經在工具欄中，跳過重複添加")
            return
        
        try:
            # 強制重新初始化車手列表，確保在重新顯示時車手列表正確
            logger.debug("[LAP_CONTROL] [DEBUG]   🔄 強制重新初始化車手列表...")
            self.main_window.initialize_driver_lists()
            
            # 在賽事會話控件後添加分隔符
            session_action = None
            for action in self.main_window.main_toolbar.actions():
                widget = self.main_window.main_toolbar.widgetForAction(action)
                if widget == self.main_window.session_combo:
                    session_action = action
                    break
            
            if session_action:
                # 找到會話控件的下一個位置
                session_index = self.main_window.main_toolbar.actions().index(session_action)
                next_action = None
                if session_index + 1 < len(self.main_window.main_toolbar.actions()):
                    next_action = self.main_window.main_toolbar.actions()[session_index + 1]
                
                # 添加分隔符
                if next_action:
                    self.main_window.lap_separator = self.main_window.main_toolbar.insertSeparator(next_action)
                else:
                    self.main_window.lap_separator = self.main_window.main_toolbar.addSeparator()
                
                # 依序添加遙測分析控件
                controls_to_add = [
                    self.main_window.driver1_label, self.main_window.driver1_combo,
                    self.main_window.lap1_label, self.main_window.lap1_spinbox,
                    self.main_window.driver2_label, self.main_window.driver2_combo,
                    self.main_window.lap2_label, self.main_window.lap2_spinbox,
                    self.main_window.fastest_lap_checkbox, self.main_window.use_time_axis_checkbox
                ]
                
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🔧 準備添加 {len(controls_to_add)} 個控件到工具欄")
                for i, control in enumerate(controls_to_add):
                    control_name = control.__class__.__name__
                    control_text = getattr(control, 'text', lambda: '')() or getattr(control, 'currentText', lambda: '')()
                    logger.debug(f"[LAP_CONTROL] [DEBUG]   添加控件 {i+1}: {control_name} - '{control_text}'")
                    
                    # 設置控件的基本屬性
                    control.setParent(self.main_window.main_toolbar)
                    control.setVisible(True)
                    control.setEnabled(True)
                    
                    # 添加到工具欄
                    if next_action:
                        self.main_window.main_toolbar.insertWidget(next_action, control)
                    else:
                        self.main_window.main_toolbar.addWidget(control)
                    
                    logger.debug(f"[LAP_CONTROL] [DEBUG]   控件 {i+1} 已添加，可見性: {control.isVisible()}, 啟用: {control.isEnabled()}")
                
                # 添加更新按鈕（檢查是否已存在）
                if not hasattr(self.main_window, 'update_all_action') or self.main_window.update_all_action is None:
                    self.main_window.update_all_action = QAction("🔄 Update All Analysis", self.main_window)
                    self.main_window.update_all_action.triggered.connect(self.main_window.update_all_lap_analysis)
                    
                    if next_action:
                        self.main_window.main_toolbar.insertAction(next_action, self.main_window.update_all_action)
                    else:
                        self.main_window.main_toolbar.addAction(self.main_window.update_all_action)
                
                # 添加遙測分析連動總開關（檢查是否已存在）
                if not hasattr(self.main_window, 'lap_linkage_action') or self.main_window.lap_linkage_action is None:
                    from core.gui_i18n import tr
                    self.main_window.lap_linkage_action = QAction(f"🔗 {tr('lap_linkage', 'Lap Linkage')}", self.main_window)
                    self.main_window.lap_linkage_action.setCheckable(True)
                    self.main_window.lap_linkage_action.setChecked(True)  # 預設啟用
                    self.main_window.lap_linkage_action.triggered.connect(self.main_window.toggle_lap_analysis_linkage)
                    
                    if next_action:
                        self.main_window.main_toolbar.insertAction(next_action, self.main_window.lap_linkage_action)
                    else:
                        self.main_window.main_toolbar.addAction(self.main_window.lap_linkage_action)
                
                logger.debug("[LAP_CONTROL] [DEBUG]   ✅ 圈速分析控件成功添加到工具欄")
                logger.debug(f"[LAP_CONTROL] [DEBUG]   📊 工具欄狀態檢查:")
                logger.debug(f"[LAP_CONTROL] [DEBUG]     - 工具欄可見: {self.main_window.main_toolbar.isVisible()}")
                logger.debug(f"[LAP_CONTROL] [DEBUG]     - 工具欄動作數量: {len(self.main_window.main_toolbar.actions())}")
                logger.debug(f"[LAP_CONTROL] [DEBUG]     - 工具欄尺寸: {self.main_window.main_toolbar.size()}")
                
                # 強制更新工具欄顯示
                self.main_window.main_toolbar.update()
                self.main_window.main_toolbar.repaint()
                
                # 檢查每個控件的狀態
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 控件狀態最終檢查:")
                for i, control in enumerate(controls_to_add):
                    widget_name = control.__class__.__name__
                    is_visible = control.isVisible()
                    is_enabled = control.isEnabled()
                    size = control.size()
                    logger.debug(f"[LAP_CONTROL] [DEBUG]     控件{i+1} ({widget_name}): 可見={is_visible}, 啟用={is_enabled}, 尺寸={size}")
                
                self.main_window._lap_controls_added = True
                self.main_window.lap_controls_visible = True
                
        except Exception as e:
            logger.debug(f"[LAP_CONTROL] [DEBUG]   ❌ 添加圈速分析控件時發生錯誤: {e}")
            e = None  # 🔴 立即釋放異常對象
