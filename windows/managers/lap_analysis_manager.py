"""
圈速分析管理器
統一管理圈速分析工具欄控件和視窗追蹤

提供的功能：
- 圈速分析工具欄控件顯示/隱藏
- 分析視窗追蹤
- 批次更新所有分析視窗
- 車手列表初始化

從 f1t_gui_main.py 中提取的方法：
- show_lap_controls()
- hide_lap_controls()
- on_lap_analysis_window_opened()
- on_lap_analysis_window_closed()
- initialize_driver_lists()
- update_all_lap_analysis()
- toggle_lap_analysis_linkage()
"""

from typing import Set, Optional, Any, TYPE_CHECKING
from PyQt5.QtWidgets import QWidget, QAction

from core.logger import get_logger
from typing import Optional
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QSpinBox
from typing import Any

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow, QToolBar, QComboBox, QSpinBox, QCheckBox, QLabel

logger = get_logger(__name__)


class LapAnalysisManager:
    """
    圈速分析管理器
    
    負責管理所有圈速分析相關操作，包括：
    - 工具欄控件的顯示/隱藏
    - 分析視窗的追蹤
    - 批次更新所有分析視窗
    - 車手列表初始化
    
    Attributes:
        main_window: 主視窗實例
        lap_analysis_windows: 追蹤開啟的分析視窗
        lap_controls_visible: 控件是否可見
    """
    
    # 支援的分析類型
    SUPPORTED_ANALYSIS_TYPES = {
        # 遙測分析類型
        'speed_analysis', 'speed', 'brake', 'throttle', 'steering',
        'gear', 'rpm', 'acceleration', 'speed_diff', 'Speeddiff',
        'distancediff', 'Distancediff', 'timediff', 'Timediff',
        'laptime', 'laptime_boxplot', 'throttle_boxplot',
        'throttle_line_chart_single_driver',
        # 賽事級分析類型
        'rain_weather', 'pitstop', 'accident', 'tire',
        'ideal_lap', 'ideal_lap_ranking', 'ideal_lap_sector_comparison',
        'ideal_lap_sector_heatmap', 'track_analysis', 'driver_position',
        'qualifying_prediction', 'race_prediction',
        'all_drivers_straight_line_speed', 'all_drivers_max_speed',
        'all_drivers_acceleration_chart', 'all_drivers_brake_chart',
        'all_drivers_brake_performance', 'all_drivers_brake_all_laps',
        'corner_performance', 'historical_track_map',
    }
    
    def __init__(self, main_window: 'QMainWindow'):
        """
        初始化圈速分析管理器
        
        Args:
            main_window: 主視窗實例（StyleHMainWindow）
        """
        self.main_window = main_window
        
        # 追蹤開啟的分析視窗
        self._lap_analysis_windows: Set[Any] = set()
        
        # 控件狀態
        self._lap_controls_added: bool = False
        self._lap_controls_visible: bool = False
        
        # 工具欄元素引用（延遲初始化）
        self._lap_separator = None
        self._update_all_action: Optional[QAction] = None
        self._lap_linkage_action: Optional[QAction] = None
        
        logger.debug("[LapAnalysisManager] Initialized")
    
    @property
    def lap_analysis_windows(self) -> Set[Any]:
        """取得分析視窗集合（向後兼容）"""
        # 優先使用主視窗的，確保向後兼容
        if hasattr(self.main_window, 'lap_analysis_windows'):
            return self.main_window.lap_analysis_windows
        return self._lap_analysis_windows
    
    @property
    def lap_controls_visible(self) -> bool:
        """控件是否可見"""
        if hasattr(self.main_window, 'lap_controls_visible'):
            return self.main_window.lap_controls_visible
        return self._lap_controls_visible
    
    @lap_controls_visible.setter
    def lap_controls_visible(self, value: bool) -> None:
        """設置控件可見性"""
        self._lap_controls_visible = value
        if hasattr(self.main_window, 'lap_controls_visible'):
            self.main_window.lap_controls_visible = value
    
    # ==================== 工具欄控制 ====================
    
    @property
    def _toolbar(self) -> Optional['QToolBar']:
        """取得主工具欄"""
        return getattr(self.main_window, 'main_toolbar', None)
    
    @property
    def _controls(self) -> list:
        """取得所有圈速分析控件"""
        mw = self.main_window
        controls = []
        
        # 嘗試獲取各個控件
        for attr in ['driver1_label', 'driver1_combo', 'lap1_label', 'lap1_spinbox',
                     'driver2_label', 'driver2_combo', 'lap2_label', 'lap2_spinbox',
                     'fastest_lap_checkbox', 'use_time_axis_checkbox']:
            if hasattr(mw, attr):
                controls.append(getattr(mw, attr))
        
        return controls
    
    def show_lap_controls(self) -> None:
        """顯示圈速分析控件（動態添加到工具欄）"""
        logger.debug("[LapAnalysisManager] Showing lap controls")
        
        # 檢查是否已經添加
        if self._lap_controls_added:
            logger.debug("[LapAnalysisManager] Controls already added, skipping")
            return
        
        toolbar = self._toolbar
        if toolbar is None:
            logger.error("[LapAnalysisManager] Main toolbar not found")
            return
        
        try:
            # 初始化車手列表
            self.initialize_driver_lists()
            
            # 找到 session_combo 的位置
            session_combo = getattr(self.main_window, 'session_combo', None)
            next_action = self._find_insertion_point(toolbar, session_combo)
            
            # 添加分隔符
            if next_action:
                self._lap_separator = toolbar.insertSeparator(next_action)
            else:
                self._lap_separator = toolbar.addSeparator()
            
            # 添加控件
            controls = self._controls
            logger.debug(f"[LapAnalysisManager] Adding {len(controls)} controls")
            
            for control in controls:
                control.setParent(toolbar)
                control.setVisible(True)
                control.setEnabled(True)
                
                if next_action:
                    toolbar.insertWidget(next_action, control)
                else:
                    toolbar.addWidget(control)
            
            # 添加更新按鈕
            self._add_action_buttons(toolbar, next_action)
            
            # 更新狀態
            self._lap_controls_added = True
            self.lap_controls_visible = True
            
            # 刷新工具欄
            toolbar.update()
            toolbar.repaint()
            
            logger.debug("[LapAnalysisManager] Lap controls shown successfully")
            
        except Exception as e:
            logger.error(f"[LapAnalysisManager] Failed to show controls: {e}")
    
    def hide_lap_controls(self) -> None:
        """隱藏圈速分析控件（從工具欄移除）"""
        # 如果還有分析視窗開啟，不隱藏
        if len(self.lap_analysis_windows) > 0:
            logger.debug("[LapAnalysisManager] Windows still open, not hiding controls")
            return
        
        if not self._lap_controls_added:
            logger.debug("[LapAnalysisManager] Controls not added, skipping hide")
            return
        
        toolbar = self._toolbar
        if toolbar is None:
            return
        
        try:
            logger.debug("[LapAnalysisManager] Hiding lap controls")
            
            # 移除分隔符
            if self._lap_separator:
                toolbar.removeAction(self._lap_separator)
                self._lap_separator = None
            
            # 移除控件
            for control in self._controls:
                for action in toolbar.actions():
                    if action.defaultWidget() == control:
                        toolbar.removeAction(action)
                        break
            
            # 移除動作按鈕
            if self._update_all_action:
                toolbar.removeAction(self._update_all_action)
                self._update_all_action = None
            
            if self._lap_linkage_action:
                toolbar.removeAction(self._lap_linkage_action)
                self._lap_linkage_action = None
            
            self._lap_controls_added = False
            self.lap_controls_visible = False
            
            logger.debug("[LapAnalysisManager] Lap controls hidden successfully")
            
        except Exception as e:
            logger.error(f"[LapAnalysisManager] Failed to hide controls: {e}")
    
    def _find_insertion_point(self, toolbar: 'QToolBar', session_combo) -> Optional[QAction]:
        """找到插入點（session_combo 之後）"""
        if session_combo is None:
            return None
        
        for action in toolbar.actions():
            widget = toolbar.widgetForAction(action)
            if widget == session_combo:
                idx = toolbar.actions().index(action)
                if idx + 1 < len(toolbar.actions()):
                    return toolbar.actions()[idx + 1]
        return None
    
    def _add_action_buttons(self, toolbar: 'QToolBar', next_action) -> None:
        """添加動作按鈕（更新全部、連動開關）"""
        from core.gui_i18n import tr
        
        # 檢查是否已存在（避免重複添加）
        if self._update_all_action is not None:
            logger.debug("[LapAnalysisManager] Action buttons already exist, skipping")
            return
        
        # 更新全部按鈕
        self._update_all_action = QAction("🔄 Update All Analysis", self.main_window)
        self._update_all_action.triggered.connect(self._on_update_all_clicked)
        
        if next_action:
            toolbar.insertAction(next_action, self._update_all_action)
        else:
            toolbar.addAction(self._update_all_action)
        
        # 連動開關
        self._lap_linkage_action = QAction(f"🔗 {tr('lap_linkage', 'Lap Linkage')}", self.main_window)
        self._lap_linkage_action.setCheckable(True)
        self._lap_linkage_action.setChecked(True)
        self._lap_linkage_action.triggered.connect(self._on_linkage_toggled)
        
        if next_action:
            toolbar.insertAction(next_action, self._lap_linkage_action)
        else:
            toolbar.addAction(self._lap_linkage_action)
    
    # ==================== 視窗追蹤 ====================
    
    def on_window_opened(self, window_object: Any, analysis_type: str) -> None:
        """
        分析視窗開啟時調用
        
        Args:
            window_object: 視窗物件
            analysis_type: 分析類型
        """
        logger.debug(f"[LapAnalysisManager] Window opened: {analysis_type}")
        
        # 標記分析類型
        if not hasattr(window_object, '_analysis_type'):
            window_object._analysis_type = analysis_type
        
        # 添加到追蹤集合
        self.lap_analysis_windows.add(window_object)
        logger.debug(f"[LapAnalysisManager] Active windows: {len(self.lap_analysis_windows)}")
        
        # 顯示控件
        self.show_lap_controls()
        
        # 觸發工具欄狀態更新（如果主視窗有此方法）
        if hasattr(self.main_window, '_trigger_toolbar_status_for_lap_analysis'):
            self.main_window._trigger_toolbar_status_for_lap_analysis(analysis_type, window_object)
    
    def on_window_closed(self, window_object: Any) -> None:
        """
        分析視窗關閉時調用
        
        Args:
            window_object: 視窗物件
        """
        logger.debug(f"[LapAnalysisManager] Window closed")
        
        # 斷開信號連接
        if hasattr(window_object, '_sub_window'):
            sub_window = window_object._sub_window
            if sub_window and hasattr(sub_window, 'window_closed'):
                try:
                    sub_window.window_closed.disconnect()
                except Exception:
                    pass
        
        # 從追蹤集合移除
        self.lap_analysis_windows.discard(window_object)
        logger.debug(f"[LapAnalysisManager] Active windows: {len(self.lap_analysis_windows)}")
        
        # 調用模組清理方法
        if hasattr(window_object, 'cleanup'):
            try:
                window_object.cleanup()
            except Exception as e:
                logger.error(f"[LapAnalysisManager] Cleanup failed: {e}")
        
        # 清理引用
        if hasattr(window_object, '_sub_window'):
            sub_window = window_object._sub_window
            if sub_window and sub_window.parent():
                mdi_area = sub_window.parent()
                if hasattr(mdi_area, 'removeSubWindow'):
                    mdi_area.removeSubWindow(sub_window)
            window_object._sub_window = None
        
        # 檢查是否需要隱藏控件
        self.hide_lap_controls()
    
    # ==================== 車手列表 ====================
    
    def initialize_driver_lists(self) -> None:
        """初始化車手列表（使用主視窗快取）"""
        logger.debug("[LapAnalysisManager] Initializing driver lists")
        
        mw = self.main_window
        
        try:
            # 獲取年份
            year_str = mw.year_combo.currentText() if hasattr(mw, 'year_combo') else "2025"
            year = int(year_str)
            
            # 獲取車手列表
            drivers = []
            if hasattr(mw, 'get_drivers_for_year'):
                drivers = mw.get_drivers_for_year(year)
            
            logger.debug(f"[LapAnalysisManager] Got {len(drivers)} drivers for year {year}")
            
            # 更新 driver1_combo
            if hasattr(mw, 'driver1_combo'):
                mw.driver1_combo.clear()
                for driver in drivers:
                    mw.driver1_combo.addItem(driver, driver)
                if drivers:
                    mw.driver1_combo.setCurrentText(drivers[0])
            
            # 更新 driver2_combo（包含 None 選項）
            if hasattr(mw, 'driver2_combo'):
                from core.gui_i18n import tr
                mw.driver2_combo.clear()
                mw.driver2_combo.addItem(tr("none_option", "None"), None)
                for driver in drivers:
                    mw.driver2_combo.addItem(driver, driver)
            
            logger.debug("[LapAnalysisManager] Driver lists initialized")
            
        except Exception as e:
            logger.error(f"[LapAnalysisManager] Failed to initialize driver lists: {e}")
    
    # ==================== 批次更新 ====================
    
    def update_all_analysis(self) -> None:
        """更新所有分析視窗"""
        logger.debug("[LapAnalysisManager] Updating all analysis windows")
        
        # 委派給主視窗的方法（保持向後兼容）
        if hasattr(self.main_window, 'update_all_lap_analysis'):
            self.main_window.update_all_lap_analysis()
        else:
            logger.warning("[LapAnalysisManager] update_all_lap_analysis not found in main_window")
    
    def _on_update_all_clicked(self) -> None:
        """更新全部按鈕點擊處理"""
        self.update_all_analysis()
    
    def _on_linkage_toggled(self, checked: bool) -> None:
        """連動開關切換處理"""
        logger.debug(f"[LapAnalysisManager] Linkage toggled: {checked}")
        
        # 委派給主視窗的方法
        if hasattr(self.main_window, 'toggle_lap_analysis_linkage'):
            self.main_window.toggle_lap_analysis_linkage(checked)
    
    # ==================== 統計資訊 ====================
    
    def get_stats(self) -> dict:
        """獲取統計資訊"""
        return {
            'active_windows': len(self.lap_analysis_windows),
            'controls_visible': self.lap_controls_visible,
            'controls_added': self._lap_controls_added,
        }
    
    def get_active_analysis_types(self) -> Set[str]:
        """獲取當前活動的分析類型"""
        types = set()
        for window in self.lap_analysis_windows:
            if hasattr(window, '_analysis_type'):
                types.add(window._analysis_type)
        return types
