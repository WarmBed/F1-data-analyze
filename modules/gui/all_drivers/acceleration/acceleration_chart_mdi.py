#!/usr/bin/env python3
"""
全車手加速度圖表 MDI 視窗
All Drivers Acceleration Chart MDI

負責管理 MDI 視窗，整合資料載入器和圖表元件
呼叫 F121 API 獲取全圈數直線速度統計並繪製速度-加速度圖表

2025-01-19: 新增 Tab-based UI 和 UniversalStintSelector 支援

作者: F1T Team
日期: 2025-12-14
版本: 1.1.0
"""

from typing import Dict, Any, Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QMessageBox, QTabWidget, QLabel, QFrame
)
from PyQt5.QtCore import pyqtSlot, Qt, QTimer

# 導入基類
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入資料載入器
from .acceleration_chart_data_loader import AccelerationChartDataLoader

# 導入圖表元件
from .acceleration_chart_widget import AccelerationChartWidget

# 導入 UniversalStintSelector
try:
    from modules.gui.base.universal_stint_selector import UniversalStintSelector, StintInfo
except ImportError:
    from modules.gui.base.universal_stint_selector import UniversalStintSelector, StintInfo

# 導入國際化
from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger("acceleration_chart_mdi", component="gui")


class AllDriversAccelerationChartMDI(UniversalAnalysisMDI):
    """
    全車手加速度圖表 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 AccelerationChartDataLoader 和 AccelerationChartWidget
    """
    
    # 模組類型註冊標記
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="all_drivers_acceleration_chart",
                display_name="All Drivers Acceleration Chart",
                default_size=(1100, 800),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("all_drivers_acceleration_chart", config)
            cls._REGISTERED = True
            logger.info("[ACCEL_CHART_MDI] 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        logger.info("[ACCEL_CHART_MDI] AllDriversAccelerationChartMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="all_drivers_acceleration_chart", parent=parent)
        
        # 初始化參數
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        logger.info("[ACCEL_CHART_MDI] 基類初始化完成，等待參數設置...")
    
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
            logger.info("[ACCEL_CHART_MDI] 開始初始化模組...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                logger.error("[ACCEL_CHART_MDI] 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                logger.error("[ACCEL_CHART_MDI] 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                logger.error("[ACCEL_CHART_MDI] 缺少 current_session 屬性")
                return False
            
            # 設置參數
            self.year = int(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            logger.info("[ACCEL_CHART_MDI] 參數已設置: %s %s %s", self.year, self.race, self.session)
            
            # 調用基類的 initialize_module
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                logger.error("[ACCEL_CHART_MDI] 基類初始化失敗")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                logger.error("[ACCEL_CHART_MDI] chart_widget 未創建")
                return False
            
            if not self.data_manager:
                logger.error("[ACCEL_CHART_MDI] data_manager 未創建")
                return False
            
            logger.info("[ACCEL_CHART_MDI] 組件創建成功")
            
            # 自動載入初始數據
            logger.info("[ACCEL_CHART_MDI] 準備載入初始數據...")
            self.load_initial_data()
            
            return True
            
        except Exception as e:
            logger.exception("[ACCEL_CHART_MDI] 初始化失敗: %s", e)
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料管理器（資料載入器）
        
        Returns:
            AccelerationChartDataLoader: 資料載入器實例
        """
        logger.info("[ACCEL_CHART_MDI] 創建資料管理器...")
        
        loader = AccelerationChartDataLoader(parent=self)
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        logger.info("[ACCEL_CHART_MDI] 資料管理器已創建")
        return loader
    
    def create_chart_widget(self):
        """
        創建圖表元件
        
        Returns:
            AccelerationChartWidget: 圖表元件實例
        """
        logger.info("[ACCEL_CHART_MDI] 創建圖表元件...")
        
        widget = AccelerationChartWidget(parent=None)
        
        logger.info("[ACCEL_CHART_MDI] 圖表元件已創建")
        return widget
    
    def create_additional_widgets(self) -> list:
        """
        創建額外的 Widget 組件
        
        Returns:
            list: 額外的 Widget 列表（空）
        """
        # Tab 架構在 _setup_ui 中創建 UniversalStintSelector
        return []
    
    def _setup_ui(self):
        """
        覆寫基類 _setup_ui 以實現 Tab-based 架構
        
        Tab 1: Chart (AccelerationChartWidget)
        Tab 2: Stint Selection (UniversalStintSelector)
        """
        logger.info("[ACCEL_CHART_MDI] _setup_ui() - Tab UI Architecture")
        
        # 初始化防抖計時器
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)  # 300ms 防抖
        self._debounce_timer.timeout.connect(self._apply_stint_filter)
        self._pending_update_data = None
        
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 創建 Tab Widget
        self.tab_widget = QTabWidget()
        
        # ============ Tab 1: 圖表顯示 ============
        chart_tab = QWidget()
        chart_tab_layout = QVBoxLayout(chart_tab)
        chart_tab_layout.setContentsMargins(5, 5, 5, 5)
        
        if self.chart_widget:
            chart_frame = QFrame()
            chart_frame.setFrameStyle(QFrame.StyledPanel)
            chart_frame.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            chart_frame.setFocusPolicy(Qt.NoFocus)
            
            chart_frame_layout = QVBoxLayout(chart_frame)
            chart_frame_layout.setContentsMargins(5, 5, 5, 5)
            chart_frame_layout.addWidget(self.chart_widget)
            chart_tab_layout.addWidget(chart_frame)
        
        self.tab_widget.addTab(chart_tab, tr("accel.tab.chart", "Chart"))
        
        # ============ Tab 2: Stint 選擇 ============
        stint_tab = QWidget()
        stint_tab_layout = QVBoxLayout(stint_tab)
        stint_tab_layout.setContentsMargins(5, 5, 5, 5)
        
        try:
            self.stint_selector = UniversalStintSelector(module_id="acceleration_chart")
            self.stint_selector.selection_changed.connect(self._on_stint_selection_changed)
            self.stint_selector.merge_mode_changed.connect(self._on_merge_mode_changed)
            # V0.15.1: 預設啟用全局同步
            self.stint_selector.enable_global_sync(True)
            stint_tab_layout.addWidget(self.stint_selector)
            logger.info("[ACCEL_CHART_MDI] Stint Selector 創建成功")
        except Exception as exc:
            logger.error(f"[ACCEL_CHART_MDI] Stint Selector 創建失敗: {exc}")
            import traceback
            traceback.print_exc()
            placeholder = QLabel(tr("accel.stint.error", "Stint Selector unavailable"))
            placeholder.setAlignment(Qt.AlignCenter)
            stint_tab_layout.addWidget(placeholder)
            self.stint_selector = None
        
        self.tab_widget.addTab(stint_tab, tr("accel.tab.stint_selection", "Stint Selection"))
        
        # 加入 Tab Widget 到主佈局
        main_layout.addWidget(self.tab_widget)
        
        self.status_bar = None
        
        logger.info("[ACCEL_CHART_MDI] Tab UI 設置完成 (Chart + Stint Selection)")
    
    def _on_stint_selection_changed(self, selected_stints: List[StintInfo]) -> None:
        """處理 Stint 選擇變更（帶防抖）"""
        logger.debug(f"[ACCEL_CHART_MDI] Stint selection changed: {len(selected_stints)} stints")
        
        if not hasattr(self, 'stint_selector') or not self.stint_selector:
            return
        
        self._pending_update_data = {'trigger': 'selection_changed', 'stints': selected_stints}
        
        self._debounce_timer.stop()
        self._debounce_timer.start()
    
    def _on_merge_mode_changed(self, is_merge_mode: bool) -> None:
        """處理 Merge 模式切換（帶防抖）"""
        logger.info(f"[ACCEL_CHART_MDI] Merge mode changed: {'Merge' if is_merge_mode else 'Split'}")
        
        self._pending_update_data = {'trigger': 'merge_mode_changed', 'is_merge': is_merge_mode}
        
        self._debounce_timer.stop()
        self._debounce_timer.start()
    
    def _apply_stint_filter(self) -> None:
        """應用 stint 過濾到圖表（防抖後調用）"""
        if not self._pending_update_data:
            return
        
        try:
            if not hasattr(self, 'stint_selector') or not self.stint_selector:
                return
            
            if not hasattr(self, 'chart_widget') or not self.chart_widget:
                return
            
            # 獲取選中的 stints
            selected_stints = self.stint_selector.get_selected_stints()
            
            # 建立過濾器: {driver: [stint_numbers]}
            filter_result: Dict[str, List[int]] = {}
            for stint in selected_stints:
                if stint.driver not in filter_result:
                    filter_result[stint.driver] = []
                filter_result[stint.driver].append(stint.stint_number)
            
            # 獲取 merge 模式
            is_merge_mode = True
            if hasattr(self.stint_selector, 'merge_mode_cb'):
                is_merge_mode = self.stint_selector.merge_mode_cb.isChecked()
            
            logger.info(f"[ACCEL_CHART_MDI] Applying stint filter: {len(filter_result)} drivers, merge_mode={is_merge_mode}")
            
            # 更新圖表狀態
            if hasattr(self.chart_widget, 'is_merge_mode'):
                self.chart_widget.is_merge_mode = is_merge_mode
            
            if hasattr(self.chart_widget, 'selected_stints'):
                self.chart_widget.selected_stints = filter_result
            
            # 更新隱藏車手
            if hasattr(self.chart_widget, 'hidden_drivers'):
                all_drivers = set()
                if hasattr(self.chart_widget, '_drivers_data'):
                    for d in self.chart_widget._drivers_data:
                        all_drivers.add(d.get("driver", ""))
                
                selected_drivers = set(filter_result.keys())
                self.chart_widget.hidden_drivers = all_drivers - selected_drivers
            
            # 重繪圖表
            if hasattr(self.chart_widget, '_plot_chart'):
                self.chart_widget._plot_chart()
            
        except Exception as e:
            logger.error(f"[ACCEL_CHART_MDI] Failed to apply stint filter: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._pending_update_data = None

    # ========== 數據處理回調 ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        數據載入完成回調
        
        2025-01-19: 更新以支援 UniversalStintSelector
        
        Args:
            data: 載入的資料
        """
        try:
            logger.info("[ACCEL_CHART_MDI] 收到資料載入完成信號")
            
            if not data:
                self._on_load_error(tr("Data is empty"))
                return
            
            self._current_data = data
            self._is_data_loaded = True
            
            # 更新圖表
            if self.chart_widget:
                self.chart_widget.set_data(data)
            
            # 更新 Stint Selector
            if hasattr(self, 'stint_selector') and self.stint_selector:
                self._update_stint_selector(data)
            
            logger.info("[ACCEL_CHART_MDI] 資料處理完成")
            
        except Exception as e:
            logger.exception("[ACCEL_CHART_MDI] 資料處理失敗: %s", e)
            self._on_load_error(f"{tr('Data processing error')}: {str(e)}")
    
    def _update_stint_selector(self, data: Dict[str, Any]):
        """
        更新 Stint Selector 的數據
        
        Args:
            data: F121 API 返回的數據
        """
        try:
            if not self.stint_selector:
                return
            
            # 檢查是否有 stint 數據
            stints_available = data.get("stints_available", False)
            
            if not stints_available:
                logger.warning("[ACCEL_CHART_MDI] 數據中無 stint 資訊")
            
            # 轉換為 UniversalStintSelector 可識別的格式 (mode_a_unified)
            # F121 格式: {"drivers": [...]} -> {"mode_a_unified": {"drivers": [...]}}
            drivers_data = data.get("drivers", [])
            
            # 將 stint_number 轉換為 stint_id 以符合 F120 格式
            for driver_data in drivers_data:
                stints = driver_data.get("stints", [])
                for stint in stints:
                    if "stint_number" in stint and "stint_id" not in stint:
                        stint["stint_id"] = stint["stint_number"]
            
            formatted_data = {
                "mode_a_unified": {
                    "drivers": drivers_data
                },
                "stints_available": stints_available  # 必須傳遞此標記，否則 Stint Selector 無法識別格式
            }
            
            # 使用 set_data() 方法讓 selector 自動偵測格式
            # V0.15.1: 設置 Session 資訊（用於 Global Sync 過濾）
            self.stint_selector.set_session_info(
                year=str(self.year),
                race=self.race,
                session=self.session
            )
            self.stint_selector.set_data(formatted_data)
            logger.info(f"[ACCEL_CHART_MDI] Stint Selector 已更新: {len(drivers_data)} drivers")
            
        except Exception as e:
            logger.error(f"[ACCEL_CHART_MDI] 更新 Stint Selector 失敗: {e}")
            import traceback
            traceback.print_exc()
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        logger.error("[ACCEL_CHART_MDI] 資料載入錯誤: %s", error_msg)
        QMessageBox.critical(None, tr("Load Error"), error_msg)
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """狀態變更回調"""
        logger.info("[ACCEL_CHART_MDI] 狀態: %s", status)
    
    def load_initial_data(self):
        """載入初始數據"""
        try:
            logger.info("[ACCEL_CHART_MDI] 開始載入初始數據...")
            
            if not self.data_manager:
                logger.error("[ACCEL_CHART_MDI] data_manager 不存在")
                return
            
            # 呼叫資料載入器
            self.data_manager.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
                
        except Exception as e:
            logger.exception("[ACCEL_CHART_MDI] 載入初始數據失敗: %s", e)
    
    # ========== 覆寫基類方法 ==========
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        生成視窗標題
        
        Returns:
            str: 模組名稱標題
        """
        module_name = tr('all_drivers_acceleration_chart', 'All Drivers Acceleration Chart')
        return module_name


__all__ = ["AllDriversAccelerationChartMDI"]
