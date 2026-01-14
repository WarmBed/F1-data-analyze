"""專為油門折線圖同步需求打造的通用圖表擴充。"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen

from modules.gui.universal_chart_widget import UniversalChartWidget


class LinkedUniversalChartWidget(UniversalChartWidget):
    """在既有的 `UniversalChartWidget` 上增加雙視窗同步能力。"""

    lapHover = pyqtSignal(int, dict)
    lapClicked = pyqtSignal(int, dict)
    viewTransformChanged = pyqtSignal(float, float)
    pinnedCleared = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(title=title, parent=parent)
        self._lap_records: List[dict] = []
        self._lap_index: Dict[int, dict] = {}
        self._x_values: List[int] = []
        self._highlight_laps: List[int] = []
        self._external_highlight: Optional[int] = None
        self._flag_markers: Dict[int, str] = {}
        self._pinned_marker: Optional[Tuple[int, Dict[str, Any]]] = None
        self._suppress_sync = False
        self._last_emitted_scale = (self.x_scale, self.x_offset)

        # 讓預設圖例顯示更佳
        self.show_grid = True
        self.show_legend = True
        
        # 🚀 性能優化：防抖機制
        self._hover_check_counter = 0
        self._hover_check_interval = 3  # 每3次滑鼠移動才檢查一次
        self._last_hovered_lap = None  # 記錄上次懸停圈數

    # ------------------------------------------------------------------
    # 公開 API
    # ------------------------------------------------------------------
    def set_lap_records(self, records: Sequence[dict]) -> None:
        self._lap_records = list(records) if records else []
        self._lap_index = {int(rec.get("lap_number", idx + 1)): rec for idx, rec in enumerate(self._lap_records)}
        self._x_values = sorted(self._lap_index.keys())

    def set_highlight_laps(self, lap_numbers: Iterable[int]) -> None:
        self._highlight_laps = sorted({int(lap) for lap in lap_numbers if isinstance(lap, (int, float))})
        self.update()

    def set_external_highlight(self, lap_number: Optional[int]) -> None:
        self._external_highlight = int(lap_number) if lap_number is not None else None
        self.update()

    def set_flag_markers(self, markers: Optional[Dict[int, str]]) -> None:
        if not markers:
            self._flag_markers = {}
        else:
            self._flag_markers = {int(k): str(v) for k, v in markers.items() if v}
        self.update()

    def set_pinned_marker(self, lap_number: Optional[int], payload: Optional[Dict[str, Any]]) -> None:
        if lap_number is None or payload is None:
            self._pinned_marker = None
        else:
            self._pinned_marker = (int(lap_number), dict(payload))
        self.update()

    def apply_view_transform(self, x_scale: float, x_offset: float) -> None:
        self._suppress_sync = True
        try:
            self.x_scale = max(0.1, min(10.0, float(x_scale)))
            self.x_offset = float(x_offset)
            self.recalculate_data_ranges()
            self.update()
        finally:
            self._suppress_sync = False

    def set_x_range(self, x_min: float, x_max: float) -> None:
        """設定 X 軸範圍（用於跨模組同步）"""
        if x_max <= x_min:
            return
        
        self._suppress_sync = True
        try:
            # 使用 get_overall_x_range() 獲取數據範圍
            data_x_min, data_x_max = self.get_overall_x_range()
            if data_x_min is not None and data_x_max is not None:
                full_range = data_x_max - data_x_min
                if full_range > 0:
                    visible_range = x_max - x_min
                    self.x_scale = full_range / visible_range if visible_range > 0 else 1.0
                    self.x_offset = (x_min - data_x_min) / full_range * self.x_scale
            
            self.recalculate_data_ranges()
            self.update()
        finally:
            self._suppress_sync = False

    # ------------------------------------------------------------------
    # 事件覆寫 - 發送同步訊號
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        
        # 🚀 防抖機制：每N次滑鼠移動才檢查一次
        self._hover_check_counter += 1
        if self._hover_check_counter < self._hover_check_interval:
            return
        self._hover_check_counter = 0

        lap_number = self._resolve_lap_from_pos(event.pos())
        if lap_number is None:
            return
        
        # 🚀 優化：僅在圈數改變時發射信號
        if lap_number != self._last_hovered_lap:
            self._last_hovered_lap = lap_number
            record = self._lap_index.get(lap_number, {})
            self.lapHover.emit(lap_number, record)

        if self.dragging:
            self._emit_view_transform_if_needed()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            if self._pinned_marker is not None:
                self.set_pinned_marker(None, None)
                self.set_external_highlight(None)
                self.pinnedCleared.emit()
                event.accept()
                return

        super().mousePressEvent(event)

        if event.button() == Qt.LeftButton:
            lap_number = self._resolve_lap_from_pos(event.pos())
            if lap_number is None:
                return
            record = self._lap_index.get(lap_number, {})
            self.lapClicked.emit(lap_number, record)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and not self.dragging:
            self._emit_view_transform_if_needed(force=True)

    def wheelEvent(self, event):
        super().wheelEvent(event)
        self._emit_view_transform_if_needed()

    # ------------------------------------------------------------------
    # 自訂繪圖 - 顯示 highlight
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        super().paintEvent(event)

        if not self._x_values:
            return

        chart_area = self.get_chart_area()
        painter = QPainter(self)

        self._draw_flag_markers(painter, chart_area)
        self._draw_pinned_annotation(painter, chart_area)

        painter.end()

    # ------------------------------------------------------------------
    # 私有工具
    # ------------------------------------------------------------------
    def draw_x_axis_labels(self, painter, chart_area):  # type: ignore[override]
        """覆寫 X 軸刻度繪製邏輯，以圈數為刻度單位。"""
        if not self.data_series or not self._x_values:
            return super().draw_x_axis_labels(painter, chart_area)

        visible_x_min, visible_x_max = self._compute_visible_lap_range(chart_area)
        if visible_x_max <= visible_x_min:
            visible_x_max = visible_x_min + 1

        interval = self._determine_lap_interval(visible_x_min, visible_x_max)
        start_tick = int(math.floor(visible_x_min / interval)) * interval
        current_tick = start_tick

        while current_tick <= visible_x_max:
            progress = (current_tick - visible_x_min) / (visible_x_max - visible_x_min)
            screen_x = int(chart_area.left() + chart_area.width() * progress)
            if chart_area.left() <= screen_x <= chart_area.right():
                painter.drawLine(screen_x, chart_area.bottom(), screen_x, chart_area.bottom() + 5)
                painter.drawText(screen_x - 8, chart_area.bottom() + 18, str(int(current_tick)))
            current_tick += interval

    def draw_grid(self, painter, chart_area):  # type: ignore[override]
        """覆寫網格繪製，確保與圈數刻度對齊。"""
        painter.setPen(QPen(QColor(220, 220, 220), 1))

        if self.data_series and self._x_values:
            visible_x_min, visible_x_max = self._compute_visible_lap_range(chart_area)
            if visible_x_max <= visible_x_min:
                visible_x_max = visible_x_min + 1
            interval = self._determine_lap_interval(visible_x_min, visible_x_max)
            start_tick = int(math.floor(visible_x_min / interval)) * interval
            current_tick = start_tick
            while current_tick <= visible_x_max:
                progress = (current_tick - visible_x_min) / (visible_x_max - visible_x_min)
                x = int(chart_area.left() + chart_area.width() * progress)
                if chart_area.left() <= x <= chart_area.right():
                    painter.drawLine(x, chart_area.top(), x, chart_area.bottom())
                current_tick += interval

        for i in range(1, 10):
            y = int(chart_area.top() + (chart_area.height() * i / 10))
            painter.drawLine(chart_area.left(), y, chart_area.right(), y)

    def _compute_visible_lap_range(self, chart_area) -> Tuple[float, float]:
        x_min, x_max = self.get_overall_x_range()
        if x_max == x_min:
            return float(x_min), float(x_max + 1)

        visible_x_range = (x_max - x_min) / max(self.x_scale, 1e-6)
        visible_x_center = x_min + (x_max - x_min) * 0.5
        offset_factor = -self.x_offset / (chart_area.width() * max(self.x_scale, 1e-6))
        visible_x_center += (x_max - x_min) * offset_factor
        visible_x_min = visible_x_center - visible_x_range * 0.5
        visible_x_max = visible_x_center + visible_x_range * 0.5
        return float(visible_x_min), float(visible_x_max)

    @staticmethod
    def _determine_lap_interval(visible_min: float, visible_max: float) -> int:
        span = max(1.0, visible_max - visible_min)
        target_ticks = 12
        interval = int(math.ceil(span / target_ticks))
        return max(1, interval)

    def _resolve_lap_from_pos(self, pos: QPoint) -> Optional[int]:
        if not self._x_values:
            return None
        chart_area = self.get_chart_area()
        if not chart_area.contains(pos):
            return None

        data_x = self.screen_to_data_x(pos.x())
        closest = min(self._x_values, key=lambda value: abs(value - data_x))
        return int(closest)

    def _emit_view_transform_if_needed(self, force: bool = False) -> None:
        if self._suppress_sync:
            return
        current = (round(self.x_scale, 4), round(self.x_offset, 4))
        if force or current != self._last_emitted_scale:
            self._last_emitted_scale = current
            self.viewTransformChanged.emit(self.x_scale, self.x_offset)

    # ------------------------------------------------------------------
    # 繪圖輔助
    # ------------------------------------------------------------------
    def _draw_flag_markers(self, painter: QPainter, chart_area) -> None:
        if not self._flag_markers:
            return

        painter.save()
        marker_font = QFont(painter.font())
        marker_font.setPointSize(max(7, marker_font.pointSize() - 1))
        painter.setFont(marker_font)
        metrics = painter.fontMetrics()
        tick_height = 6
        baseline = chart_area.bottom() + metrics.height() + 12

        for lap, label in self._flag_markers.items():
            x = int(self.data_to_screen_x(lap))
            if chart_area.left() <= x <= chart_area.right():
                text_width = metrics.horizontalAdvance(label)
                painter.setPen(QPen(self._get_flag_color(label), 2))
                painter.drawLine(x, chart_area.bottom(), x, chart_area.bottom() + tick_height)
                painter.drawText(x - text_width // 2, baseline, label)

        painter.restore()

    def _draw_pinned_annotation(self, painter: QPainter, chart_area) -> None:
        # 由子類決定如何繪製固定標籤
        return

    @staticmethod
    def _get_flag_color(label: str) -> QColor:
        mapping = {
            "Y": QColor(255, 196, 38),
            "S": QColor(120, 144, 156),
            "R": QColor(229, 57, 53),
            "P": QColor(255, 152, 0),
        }
        return mapping.get(label, QColor(158, 158, 158))
