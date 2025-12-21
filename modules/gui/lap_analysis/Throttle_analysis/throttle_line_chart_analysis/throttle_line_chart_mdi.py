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

from .lap_time_chart_widget import LapTimeChartWidget
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
    """側邊控制面板，調整圖表顯示設定。"""

    settingsChanged = pyqtSignal(dict)
    reloadRequested = pyqtSignal()
    exportRequested = pyqtSignal()
    resetRequested = pyqtSignal()
    driverChanged = pyqtSignal(str)
    driver2Changed = pyqtSignal(str)  # 新增：第二位車手變更訊號

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = dict(_DEFAULT_SETTINGS)
        self._available_drivers: List[str] = []
        self._selected_driver: Optional[str] = None
        self._selected_driver2: Optional[str] = None  # 新增：第二位車手
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 移除 "Driver Selection" 標題，直接顯示車手選擇器

        # 車手選擇器（並排顯示以節省空間）
        drivers_layout = QHBoxLayout()
        drivers_layout.setSpacing(10)  # 與 Detailed Lap Analysis 一致
        
        # Driver 1（左側）
        driver1_label = QLabel(tr("throttle_line_chart.option_driver1", "Driver 1"))
        driver1_label.setFixedWidth(55)
        self.driver_combo = QComboBox()
        self.driver_combo.setEditable(False)
        self.driver_combo.setMaximumWidth(100)
        self.driver_combo.currentTextChanged.connect(self._emit_driver_change)
        drivers_layout.addWidget(driver1_label)
        drivers_layout.addWidget(self.driver_combo)
        
        drivers_layout.addSpacing(10)  # 間隔（與 Detailed Lap Analysis 一致）
        
        # Driver 2（右側）
        driver2_label = QLabel(tr("throttle_line_chart.option_driver2", "Driver 2"))
        driver2_label.setFixedWidth(55)
        self.driver2_combo = QComboBox()
        self.driver2_combo.setEditable(False)
        self.driver2_combo.setMaximumWidth(100)
        self.driver2_combo.currentTextChanged.connect(self._emit_driver2_change)
        drivers_layout.addWidget(driver2_label)
        drivers_layout.addWidget(self.driver2_combo)
        
        drivers_layout.addStretch()  # 右側留空
        layout.addLayout(drivers_layout)

        # 移除提示文字和隱藏按鈕，保持簡潔
        # 不新增 layout.addStretch()，讓控制面板自動縮小到內容高度

    def _emit_settings(self) -> None:
        """不再從控制面板發射設定變更（設定已移至 System Settings）"""
        # 設定現在由系統設定管理，此方法保留以維持相容性
        pass

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        """外部下發設定時更新控制面板狀態（簡化版本，只更新內部狀態）"""
        self._settings.update(settings)
        self._settings.update(settings)

    def set_available_drivers(self, drivers: Sequence[str], selected: Optional[str], selected2: Optional[str] = None) -> None:
        """設定可用車手列表，並同時更新兩個選擇器"""
        normalized = [str(driver).upper() for driver in drivers if driver]
        if normalized == self._available_drivers and (selected or "") == (self._selected_driver or ""):
            return

        self._available_drivers = normalized
        
        # 更新車手1選擇器
        self.driver_combo.blockSignals(True)
        self.driver_combo.clear()
        placeholder = tr("throttle_line_chart.option_driver_placeholder", "Select driver")
        if not normalized:
            self.driver_combo.addItem(placeholder, "")
            self.driver_combo.setCurrentIndex(0)
            self._selected_driver = None
        else:
            for code in normalized:
                self.driver_combo.addItem(code, code)

            desired = (selected or self._selected_driver or normalized[0]).upper()
            if desired not in normalized:
                desired = normalized[0]
            index = self.driver_combo.findData(desired)
            if index == -1:
                index = self.driver_combo.findText(desired)
            if index != -1:
                self.driver_combo.setCurrentIndex(index)
                self._selected_driver = desired
            else:
                self.driver_combo.setCurrentIndex(0)
                self._selected_driver = normalized[0]

        self.driver_combo.blockSignals(False)
        
        # 更新車手2選擇器（新增）
        self.driver2_combo.blockSignals(True)
        self.driver2_combo.clear()
        if not normalized:
            self.driver2_combo.addItem(placeholder, "")
            self.driver2_combo.setCurrentIndex(0)
            self._selected_driver2 = None
        else:
            # 新增「無」選項
            self.driver2_combo.addItem(tr("throttle_line_chart.option_no_driver2", "None"), "")
            for code in normalized:
                self.driver2_combo.addItem(code, code)

            # 🔧 修改：預設選擇「無」（None）
            if selected2 and selected2.upper() in normalized:
                # 只有明確指定 selected2 時才設定
                desired2 = selected2.upper()
                index = self.driver2_combo.findData(desired2)
                if index == -1:
                    index = self.driver2_combo.findText(desired2)
                if index != -1:
                    self.driver2_combo.setCurrentIndex(index)
                    self._selected_driver2 = desired2
                else:
                    # 找不到則預設為 None
                    self.driver2_combo.setCurrentIndex(0)
                    self._selected_driver2 = None
            else:
                # 未指定 selected2，預設為 None
                self.driver2_combo.setCurrentIndex(0)
                self._selected_driver2 = None

        self.driver2_combo.blockSignals(False)

    def _emit_driver_change(self, value: str) -> None:
        driver = str(value).strip().upper()
        if not driver:
            return
        if driver == self._selected_driver:
            return
        self._selected_driver = driver
        self.driverChanged.emit(driver)
    
    def _emit_driver2_change(self, value: str) -> None:
        """發射第二位車手變更訊號（新增）"""
        driver = str(value).strip().upper()
        # 允許空值（表示取消第二位車手）
        if driver == self._selected_driver2:
            return
        self._selected_driver2 = driver if driver else None
        self.driver2Changed.emit(driver if driver else "")


class ThrottleLineChartView(QWidget):
    """主視圖，包含雙圖表與同步功能。"""

    def __init__(self, signal_bus: ThrottleLineChartSignalBus, parent=None):
        super().__init__(parent)
        self.signal_bus = signal_bus
        self._settings = dict(_DEFAULT_SETTINGS)
        self._prepared_cache: Optional[Dict[str, Any]] = None
        self._prepared_cache_driver2: Optional[Dict[str, Any]] = None  # 新增：第二位車手緩存
        self._last_tooltip_key: Optional[Tuple[str, int]] = None

        self.throttle_chart = ThrottleDurationChartWidget(self)
        self.laptime_chart = LapTimeChartWidget(self)
        # 移除底部資訊摘要列（summary_label）以保持簡潔

        splitter = QSplitter(Qt.Vertical)
        throttle_frame = QFrame()
        throttle_layout = QVBoxLayout(throttle_frame)
        throttle_layout.setContentsMargins(0, 0, 0, 0)
        throttle_layout.addWidget(self.throttle_chart)
        splitter.addWidget(throttle_frame)

        lap_frame = QFrame()
        lap_layout = QVBoxLayout(lap_frame)
        lap_layout.setContentsMargins(0, 0, 0, 0)
        lap_layout.addWidget(self.laptime_chart)
        splitter.addWidget(lap_frame)
        splitter.setSizes([700, 400])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(splitter)
        # 不再新增 summary_label 到佈局

        self._connect_signals()

    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self.throttle_chart.lapHover.connect(lambda lap, record: self._on_chart_hover("throttle", lap, record))
        self.laptime_chart.lapHover.connect(lambda lap, record: self._on_chart_hover("laptime", lap, record))

        self.throttle_chart.lapClicked.connect(lambda lap, record: self._handle_lap_clicked("throttle", lap))
        self.laptime_chart.lapClicked.connect(lambda lap, record: self._handle_lap_clicked("laptime", lap))
        self.throttle_chart.pinnedCleared.connect(lambda: self._handle_pinned_cleared("throttle"))
        self.laptime_chart.pinnedCleared.connect(lambda: self._handle_pinned_cleared("laptime"))

        self.throttle_chart.viewTransformChanged.connect(
            lambda scale, offset: self.signal_bus.emit_view_transform("throttle", scale, offset)
        )
        self.laptime_chart.viewTransformChanged.connect(
            lambda scale, offset: self.signal_bus.emit_view_transform("laptime", scale, offset)
        )

        self.signal_bus.hoverLapChanged.connect(self._on_bus_hover)
        self.signal_bus.viewTransformChanged.connect(self._on_bus_view_transform)
        self.signal_bus.highlightRequested.connect(self._on_bus_highlight)

    # ------------------------------------------------------------------
    def update_data(self, payload: Dict[str, Any], payload_driver2: Optional[Dict[str, Any]] = None) -> None:
        """更新資料，支援雙車手模式"""
        self._prepared_cache = self._prepare_payload(payload)
        self._prepared_cache_driver2 = self._prepare_payload(payload_driver2) if payload_driver2 else None
        self._render_prepared()

    def clear(self) -> None:
        self._prepared_cache = None
        self._prepared_cache_driver2 = None  # 新增
        self._last_tooltip_key = None
        self.throttle_chart.clear_data()
        self.laptime_chart.clear_data()
        # 移除 summary_label 更新（已移除該元件）

    def apply_settings(self, settings: Dict[str, Any]) -> None:
        self._settings.update(settings)
        self._render_prepared()

    def reset_view(self) -> None:
        if hasattr(self.throttle_chart, "reset_view"):
            self.throttle_chart.reset_view()
        if hasattr(self.laptime_chart, "reset_view"):
            self.laptime_chart.reset_view()

    def export_charts(self, directory: str, base_name: str) -> List[str]:
        exported: List[str] = []
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        throttle_path = os.path.join(directory, f"{base_name}_throttle_{timestamp}.png")
        laptime_path = os.path.join(directory, f"{base_name}_lap_{timestamp}.png")
        if self.throttle_chart.grab().save(throttle_path):
            exported.append(throttle_path)
        if self.laptime_chart.grab().save(laptime_path):
            exported.append(laptime_path)
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

        self.laptime_chart.update_series(
            lap_records=records,
            tooltip_map=tooltip_map,
            show_delta=self._settings.get("show_delta", True),
            rolling_average=self._settings.get("rolling_average", False),
            rolling_window=self._settings.get("rolling_window", 3),
            highlight_invalid=annotations.get("invalid_laps"),
            highlight_caution=annotations.get("caution_laps"),
            flag_markers=flag_markers,
            lap_records_driver2=records_d2,  # 新增
            tooltip_map_driver2=tooltip_map_d2,  # 新增
        )

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
        laptime_payload = self.laptime_chart.get_tooltip_payload(lap)

        self.throttle_chart.set_pinned_marker(lap, throttle_payload)
        self.laptime_chart.set_pinned_marker(lap, laptime_payload)
        self.signal_bus.emit_highlight(source, int(lap))

    def _handle_pinned_cleared(self, source: str) -> None:
        self._clear_pinned_markers()
        self.signal_bus.emit_highlight(source, -1)

    def _on_bus_hover(self, source: str, lap: int, payload: Dict[str, Any]) -> None:
        if source != "throttle":
            self.throttle_chart.set_external_highlight(lap)
        if source != "laptime":
            self.laptime_chart.set_external_highlight(lap)

        # ❌ 已禁用原生 QToolTip（改用新的數據點互動系統）
        # key = (source, lap)
        # if payload and key != self._last_tooltip_key:
        #     self._last_tooltip_key = key
        #     QToolTip.showText(QCursor.pos(), self._format_tooltip(payload), self)

    def _on_bus_view_transform(self, source: str, x_scale: float, x_offset: float) -> None:
        if source == "throttle":
            self.laptime_chart.apply_view_transform(x_scale, x_offset)
        elif source == "laptime":
            self.throttle_chart.apply_view_transform(x_scale, x_offset)

    def _on_bus_highlight(self, source: str, lap: int) -> None:
        if lap is None or lap <= 0:
            self._clear_pinned_markers()
            self.throttle_chart.set_external_highlight(None)
            self.laptime_chart.set_external_highlight(None)
            QToolTip.hideText()
            return

        self.throttle_chart.set_external_highlight(lap)
        self.laptime_chart.set_external_highlight(lap)
        self.throttle_chart.set_pinned_marker(lap, self.throttle_chart.get_tooltip_payload(lap))
        self.laptime_chart.set_pinned_marker(lap, self.laptime_chart.get_tooltip_payload(lap))

    # ------------------------------------------------------------------
    def _clear_pinned_markers(self) -> None:
        self.throttle_chart.set_pinned_marker(None, None)
        self.laptime_chart.set_pinned_marker(None, None)
        self.throttle_chart.set_external_highlight(None)
        self.laptime_chart.set_external_highlight(None)
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
        self.control_panel.apply_settings(self._settings_cache)
        self.control_panel.driverChanged.connect(self._on_driver_selection_changed)
        self.control_panel.driver2Changed.connect(self._on_driver2_selection_changed)  # 新增：連接第二位車手訊號
        initial_driver = (self.driver1 or self._desired_driver) if hasattr(self, "driver1") else self._desired_driver
        initial_driver2 = getattr(self, "driver2", "")
        drivers_seed = self._available_drivers or ([initial_driver] if initial_driver else [])
        if drivers_seed:
            self.control_panel.set_available_drivers(drivers_seed, initial_driver, initial_driver2)  # 更新參數
        return [self.control_panel]

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
            # 🔴 新增：斷開 control_panel 的所有信號連接（修復洩漏）
            if hasattr(self, 'control_panel') and self.control_panel:
                try:
                    self.control_panel.settingsChanged.disconnect(self._on_control_settings_changed)
                    self.control_panel.reloadRequested.disconnect(self._on_reload_requested)
                    self.control_panel.resetRequested.disconnect(self._on_reset_requested)
                    self.control_panel.exportRequested.disconnect(self._on_export_requested)
                    self.control_panel.driverChanged.disconnect(self._on_driver_selection_changed)
                    self.control_panel.driver2Changed.disconnect(self._on_driver2_selection_changed)
                    logger.debug("[THROTTLE_LINE_CHART] control_panel signals disconnected (6)")
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
        current = getattr(self, "driver1", None) or self._desired_driver
        current2 = getattr(self, "driver2", "")
        self.control_panel.set_available_drivers(drivers, current, current2)  # 更新參數

    def _on_driver_selection_changed(self, driver_code: str) -> None:
        """處理 Driver 1 選擇變更 - 只更新 Driver 1 資料，不影響 Driver 2"""
        code = str(driver_code or "").strip().upper()
        if not code:
            return
        if code == getattr(self, "driver1", None):
            return
        
        # 更新 Driver 1
        self.driver1 = code
        self._desired_driver = code
        self.driverChanged.emit(code)
        
        # 🔧 修改：只重新載入 Driver 1 資料，不清除整個圖表
        logger.info(
            "[Driver1 Changed] New driver1: %s, driver2: %s",
            self.driver1,
            getattr(self, "driver2", None) or "(None)",
        )
        
        # 重新載入 Driver 1 資料（preserve_driver2=True 保留 Driver 2）
        self.load_data(
            year=self.current_year,
            race=self.current_race,
            session=self.current_session,
            driver=code,
            force_refresh=False,
        )
    
    def _on_driver2_selection_changed(self, driver_code: str) -> None:
        """處理第二位車手選擇變更（新增）"""
        logger.debug("[_on_driver2_selection_changed] Called with driver_code: %s", driver_code)
        logger.debug("[MDI] Current _global_filter_settings: %s", self._global_filter_settings)
        
        code = str(driver_code or "").strip().upper()
        # 允許空值（取消第二位車手）
        if code == getattr(self, "driver2", ""):
            logger.debug("[_on_driver2_selection_changed] Driver2 unchanged: %s", code)
            return
        self.driver2 = code
        
        # 重新載入資料以顯示雙車手比較
        logger.info("[Driver2 Changed] New driver2: %s", self.driver2 or "(None)")
        
        # 如果 driver2 為空，清除第二位車手資料
        if not self.driver2:
            if hasattr(self.chart_widget, "_prepared_cache_driver2"):
                self.chart_widget._prepared_cache_driver2 = None
                self.chart_widget._render_prepared()
            logger.info("[_on_driver2_selection_changed] Driver2 cleared")
            return
        
        # 載入第二位車手資料
        if hasattr(self.data_manager, "load_data"):
            # 建立第二個資料載入器實例
            from .throttle_line_chart_data_loader import ThrottleLineChartDataLoader
            
            # ✅ 修復：temp_loader 在 __init__() 中會自動從 settings_manager 讀取最新設定
            # 不需要再次調用 update_filter_settings()，避免重複設定和時序問題
            logger.debug("[_on_driver2_selection_changed] Creating temp_loader for Driver2...")
            temp_loader = ThrottleLineChartDataLoader(self)
            
            # 🔍 DEBUG: 顯示 temp_loader 實際使用的過濾設定（來自 __init__）
            logger.debug(
                "[Driver2 Loader Created] Filter settings: pit=%s, yellow=%s, red=%s",
                temp_loader._filter_pit_laps,
                temp_loader._filter_yellow_flags,
                temp_loader._filter_red_flags,
            )
            
            # 載入第二位車手資料
            temp_loader.data_loaded.connect(self._on_driver2_data_loaded)
            logger.debug(
                "[_on_driver2_selection_changed] Calling temp_loader.load_data() for %s",
                self.driver2,
            )
            temp_loader.load_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver=self.driver2,
                force_refresh=False,
            )
        else:
            logger.error("[_on_driver2_selection_changed] data_manager has no load_data method")
    
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
