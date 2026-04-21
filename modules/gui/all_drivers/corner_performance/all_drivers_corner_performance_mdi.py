#!/usr/bin/env python3
"""
All Drivers Corner Performance MDI

Manages MDI window, integrating data loader and chart widget

Author: F1T Team
Date: 2025-10-26
Version: 2.0.0
Update: 2026-01-18 - Tab-based UI with UniversalStintSelector
"""

import sys
from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QMessageBox, QSplitter,
    QTabWidget, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer

# Import base class
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# Import data loader
try:
    from .corner_performance_loader import CornerPerformanceDataLoader
except ImportError:
    from modules.gui.all_drivers.corner_performance.corner_performance_loader import (
        CornerPerformanceDataLoader
    )

# Import chart widget
try:
    from .corner_performance_scatter_widget import CornerPerformanceScatterWidget
except ImportError:
    from modules.gui.all_drivers.corner_performance.corner_performance_scatter_widget import (
        CornerPerformanceScatterWidget
    )

# Import UniversalStintSelector (for Tab 2)
try:
    from modules.gui.base.universal_stint_selector import UniversalStintSelector, StintInfo
except ImportError:
    from modules.gui.base.universal_stint_selector import UniversalStintSelector, StintInfo

# Import i18n
from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)

logger = get_logger(component="gui")

def _log_to_logger(*args, sep=" ", end=""):
    message = sep.join(str(arg) for arg in args)
    if message.startswith("[ERROR]") or "❌" in message:
        logger.error(message)
    elif message.startswith("[WARNING]") or "⚠️" in message:
        logger.warning(message)
    else:
        logger.info(message)


# print = _log_to_logger  # 已停用：避免 print 輸出到終端


class AllDriversCornerPerformanceMDI(UniversalAnalysisMDI):
    """
    全車手彎道性能分析 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 CornerPerformanceDataLoader 和 CornerPerformanceScatterWidget
    """
    
    # 模組類型註冊標記
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="corner_performance",
                display_name=tr("corner_performance", "Corner Performance"),
                default_size=(1400, 1000),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("corner_performance", config)
            cls._REGISTERED = True
            logger.debug("[CORNER_MDI] 模組類型已註冊")
    
    def __init__(self, parent=None, corner_type="low_speed"):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
            corner_type: 彎道類型 ("low_speed", "mid_speed", "high_speed")
        """
        logger.debug(f"[CORNER_MDI] AllDriversCornerPerformanceMDI 開始初始化... corner_type={corner_type}")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 保存彎道類型
        self.corner_type = corner_type
        
        # 調用基類初始化
        super().__init__(analysis_type="corner_performance", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        logger.debug(f"[CORNER_MDI] 基類初始化完成，等待參數設置... corner_type={corner_type}")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組（設置參數並載入初始數據）
        
        Args:
            parent_widget: 父級 widget（可選）
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.debug("[CORNER_MDI] 開始初始化模組...")
            
            # ✅ 驗證必要屬性（與 Brake Performance 完全相同）
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.debug("[CORNER_MDI] 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.debug("[CORNER_MDI] 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.debug("[CORNER_MDI] 缺少 current_session 屬性")
                return False
            
            # ✅ 設置參數（從實例屬性獲取，與 Brake Performance 完全相同）
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.debug(f"[CORNER_MDI] 參數已設置: {self.year} {self.race} {self.session}")
            
            # ✅ 調用基類的 initialize_module（與 Brake Performance 完全相同）
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.debug("[CORNER_MDI] 基類初始化失敗")
                return False
            
            # ✅ 驗證組件已創建（與 Brake Performance 完全相同）
            if not self.chart_widget:
                logger.debug("[CORNER_MDI] chart_widget 未創建")
                return False
            
            if not self.data_manager:
                logger.debug("[CORNER_MDI] data_manager 未創建")
                return False
            
            logger.debug(f"[CORNER_MDI] 組件創建成功")
            
            # ✅ 自動載入初始數據（與 Brake Performance 完全相同）
            logger.debug("[CORNER_MDI] 準備載入初始數據...")
            self.load_initial_data()
            
            return True
            
        except Exception as e:
            logger.debug(f"[CORNER_MDI] 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ------------------------------------------------------------------
    # 抽象方法實現（基類要求）
    # ------------------------------------------------------------------
    
    def create_data_manager(self):
        """
        創建資料管理器（資料載入器）- 基類抽象方法
        
        Returns:
            CornerPerformanceDataLoader: 資料載入器實例
        """
        logger.debug("[CORNER_MDI] 創建資料管理器...")
        
        loader = CornerPerformanceDataLoader(parent=self)
        
        # ✅ 連接信號（與 Brake Performance 完全相同，移除 load_progress）
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        logger.debug("[CORNER_MDI] 資料管理器已創建")
        return loader
    
    def create_chart_widget(self):
        """
        創建圖表元件 - 基類抽象方法
        
        Returns:
            CornerPerformanceScatterWidget: 散點圖元件實例
        """
        logger.debug(f"[CORNER_MDI] 創建圖表元件... corner_type={self.corner_type}")
        
        # 創建散點圖元件（傳遞彎道類型）
        widget = CornerPerformanceScatterWidget(parent=None, corner_type=self.corner_type)
        
        # 連接信號
        widget.driver_clicked.connect(self._on_driver_clicked)
        widget.corner_switched.connect(self._on_corner_switched)
        
        logger.debug(f"[CORNER_MDI] 圖表元件已創建 corner_type={self.corner_type}")
        return widget
    
    def create_additional_widgets(self) -> list:
        """
        Create additional widgets - Optional method
        
        2026-01-18: StintSelector moved to Tab 2, no additional widgets needed here
        
        Returns:
            list: Empty list (Stint selector is in Tab 2)
        """
        return []
    
    # ========== Tab UI Setup ==========
    
    def _setup_ui(self):
        """
        Override base class _setup_ui to implement Tab-based architecture
        
        Tab 1: Chart (CornerPerformanceScatterWidget)
        Tab 2: Stint Selection (UniversalStintSelector)
        
        Reference: lap_box_plot_analysis_mdi.py
        """
        logger.info("[CORNER_MDI] _setup_ui() - Tab UI Architecture")
        
        # Initialize debounce timer for stint selection changes
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)  # 300ms debounce
        self._debounce_timer.timeout.connect(self._apply_stint_filter)
        self._pending_update_data = None
        
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create Tab Widget
        self.tab_widget = QTabWidget()
        
        # ============ Tab 1: Chart Display ============
        chart_tab = QWidget()
        chart_tab_layout = QVBoxLayout(chart_tab)
        chart_tab_layout.setContentsMargins(5, 5, 5, 5)
        
        # Chart area
        if self.chart_widget and not self._is_widget_valid(self.chart_widget):
            self._debug("Detected invalid chart widget, recreating")
            self._disconnect_chart_widget_signals()
            try:
                self.chart_widget = self.create_chart_widget()
            except Exception as create_exc:
                self._error(f"Failed to recreate chart widget: {create_exc}")
                self.chart_widget = None
            else:
                self._connect_chart_widget_signals()
        
        if self.chart_widget:
            chart_frame = QFrame()
            chart_frame.setFrameStyle(QFrame.StyledPanel)
            chart_frame.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            chart_frame.setFocusPolicy(Qt.NoFocus)
            
            chart_frame_layout = QVBoxLayout(chart_frame)
            chart_frame_layout.setContentsMargins(5, 5, 5, 5)
            chart_frame_layout.addWidget(self.chart_widget)
            chart_tab_layout.addWidget(chart_frame)
        
        self.tab_widget.addTab(chart_tab, tr("corner.tab.chart", "Chart"))
        
        # ============ Tab 2: Stint Selection ============
        stint_tab = QWidget()
        stint_tab_layout = QVBoxLayout(stint_tab)
        stint_tab_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create Stint Selector
        try:
            # 使用 corner_type 區分不同彎道分析視窗，確保 Global Sync 正確運作
            module_id = f"corner_performance_{self.corner_type}"
            self.stint_selector = UniversalStintSelector(module_id=module_id)
            self.stint_selector.selection_changed.connect(self._on_stint_selection_changed)
            self.stint_selector.merge_mode_changed.connect(self._on_merge_mode_changed)
            # V0.15.1: 預設啟用全局同步
            self.stint_selector.enable_global_sync(True)
            stint_tab_layout.addWidget(self.stint_selector)
            logger.info(f"[CORNER_MDI] Stint Selector created successfully (module_id={module_id})")
        except Exception as exc:
            logger.error(f"[CORNER_MDI] Failed to create Stint Selector: {exc}")
            import traceback
            traceback.print_exc()
            # Add placeholder label
            placeholder = QLabel(tr("corner.stint.error", "Stint Selector unavailable"))
            placeholder.setAlignment(Qt.AlignCenter)
            stint_tab_layout.addWidget(placeholder)
            self.stint_selector = None
        
        self.tab_widget.addTab(stint_tab, tr("corner.tab.stint_selection", "Stint Selection"))
        
        # Add Tab Widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Status bar (optional, hidden)
        self.status_bar = None
        
        logger.info("[CORNER_MDI] Tab UI setup complete (Chart + Stint Selection)")
    
    def _on_stint_selection_changed(self, selected_stints: List[StintInfo]) -> None:
        """Handle Stint selection change (with debounce)"""
        logger.debug(f"[CORNER_MDI] Stint selection changed: {len(selected_stints)} stints")
        
        if not hasattr(self, 'stint_selector') or not self.stint_selector:
            return
        
        # Prepare update data
        self._pending_update_data = {'trigger': 'selection_changed', 'stints': selected_stints}
        
        # Reset debounce timer
        self._debounce_timer.stop()
        self._debounce_timer.start()
    
    def _on_merge_mode_changed(self, is_merge_mode: bool) -> None:
        """Handle merge mode toggle (with debounce)"""
        logger.info(f"[CORNER_MDI] Merge mode changed: {'Merge' if is_merge_mode else 'Split'}")
        
        # Prepare update data
        self._pending_update_data = {'trigger': 'merge_mode_changed', 'is_merge': is_merge_mode}
        
        # Reset debounce timer
        self._debounce_timer.stop()
        self._debounce_timer.start()
    
    def _apply_stint_filter(self) -> None:
        """Apply stint filter to chart (called after debounce)"""
        if not self._pending_update_data:
            return
        
        try:
            if not hasattr(self, 'stint_selector') or not self.stint_selector:
                return
            
            if not hasattr(self, 'chart_widget') or not self.chart_widget:
                return
            
            # Get selected stints
            selected_stints = self.stint_selector.get_selected_stints()
            
            # Build filter: {driver: [stint_numbers]}
            filter_result: Dict[str, List[int]] = {}
            for stint in selected_stints:
                if stint.driver not in filter_result:
                    filter_result[stint.driver] = []
                filter_result[stint.driver].append(stint.stint_number)
            
            # Get merge mode from stint selector
            is_merge_mode = True
            if hasattr(self.stint_selector, 'merge_mode_cb'):
                is_merge_mode = self.stint_selector.merge_mode_cb.isChecked()
            
            logger.info(f"[CORNER_MDI] Applying stint filter: {len(filter_result)} drivers, merge_mode={is_merge_mode}")
            
            # Update chart's mode and filter
            if hasattr(self.chart_widget, 'is_merge_mode'):
                self.chart_widget.is_merge_mode = is_merge_mode
            
            if hasattr(self.chart_widget, 'selected_stints'):
                self.chart_widget.selected_stints = filter_result
            
            # Update hidden_drivers based on filter
            if hasattr(self.chart_widget, 'hidden_drivers'):
                # Get all drivers from data
                all_drivers = set()
                if hasattr(self.chart_widget, 'current_data') and self.chart_widget.current_data:
                    mode_a = self.chart_widget.current_data.get("mode_a_unified", {})
                    drivers_data = mode_a.get("drivers", [])
                    for d in drivers_data:
                        all_drivers.add(d.get("driver", ""))
                    
                    # Also check fastest_lap_analysis
                    if not all_drivers:
                        fla = self.chart_widget.current_data.get("fastest_lap_analysis", {})
                        for d in fla.get("drivers", []):
                            all_drivers.add(d.get("driver", ""))
                
                # Hide drivers not in selection
                selected_drivers = set(filter_result.keys())
                self.chart_widget.hidden_drivers = all_drivers - selected_drivers
            
            # Redraw chart
            if hasattr(self.chart_widget, 'draw_scatter_chart'):
                self.chart_widget.draw_scatter_chart()
            
        except Exception as e:
            logger.error(f"[CORNER_MDI] Failed to apply stint filter: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._pending_update_data = None
    
    # ========== Data Processing Callbacks ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        Data loaded callback
        
        2026-01-18: Updated to use UniversalStintSelector
        
        Args:
            data: Loaded data (F120 format with stints)
        """
        try:
            logger.debug("[CORNER_MDI] Received data loaded signal")
            
            # Check if data is empty
            if not data:
                self._on_load_error(tr("data_empty", "Data is empty"))
                return
            
            self._current_data = data
            self._is_data_loaded = True
            
            # Update chart
            if self.chart_widget:
                self.chart_widget.update_data(data)
            
            # Populate Stint Selector (Tab 2)
            if hasattr(self, 'stint_selector') and self.stint_selector:
                stints_available = data.get("stints_available", False)
                
                logger.debug(f"[CORNER_MDI] Stint data: available={stints_available}")
                
                if stints_available:
                    # V0.15.1: 設置 Session 資訊（用於 Global Sync 過濾）
                    self.stint_selector.set_session_info(
                        year=str(self.year),
                        race=self.race,
                        session=self.session
                    )
                    # Pass data to UniversalStintSelector (it will detect F120 format)
                    self.stint_selector.set_data(data)
                    logger.info("[CORNER_MDI] Stint data loaded into UniversalStintSelector")
                else:
                    logger.warning("[CORNER_MDI] No stint data available for this session")
            
            logger.debug("[CORNER_MDI] Data processing complete")
            
        except Exception as e:
            logger.debug(f"[CORNER_MDI] Data processing failed: {e}")
            import traceback
            traceback.print_exc()
            self._on_load_error(f"{tr('data_processing_error', 'Data processing error')}: {str(e)}")
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調（與 Brake Performance 完全相同）
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.debug(f"[CORNER_MDI] 資料載入錯誤: {error_msg}")
        QMessageBox.critical(None, tr("load_error", "載入錯誤"), error_msg)
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """Status change callback"""
        logger.debug(f"[CORNER_MDI] Status: {status}")
    
    def load_initial_data(self):
        """載入初始數據（與 Brake Performance 完全相同）"""
        try:
            logger.debug("[CORNER_MDI] 開始載入初始數據...")
            
            if not self.data_manager:
                logger.debug("[CORNER_MDI] data_manager 不存在")
                return
            
            # ✅ 呼叫資料載入器（與 Brake Performance 完全相同）
            success = self.data_manager.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
            
            if not success:
                logger.debug("[CORNER_MDI] 資料載入失敗")
                
        except Exception as e:
            logger.debug(f"[CORNER_MDI] 載入初始數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    # ========== 覆寫基類方法 ==========
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        生成視窗標題（覆寫基類方法）- 根據彎道類型顯示不同標題
        
        Args:
            year: 年份（忽略）
            race: 賽事（忽略）
            session: 場次（忽略）
            
        Returns:
            str: 模組名稱標題
        """
        from core.gui_i18n import tr
        
        # 根據彎道類型返回不同標題
        corner_type_titles = {
            "low_speed": tr('low_speed_corner_analysis', 'Low-Speed Corner Analysis'),
            "mid_speed": tr('mid_speed_corner_analysis', 'Mid-Speed Corner Analysis'),
            "high_speed": tr('high_speed_corner_analysis', 'High-Speed Corner Analysis')
        }
        
        return corner_type_titles.get(self.corner_type, tr('corner_performance_analysis', 'Corner Performance Analysis'))
    
    # ========== 事件處理 ==========
    
    @pyqtSlot(str)
    def _on_driver_clicked(self, driver_code: str):
        """車手點擊事件（與 Brake Performance 完全相同）"""
        logger.debug(f"[CORNER_MDI] 車手被點擊: {driver_code}")
    
    @pyqtSlot(str)
    def _on_corner_switched(self, corner_type: str):
        """
        彎道類型切換事件（Corner Performance 專屬）
        
        Args:
            corner_type: 彎道類型（low_speed, mid_speed, high_speed）
        """
        logger.debug(f"[CORNER_MDI] 彎道類型切換: {corner_type}")
    
    # ========== 參數更新機制（完全複製 Ideal Lap Ranking）==========
    
    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        """
        更新分析參數並重新載入資料
        
        完全複製 Ideal Lap Ranking 的實現
        
        Args:
            year: 新的年份
            race: 新的賽事
            session: 新的賽段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            logger.debug(f"[CORNER_MDI] 🔄 更新參數: {year} {race} {session}")
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.year = str(year)
            self.race = race
            self.session = session
            
            # 同時更新 DataLoader 的參數
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager.year = str(year)
                self.data_manager.race = race
                self.data_manager.session = session
                logger.info(f"[CORNER_MDI] ✅ DataManager 參數已同步")
            elif hasattr(self, 'data_loader') and self.data_loader:
                self.data_loader.year = str(year)
                self.data_loader.race = race
                self.data_loader.session = session
                logger.info(f"[CORNER_MDI] ✅ DataLoader 參數已同步")
            
            # 🔑 重點：調用 load_initial_data() 觸發資料重新載入
            # 這個方法會啟動 DataLoader 並更新 UI
            logger.debug(f"[CORNER_MDI] 🌐 觸發資料重新載入...")
            self.load_initial_data()
            
            # 異步載入，返回 True 表示啟動成功
            return True
            
        except Exception as e:
            logger.error(f"[CORNER_MDI] 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """
        覆寫通用參數更新邏輯，確保觸發資料載入
        
        完全複製 Ideal Lap Ranking 的實現
        
        Args:
            year: 年份
            race: 賽事
            session: 賽段
            **kwargs: 額外參數
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 步驟 1: 確定目標參數（使用新值或保留當前值）
            target_year = year if year is not None else (self.year or getattr(self, 'current_year', None))
            target_race = race if race is not None else (self.race or getattr(self, 'current_race', None))
            target_session = session if session is not None else (self.session or getattr(self, 'current_session', None))

            # 驗證必要參數
            if not all([target_year, target_race, target_session]):
                logger.error("[CORNER_MDI] 參數更新失敗：缺少必要參數")
                return False

            # 步驟 2: 標準化參數
            normalized_year = str(target_year)
            normalized_race = target_race
            normalized_session = target_session

            # 步驟 3: 更新實例屬性
            self.current_year = normalized_year
            self.current_race = normalized_race
            self.current_session = normalized_session

            # 步驟 4: 發射參數更新信號
            params_payload = {
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session
            }
            self.parameters_updated.emit(params_payload)
            
            # 步驟 5: 更新視窗標題
            self.update_window_title()

            # 步驟 6: 觸發實際的數據載入（關鍵步驟）
            logger.debug(f"[CORNER_MDI] 📊 調用 update_analysis_parameters...")
            return self.update_analysis_parameters(
                self.current_year,
                self.current_race,
                self.current_session
            )

        except Exception as exc:
            logger.error(f"[CORNER_MDI] update_parameters 失敗: {exc}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========== 🆕 主 GUI "Show All Data" 按鈕橋接方法 ==========
    
    def reset_chart_view(self):
        """
        重置圖表視圖（主 GUI "Show All Data" 按鈕調用）
        
        這個方法會被主 GUI 的 show_all_data_in_current_tab() 調用
        用於恢復所有被隱藏的車手數據
        """
        try:
            logger.debug("[CORNER_MDI] 🔄 收到 reset_chart_view 請求")
            
            # 檢查 chart_widget 是否存在
            if not hasattr(self, 'chart_widget') or not self.chart_widget:
                logger.warning("[CORNER_MDI] ⚠️  chart_widget 不存在")
                return
            
            # 檢查 chart_widget 是否有 show_all_drivers 方法
            if not hasattr(self.chart_widget, 'show_all_drivers'):
                logger.warning("[CORNER_MDI] ⚠️  chart_widget 沒有 show_all_drivers 方法")
                return
            
            # 調用 Widget 的 show_all_drivers() 方法
            logger.info("[CORNER_MDI] ✅ 調用 chart_widget.show_all_drivers()")
            self.chart_widget.show_all_drivers()
            
        except Exception as e:
            logger.error(f"[CORNER_MDI] ❌ reset_chart_view 失敗: {e}")
            import traceback
            traceback.print_exc()


__all__ = ["AllDriversCornerPerformanceMDI"]
