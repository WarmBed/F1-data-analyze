# -*- coding: utf-8 -*-
"""專責處理單車手油門折線圖的圖表元件。"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QFontMetrics, QPen

from core.gui_i18n import tr
from modules.gui.universal_chart_widget import ChartDataSeries

from .linked_chart_widget import LinkedUniversalChartWidget


class ThrottleDurationChartWidget(LinkedUniversalChartWidget):
    """呈現單車手全油門秒數與比例折線圖。"""

    def __init__(self, parent=None):
        super().__init__(title=tr("throttle_line_chart.throttle_duration_title", "Full Throttle Duration"), parent=parent)

        # ⚙️ Throttle Line Chart 專屬設定：禁用舊功能，使用新的通用互動系統
        self.show_value_tooltips = False  # 禁用垂直虛線旁的數值提示
        self.mouse_x = -1  # 禁用垂直虛線追蹤（設為 -1 使其不顯示）

        self.set_axis_labels(
            tr("throttle_line_chart.axis_lap", "Lap"),
            tr("throttle_line_chart.axis_full_throttle_percent", "Full Throttle %"),  # 左Y軸：百分比
            tr("throttle_line_chart.axis_full_throttle_seconds", "Full Throttle Time"),  # 右Y軸：秒數（備用）
            x_unit="",
            left_y_unit="%",   # 左Y軸單位：百分比
            right_y_unit="s",  # 右Y軸單位：秒數（備用）
        )

        # 🆕 雙車手模式：分別儲存兩位車手的 tooltip 數據
        self._tooltip_map_driver1: Dict[int, Dict[str, object]] = {}
        self._tooltip_map_driver2: Dict[int, Dict[str, object]] = {}
        self._tooltip_map: Dict[int, Dict[str, object]] = {}  # 保留向下相容性（指向 driver1）
        
        self._active_settings: Dict[str, bool] = {
            "show_full_duration": False,
            "show_ratio": True,
            "show_average": False,
            "highlight_threshold": False,
        }

    # ------------------------------------------------------------------
    # 公開 API
    # ------------------------------------------------------------------
    def update_series(
        self,
        lap_records: Sequence[Dict[str, object]],
        tooltip_map: Dict[int, Dict[str, object]],
        *,
        show_full_duration: bool,
        show_ratio: bool,
        show_average: bool,
        highlight_threshold: bool,
        threshold_percent: Optional[float] = None,
        pit_laps: Optional[Iterable[int]] = None,
        caution_laps: Optional[Iterable[int]] = None,
        flag_markers: Optional[Dict[int, str]] = None,
        lap_records_driver2: Optional[Sequence[Dict[str, object]]] = None,  # 新增：第二位車手資料
        tooltip_map_driver2: Optional[Dict[int, Dict[str, object]]] = None,  # 新增：第二位車手提示
    ) -> None:
        """用新資料刷新圖表。"""

        self._active_settings.update(
            {
                "show_full_duration": show_full_duration,
                "show_ratio": show_ratio,
                "show_average": show_average,
                "highlight_threshold": highlight_threshold,
            }
        )
        
        # 🆕 雙車手模式：分別儲存兩位車手的 tooltip 數據
        self._tooltip_map_driver1 = dict(tooltip_map or {})
        self._tooltip_map_driver2 = dict(tooltip_map_driver2 or {})
        self._tooltip_map = self._tooltip_map_driver1  # 向下相容性

        self.clear_data()
        self.set_lap_records(lap_records)

        lap_numbers: List[int] = []
        throttle_values: List[float] = []
        ratio_values: List[float] = []
        average_values: List[float] = []

        for record in lap_records:
            lap_no = self._safe_int(record.get("lap_number"))
            throttle = self._safe_float(record.get("full_throttle_duration_s"))
            ratio = self._safe_float(record.get("full_throttle_ratio_percent"))
            avg = self._safe_float(record.get("average_throttle_percent"))

            if lap_no is None or throttle is None:
                continue

            lap_numbers.append(lap_no)
            throttle_values.append(throttle)
            ratio_values.append(ratio if ratio is not None else float("nan"))
            average_values.append(avg if avg is not None else float("nan"))

        if show_full_duration and lap_numbers:
            self.add_data_series(
                ChartDataSeries(
                    name=tr("throttle_line_chart.series_full_throttle", "Full Throttle (s)"),
                    x_data=lap_numbers,
                    y_data=throttle_values,
                    color="#FF914D",
                    line_width=2,
                    y_axis="left",
                )
            )

        cleaned_ratio: List[float] = []
        if show_ratio and lap_numbers:
            cleaned_ratio = self._replace_nan_with_previous(ratio_values)
            if cleaned_ratio:
                self.add_data_series(
                    ChartDataSeries(
                        name=tr("throttle_line_chart.series_ratio", "Full Throttle %"),
                        x_data=lap_numbers,
                        y_data=cleaned_ratio,
                        color="#0064C8",  # 柔和藍色 - 車手1 (參考速度模組)
                        line_width=2,
                        y_axis="left",
                        line_style=Qt.SolidLine,  # 實線
                    )
                )

        if show_average and lap_numbers:
            cleaned_average = self._replace_nan_with_previous(average_values)
            if cleaned_average:
                self.add_data_series(
                    ChartDataSeries(
                        name=tr("throttle_line_chart.series_average", "Average Throttle %"),
                        x_data=lap_numbers,
                        y_data=cleaned_average,
                        color="#4D94D9",  # 淺藍色 - 車手1次要線條
                        line_width=2,
                        y_axis="left",
                        line_style=Qt.DashLine,  # 虛線
                    )
                )

        if highlight_threshold and threshold_percent is not None:
            _ = [
                lap
                for lap, ratio in zip(lap_numbers, cleaned_ratio or ratio_values)
                if ratio is not None and not self._is_nan(ratio) and ratio >= threshold_percent
            ]

        # 🆕 處理第二位車手資料（使用紅色）
        if lap_records_driver2:
            lap_numbers_d2: List[int] = []
            ratio_values_d2: List[float] = []
            average_values_d2: List[float] = []

            for record in lap_records_driver2:
                lap_no = self._safe_int(record.get("lap_number"))
                ratio = self._safe_float(record.get("full_throttle_ratio_percent"))
                avg = self._safe_float(record.get("average_throttle_percent"))

                if lap_no is None:
                    continue

                lap_numbers_d2.append(lap_no)
                ratio_values_d2.append(ratio if ratio is not None else float("nan"))
                average_values_d2.append(avg if avg is not None else float("nan"))

            # Driver2 Full Throttle % (紅色實線)
            if show_ratio and lap_numbers_d2:
                cleaned_ratio_d2 = self._replace_nan_with_previous(ratio_values_d2)
                if cleaned_ratio_d2:
                    self.add_data_series(
                        ChartDataSeries(
                            name=tr("throttle_line_chart.series_ratio_driver2", "Full Throttle % (D2)"),
                            x_data=lap_numbers_d2,
                            y_data=cleaned_ratio_d2,
                            color="#C83232",  # 柔和紅色 - 車手2 (參考速度模組)
                            line_width=2,
                            y_axis="left",
                            line_style=Qt.SolidLine,  # 實線
                        )
                    )

            # Driver2 Average Throttle % (淺紅色虛線)
            if show_average and lap_numbers_d2:
                cleaned_average_d2 = self._replace_nan_with_previous(average_values_d2)
                if cleaned_average_d2:
                    self.add_data_series(
                        ChartDataSeries(
                            name=tr("throttle_line_chart.series_average_driver2", "Average Throttle % (D2)"),
                            x_data=lap_numbers_d2,
                            y_data=cleaned_average_d2,
                            color="#E57373",  # 淺紅色 - 車手2次要線條
                            line_width=2,
                            y_axis="left",
                            line_style=Qt.DashLine,  # 虛線
                        )
                    )

        self.set_highlight_laps([])  # 已移除垂直 highlight，僅保留狀態同步
        self.set_flag_markers(flag_markers)
        self.set_pinned_marker(None, None)
        self.recalculate_data_ranges()
        self.update()

    def get_tooltip_payload(self, lap_number: int, series_name: str = "") -> Dict[str, object]:
        """
        獲取指定圈數的 tooltip 數據
        
        Args:
            lap_number: 圈數
            series_name: 系列名稱（用於判斷是 Driver 1 還是 Driver 2）
        
        Returns:
            Tooltip 數據字典
        """
        # 🆕 雙車手模式：根據系列名稱判斷使用哪個 tooltip map
        # 如果系列名稱包含 "(D2)" 或 "(Driver 2)"，使用 Driver 2 的數據
        if series_name and ("(D2)" in series_name or "(Driver 2)" in series_name or "Driver 2" in series_name):
            return dict(self._tooltip_map_driver2.get(int(lap_number), {}))
        else:
            # 默認使用 Driver 1 的數據
            return dict(self._tooltip_map_driver1.get(int(lap_number), {}))
    
    def format_tooltip_for_data_point(self, lap_number: int, series_name: str = "") -> List[str]:
        """
        為數據點互動系統格式化 tooltip 文字
        只顯示：Lap, Ave Throttle %, Full throttle %, Lap time, DRS %, Tyre
        
        Args:
            lap_number: 圈數
            series_name: 系列名稱（用於雙車手模式判斷）
        """
        payload = self.get_tooltip_payload(lap_number, series_name)
        if not payload:
            return []
        
        lines = []
        
        # Lap
        lines.append(f"Lap {lap_number}")
        
        # Full Throttle % (Full throttle %)
        ratio = payload.get("full_throttle_ratio_percent")
        if ratio is not None:
            try:
                lines.append(f"Full Throttle %: {float(ratio):.1f}%")
            except (TypeError, ValueError):
                pass
        
        # Average Throttle % (Ave Throttle %)
        avg = payload.get("average_throttle_percent")
        if avg is not None:
            try:
                lines.append(f"Ave Throttle %: {float(avg):.1f}%")
            except (TypeError, ValueError):
                pass
        
        # Lap Time
        lap_time_fmt = payload.get("lap_time_formatted") or payload.get("lap_time")
        if lap_time_fmt:
            lines.append(f"Lap Time: {lap_time_fmt}")
        elif payload.get("lap_time_seconds") is not None:
            try:
                lines.append(f"Lap Time: {float(payload['lap_time_seconds']):.3f}s")
            except (TypeError, ValueError):
                pass
        
        # DRS %
        drs = payload.get("drs_percent")
        if drs is not None:
            try:
                lines.append(f"DRS %: {float(drs):.1f}%")
            except (TypeError, ValueError):
                pass
        
        # Tyre
        compound = payload.get("compound", "N/A")
        lines.append(f"Tyre: {compound}")
        
        return lines

    # ------------------------------------------------------------------
    # 輔助工具
    # ------------------------------------------------------------------
    @staticmethod
    def _replace_nan_with_previous(series: Sequence[Optional[float]]) -> List[float]:
        cleaned: List[float] = []
        last_value: Optional[float] = None
        for value in series:
            if value is None or (isinstance(value, float) and value != value):  # NaN 檢查
                fallback = last_value if last_value is not None else 0.0
                cleaned.append(fallback)
            else:
                numeric = float(value)
                cleaned.append(numeric)
                last_value = numeric
        return cleaned

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _is_nan(value) -> bool:
        return isinstance(value, float) and value != value

    # ------------------------------------------------------------------
    # 覆寫繪圖：固定標籤
    # ------------------------------------------------------------------
    def _draw_pinned_annotation(self, painter, chart_area) -> None:
        """❌ 已禁用舊的 pinned_marker 系統，使用通用的 pinned_data_points 替代"""
        # 不再繪製淺藍色的 "Lap XX full throttle(s)" 提示
        # 新系統使用 universal_chart_widget.py 中的 draw_hover_and_pinned_data_points()
        pass

    def _build_pinned_lines(self, lap: int, payload: Dict[str, object]) -> List[str]:
        """❌ 已禁用 - 舊系統不再使用"""
        return []


__all__ = ["ThrottleDurationChartWidget"]
