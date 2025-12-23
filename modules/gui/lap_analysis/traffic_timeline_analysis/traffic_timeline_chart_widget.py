#!/usr/bin/env python3
"""
TrafficTimelineChartWidget - Traffic 時間線圖表組件 (純 PyQt5 實現)

功能：
- 使用 PyQt5 QPainter 繪製時間線圖表（100% Qt 原生）
- 顯示所有車手每一圈的 traffic 狀態
- 白色風格主題，與 ThrottleBoxPlotChartWidget 一致
- 支援滑鼠懸停顯示詳細資訊
- 支援圖表匯出（PNG, JPG）
- 支援多國語言（i18n）

Author: F1T Team
Date: 2025-12-23
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import QWidget, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QPainterPath,
    QImage,
    QPainter as QPainterForExport,
)

from core.gui_i18n import tr
from modules.gui.themes import color_palette_provider
from core.logger import get_logger


logger = get_logger("gui.traffic_timeline_chart", component="gui")


# Status Colors (White Theme)
STATUS_COLORS = {
    "clean": QColor("#4CAF50"),      # Green
    "traffic": QColor("#FF9800"),    # Orange
    "excluded": QColor("#9E9E9E"),   # Gray
    "no_data": QColor("#E0E0E0"),    # Light gray
}


class TrafficTimelineChartWidget(QWidget):
    """Traffic Timeline 圖表組件 (純 PyQt5 QPainter 實現，白色風格)"""

    DEFAULT_COLOR = QColor(128, 128, 128)

    chart_clicked = pyqtSignal(str)  # driver code

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data
        self._drivers_data: List[Dict[str, Any]] = []
        self._max_lap: int = 0
        self._metadata: Dict[str, Any] = {}
        self.current_data: Optional[Dict] = None

        # Layout margins (標題已移至 MDI 視窗，減少頂部邊距)
        self.margin_left = 100
        self.margin_right = 20
        self.margin_top = 25
        self.margin_bottom = 40

        # Cell dimensions
        self.cell_width = 10
        self.cell_height = 18
        self.cell_gap = 1

        # Chart rect
        self.chart_rect = QRect()

        # Interaction
        self.hover_driver: Optional[str] = None
        self.hover_lap: Optional[int] = None
        self.hover_position: Optional[QPoint] = None

        self.setMouseTracking(True)
        self.setMinimumSize(400, 200)
        
        # 設置大小策略，讓圖表能自動擴展填滿可用空間
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        logger.info("[TRAFFIC_TIMELINE_CHART] Chart widget initialized (QPainter version)")

    def update_data(self, data: Dict[str, Any]):
        """Update chart data and redraw"""
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[TRAFFIC_TIMELINE_CHART] Invalid data format")
                return

            self.current_data = data
            self._parse_data(data)
            self._ensure_palette_for_data(data)
            self._update_size()

            logger.info("[TRAFFIC_TIMELINE_CHART] Data updated: %d drivers, %d laps",
                        len(self._drivers_data), self._max_lap)
            self.update()

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_CHART] Failed to update data")

    def _ensure_palette_for_data(self, data: Dict[str, Any]) -> None:
        """Ensure the colour palette is ready for the dataset season."""
        if not isinstance(data, dict):
            return

        metadata = data.get("metadata", {}) or {}
        target_year = None

        api_meta = metadata.get("api")
        if isinstance(api_meta, dict):
            params = api_meta.get("params")
            if isinstance(params, dict):
                target_year = params.get("year") or params.get("season_year")

        if target_year is None:
            target_year = metadata.get("year") or metadata.get("season_year")

        try:
            if target_year is not None:
                color_palette_provider.ensure_loaded(year=int(target_year))
            else:
                color_palette_provider.ensure_loaded()
        except Exception:
            pass

    def _parse_data(self, data: Dict[str, Any]):
        """Parse API response data"""
        drivers = data.get("drivers") or {}
        self._metadata = data.get("metadata") or {}

        self._drivers_data = []
        self._max_lap = 0

        for driver_number, d in drivers.items():
            if not isinstance(d, dict):
                continue

            driver_tla = str(d.get("driver_tla") or driver_number)
            team = str(d.get("team") or "")
            per_lap = d.get("per_lap") or []
            laps_in_traffic = int(d.get("laps_in_traffic") or 0)
            laps_analyzed = int(d.get("laps_analyzed") or 0)
            time_in_traffic_ratio = float(d.get("time_in_traffic_ratio") or 0.0)

            lap_states: Dict[int, int] = {}  # lap_num -> state
            for lap_data in per_lap:
                if not isinstance(lap_data, dict):
                    continue
                lap_num = int(lap_data.get("lap") or 0)
                in_traffic = bool(lap_data.get("lap_in_traffic"))
                excluded = bool(lap_data.get("excluded_sc_vsc"))

                if lap_num > self._max_lap:
                    self._max_lap = lap_num

                # State: 0=clean, 1=traffic, 2=excluded
                if excluded:
                    state = 2
                elif in_traffic:
                    state = 1
                else:
                    state = 0

                lap_states[lap_num] = state

            self._drivers_data.append({
                "driver_tla": driver_tla,
                "team": team,
                "lap_states": lap_states,
                "laps_in_traffic": laps_in_traffic,
                "laps_analyzed": laps_analyzed,
                "time_in_traffic_ratio": time_in_traffic_ratio,
            })

        # Sort by traffic count (most traffic first)
        self._drivers_data.sort(key=lambda x: (-x["laps_in_traffic"], x["driver_tla"]))

    def _update_size(self):
        """Update widget minimum size based on data"""
        if not self._drivers_data or self._max_lap == 0:
            return

        # 設置合理的最小尺寸，但允許擴展
        min_width = max(600, self.margin_left + self._max_lap * 8 + self.margin_right)
        min_height = max(300, self.margin_top + len(self._drivers_data) * 16 + self.margin_bottom)
        self.setMinimumSize(min_width, min_height)

    def _calculate_cell_dimensions(self):
        """動態計算 cell 尺寸以填滿可用空間"""
        if not self._drivers_data or self._max_lap == 0:
            return
        
        # 計算可用區域
        available_width = self.chart_rect.width()
        available_height = self.chart_rect.height() - 30  # 減去 legend 高度
        
        # 計算每個 cell 的大小
        # 寬度：根據圈數平均分配
        self.cell_width = max(8, (available_width - self._max_lap * self.cell_gap) // self._max_lap)
        
        # 高度：根據車手數量平均分配
        num_drivers = len(self._drivers_data)
        self.cell_height = max(14, (available_height - num_drivers * self.cell_gap) // num_drivers)
        
        # 限制最大尺寸避免過大
        self.cell_width = min(self.cell_width, 20)
        self.cell_height = min(self.cell_height, 28)

    def _get_team_color(self, team: str, driver: str = "") -> QColor:
        """Get team color from palette or fallback"""
        if driver:
            try:
                color = color_palette_provider.get_driver_color(driver, format="qcolor")
                if isinstance(color, QColor):
                    return QColor(color)
            except Exception:
                pass

        return QColor(self.DEFAULT_COLOR)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            self.chart_rect = QRect(
                self.margin_left,
                self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom,
            )
            
            # 動態計算 cell 大小以填滿可用空間
            self._calculate_cell_dimensions()

            self._draw_background(painter)
            # 標題已移至 MDI 視窗標題列，不再繪製
            # self._draw_title(painter)

            if self._drivers_data and self._max_lap > 0:
                self._draw_lap_axis(painter)
                self._draw_timeline(painter)
                self._draw_legend(painter)

                if self.hover_driver and self.hover_position:
                    self._draw_tooltip(painter)
            else:
                self._draw_no_data_message(painter)
        finally:
            painter.end()

    def _draw_background(self, painter: QPainter):
        """Draw white background"""
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        painter.fillRect(self.chart_rect, QColor(255, 255, 255))

    def _draw_title(self, painter: QPainter):
        """Draw title"""
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(50, 50, 50)))

        year = self._metadata.get("year", "")
        race = self._metadata.get("race", "")
        session = self._metadata.get("session", "")

        title = tr("traffic_timeline.title", "Traffic Timeline")
        if year and race:
            title = f"{title} - {year} {race} {session}"

        painter.drawText(
            QRect(self.margin_left, 5, self.chart_rect.width(), 30),
            Qt.AlignLeft | Qt.AlignVCenter,
            title
        )

    def _draw_lap_axis(self, painter: QPainter):
        """Draw lap number axis at top"""
        axis_font = QFont()
        axis_font.setPointSize(7)
        painter.setFont(axis_font)
        painter.setPen(QPen(QColor(100, 100, 100)))

        # Draw lap numbers every 5 laps
        for lap in range(1, self._max_lap + 1):
            if lap == 1 or lap % 5 == 0 or lap == self._max_lap:
                x = self.margin_left + (lap - 1) * (self.cell_width + self.cell_gap) + self.cell_width // 2
                y = self.margin_top - 3

                painter.drawText(
                    QRect(x - 12, y - 12, 24, 12),
                    Qt.AlignCenter,
                    str(lap)
                )

    def _draw_timeline(self, painter: QPainter):
        """Draw timeline for all drivers"""
        for idx, driver_data in enumerate(self._drivers_data):
            y = self.margin_top + idx * (self.cell_height + self.cell_gap)
            self._draw_driver_row(painter, driver_data, y, idx)

    def _draw_driver_row(self, painter: QPainter, driver_data: Dict, y: int, idx: int):
        """Draw a single driver's timeline row"""
        driver_tla = driver_data["driver_tla"]
        team = driver_data["team"]
        lap_states = driver_data["lap_states"]
        laps_in_traffic = driver_data["laps_in_traffic"]
        laps_analyzed = driver_data["laps_analyzed"]

        # Get team color
        team_color = self._get_team_color(team, driver_tla)
        is_hovered_row = self.hover_driver == driver_tla

        # ===== Draw driver label with team color background =====
        label_font = QFont()
        label_font.setPointSize(8)
        label_font.setBold(is_hovered_row)
        painter.setFont(label_font)
        fm = QFontMetrics(label_font)

        # Driver label text with stats
        label_text = f"{driver_tla} ({laps_in_traffic}/{laps_analyzed})"

        # Background for driver label
        label_width = fm.horizontalAdvance(label_text) + 12
        label_rect = QRectF(5, y, min(label_width, self.margin_left - 10), self.cell_height)

        # Draw rounded background
        bg_color = QColor(team_color)
        bg_color.setAlpha(180 if is_hovered_row else 140)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))

        path = QPainterPath()
        path.addRoundedRect(label_rect, 3, 3)
        painter.drawPath(path)

        # Calculate text color based on luminance
        luminance = 0.299 * team_color.red() + 0.587 * team_color.green() + 0.114 * team_color.blue()
        text_color = QColor(0, 0, 0) if luminance > 128 else QColor(255, 255, 255)

        painter.setPen(text_color)
        painter.drawText(
            QRect(8, y, int(self.margin_left - 15), self.cell_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            label_text
        )

        # ===== Draw lap cells =====
        for lap in range(1, self._max_lap + 1):
            x = self.margin_left + (lap - 1) * (self.cell_width + self.cell_gap)

            # Get state
            state = lap_states.get(lap, -1)  # -1 = no data

            # Determine cell color
            if state == 0:
                cell_color = STATUS_COLORS["clean"]
            elif state == 1:
                cell_color = STATUS_COLORS["traffic"]
            elif state == 2:
                cell_color = STATUS_COLORS["excluded"]
            else:
                cell_color = STATUS_COLORS["no_data"]

            # Check if this cell is hovered
            is_hovered_cell = (self.hover_driver == driver_tla and self.hover_lap == lap)

            # Brighten if hovered
            if is_hovered_cell:
                cell_color = cell_color.lighter(120)

            # Draw cell with rounded corners
            cell_rect = QRectF(x, y, self.cell_width, self.cell_height)

            painter.setPen(QPen(QColor(200, 200, 200), 0.5))
            painter.setBrush(QBrush(cell_color))

            path = QPainterPath()
            path.addRoundedRect(cell_rect, 2, 2)
            painter.drawPath(path)

    def _draw_legend(self, painter: QPainter):
        """Draw legend at bottom"""
        legend_y = self.height() - 25
        legend_x = self.margin_left

        legend_items = [
            (tr("traffic_timeline.clean_lap", "Clean Lap"), STATUS_COLORS["clean"]),
            (tr("traffic_timeline.in_traffic", "In Traffic"), STATUS_COLORS["traffic"]),
            (tr("traffic_timeline.sc_vsc", "SC/VSC"), STATUS_COLORS["excluded"]),
            (tr("traffic_timeline.no_data", "No Data"), STATUS_COLORS["no_data"]),
        ]

        legend_font = QFont()
        legend_font.setPointSize(8)
        painter.setFont(legend_font)

        for label, color in legend_items:
            # Color box
            box_rect = QRectF(legend_x, legend_y, 12, 12)
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.setBrush(QBrush(color))
            path = QPainterPath()
            path.addRoundedRect(box_rect, 2, 2)
            painter.drawPath(path)

            # Label
            painter.setPen(QPen(QColor(80, 80, 80)))
            fm = QFontMetrics(legend_font)
            label_width = fm.horizontalAdvance(label)
            painter.drawText(
                QRect(int(legend_x + 16), int(legend_y - 1), label_width + 10, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                label
            )

            legend_x += label_width + 35

    def _draw_tooltip(self, painter: QPainter):
        """Draw tooltip for hovered cell"""
        if not self.hover_driver or not self.hover_position:
            return

        # Find driver data
        driver_data = next((d for d in self._drivers_data if d["driver_tla"] == self.hover_driver), None)
        if not driver_data:
            return

        # Build tooltip lines
        lines = [
            f"{tr('driver', 'Driver')}: {self.hover_driver}",
            f"{tr('team', 'Team')}: {driver_data['team']}",
        ]

        if self.hover_lap:
            state = driver_data["lap_states"].get(self.hover_lap, -1)
            state_text = {
                0: tr("traffic_timeline.clean_lap", "Clean Lap"),
                1: tr("traffic_timeline.in_traffic", "In Traffic"),
                2: tr("traffic_timeline.sc_vsc", "SC/VSC"),
                -1: tr("traffic_timeline.no_data", "No Data")
            }
            lines.append(f"{tr('lap', 'Lap')} {self.hover_lap}: {state_text.get(state, 'Unknown')}")

        lines.append(f"{tr('traffic_laps', 'Traffic Laps')}: {driver_data['laps_in_traffic']}/{driver_data['laps_analyzed']}")
        lines.append(f"{tr('traffic_ratio', 'Traffic Ratio')}: {driver_data['time_in_traffic_ratio']*100:.1f}%")

        # Calculate tooltip size
        tooltip_font = QFont()
        tooltip_font.setPointSize(9)
        painter.setFont(tooltip_font)
        fm = QFontMetrics(tooltip_font)

        max_width = max(fm.horizontalAdvance(line) for line in lines) + 16
        total_height = len(lines) * fm.height() + 12

        # Position tooltip
        x = self.hover_position.x() + 15
        y = self.hover_position.y() - total_height - 10

        if x + max_width > self.width():
            x = self.hover_position.x() - max_width - 15
        if y < 0:
            y = self.hover_position.y() + 20

        # Draw tooltip background
        tooltip_rect = QRectF(x, y, max_width, total_height)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(QColor(40, 40, 40), 1))
        bg_color = QColor(255, 255, 255, 245)
        painter.setBrush(QBrush(bg_color))

        path = QPainterPath()
        path.addRoundedRect(tooltip_rect, 6, 6)
        painter.drawPath(path)

        # Draw tooltip text
        painter.setPen(QPen(QColor(30, 30, 30)))
        text_y = y + 8
        for line in lines:
            painter.drawText(
                QRect(int(x + 8), int(text_y), int(max_width - 16), fm.height()),
                Qt.AlignLeft | Qt.AlignVCenter,
                line
            )
            text_y += fm.height()

        painter.restore()

    def _draw_no_data_message(self, painter: QPainter):
        """Draw no data message"""
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            self.chart_rect,
            Qt.AlignCenter,
            tr("traffic_timeline.no_data_available", "No traffic data available"),
        )

    def resizeEvent(self, event):
        """視窗大小變化時重新繪製"""
        super().resizeEvent(event)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for hover detection"""
        pos = event.pos()
        prev_driver = self.hover_driver
        prev_lap = self.hover_lap

        # Reset
        self.hover_driver = None
        self.hover_lap = None

        # Check if over a driver row
        for idx, driver_data in enumerate(self._drivers_data):
            y = self.margin_top + idx * (self.cell_height + self.cell_gap)

            if y <= pos.y() <= y + self.cell_height:
                self.hover_driver = driver_data["driver_tla"]
                self.hover_position = pos

                # Check which lap
                for lap in range(1, self._max_lap + 1):
                    x = self.margin_left + (lap - 1) * (self.cell_width + self.cell_gap)
                    if x <= pos.x() <= x + self.cell_width:
                        self.hover_lap = lap
                        break
                break

        if self.hover_driver != prev_driver or self.hover_lap != prev_lap:
            self.update()

    def leaveEvent(self, event):
        """Handle mouse leave"""
        self.hover_driver = None
        self.hover_lap = None
        self.hover_position = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton and self.hover_driver:
            self.chart_clicked.emit(self.hover_driver)

    def export_chart(self, file_path: str) -> bool:
        """Export chart to image file"""
        try:
            export_image = QImage(self.size(), QImage.Format_ARGB32)
            export_image.fill(Qt.white)

            painter = QPainterForExport(export_image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            # Save current hover state
            saved_hover_driver = self.hover_driver
            saved_hover_lap = self.hover_lap
            saved_hover_position = self.hover_position

            # Clear hover for export
            self.hover_driver = None
            self.hover_lap = None
            self.hover_position = None

            # Paint
            self.chart_rect = QRect(
                self.margin_left,
                self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom,
            )

            self._draw_background(painter)
            self._draw_title(painter)

            if self._drivers_data and self._max_lap > 0:
                self._draw_lap_axis(painter)
                self._draw_timeline(painter)
                self._draw_legend(painter)
            else:
                self._draw_no_data_message(painter)

            painter.end()

            # Restore hover state
            self.hover_driver = saved_hover_driver
            self.hover_lap = saved_hover_lap
            self.hover_position = saved_hover_position

            if export_image.save(file_path):
                logger.info("[TRAFFIC_TIMELINE_CHART] Chart exported: %s", file_path)
                return True

            raise RuntimeError("Failed to save image")

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_CHART] Export failed")
            QMessageBox.critical(
                self,
                tr("traffic_timeline.export_failed_title", "Export Failed"),
                tr("traffic_timeline.export_failed_body", "Unable to export chart."),
            )
            return False
