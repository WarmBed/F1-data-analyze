#!/usr/bin/env python3
"""
PedalBehaviorAnalysisMDI - 油門/煞車行為分析 MDI 模組
======================================================

基於通用 MDI 架構實現的油門/煞車行為分析模組，支援：
- 疊加棒狀圖顯示 Pedal State 分布
- 4 種 Pedal State：throttle_only, brake_only, trail_braking, coasting
- 進站圈/黃旗圈/紅旗圈過濾
- Stint Selection 分段過濾
- 車隊顏色標記車手

數據來源：driver_throttle_ratio JSON 檔案（CLI Function 54）
圖表類型：垂直疊加棒狀圖

Author: F1T Team
Date: 2026-01-12
Version: 1.0.0
"""

import sys
import os
import time
from core import local_requests as requests
import certifi
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QCheckBox, QPushButton, QLabel,
    QSplitter, QMessageBox, QFileDialog, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread

from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
from modules.gui.base.universal_stint_selector import UniversalStintSelector, StintInfo

# 導入專用組件
from .pedal_behavior_data_manager import PedalBehaviorDataManager
from .pedal_behavior_chart_widget import PedalBehaviorStackedBarChartWidget

logger = get_logger(__name__)


class PedalBehaviorApiWorker(QThread):
    """背景工作執行緒 - 從 REST API 獲取 Pedal Behavior 數據"""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, base_url: str, params: Dict[str, Any], timeout: float = 30.0, parent=None):
        super().__init__(parent)
        self.base_url = (base_url or "http://localhost:8000").rstrip('/')
        self.params = dict(params)
        self.timeout = timeout
    
    def run(self):
        try:
            if self.isInterruptionRequested():
                logger.debug("[PEDAL_API_WORKER] 啟動前已被請求中斷，跳過執行")
                return
            
            self.progress.emit(20)
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            query_params: Dict[str, Any] = {
                "function_id": 54,  # Pedal Behavior 使用 Function 54
                "year": int(self.params.get("year")),
                "race": self.params.get("race"),
                "session": self.params.get("session"),
            }
            if self.params.get("force_refresh"):
                query_params["force_refresh"] = True
            
            if self.isInterruptionRequested():
                logger.debug("[PEDAL_API_WORKER] 發送請求前被請求中斷")
                return
            
            logger.debug(f"[PEDAL_API_WORKER] 發送 API 請求: {endpoint}")
            logger.debug(f"[PEDAL_API_WORKER] 參數: {query_params}")
            
            start_ts = time.perf_counter()
            response = requests.post(
                endpoint,
                params=query_params,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=certifi.where()
            )
            
            if self.isInterruptionRequested():
                logger.debug("[PEDAL_API_WORKER] API 回應後被請求中斷，放棄處理結果")
                return
            
            self.progress.emit(70)
            response.raise_for_status()
            
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("API response must be a JSON object")
            if not payload.get("success", False):
                raise RuntimeError(payload.get("message", "API returned success=False"))
            
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("API response missing 'data' object")
            
            latency_ms = (time.perf_counter() - start_ts) * 1000.0
            meta = {
                "source": payload.get("source", "api"),
                "execution_time": payload.get("execution_time"),
                "request_id": payload.get("request_id"),
                "timestamp": payload.get("timestamp"),
                "function_spec": payload.get("function_spec"),
                "latency_ms": round(latency_ms, 2),
                "base_url": self.base_url,
            }
            
            if self.isInterruptionRequested():
                logger.debug("[PEDAL_API_WORKER] 發送成功信號前被請求中斷，放棄發送")
                return
            
            logger.debug(f"[PEDAL_API_WORKER] API 請求成功，延遲: {latency_ms:.2f}ms")
            self.progress.emit(90)
            self.success.emit({"data": data, "meta": meta})
            
        except Exception as exc:
            if not self.isInterruptionRequested():
                logger.error(f"[PEDAL_API_WORKER] API 請求失敗: {exc}")
                self.failure.emit(str(exc))
        finally:
            if not self.isInterruptionRequested():
                self.progress.emit(100)


class PedalBehaviorControlWidget(QWidget):
    """Pedal Behavior 控制面板"""
    
    # 信號
    filter_changed = pyqtSignal(dict)
    reload_requested = pyqtSignal()
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 過濾設定組
        filter_group = QGroupBox(tr("Filter Settings"))
        filter_layout = QVBoxLayout()
        
        self.filter_pit_laps = QCheckBox(tr("Filter Pit Laps"))
        self.filter_pit_laps.setChecked(True)
        self.filter_pit_laps.toggled.connect(self._on_filter_changed)
        
        self.filter_yellow_flags = QCheckBox(tr("Filter Yellow Flags"))
        self.filter_yellow_flags.setChecked(True)
        self.filter_yellow_flags.toggled.connect(self._on_filter_changed)
        
        self.filter_red_flags = QCheckBox(tr("Filter Red Flags"))
        self.filter_red_flags.setChecked(True)
        self.filter_red_flags.toggled.connect(self._on_filter_changed)
        
        self.filter_safety_car = QCheckBox(tr("Filter Safety Car"))
        self.filter_safety_car.setChecked(True)
        self.filter_safety_car.toggled.connect(self._on_filter_changed)
        
        self.filter_vsc = QCheckBox(tr("Filter VSC"))
        self.filter_vsc.setChecked(True)
        self.filter_vsc.toggled.connect(self._on_filter_changed)
        
        filter_layout.addWidget(self.filter_pit_laps)
        filter_layout.addWidget(self.filter_yellow_flags)
        filter_layout.addWidget(self.filter_red_flags)
        filter_layout.addWidget(self.filter_safety_car)
        filter_layout.addWidget(self.filter_vsc)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 操作按鈕組
        button_layout = QHBoxLayout()
        
        self.reload_button = QPushButton(tr("Reload"))
        self.reload_button.clicked.connect(self.reload_requested.emit)
        
        self.export_button = QPushButton(tr("Export Chart"))
        self.export_button.clicked.connect(self.export_requested.emit)
        
        button_layout.addWidget(self.reload_button)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        # 統計標籤
        self.stats_label = QLabel(tr("No data loaded"))
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        # 彈簧
        layout.addStretch()
    
    def _on_filter_changed(self):
        """過濾設定變更"""
        settings = {
            'filter_pit_laps': self.filter_pit_laps.isChecked(),
            'filter_yellow_flags': self.filter_yellow_flags.isChecked(),
            'filter_red_flags': self.filter_red_flags.isChecked(),
            'filter_safety_car': self.filter_safety_car.isChecked(),
            'filter_vsc': self.filter_vsc.isChecked()
        }
        self.filter_changed.emit(settings)
    
    def update_statistics(self, stats_text: str):
        """更新統計標籤"""
        self.stats_label.setText(stats_text)


class PedalBehaviorAnalysisMDI(UniversalAnalysisMDI):
    """油門/煞車行為分析 MDI 主模組"""
    
    def __init__(self, year: int = None, race: str = None, session: str = None, parent=None):
        # 註冊 Pedal Behavior 模組類型（如果尚未註冊）
        if "pedal_behavior" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            pedal_config = AnalysisMDIConfig(
                analysis_type="pedal_behavior",
                display_name=tr("pedal_behavior_analysis", "Pedal Behavior Analysis"),
                default_size=(1200, 800),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False,
                cli_function=54
            )
            UniversalAnalysisMDI.register_mdi_module_type("pedal_behavior", pedal_config)
        
        # 用字符串調用父類
        super().__init__("pedal_behavior", parent)
        
        # 初始化模組組件
        if not self.initialize_module():
            logger.error("[PEDAL_MDI] 模組組件初始化失敗")
            return
        
        # API Worker 引用
        self._api_worker: Optional[PedalBehaviorApiWorker] = None
        
        # 設置當前參數
        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session
        
        logger.debug(f"[PEDAL_MDI] 初始化完成，參數: {year} {race} {session}")
        
        # 自動載入數據（如果提供了參數）- 使用 API
        if year and race and session:
            logger.debug(f"[PEDAL_MDI] 開始自動載入數據（API）...")
            if self.data_manager:
                self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                )
    
    # ========== 抽象方法實現 ==========
    
    def create_data_manager(self) -> PedalBehaviorDataManager:
        """創建數據管理器（實現抽象方法）"""
        manager = PedalBehaviorDataManager(parent=self)
        
        # 連接信號
        manager.data_loaded.connect(self._on_data_loaded)
        manager.load_error.connect(self._on_data_load_error)
        manager.filter_settings_changed.connect(self._on_filter_data_updated)
        
        logger.debug("[PEDAL_MDI] 數據管理器創建完成")
        return manager
    
    def create_chart_widget(self) -> PedalBehaviorStackedBarChartWidget:
        """創建圖表組件（實現抽象方法）"""
        chart = PedalBehaviorStackedBarChartWidget()
        chart.chart_clicked.connect(self._on_chart_clicked)
        logger.debug("[PEDAL_MDI] 圖表組件創建完成")
        return chart
    
    # ========== UI 創建方法 ==========
    
    def _setup_ui(self):
        """
        覆寫 UI 設置 - 添加 Tab 架構
        
        Tab 1: 圖表顯示（油門/煞車行為分析堆疊棒狀圖）
        Tab 2: Stint Selection（使用 UniversalStintSelector）
        """
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
        
        # 圖表區域
        if self.chart_widget and not self._is_widget_valid(self.chart_widget):
            self._debug("檢測到已失效的圖表組件，重新建立")
            self._disconnect_chart_widget_signals()
            try:
                self.chart_widget = self.create_chart_widget()
            except Exception as create_exc:
                self._error(f"重新建立圖表組件失敗: {create_exc}")
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
        
        self.tab_widget.addTab(chart_tab, tr("pedal_behavior.tab_chart", "Chart"))
        
        # ============ Tab 2: Stint Selection ============
        stint_tab = QWidget()
        stint_tab_layout = QVBoxLayout(stint_tab)
        stint_tab_layout.setContentsMargins(5, 5, 5, 5)
        
        # 創建 Stint Selector (V0.15.1: 添加 module_id 和 Global Sync)
        self.stint_selector = UniversalStintSelector(module_id="pedal_behavior")
        self.stint_selector.selection_changed.connect(self._on_stint_selection_changed)
        self.stint_selector.merge_mode_changed.connect(self._on_merge_mode_changed)
        # V0.15.1: 預設啟用全局同步
        self.stint_selector.enable_global_sync(True)
        stint_tab_layout.addWidget(self.stint_selector)
        
        self.tab_widget.addTab(stint_tab, tr("pedal_behavior.tab_stint", "Stint Selection"))
        
        # 添加 Tab Widget 到主佈局
        main_layout.addWidget(self.tab_widget)
        
        # 控制面板（創建但隱藏）
        self.control_widget = PedalBehaviorControlWidget()
        self.control_widget.filter_changed.connect(self._on_filter_changed)
        self.control_widget.reload_requested.connect(self._on_reload_requested)
        self.control_widget.export_requested.connect(self._on_export_requested)
        self.control_widget.setVisible(False)  # 隱藏控制面板
        
        # 狀態列（可選）
        self.status_bar = None
        
        logger.debug("[PEDAL_MDI] Tab UI 設置完成")
    
    def _on_data_loaded(self, data: Dict[str, Any]):
        """數據載入完成"""
        logger.debug("[PEDAL_MDI] 數據載入完成")
        
        # 更新 Stint Selector（使用原始數據）
        if self.stint_selector and self.data_manager:
            raw_data = self.data_manager.get_raw_data()
            if raw_data:
                logger.debug("[PEDAL_MDI] 更新 Stint Selector...")
                # V0.15.1: 設置 Session 資訊（用於 Global Sync 過濾）
                self.stint_selector.set_session_info(
                    year=str(self.current_year),
                    race=self.current_race,
                    session=self.current_session
                )
                self.stint_selector.set_data(raw_data)
                # Stint Selector 會自動觸發 selection_changed 信號
                return
        
        # 如果沒有 Stint Selector，直接更新圖表
        self._update_chart(data)
        
        # 更新統計
        if self.control_widget:
            driver_pedal_data = data.get('driver_pedal_data', {})
            total_drivers = len(driver_pedal_data)
            total_laps = sum(pd.get('valid_lap_count', 0) for pd in driver_pedal_data.values())
            self.control_widget.update_statistics(
                f"Drivers: {total_drivers} | Laps: {total_laps}"
            )
    
    def _on_stint_selection_changed(self, selected_stints: List[StintInfo]):
        """Stint 選擇變更"""
        logger.debug(f"[PEDAL_MDI] Stint 選擇變更: {len(selected_stints)} stints")
        
        if not self.stint_selector or not self.chart_widget or not self.data_manager:
            return
        
        # 獲取原始 Lap 數據
        raw_lap_data = self.data_manager.get_raw_lap_data()
        if not raw_lap_data:
            return
        
        # 根據合併模式獲取選中的 Lap 數據
        if self.stint_selector.is_merge_mode():
            # 合併模式：合併所有選中 Stint 的 Laps（按車手）
            selected_laps_by_driver = self._merge_selected_stints(selected_stints, raw_lap_data)
            if not selected_laps_by_driver:
                logger.debug("[PEDAL_MDI] 沒有選中的 Lap 數據")
                return
            # 計算平均 Pedal State（應用過濾）
            driver_pedal_data = self._calculate_pedal_states_from_laps(selected_laps_by_driver)
        else:
            # 分組模式：每個 Stint 單獨計算（如 ALB S1, ALB S2）
            stint_laps_dict = self._split_selected_stints(selected_stints, raw_lap_data)
            if not stint_laps_dict:
                logger.debug("[PEDAL_MDI] 沒有選中的 Lap 數據")
                return
            # 計算每個 Stint 的 Pedal State
            driver_pedal_data = self._calculate_pedal_states_from_laps(stint_laps_dict)
        
        # 更新圖表
        processed_data = {
            'driver_pedal_data': driver_pedal_data,
            'metadata': {}
        }
        
        self.chart_widget.update_data(processed_data)
        
        # 更新統計
        if self.control_widget:
            total_drivers = len(driver_pedal_data)
            total_laps = sum(pd.get('valid_lap_count', 0) for pd in driver_pedal_data.values())
            self.control_widget.update_statistics(
                f"Drivers: {total_drivers} | Laps: {total_laps} (Stint filtered)"
            )
    
    def _on_merge_mode_changed(self, is_merge_mode: bool):
        """合併模式變更"""
        logger.debug(f"[PEDAL_MDI] 合併模式變更: {is_merge_mode}")
        # 重新觸發選擇變更以更新圖表
        if self.stint_selector:
            selected = self.stint_selector.get_selected_stints()
            self._on_stint_selection_changed(selected)
    
    def _merge_selected_stints(self, selected_stints: List[StintInfo], raw_lap_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """合併選中 Stint 的 Lap 數據（按車手合併）"""
        merged = {}
        
        for stint in selected_stints:
            driver_code = stint.driver
            
            if driver_code not in raw_lap_data:
                continue
            
            # 過濾出 Stint 範圍內的 Laps
            driver_laps = raw_lap_data[driver_code]
            stint_laps = [lap for lap in driver_laps if stint.start_lap <= lap.get('lap_number', 0) <= stint.end_lap]
            
            if driver_code not in merged:
                merged[driver_code] = []
            
            merged[driver_code].extend(stint_laps)
        
        return merged
    
    def _split_selected_stints(self, selected_stints: List[StintInfo], raw_lap_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        分離選中 Stint 的 Lap 數據（每個 Stint 獨立）
        
        返回格式: {"ALB S1": [...], "ALB S2": [...], "VER S1": [...]}
        """
        split_data = {}
        
        for stint in selected_stints:
            driver_code = stint.driver
            stint_number = stint.stint_number
            
            if driver_code not in raw_lap_data:
                continue
            
            # 過濾出 Stint 範圍內的 Laps
            driver_laps = raw_lap_data[driver_code]
            stint_laps = [lap for lap in driver_laps if stint.start_lap <= lap.get('lap_number', 0) <= stint.end_lap]
            
            if stint_laps:
                # 使用 "VER S1" 格式作為 key
                stint_key = f"{driver_code} S{stint_number}"
                split_data[stint_key] = stint_laps
        
        return split_data
    
    def _calculate_pedal_states_from_laps(self, laps_by_driver: Dict[str, List[Dict]]) -> Dict[str, Dict[str, float]]:
        """從 Lap 數據計算平均 Pedal State（應用過濾）"""
        driver_pedal_data = {}
        
        for driver_code, laps in laps_by_driver.items():
            # 過濾圈數
            filtered_laps = self._filter_laps(laps)
            
            if not filtered_laps:
                continue
            
            # 累加 Pedal State 比例
            total_throttle_only = 0.0
            total_brake_only = 0.0
            total_trail_braking = 0.0
            total_coasting = 0.0
            valid_lap_count = 0
            
            for lap in filtered_laps:
                pedal_states = lap.get('pedal_states', {})
                if not pedal_states:
                    continue
                
                total_throttle_only += pedal_states.get('throttle_only_ratio', 0.0)
                total_brake_only += pedal_states.get('brake_only_ratio', 0.0)
                total_trail_braking += pedal_states.get('trail_braking_ratio', 0.0)
                total_coasting += pedal_states.get('coasting_ratio', 0.0)
                valid_lap_count += 1
            
            if valid_lap_count == 0:
                continue
            
            # 計算平均值
            driver_pedal_data[driver_code] = {
                'throttle_only': total_throttle_only / valid_lap_count,
                'brake_only': total_brake_only / valid_lap_count,
                'trail_braking': total_trail_braking / valid_lap_count,
                'coasting': total_coasting / valid_lap_count,
                'valid_lap_count': valid_lap_count
            }
        
        return driver_pedal_data
    
    def _filter_laps(self, laps: List[Dict]) -> List[Dict]:
        """根據控制面板設定過濾圈數"""
        if not self.control_widget:
            return laps
        
        filtered = []
        
        for lap in laps:
            # 過濾進站圈
            if self.control_widget.filter_pit_laps.isChecked():
                if lap.get('is_pit_lap', False):
                    continue
            
            # 過濾黃旗圈
            if self.control_widget.filter_yellow_flags.isChecked():
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('yellow_flag', False):
                    continue
            
            # 過濾紅旗圈
            if self.control_widget.filter_red_flags.isChecked():
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('red_flag', False):
                    continue
            
            # 過濾安全車圈
            if self.control_widget.filter_safety_car.isChecked():
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('safety_car', False):
                    continue
            
            # 過濾 VSC 圈
            if self.control_widget.filter_vsc.isChecked():
                smart_markers = lap.get('smart_markers', {})
                if smart_markers.get('vsc', False):
                    continue
            
            filtered.append(lap)
        
        return filtered
    
    def _update_chart(self, data: Dict[str, Any]):
        """更新圖表"""
        if not self.chart_widget:
            return
        
        self.chart_widget.update_data(data)
    
    def _on_filter_changed(self, settings: Dict[str, bool]):
        """過濾設定變更"""
        logger.debug(f"[PEDAL_MDI] 過濾設定變更: {settings}")
        
        if not self.data_manager:
            return
        
        # 更新數據管理器的過濾設定
        self.data_manager.set_filter_settings(settings)
    
    def _on_filter_data_updated(self, processed_data: Dict[str, Any]):
        """過濾後的數據更新"""
        logger.debug("[PEDAL_MDI] 過濾數據已更新")
        
        # 如果有 Stint Selector，重新觸發選擇
        if self.stint_selector:
            selected = self.stint_selector.get_selected_stints()
            if selected:
                self._on_stint_selection_changed(selected)
                return
        
        # 否則直接更新圖表
        self._update_chart(processed_data)
        
        # 更新統計
        if self.control_widget:
            driver_pedal_data = processed_data.get('driver_pedal_data', {})
            total_drivers = len(driver_pedal_data)
            total_laps = sum(pd.get('valid_lap_count', 0) for pd in driver_pedal_data.values())
            self.control_widget.update_statistics(
                f"Drivers: {total_drivers} | Laps: {total_laps}"
            )
    
    # ========== API 載入方法 ==========
    
    def _load_data_via_api(self, force_refresh: bool = False):
        """通過 API 載入數據"""
        logger.debug(f"[PEDAL_MDI] 啟動 API 載入: {self.current_year} {self.current_race} {self.current_session}")
        
        # 停止之前的 worker
        if self._api_worker and self._api_worker.isRunning():
            logger.debug("[PEDAL_MDI] 正在停止舊的 API Worker...")
            self._api_worker.requestInterruption()
            self._api_worker.wait(2000)
        
        # 創建新的 API Worker
        base_url = "http://localhost:8000"
        params = {
            "year": self.current_year,
            "race": self.current_race,
            "session": self.current_session,
            "force_refresh": force_refresh
        }
        
        self._api_worker = PedalBehaviorApiWorker(base_url, params, parent=self)
        self._api_worker.success.connect(self._on_api_success)
        self._api_worker.failure.connect(self._on_api_failure)
        self._api_worker.progress.connect(self._on_api_progress)
        
        logger.debug("[PEDAL_MDI] 啟動 API Worker...")
        self._api_worker.start()
    
    def _on_api_success(self, result: Dict[str, Any]):
        """API 請求成功"""
        logger.debug(f"[PEDAL_MDI] API 請求成功")
        
        data = result.get("data", {})
        meta = result.get("meta", {})
        
        logger.debug(f"[PEDAL_MDI] 數據來源: {meta.get('source', 'unknown')}")
        logger.debug(f"[PEDAL_MDI] 延遲: {meta.get('latency_ms', 0):.2f}ms")
        
        # 處理數據並更新圖表
        if self.data_manager:
            # 將 API 數據傳給數據管理器處理
            processed_data = self.data_manager._process_data(data)
            if processed_data:
                self._on_data_loaded(processed_data)
            else:
                logger.warning("[PEDAL_MDI] API 數據處理失敗")
                self._on_api_failure("數據處理失敗")
        else:
            logger.error("[PEDAL_MDI] 數據管理器不存在")
            self._on_api_failure("數據管理器不存在")
    
    def _on_api_failure(self, error_msg: str):
        """API 請求失敗"""
        logger.error(f"[PEDAL_MDI] API 請求失敗: {error_msg}")
        
        # 嘗試從本地 JSON 載入
        logger.debug("[PEDAL_MDI] 嘗試從本地 JSON 載入...")
        if self.data_manager:
            success = self.data_manager.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session
            )
            if not success:
                logger.warning("[PEDAL_MDI] 本地 JSON 載入也失敗")
                if self.control_widget:
                    self.control_widget.update_statistics(f"Error: {error_msg}")
    
    def _on_api_progress(self, progress: int):
        """API 進度更新"""
        logger.debug(f"[PEDAL_MDI] API 進度: {progress}%")
    
    def _on_reload_requested(self):
        """重新載入數據 - 使用 API"""
        logger.debug("[PEDAL_MDI] 重新載入數據（API）...")
        if self.data_manager:
            self.data_manager.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                force_refresh=True,
            )
    
    def _on_export_requested(self):
        """匯出圖表"""
        logger.debug("[PEDAL_MDI] 匯出圖表...")
        
        if not self.chart_widget:
            return
        
        # 預設檔案名稱
        default_filename = f"pedal_behavior_{self.current_year}_{self.current_race}_{self.current_session}.png"
        default_path = os.path.join(os.getcwd(), "exports", default_filename)
        
        # 選擇儲存路徑
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export Chart"),
            default_path,
            "PNG (*.png);;JPEG (*.jpg)"
        )
        
        if filepath:
            try:
                # 確保目錄存在
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # 匯出圖表
                self.chart_widget._export_chart()
                
                QMessageBox.information(
                    self,
                    tr("Export Successful"),
                    f"Chart exported to:\n{filepath}"
                )
            except Exception as e:
                logger.debug(f"[PEDAL_MDI] 匯出失敗: {e}")
                QMessageBox.warning(
                    self,
                    tr("Export Failed"),
                    f"Cannot export chart:\n{e}"
                )
    
    def _on_chart_clicked(self, driver_code: str):
        """圖表點擊事件"""
        logger.debug(f"[PEDAL_MDI] 圖表點擊: {driver_code}")
        # 未來可以添加互動功能（例如：顯示詳細資訊）
    
    def _on_data_load_error(self, error_message: str):
        """處理數據載入錯誤"""
        logger.error(f"[PEDAL_MDI] 數據載入錯誤: {error_message}")
        
        if self.control_widget:
            self.control_widget.update_statistics("Data load failed")
        
        QMessageBox.warning(
            self.main_widget,
            tr("Pedal Behavior Analysis") + " - " + tr("Data Load Error"),
            f"Cannot load pedal behavior data:\n{error_message}\n\n"
            "Please ensure:\n"
            "1. API server is running (python refactored_api.py)\n"
            "2. Or JSON file exists in json/ directory\n"
            f"   (Run: python f1_analysis_modular_main.py -f 54 -y {self.current_year} -r {self.current_race} -s {self.current_session})",
            QMessageBox.Ok
        )
    
    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """更新參數 - 使用 data_manager.load_data() 載入數據（API 優先）"""
        try:
            logger.info("[PEDAL_MDI] ========== Pedal Behavior 參數更新 ==========")
            logger.info(f"[PEDAL_MDI] 收到參數: {year} {race} {session}")
            
            # 更新當前參數
            self.current_year = str(year)
            self.current_race = str(race)
            self.current_session = str(session)
            
            # 連接錯誤處理器（只連接一次）
            if not hasattr(self, "_error_handler_connected"):
                if hasattr(self, "data_manager") and self.data_manager:
                    self.data_manager.load_error.connect(self._on_data_load_error)
                    self._error_handler_connected = True
            
            # 使用 data_manager 載入數據（API 優先）
            if hasattr(self, "data_manager") and self.data_manager:
                self.data_manager.year = self.current_year
                self.data_manager.race = self.current_race
                self.data_manager.session = self.current_session
                
                result = self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    **kwargs,
                )
                logger.info(f"[PEDAL_MDI] 數據載入結果: {result}")
                if not result:
                    logger.warning("[PEDAL_MDI] 數據載入請求未成功提交")
            
            logger.info("[PEDAL_MDI] 參數更新完成")
            return True
            
        except Exception as e:
            logger.error(f"[PEDAL_MDI] 參數更新失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


# 模組註冊
def register_pedal_behavior_module():
    """註冊 Pedal Behavior 分析模組"""
    try:
        logger.debug("[PEDAL_MDI] Pedal Behavior 分析模組已註冊")
    except Exception as e:
        logger.warning(f"Pedal Behavior 分析模組註冊失敗: {str(e)}")


# 自動註冊
register_pedal_behavior_module()
