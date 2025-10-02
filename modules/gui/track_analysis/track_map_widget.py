#!/usr/bin/env python3
"""
賽道地圖繪製元件 - TrackMapWidget (Universal 版)
===============================================

從舊版 Track Analysis Module 移植的完整賽道繪圖邏輯，
支援：
1. 依據位置點繪製平滑賽道路徑
2. 顯示起迄點與距離標記
3. 視窗縮放自適應與手動縮放
4. 選項控制：網格、標記、標籤

Author: F1T Team
Date: 2025-10-02
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple

from PyQt5.QtCore import QPointF, Qt, pyqtSignal, QSize
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt5.QtWidgets import QWidget


class TrackMapWidget(QWidget):
    """可視化賽道位置資料的 PyQt Widget。"""

    point_clicked = pyqtSignal(dict)
    point_hovered = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.track_data: Optional[Dict[str, Any]] = None
        self.position_data: List[Dict[str, Any]] = []
        self.track_bounds: Optional[Dict[str, float]] = None

        self._base_scale: float = 1.0
        self.scale_factor: float = 1.0
        self._pending_fit: bool = False
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self._last_size: QSize = QSize(0, 0)

        self.show_start_point: bool = False
        self.show_finish_point: bool = False
        self.show_distance_markers: bool = False
        self.show_track_labels: bool = False
        self.show_grid: bool = False

        self._grid_spacing: float = 500.0  # 公尺
        self._max_grid_lines: int = 12

        self.setMouseTracking(True)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")

    # ------------------------------------------------------------------
    # 資料載入與設定
    # ------------------------------------------------------------------
    def load_track_data(self, track_data: Dict[str, Any]) -> bool:
        """供 Universal MDI 呼叫的資料載入接口。"""
        try:
            self.track_data = track_data or {}
            records = track_data.get("detailed_position_records") or track_data.get("position_records") or []
            self.position_data = [record for record in records if isinstance(record, dict)]

            bounds = track_data.get("position_analysis", {}).get("track_bounds")
            if not bounds:
                bounds = track_data.get("track_bounds")
            if not bounds:
                bounds = self._calculate_bounds_from_positions(self.position_data)

            self.track_bounds = bounds if isinstance(bounds, dict) else None

            if self.track_bounds:
                self._pending_fit = True
                self.fit_to_view()
            else:
                self.scale_factor = 1.0
                self.offset_x = 0.0
                self.offset_y = 0.0

            self.update()

            info = track_data.get("session_info", {})
            track_name = info.get("track_name") or info.get("event_name") or "Unknown"
            print(f"[TRACK_MAP] Data loaded: {track_name}, points={len(self.position_data)} bounds={self.track_bounds}")
            return bool(self.position_data)
        except Exception as exc:
            print(f"[TRACK_MAP] Failed to load data: {exc}")
            return False

    def set_track_data(self, position_data: List[Dict[str, Any]], track_bounds: Dict[str, float]) -> None:
        """兼容 legacy API。"""
        self.position_data = position_data or []
        self.track_bounds = track_bounds or self._calculate_bounds_from_positions(self.position_data)
        self._pending_fit = True
        self.fit_to_view()
        self.update()

    def set_display_options(
        self,
        show_start: Optional[bool] = None,
        show_finish: Optional[bool] = None,
        show_markers: Optional[bool] = None,
        show_labels: Optional[bool] = None,
        show_grid: Optional[bool] = None,
    ) -> None:
        if show_start is not None:
            self.show_start_point = bool(show_start)
        if show_finish is not None:
            self.show_finish_point = bool(show_finish)
        if show_markers is not None:
            self.show_distance_markers = bool(show_markers)
        if show_labels is not None:
            self.show_track_labels = bool(show_labels)
        if show_grid is not None:
            self.show_grid = bool(show_grid)
        self.update()

    # ------------------------------------------------------------------
    # 縮放與視圖控制
    # ------------------------------------------------------------------
    def fit_to_view(self) -> None:
        if not self.track_bounds:
            return

        self._base_scale, self.offset_x, self.offset_y = self._compute_fit_to_view()
        self.scale_factor = self._base_scale
        self._pending_fit = False
        self.update()

    def set_zoom(self, zoom_factor: float) -> None:
        if zoom_factor <= 0.0:
            self.fit_to_view()
            return

        if not self.track_bounds:
            return

        if self._pending_fit:
            self.fit_to_view()

        self.scale_factor = self._base_scale * zoom_factor
        self._recenter_after_zoom()
        self.update()

    def get_zoom(self) -> float:
        if self._base_scale == 0:
            return 1.0
        return self.scale_factor / self._base_scale

    def set_show_grid(self, show: bool) -> None:
        self.show_grid = bool(show)
        self.update()

    def set_show_markers(self, show: bool) -> None:
        self.show_distance_markers = bool(show)
        self.update()

    def _recenter_after_zoom(self) -> None:
        if not self.track_bounds:
            return

        track_width = self.track_bounds["x_max"] - self.track_bounds["x_min"]
        track_height = self.track_bounds["y_max"] - self.track_bounds["y_min"]
        scaled_width = track_width * self.scale_factor
        scaled_height = track_height * self.scale_factor
        self.offset_x = (self.width() - scaled_width) / 2
        self.offset_y = (self.height() - scaled_height) / 2

    def _compute_fit_to_view(self) -> Tuple[float, float, float]:
        widget_width = max(1, self.width())
        widget_height = max(1, self.height())
        track_width = self.track_bounds["x_max"] - self.track_bounds["x_min"]
        track_height = self.track_bounds["y_max"] - self.track_bounds["y_min"]

        if track_width <= 0 or track_height <= 0:
            return 1.0, 0.0, 0.0

        margin_ratio = 0.9
        scale_x = (widget_width * margin_ratio) / track_width
        scale_y = (widget_height * margin_ratio) / track_height
        base_scale = min(scale_x, scale_y)

        offset_x = (widget_width - track_width * base_scale) / 2
        offset_y = (widget_height - track_height * base_scale) / 2
        return base_scale, offset_x, offset_y

    # ------------------------------------------------------------------
    # 繪圖邏輯
    # ------------------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: D401 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(245, 245, 245))

        if not self.position_data or not self.track_bounds:
            painter.setPen(QPen(QColor(120, 120, 120)))
            painter.setFont(QFont("Microsoft YaHei", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "賽道地圖\n等待數據...")
            return

        if self._pending_fit or self.size() != self._last_size:
            self.fit_to_view()
            self._last_size = self.size()

        if self.show_grid:
            self._draw_grid(painter)

        points = self._create_screen_points()
        if len(points) < 2:
            painter.setPen(QPen(QColor(120, 120, 120)))
            painter.drawText(self.rect(), Qt.AlignCenter, "賽道點數不足以繪製")
            return

        path = self._build_track_path(points)

        painter.setPen(QPen(QColor(40, 40, 200), 4))
        painter.drawPath(path)

        painter.setPen(QPen(QColor(120, 120, 255), 1))
        painter.drawPath(path)

        if self.show_distance_markers:
            self._draw_distance_markers(painter, points)

    def _draw_grid(self, painter: QPainter) -> None:
        if not self.track_bounds:
            return

        spacing = self._grid_spacing
        bounds = self.track_bounds
        x_min, x_max = bounds["x_min"], bounds["x_max"]
        y_min, y_max = bounds["y_min"], bounds["y_max"]

        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))

        count = 0
        x = (int(x_min // spacing) + 1) * spacing
        while x < x_max and count < self._max_grid_lines:
            sx1, sy1 = self.world_to_screen(x, y_min)
            sx2, sy2 = self.world_to_screen(x, y_max)
            painter.drawLine(sx1, sy1, sx2, sy2)
            count += 1
            x += spacing

        count = 0
        y = (int(y_min // spacing) + 1) * spacing
        while y < y_max and count < self._max_grid_lines:
            sx1, sy1 = self.world_to_screen(x_min, y)
            sx2, sy2 = self.world_to_screen(x_max, y)
            painter.drawLine(sx1, sy1, sx2, sy2)
            count += 1
            y += spacing

    def _create_screen_points(self) -> List[QPointF]:
        return [QPointF(*self.world_to_screen(rec.get("position_x", 0), rec.get("position_y", 0))) for rec in self.position_data]

    def _build_track_path(self, points: List[QPointF]) -> QPainterPath:
        path = QPainterPath()
        path.moveTo(points[0])
        for idx in range(1, len(points)):
            if idx < len(points) - 1:
                mid = QPointF((points[idx].x() + points[idx + 1].x()) / 2, (points[idx].y() + points[idx + 1].y()) / 2)
                path.quadTo(points[idx], mid)
            else:
                path.lineTo(points[idx])
        return path

    def _draw_start_finish(self, painter: QPainter, points: List[QPointF]) -> None:
        if self.show_start_point and points:
            painter.setBrush(QBrush(QColor(0, 200, 0)))
            painter.setPen(QPen(QColor(0, 120, 0), 2))
            painter.drawEllipse(points[0], 6, 6)
            if self.show_track_labels:
                painter.setFont(QFont("Arial", 8, QFont.Bold))
                painter.setPen(QPen(QColor(0, 100, 0)))
                painter.drawText(int(points[0].x()) + 10, int(points[0].y()) - 5, "START")

        if self.show_finish_point and len(points) > 1:
            painter.setBrush(QBrush(QColor(200, 0, 0)))
            painter.setPen(QPen(QColor(120, 0, 0), 2))
            painter.drawEllipse(points[-1], 6, 6)
            if self.show_track_labels:
                painter.setFont(QFont("Arial", 8, QFont.Bold))
                painter.setPen(QPen(QColor(100, 0, 0)))
                painter.drawText(int(points[-1].x()) + 10, int(points[-1].y()) - 5, "FINISH")

    def _draw_distance_markers(self, painter: QPainter, points: List[QPointF]) -> None:
        if not self.position_data:
            return

        painter.setBrush(QBrush(QColor(0, 0, 200)))
        painter.setPen(QPen(QColor(0, 0, 150), 1))
        step = max(1, len(points) // 8)
        for idx in range(step, len(points) - 1, step):
            painter.drawEllipse(points[idx], 3, 3)
            distance_m = self.position_data[idx].get("distance_m")
            if distance_m is not None:
                painter.setFont(QFont("Arial", 7))
                painter.setPen(QPen(QColor(0, 0, 120)))
                painter.drawText(int(points[idx].x()) + 5, int(points[idx].y()) + 15, f"{distance_m/1000:.1f} km")

    # ------------------------------------------------------------------
    # 座標轉換
    # ------------------------------------------------------------------
    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        if not self.track_bounds:
            return int(x), int(y)

        sx = (x - self.track_bounds["x_min"]) * self.scale_factor + self.offset_x
        sy = (self.track_bounds["y_max"] - y) * self.scale_factor + self.offset_y
        return int(sx), int(sy)

    def _calculate_bounds_from_positions(self, positions: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        if not positions:
            return None
        xs = [p.get("position_x", 0.0) for p in positions]
        ys = [p.get("position_y", 0.0) for p in positions]
        return {
            "x_min": min(xs),
            "x_max": max(xs),
            "y_min": min(ys),
            "y_max": max(ys),
        }

    # ------------------------------------------------------------------
    # 互動事件
    # ------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: D401 - Qt override
        if event.button() == Qt.LeftButton and self.position_data:
            info = {
                "x": event.x(),
                "y": event.y(),
                "total_points": len(self.position_data),
            }
            self.point_clicked.emit(info)
        super().mousePressEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: D401 - Qt override
        super().resizeEvent(event)
        if self.track_bounds:
            self._pending_fit = True
        self.update()

    # ------------------------------------------------------------------
    # 輔助工具
    # ------------------------------------------------------------------
    def clear_map(self) -> None:
        self.track_data = None
        self.position_data = []
        self.track_bounds = None
        self.scale_factor = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.update()

    def get_track_info(self) -> Dict[str, Any]:
        return {
            "position_count": len(self.position_data),
            "track_bounds": dict(self.track_bounds) if self.track_bounds else {},
            "has_data": bool(self.position_data),
        }

    def force_rescale(self) -> None:
        if not self.track_bounds:
            return
        self._pending_fit = True
        self.fit_to_view()


__all__ = ["TrackMapWidget"]
