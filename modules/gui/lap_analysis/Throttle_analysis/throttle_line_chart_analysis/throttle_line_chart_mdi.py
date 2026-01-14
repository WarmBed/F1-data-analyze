# -*- coding: utf-8 -*-
"""ThrottleLineChartMDI - 單車手油門折線圖 MDI 模組。"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QSpinBox,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QComboBox,
)

from core.gui_i18n import tr
from core.gui_settings_manager import gui_settings_manager
from core.logger import get_logger

try:  # pragma: no cover - 避免相對匯入在測試環境失敗
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:  # pragma: no cover
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 跨模組同步信號
from modules.gui.base.global_chart_sync_signal import GlobalChartSyncSignal

# 模組標識常量
MODULE_THROTTLE_LINE = GlobalChartSyncSignal.MODULE_THROTTLE_LINE

# from .lap_time_chart_widget import LapTimeChartWidget  # 已移除 - 只顯示 throttle chart
from .signal_bus import ThrottleLineChartSignalBus
from .throttle_duration_chart_widget import ThrottleDurationChartWidget
from .throttle_line_chart_data_loader import ThrottleLineChartDataLoader


_DEFAULT_SETTINGS = {
    "show_full_duration": False,
    "show_ratio": True,
    "show_average": True,
    "show_delta": False,  # 取消 Δ vs Best 顯示
    "rolling_average": False,
    "rolling_window": 3,
    "highlight_threshold": True,
    "threshold_percent": 90.0,
}

logger = get_logger(component="ThrottleLineChartMDI")


class ThrottleLineChartControlPanel(QWidget):
    """側邊控制面板，調整圖表顯示設定。改為5個車手選擇器與 Detailed Lap Analysis 同步。"""

    settingsChanged = pyqtSignal(dict)
    reloadRequested = pyqtSignal()
    exportRequested = pyqtSignal()
    resetRequested = pyqtSignal()
    driversChanged = pyqtSignal(list)  # 改為多車手信號
    clearLabelsRequested = pyqtSignal()  # 清除圖表標籤信號

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = dict(_DEFAULT_SETTINGS)
        self._available_drivers: List[str] = []
        self._selected_drivers: List[str] = []  # 改為列表
        self.driver_combos: List[QComboBox] = []  # 5 個選擇器
        self._is_syncing = False  # 防止循環觸發
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 車手選擇區域 - 水平布局（與 Detailed Lap Analysis 一致）
        drivers_layout = QHBoxLayout()
        drivers_layout.setSpacing(10)
        
        # 創建5個車手選擇下拉選單
        placeholder = tr("throttle_line_chart.option_driver_placeholder", "-- Select --")
        for i in range(5):
            combo = QComboBox()
            combo.setEditable(False)
            combo.addItem(placeholder, "")
            combo.currentTextChanged.connect(self._on_driver_selection_changed)
            combo.setMinimumWidth(50)
            combo.setMaximumWidth(120)
            
            self.driver_combos.append(combo)
            drivers_layout.addWidget(combo)
        
        drivers_layout.addSpacing(10)
        
        # Clear 按鈕
        self.clear_button = QPushButton(tr('clear_button', 'Clear'))
        self.clear_button.clicked.connect(self._clear_selections)
        self.clear_button.setMaximumWidth(60)
        
        drivers_layout.addWidget(self.clear_button)
        
        # Clear Labels 按鈕 - 清除圖表上的標籤
        self.clear_labels_button = QPushButton(tr('clear_labels_button', 'Clear Labels'))
        self.clear_labels_button.clicked.connect(self._on_clear_labels_clicked)
        self.clear_labels_button.setMaximumWidth(100)
        self.clear_labels_button.setToolTip(tr('clear_labels_tooltip', 'Clear all pinned labels on the chart'))
        
        drivers_layout.addWidget(self.clear_labels_button)
        drivers_layout.addStretch()
        
        layout.addLayout(drivers_layout)

    def _on_driver_selection_changed(self) -> None:
        """車手選擇變更處理"""
        if self._is_syncing:
            return
            
        # 收集所有選中的車手
        placeholder = tr("throttle_line_chart.option_driver_placeholder", "-- Select --")
        selected = []
        for combo in self.driver_combos:
            text = combo.currentText()
            if text and text != placeholder and text.strip():
                driver = text.strip().upper()
                if driver not in selected:  # 避免重複
                    selected.append(driver)
        
        if selected != self._selected_drivers:
            self._selected_drivers = selected
            self.driversChanged.emit(selected)

    def _clear_selections(self) -> None:
        """清除所有選擇"""
        self._is_syncing = True
        placeholder = tr("throttle_line_chart.option_driver_placeholder", "-- Select --")
        for combo in self.driver_combos:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)  # 選擇 placeholder
            combo.blockSignals(False)
        self._is_syncing = False
        
        self._selected_drivers = []
        self.driversChanged.emit([])

    def _on_clear_labels_clicked(self) -> None:
        """清除圖表上的所有標籤"""
        self.clearLabelsRequested.emit()

    def _emit_settings(self) -> None:
        """設定現在由系統設定管理，此方法保留以維持相容性"""
        pass

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """外部下發設定時更新控制面板狀態"""
        self._settings.update(settings)

    def set_available_drivers(self, drivers: Sequence[str], selected: Optional[List[str]] = None) -> None:
        """設定可用車手列表"""
        normalized = [str(driver).upper() for driver in drivers if driver]
        if normalized == self._available_drivers:
            return

        self._available_drivers = normalized
        placeholder = tr("throttle_line_chart.option_driver_placeholder", "-- Select --")
        
        self._is_syncing = True
        for combo in self.driver_combos:
            combo.blockSignals(True)
            current = combo.currentText()
            combo.clear()
            combo.addItem(placeholder, "")
            for code in normalized:
                combo.addItem(code, code)
            
            # 嘗試恢復之前的選擇
            if current and current != placeholder and current.upper() in normalized:
                index = combo.findText(current.upper())
                if index != -1:
                    combo.setCurrentIndex(index)
            combo.blockSignals(False)
        self._is_syncing = False
        
        # 如果有指定初始選擇
        if selected:
            self.set_selected_drivers(selected)

    def set_selected_drivers(self, drivers: List[str]) -> None:
        """設定選中的車手（用於同步）"""
        if self._is_syncing:
            return
            
        self._is_syncing = True
        placeholder = tr("throttle_line_chart.option_driver_placeholder", "-- Select --")
        
        # 先清空所有選擇
        for combo in self.driver_combos:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        
        # 設定新選擇
        for i, driver in enumerate(drivers[:5]):  # 最多 5 個
            if i < len(self.driver_combos):
                combo = self.driver_combos[i]
                combo.blockSignals(True)
                index = combo.findText(driver.upper())
                if index != -1:
                    combo.setCurrentIndex(index)
                combo.blockSignals(False)
        
        self._selected_drivers = [d.upper() for d in drivers if d]
        self._is_syncing = False

    def get_selected_drivers(self) -> List[str]:
        """獲取當前選中的車手列表"""
        return self._selected_drivers.copy()


class ThrottleLineChartView(QWidget):
    """主視圖，只包含油門圖表。支援多車手顯示。"""

    def __init__(self, signal_bus: ThrottleLineChartSignalBus, parent=None):
        super().__init__(parent)
        self.signal_bus = signal_bus
        self._settings = dict(_DEFAULT_SETTINGS)
        self._prepared_cache: Optional[Dict[str, Any]] = None
        self._prepared_cache_driver2: Optional[Dict[str, Any]] = None  # 舊版相容
        self._last_tooltip_key: Optional[Tuple[str, int]] = None
        
        # 多車手數據緩存
        self._all_drivers_data: Dict[str, Sequence[Dict[str, Any]]] = {}  # {driver_code: [lap_records]}
        self._all_drivers_tooltip: Dict[str, Dict[int, Dict[str, Any]]] = {}  # {driver_code: {lap: tooltip}}
        self._selected_drivers: List[str] = []  # 當前選中的車手
        self._available_drivers: List[str] = []  # 所有可用車手

        self.throttle_chart = ThrottleDurationChartWidget(self)
        # 移除 lap time chart - 只顯示 throttle
        self.laptime_chart = None

        # 簡化佈局 - 只顯示 throttle chart
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.throttle_chart)

        self._connect_signals()

    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self.throttle_chart.lapHover.connect(lambda lap, record: self._on_chart_hover("throttle", lap, record))
        # laptime_chart 已移除

        self.throttle_chart.lapClicked.connect(lambda lap, record: self._handle_lap_clicked("throttle", lap))
        # laptime_chart 已移除
        self.throttle_chart.pinnedCleared.connect(lambda: self._handle_pinned_cleared("throttle"))
        # laptime_chart 已移除

        self.throttle_chart.viewTransformChanged.connect(
            lambda scale, offset: self.signal_bus.emit_view_transform("throttle", scale, offset)
        )
        # laptime_chart 已移除

        self.signal_bus.hoverLapChanged.connect(self._on_bus_hover)
        self.signal_bus.viewTransformChanged.connect(self._on_bus_view_transform)
        self.signal_bus.highlightRequested.connect(self._on_bus_highlight)

    # ------------------------------------------------------------------
    def update_data(self, payload: Dict[str, Any], payload_driver2: Optional[Dict[str, Any]] = None) -> None:
        """更新資料，支援多車手模式"""
        # 檢查是否有多車手數據
        all_drivers_data = payload.get("all_drivers_data", {})
        all_drivers_tooltip = payload.get("all_drivers_tooltip", {})
        available_drivers = payload.get("available_drivers", [])
        annotations = payload.get("annotations", {})
        
        if all_drivers_data:
            # 新版：使用多車手數據
            self._all_drivers_data = dict(all_drivers_data)
            self._all_drivers_tooltip = dict(all_drivers_tooltip)
            self._available_drivers = list(available_drivers)
            self._annotations = dict(annotations)
            
            # 如果沒有選中的車手，使用主車手
            if not self._selected_drivers:
                driver_code = payload.get("driver", {}).get("code", "")
                if driver_code:
                    self._selected_drivers = [driver_code.upper()]
            
            self._render_multi_driver()
        else:
            # 舊版：向下相容
            self._prepared_cache = self._prepare_payload(payload)
            self._prepared_cache_driver2 = self._prepare_payload(payload_driver2) if payload_driver2 else None
            self._render_prepared()

    def update_multi_driver_data(
        self,
        all_drivers_data: Dict[str, Sequence[Dict[str, Any]]],
        all_drivers_tooltip: Dict[str, Dict[int, Dict[str, Any]]],
        available_drivers: List[str],
        selected_drivers: List[str],
        annotations: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        更新多車手數據（新版 API）
        
        Args:
            all_drivers_data: 所有車手的圈數數據 {driver_code: [lap_records]}
            all_drivers_tooltip: 所有車手的 tooltip {driver_code: {lap: tooltip}}
            available_drivers: 所有可用車手列表
            selected_drivers: 選中的車手列表
            annotations: 標記數據（旗幟等）
        """
        self._all_drivers_data = dict(all_drivers_data or {})
        self._all_drivers_tooltip = dict(all_drivers_tooltip or {})
        self._available_drivers = list(available_drivers or [])
        self._selected_drivers = list(selected_drivers or [])
        self._annotations = dict(annotations or {})
        
        self._render_multi_driver()

    def update_selected_drivers(self, drivers: List[str]) -> None:
        """更新選中的車手（用於同步）"""
        if drivers == self._selected_drivers:
            return
        
        self._selected_drivers = list(drivers or [])
        
        # 如果有多車手數據，重新渲染
        if self._all_drivers_data:
            self._render_multi_driver()

    def _render_multi_driver(self) -> None:
        """渲染多車手圖表"""
        if not self._all_drivers_data:
            return
        
        flag_markers = self._annotations.get("flag_labels") or {} if hasattr(self, '_annotations') else {}
        
        self.throttle_chart.update_series_multi_driver(
            all_drivers_data=self._all_drivers_data,
            all_tooltip_maps=self._all_drivers_tooltip,
            selected_drivers=self._selected_drivers,
            show_ratio=self._settings.get("show_ratio", True),
            show_average=self._settings.get("show_average", False),
            flag_markers=flag_markers,
        )

    def clear(self) -> None:
        self._prepared_cache = None
        self._prepared_cache_driver2 = None
        self._all_drivers_data = {}
        self._all_drivers_tooltip = {}
        self._selected_drivers = []
        self._available_drivers = []
        self._last_tooltip_key = None
        self.throttle_chart.clear_data()
        # laptime_chart 已移除

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        self._settings.update(settings)
        self._render_prepared()

    def reset_view(self) -> None:
        """重置視圖 - 包含縮放重置"""
        # 先重置縮放狀態
        if hasattr(self.throttle_chart, "reset_zoom"):
            self.throttle_chart.reset_zoom()
        # 再調用父類的 reset_view
        if hasattr(self.throttle_chart, "reset_view"):
            self.throttle_chart.reset_view()
        # laptime_chart 已移除

    def export_charts(self, directory: str, base_name: str) -> List[str]:
        exported: List[str] = []
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        throttle_path = os.path.join(directory, f"{base_name}_throttle_{timestamp}.png")
        # laptime_chart 已移除
        if self.throttle_chart.grab().save(throttle_path):
            exported.append(throttle_path)
        # laptime_chart 已移除
        return exported

    # ------------------------------------------------------------------
    def _prepare_payload(self, payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not payload:
            return None

        lap_records = payload.get("lap_records") or []
        chart_series = payload.get("chart_series") or {}
        tooltip_map = chart_series.get("tooltip") or {}

        lap_numbers = self._to_int_list(chart_series.get("lap_numbers", []))
        throttle_values = self._to_float_list(chart_series.get("full_throttle_duration_s", []))
        ratio_values = self._to_float_list(chart_series.get("full_throttle_ratio_percent", []))
        average_values = self._to_float_list(chart_series.get("average_throttle_percent", []))
        lap_time_values = self._to_float_list(chart_series.get("lap_time_seconds", []))

        value_maps = {
            "full_throttle_duration_s": dict(zip(lap_numbers, throttle_values)),
            "full_throttle_ratio_percent": dict(zip(lap_numbers, ratio_values)),
            "average_throttle_percent": dict(zip(lap_numbers, average_values)),
            "lap_time_seconds": dict(zip(lap_numbers, lap_time_values)),
        }

        enriched_records: List[Dict[str, Any]] = []
        for record in lap_records:
            lap = self._safe_int(record.get("lap_number"))
            if lap is None:
                continue
            enriched = dict(record)
            for key, mapping in value_maps.items():
                if lap in mapping:
                    enriched[key] = mapping[lap]
            enriched_records.append(enriched)

        prepared = {
            "records": enriched_records,
            "tooltip": tooltip_map,
            "metadata": dict(payload.get("metadata") or {}),
            "driver": dict(payload.get("driver") or {}),
            "annotations": dict(payload.get("annotations") or {}),
            "source_payload": payload,
        }
        return prepared

    def _render_prepared(self) -> None:
        if not self._prepared_cache:
            return

        records = self._prepared_cache.get("records", [])
        tooltip_map = self._prepared_cache.get("tooltip", {})
        annotations = self._prepared_cache.get("annotations", {})
        metadata = self._prepared_cache.get("metadata", {})
        driver_info = self._prepared_cache.get("driver", {})
        flag_markers = annotations.get("flag_labels") or {}

        # 🆕 提取第二位車手資料
        records_d2 = None
        tooltip_map_d2 = None
        if self._prepared_cache_driver2:
            records_d2 = self._prepared_cache_driver2.get("records", [])
            tooltip_map_d2 = self._prepared_cache_driver2.get("tooltip", {})

        self.throttle_chart.update_series(
            lap_records=records,
            tooltip_map=tooltip_map,
            show_full_duration=self._settings.get("show_full_duration", False),
            show_ratio=self._settings.get("show_ratio", True),
            show_average=self._settings.get("show_average", True),
            highlight_threshold=self._settings.get("highlight_threshold", True),
            threshold_percent=self._settings.get("threshold_percent", 90.0),
            pit_laps=annotations.get("pit_laps"),
            caution_laps=annotations.get("caution_laps"),
            flag_markers=flag_markers,
            lap_records_driver2=records_d2,  # 新增
            tooltip_map_driver2=tooltip_map_d2,  # 新增
        )

        # laptime_chart 已移除

        self._update_summary(metadata, driver_info, len(records))

    # ------------------------------------------------------------------
    def _update_summary(self, metadata: Dict[str, Any], driver: Dict[str, Any], lap_count: int) -> None:
        """更新摘要資訊（已移除 summary_label，此方法保留以維持相容性）"""
        # 移除底部摘要資訊顯示
        # 原本顯示：Driver: {driver} | Team: {team} | Laps: {laps} | Highlight ≥ {threshold}% | Source: {source}
        pass

    # ------------------------------------------------------------------
    def _on_chart_hover(self, source: str, lap: int, record: Dict[str, Any]) -> None:
        payload = self._prepared_cache or {}
        tooltip_map = payload.get("tooltip", {})
        tooltip_payload = dict(tooltip_map.get(int(lap), {}))
        tooltip_payload.update(record or {})
        self.signal_bus.emit_hover(source, int(lap), tooltip_payload)

    def _handle_lap_clicked(self, source: str, lap: int) -> None:
        throttle_payload = self.throttle_chart.get_tooltip_payload(lap)
        # laptime_chart 已移除

        self.throttle_chart.set_pinned_marker(lap, throttle_payload)
        # laptime_chart 已移除
        self.signal_bus.emit_highlight(source, int(lap))

    def _handle_pinned_cleared(self, source: str) -> None:
        self._clear_pinned_markers()
        self.signal_bus.emit_highlight(source, -1)

    def _on_bus_hover(self, source: str, lap: int, payload: Dict[str, Any]) -> None:
        if source != "throttle":
            self.throttle_chart.set_external_highlight(lap)
        # laptime_chart 已移除

        # ❌ 已禁用原生 QToolTip（改用新的數據點互動系統）
        # key = (source, lap)
        # if payload and key != self._last_tooltip_key:
        #     self._last_tooltip_key = key
        #     QToolTip.showText(QCursor.pos(), self._format_tooltip(payload), self)

    def _on_bus_view_transform(self, source: str, x_scale: float, x_offset: float) -> None:
        # laptime_chart 已移除，不再需要同步視圖轉換
        pass

    def _on_bus_highlight(self, source: str, lap: int) -> None:
        if lap is None or lap <= 0:
            self._clear_pinned_markers()
            self.throttle_chart.set_external_highlight(None)
            # laptime_chart 已移除
            QToolTip.hideText()
            return

        self.throttle_chart.set_external_highlight(lap)
        # laptime_chart 已移除
        self.throttle_chart.set_pinned_marker(lap, self.throttle_chart.get_tooltip_payload(lap))
        # laptime_chart 已移除

    # ------------------------------------------------------------------
    def _clear_pinned_markers(self) -> None:
        self.throttle_chart.set_pinned_marker(None, None)
        # laptime_chart 已移除
        self.throttle_chart.set_external_highlight(None)
        # laptime_chart 已移除
        QToolTip.hideText()

    # ------------------------------------------------------------------
    @staticmethod
    def _format_tooltip(payload: Dict[str, Any]) -> str:
        lap = payload.get("lap_number") or payload.get("lap")
        throttle = payload.get("full_throttle_duration_s")
        lap_time_fmt = payload.get("lap_time_formatted") or payload.get("lap_time")
        compound = payload.get("compound", "N/A")
        drs = payload.get("drs_percent")
        ers = payload.get("ers_percent")
        ratio = payload.get("full_throttle_ratio_percent")
        avg = payload.get("average_throttle_percent")

        lines = [tr("throttle_line_chart.tooltip_lap", "Lap {lap}").format(lap=lap)]
        if throttle is not None:
            lines.append(tr("throttle_line_chart.tooltip_full", "Full Throttle: {value:.2f} s").format(value=float(throttle)))
        if lap_time_fmt:
            lines.append(tr("throttle_line_chart.tooltip_lap_time", "Lap Time: {value}").format(value=lap_time_fmt))
        elif payload.get("lap_time_seconds") is not None:
            lines.append(tr("throttle_line_chart.tooltip_lap_time_seconds", "Lap Time: {value:.3f} s").format(value=float(payload["lap_time_seconds"])))
        if ratio is not None:
            lines.append(tr("throttle_line_chart.tooltip_ratio", "Full Throttle %: {value:.1f}%").format(value=float(ratio)))
        if avg is not None:
            lines.append(tr("throttle_line_chart.tooltip_average", "Average Throttle %: {value:.1f}%").format(value=float(avg)))
        if drs is not None:
            lines.append(tr("throttle_line_chart.tooltip_drs", "DRS %: {value:.1f}%").format(value=float(drs)))
        if ers is not None:
            lines.append(tr("throttle_line_chart.tooltip_ers", "ERS Deploy %: {value:.1f}%").format(value=float(ers)))
        lines.append(tr("throttle_line_chart.tooltip_compound", "Tyre: {compound}").format(compound=compound))
        return "\n".join(lines)

    @staticmethod
    def _to_int_list(values: Iterable[Any]) -> List[int]:
        result: List[int] = []
        for value in values:
            try:
                result.append(int(value))
            except (TypeError, ValueError):
                continue
        return result

    @staticmethod
    def _to_float_list(values: Iterable[Any]) -> List[float]:
        result: List[float] = []
        for value in values:
            try:
                result.append(float(value))
            except (TypeError, ValueError):
                result.append(float("nan"))
        return result

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None


class ThrottleLineChartMDI(UniversalAnalysisMDI):
    """油門折線圖 MDI 主類別。"""

    driverChanged = pyqtSignal(str)

    def __init__(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        driver: Optional[str] = None,
        parent=None,
        **kwargs,
    ):
        if "throttle_line_chart_single_driver" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            config = AnalysisMDIConfig(
                analysis_type="throttle_line_chart_single_driver",
                display_name=tr("throttle_line_chart.title", "Throttle Line Chart (Single Driver)"),
                default_size=(1400, 820),
                requires_driver_params=True,
                requires_lap_params=False,
                supports_single_driver=True,
                supports_dual_driver=False,
            )
            UniversalAnalysisMDI.register_mdi_module_type("throttle_line_chart_single_driver", config)

        self._desired_driver = driver or "VER"
        self.signal_bus = ThrottleLineChartSignalBus()
        self.control_panel: Optional[ThrottleLineChartControlPanel] = None
        self._available_drivers: List[str] = []
        self._selected_drivers: List[str] = []  # 選中的車手列表
        self.settings_manager = gui_settings_manager
        self._global_filter_settings: Dict[str, Any] = dict(self.settings_manager.get_boxplot_settings())

        super().__init__("throttle_line_chart_single_driver", parent)

        if year is not None:
            self.current_year = str(year)
        if race is not None:
            self.current_race = race
        if session is not None:
            self.current_session = session
        if driver:
            self.driver1 = driver
            self.driver2 = ""  # 預設第二位車手為空

        # 從系統設定載入預設值（取代 _DEFAULT_SETTINGS）
        self._settings_cache = dict(self.settings_manager.get_throttle_line_chart_settings())

        try:
            self.settings_manager.boxplot_settings_changed.connect(self._on_global_filter_settings_changed)
            self.settings_manager.throttle_line_chart_settings_changed.connect(
                self._on_throttle_settings_changed
            )
        except Exception:  # pragma: no cover - defensive
            pass

        if not self.initialize_module(parent_widget=None, **kwargs):
            raise RuntimeError("Failed to initialize Throttle Line Chart module")

        self._apply_initial_parameters()

    # ------------------------------------------------------------------
    def create_data_manager(self) -> ThrottleLineChartDataLoader:
        loader = ThrottleLineChartDataLoader(self)
        loader.update_filter_settings(
            filter_pit_laps=self._global_filter_settings.get("filter_pit_laps", True),
            filter_yellow_flags=self._global_filter_settings.get("filter_yellow_flags", True),
            filter_red_flags=self._global_filter_settings.get("filter_red_flags", True),
            filter_first_laps=self._global_filter_settings.get("filter_first_laps", True),
            reprocess=False,
        )
        return loader

    def create_chart_widget(self) -> ThrottleLineChartView:
        return ThrottleLineChartView(self.signal_bus, parent=None)

    def create_additional_widgets(self) -> List[QWidget]:
        self.control_panel = ThrottleLineChartControlPanel()
        self.control_panel.settingsChanged.connect(self._on_control_settings_changed)
        self.control_panel.reloadRequested.connect(self._on_reload_requested)
        self.control_panel.resetRequested.connect(self._on_reset_requested)
        self.control_panel.exportRequested.connect(self._on_export_requested)
        self.control_panel.clearLabelsRequested.connect(self._on_clear_labels_requested)
        self.control_panel.apply_settings(self._settings_cache)
        # 改為使用多車手信號
        self.control_panel.driversChanged.connect(self._on_drivers_selection_changed)
        
        # 初始化車手列表
        initial_drivers = []
        if hasattr(self, "driver1") and self.driver1:
            initial_drivers.append(self.driver1)
        elif self._desired_driver:
            initial_drivers.append(self._desired_driver)
        
        drivers_seed = self._available_drivers or initial_drivers
        if drivers_seed:
            self.control_panel.set_available_drivers(drivers_seed, initial_drivers)
        
        # 連接 chart widget 的 view transform 到全局同步
        if hasattr(self.chart_widget, 'throttle_chart'):
            self.chart_widget.throttle_chart.viewTransformChanged.connect(
                self._on_local_view_transform_changed
            )
        
        # 註冊 GlobalChartSyncSignal
        self._register_global_sync()
        
        return [self.control_panel]

    def _on_local_view_transform_changed(self, x_scale: float, x_offset: float) -> None:
        """處理本地視圖變換變更，發送到全局同步"""
        # 計算 x_min 和 x_max
        if hasattr(self.chart_widget, 'throttle_chart'):
            chart = self.chart_widget.throttle_chart
            # 使用 get_overall_x_range() 獲取數據範圍
            if hasattr(chart, 'get_overall_x_range'):
                data_x_min, data_x_max = chart.get_overall_x_range()
                if data_x_min is not None and data_x_max is not None:
                    full_range = data_x_max - data_x_min
                    if full_range > 0 and x_scale > 0:
                        visible_range = full_range / x_scale
                        x_min = data_x_min + (x_offset / x_scale) * full_range
                        x_max = x_min + visible_range
                        
                        # 發送到全局同步
                        sync = GlobalChartSyncSignal.get_instance()
                        sync.emit_x_range_changed(x_min, x_max, MODULE_THROTTLE_LINE)

    # ------------------------------------------------------------------
    def _apply_initial_parameters(self) -> None:
        self.driver1 = (self._desired_driver or getattr(self, "driver1", "VER")).upper()
        self.driver2 = ""  # 預設第二位車手為空
        self.update_analysis_parameters(self.current_year, self.current_race, self.current_session, self.driver1)

    def _on_control_settings_changed(self, settings: Dict[str, Any]) -> None:
        self._settings_cache.update(settings)
        if hasattr(self.chart_widget, "apply_settings"):
            self.chart_widget.apply_settings(settings)

    def _on_reload_requested(self) -> None:
        self.load_data(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            driver=self.driver1,
            force_refresh=True,
        )

    def _on_reset_requested(self) -> None:
        if hasattr(self.chart_widget, "reset_view"):
            self.chart_widget.reset_view()

    def _on_export_requested(self) -> None:
        if not hasattr(self.chart_widget, "export_charts"):
            return
        directory = QFileDialog.getExistingDirectory(
            self.main_widget,
            tr("throttle_line_chart.export_dialog_title", "選擇匯出資料夾"),
        )
        if not directory:
            return
        base_name = f"throttle_line_chart_{self.current_year}_{self.current_race}_{self.current_session}_{self.driver1}"
        exported = self.chart_widget.export_charts(directory, base_name)
        if exported:
            QMessageBox.information(
                self.main_widget,
                tr("throttle_line_chart.export_success", "匯出成功"),
                "\n".join(exported),
            )

    def _on_clear_labels_requested(self) -> None:
        """清除圖表上的所有固定標籤（pinned data points）"""
        if hasattr(self.chart_widget, "throttle_chart"):
            chart = self.chart_widget.throttle_chart
            if hasattr(chart, "pinned_data_points"):
                chart.pinned_data_points.clear()
                chart.update()
                logger.info("[DEBUG] Throttle Line Chart: 已清除所有固定標籤")

    # ------------------------------------------------------------------
    def _load_data_with_current_parameters(self):
        if getattr(self, "_cleanup_performed", False):
            return
        if not self.data_manager:
            return
        try:
            year_value = int(self.current_year)
        except (TypeError, ValueError):
            year_value = self.current_year
        params = {
            "year": year_value,
            "race": self.current_race,
            "session": self.current_session,
            "driver": self.driver1 or self._desired_driver,
        }
        if hasattr(self.data_manager, "load_data"):
            self.data_manager.load_data(**params)

    def update_analysis_parameters(self, year: str, race: str, session: str, driver: Optional[str] = None) -> bool:
        try:
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            if driver:
                driver_code = str(driver).upper()
                self.driver1 = driver_code
                self.driver2 = driver_code
            self._load_data_with_current_parameters()
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self._error(f"更新分析參數失敗: {exc}")
            return False

    def load_data(self, **kwargs) -> bool:
        driver = kwargs.get("driver") or kwargs.get("driver_code") or self.driver1 or self._desired_driver
        kwargs = dict(kwargs)
        kwargs["driver"] = driver
        if hasattr(self.data_manager, "load_data"):
            return bool(self.data_manager.load_data(**kwargs))
        return False

    def refresh_analysis(self) -> None:
        self._on_reload_requested()

    def clear_data(self) -> None:
        if hasattr(self.chart_widget, "clear"):
            self.chart_widget.clear()

    def reset_chart_view(self) -> None:
        """重置圖表視圖 - 供 Show All Data 按鈕使用"""
        logger.debug("[THROTTLE_LINE_CHART] reset_chart_view called")
        
        # 重置 ThrottleLineChartView 的視圖
        if hasattr(self.chart_widget, 'reset_view'):
            self.chart_widget.reset_view()
        
        # 重置 throttle_chart (ThrottleDurationChartWidget) 的縮放
        if hasattr(self.chart_widget, 'throttle_chart') and hasattr(self.chart_widget.throttle_chart, 'reset_zoom'):
            self.chart_widget.throttle_chart.reset_zoom()

    # ------------------------------------------------------------------
    # GlobalChartSyncSignal 跨模組同步
    # ------------------------------------------------------------------
    def _register_global_sync(self) -> None:
        """註冊到全局同步信號"""
        # 🚀 暫時停用 GlobalChartSyncSignal 以排查性能問題
        return
        # sync = GlobalChartSyncSignal.get_instance()
        # sync.register_module(MODULE_THROTTLE_LINE)
        # sync.drivers_changed.connect(self._on_global_drivers_changed)
        # sync.x_range_changed.connect(self._on_global_x_range_changed)
        # sync.reset_view.connect(self._on_global_reset_view)
        # logger.debug("[THROTTLE_LINE_CHART] Registered to GlobalChartSyncSignal")

    def _unregister_global_sync(self) -> None:
        """取消註冊全局同步信號"""
        try:
            sync = GlobalChartSyncSignal.get_instance()
            sync.drivers_changed.disconnect(self._on_global_drivers_changed)
            sync.x_range_changed.disconnect(self._on_global_x_range_changed)
            sync.reset_view.disconnect(self._on_global_reset_view)
            sync.unregister_module(MODULE_THROTTLE_LINE)
            logger.debug("[THROTTLE_LINE_CHART] Unregistered from GlobalChartSyncSignal")
        except (TypeError, RuntimeError):
            pass

    def _on_global_drivers_changed(self, drivers: List[str], source: str) -> None:
        """處理來自其他模組的車手同步事件"""
        if source == MODULE_THROTTLE_LINE:
            return  # 忽略自己發出的
        
        # 🚀 優化：如果車手列表未變更，跳過處理
        if drivers == self._selected_drivers:
            return
        
        # logger 降級為 debug 減少 I/O
        # logger.debug("[THROTTLE_LINE_CHART] Sync drivers from %s: %s", source, drivers)
        
        # 更新控制面板選擇
        if hasattr(self, 'control_panel') and self.control_panel:
            self.control_panel.set_selected_drivers(drivers)
        
        # 更新選中的車手列表
        self._selected_drivers = drivers
        
        # 重新渲染圖表
        if hasattr(self.chart_widget, 'update_selected_drivers'):
            self.chart_widget.update_selected_drivers(drivers)

    def _on_global_x_range_changed(self, x_min: float, x_max: float, source: str) -> None:
        """處理來自其他模組的X軸範圍同步事件"""
        if source == MODULE_THROTTLE_LINE:
            return  # 忽略自己發出的
        
        # 🚀 移除 logger 調用減少 I/O
        # logger.debug("[THROTTLE_LINE_CHART] Sync X range from %s: %.2f - %.2f", source, x_min, x_max)
        
        # 同步X軸範圍到圖表
        if hasattr(self.chart_widget, 'throttle_chart') and hasattr(self.chart_widget.throttle_chart, 'set_x_range'):
            # chart_widget 是 ThrottleLineChartView
            self.chart_widget.throttle_chart.set_x_range(x_min, x_max)
        elif hasattr(self.chart_widget, 'set_x_range'):
            self.chart_widget.set_x_range(x_min, x_max)

    def _on_global_reset_view(self, source: str) -> None:
        """處理來自其他模組的重置視圖事件"""
        if source == MODULE_THROTTLE_LINE:
            return  # 忽略自己發出的
        
        # 🚀 移除 logger 調用減少 I/O
        # logger.debug("[THROTTLE_LINE_CHART] Reset view from %s", source)
        
        if hasattr(self.chart_widget, 'reset_view'):
            self.chart_widget.reset_view()

    def _on_drivers_selection_changed(self, drivers: List[str]) -> None:
        """處理本模組的車手選擇變更"""
        # 🚀 移除 logger.info 調用減少 I/O
        # logger.info("[THROTTLE_LINE_CHART] Drivers selection changed: %s", drivers)
        
        # 🚀 優化：如果車手列表未變更，跳過處理
        if drivers == self._selected_drivers:
            return
        
        self._selected_drivers = drivers
        
        # 發送同步信號到其他模組
        sync = GlobalChartSyncSignal.get_instance()
        sync.emit_drivers_changed(drivers, MODULE_THROTTLE_LINE)
        
        # 更新圖表顯示
        if hasattr(self.chart_widget, 'update_selected_drivers'):
            self.chart_widget.update_selected_drivers(drivers)

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        if export_format.lower() != "json":
            self._error(f"不支援的匯出格式: {export_format}")
            return False
        payload = None
        if hasattr(self.data_manager, "get_chart_payload"):
            payload = self.data_manager.get_chart_payload()
        if not payload and hasattr(self.chart_widget, "_prepared_cache"):
            payload = getattr(self.chart_widget, "_prepared_cache")
        if not payload:
            self._error("目前沒有可匯出的資料")
            return False
        try:
            with open(export_path, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, ensure_ascii=False, indent=2)
            return True
        except Exception as exc:  # pragma: no cover - IO 錯誤
            self._error(f"匯出失敗: {exc}")
            return False

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        if hasattr(self.data_manager, "get_chart_payload"):
            payload = self.data_manager.get_chart_payload()
            if payload:
                return payload
        if hasattr(self.chart_widget, "_prepared_cache"):
            cache = getattr(self.chart_widget, "_prepared_cache")
            if cache:
                return json.loads(json.dumps(cache, ensure_ascii=False))
        return None

    def update_window_title(self) -> None:
        super().update_window_title()
        if self.control_panel:
            self.control_panel.apply_settings(self._settings_cache)

    def cleanup(self) -> None:  # type: ignore[override]
        try:
            # 取消註冊 GlobalChartSyncSignal
            self._unregister_global_sync()
            
            # 斷開 control_panel 的所有信號連接
            if hasattr(self, 'control_panel') and self.control_panel:
                try:
                    self.control_panel.settingsChanged.disconnect(self._on_control_settings_changed)
                    self.control_panel.reloadRequested.disconnect(self._on_reload_requested)
                    self.control_panel.resetRequested.disconnect(self._on_reset_requested)
                    self.control_panel.exportRequested.disconnect(self._on_export_requested)
                    self.control_panel.driversChanged.disconnect(self._on_drivers_selection_changed)
                    logger.debug("[THROTTLE_LINE_CHART] control_panel signals disconnected (5)")
                except (TypeError, RuntimeError):
                    pass
                
                # 清理 control_panel
                try:
                    self.control_panel.deleteLater()
                    self.control_panel = None
                    logger.debug("[THROTTLE_LINE_CHART] control_panel cleaned")
                except Exception as e:
                    logger.warning("[THROTTLE_LINE_CHART] control_panel clean warning: %s", e)
            
            # 斷開 settings_manager 信號連接
            if self.settings_manager:
                self.settings_manager.boxplot_settings_changed.disconnect(self._on_global_filter_settings_changed)
                self.settings_manager.throttle_line_chart_settings_changed.disconnect(
                    self._on_throttle_settings_changed
                )
                logger.debug("[THROTTLE_LINE_CHART] settings_manager signals disconnected")
        except (TypeError, RuntimeError):  # pragma: no cover - already disconnected
            pass
        super().cleanup()

    def _update_chart(self, data: dict):  # type: ignore[override]
        super()._update_chart(data)
        self._sync_available_drivers(data)

    def _sync_available_drivers(self, data: Optional[Dict[str, Any]]) -> None:
        if not self.control_panel:
            return
        drivers: List[str] = []
        if isinstance(data, dict):
            raw = data.get("available_drivers")
            if isinstance(raw, list):
                drivers = [str(code).upper() for code in raw if code]
            if not drivers:
                meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
                raw_meta = meta.get("available_drivers") if meta else None
                if isinstance(raw_meta, list):
                    drivers = [str(code).upper() for code in raw_meta if code]
        if not drivers and self._available_drivers:
            drivers = list(self._available_drivers)
        if not drivers and getattr(self, "driver1", None):
            drivers = [self.driver1]
        self._available_drivers = drivers
        # 更新控制面板可用車手列表
        if hasattr(self, '_selected_drivers'):
            self.control_panel.set_available_drivers(drivers, self._selected_drivers)
        else:
            self.control_panel.set_available_drivers(drivers)

    def _on_driver2_data_loaded(self, data: Dict[str, Any]) -> None:
        """處理第二位車手資料載入完成（新增）"""
        logger.debug("[_on_driver2_data_loaded] Called")
        logger.debug("[_on_driver2_data_loaded] Data received: %s", bool(data))
        if data:
            logger.debug("[_on_driver2_data_loaded] Data keys: %s", list(data.keys()))
            if 'lap_records' in data:
                logger.debug("[_on_driver2_data_loaded] lap_records count: %s", len(data['lap_records']))
            if 'filters_applied' in data:
                logger.debug("[_on_driver2_data_loaded] filters_applied: %s", data['filters_applied'])
        
        if not data or not hasattr(self.chart_widget, "update_data"):
            logger.error("[_on_driver2_data_loaded] No data or chart_widget has no update_data method")
            return
        
        # 獲取主車手資料
        payload_driver1 = self.data_manager.get_chart_payload() if hasattr(self.data_manager, "get_chart_payload") else {}
        
        # 更新圖表（傳入雙車手資料）
        logger.debug("[_on_driver2_data_loaded] Calling chart_widget.update_data()...")
        self.chart_widget.update_data(payload_driver1, data)
        logger.info("[Driver2 Data Loaded] Successfully loaded data for %s", self.driver2)

    def _on_throttle_settings_changed(self, settings: Dict[str, Any]) -> None:
        """處理 Throttle Line Chart 系統設定變更（新增）"""
        if not isinstance(settings, dict):
            return
        
        logger.info("[Throttle Settings Changed] Received: %s", settings)
        
        # 更新設定快取
        self._settings_cache.update(settings)
        
        # 通知圖表視圖重新渲染
        if hasattr(self.chart_widget, "apply_settings"):
            self.chart_widget.apply_settings(settings)
        
        # 通知控制面板更新（雖然現在控制面板已簡化）
        if self.control_panel:
            self.control_panel.apply_settings(settings)

    def _on_global_filter_settings_changed(self, settings: Dict[str, Any]) -> None:
        logger.debug("[_on_global_filter_settings_changed] Called")
        logger.debug("[MDI] Received settings: %s", settings)
        
        if not isinstance(settings, dict):
            logger.error("[_on_global_filter_settings_changed] Settings is not a dict: %s", type(settings))
            return
        
        # 🔍 DEBUG: 追蹤全域設定變更
        logger.info("[Global Settings Changed] Received: %s", settings)
        
        # ✅ 修復：直接使用 settings，不要用預設值覆蓋
        self._global_filter_settings.update({
            "filter_pit_laps": settings.get("filter_pit_laps", True),
            "filter_yellow_flags": settings.get("filter_yellow_flags", True),
            "filter_red_flags": settings.get("filter_red_flags", True),
            "filter_first_laps": settings.get("filter_first_laps", True),
        })
        
        logger.info(
            "[Global Settings Updated] New state: pit=%s, yellow=%s, red=%s, first_laps=%s",
            self._global_filter_settings.get("filter_pit_laps"),
            self._global_filter_settings.get("filter_yellow_flags"),
            self._global_filter_settings.get("filter_red_flags"),
            self._global_filter_settings.get("filter_first_laps"),
        )
        
        # ✅ 修復：更新 Driver 1 的過濾設定
        if isinstance(self.data_manager, ThrottleLineChartDataLoader):
            logger.debug("[_on_global_filter_settings_changed] Updating Driver 1 filter settings...")
            self.data_manager.update_filter_settings(
                filter_pit_laps=self._global_filter_settings["filter_pit_laps"],
                filter_yellow_flags=self._global_filter_settings["filter_yellow_flags"],
                filter_red_flags=self._global_filter_settings["filter_red_flags"],
                filter_first_laps=self._global_filter_settings["filter_first_laps"],
                reprocess=True,
            )
            logger.debug("[_on_global_filter_settings_changed] Driver 1 updated")
        
        # ✅ 修復 V3: 如果 Driver 2 已載入，重新載入其數據
        if self.driver2:
            logger.info(
                "[Reload Driver2] Detected Driver2=%s, reloading with new filter settings...",
                self.driver2,
            )
            self._on_driver2_selection_changed(self.driver2)
        else:
            logger.info("[Reload Driver2] No Driver2 loaded, skipping reload")


__all__ = ["ThrottleLineChartMDI"]
