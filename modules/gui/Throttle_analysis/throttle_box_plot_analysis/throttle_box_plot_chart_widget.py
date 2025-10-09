"""
ThrottleBoxPlotChartWidget - 全油門百分比箱型圖圖表組件 (純 PyQt5 實現)

功能：
- 使用 PyQt5 QPainter 繪製箱型圖（100% Qt 原生）
- 顯示所有車手的全油門百分比分布（使用 full_throttle_ratio）
- 應用車隊配色方案
- 顯示統計資訊（中位數、Q1、Q3、鬚線、異常值）
- 支援圖表匯出（PNG, JPG）
- 支援多國語言（i18n）

作者: F1T Team
日期: 2025-10-08 (百分比模式更新)
版本: 1.1.0
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
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

# 匯入多國語言支援
from core.gui_i18n import tr
from modules.gui.themes import color_palette_provider


class ThrottleBoxPlotChartWidget(QWidget):
    """全油門秒數箱型圖圖表組件 (純 PyQt5 QPainter 實現)"""

    DEFAULT_COLOR = QColor(128, 128, 128)

    chart_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.driver_throttle_durations: Dict[str, List[float]] = {}
        self.statistics: Dict[str, Dict[str, float]] = {}
        self.current_data: Optional[Dict] = None

        self.margin_left = 60
        self.margin_right = 30
        self.margin_top = 50
        self.margin_bottom = 80

        self.chart_rect = QRect()

        self.hover_driver: Optional[str] = None
        self.hover_position: Optional[QPoint] = None

        self.y_min = 0.0
        self.y_max = 100.0

        self.setMouseTracking(True)
        self.setMinimumSize(200, 100)

        print("[THROTTLE_CHART] 圖表組件初始化完成 (QPainter 版本)")

    def update_data(self, data: Dict[str, Any]):
        """更新圖表數據並重新繪製"""
        try:
            if not data or not isinstance(data, dict):
                print("[WARNING] [THROTTLE_CHART] 無效的數據格式")
                return

            self.current_data = data
            self.driver_throttle_durations = data.get("driver_throttle_durations", {}) or {}
            self.statistics = data.get("statistics", {}) or {}
            self._ensure_palette_for_data(data)

            if not self.driver_throttle_durations:
                print("[WARNING] [THROTTLE_CHART] 沒有油門數據")
                self.update()
                return

            self._calculate_y_range()
            print(f"[THROTTLE_CHART] 更新數據: {len(self.driver_throttle_durations)} 位車手")
            self.update()

        except Exception as exc:
            print(f"[ERROR] [THROTTLE_CHART] 更新數據失敗: {exc}")
            import traceback

            traceback.print_exc()

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
            target_year = metadata.get("season_year") or metadata.get("year")

        try:
            if target_year is not None:
                color_palette_provider.ensure_loaded(year=int(target_year))
            else:
                color_palette_provider.ensure_loaded()
        except Exception:
            pass

    def _driver_color(self, driver: str) -> QColor:
        """Return the colour for the given driver code."""
        color = color_palette_provider.get_driver_color(driver, format="qcolor")
        if isinstance(color, QColor):
            return QColor(color)
        return QColor(self.DEFAULT_COLOR)

    def _calculate_y_range(self):
        if not self.driver_throttle_durations:
            self.y_min = 0.0
            self.y_max = 100.0
            return

        all_values: List[float] = []
        for durations in self.driver_throttle_durations.values():
            all_values.extend(durations)

        if all_values:
            self.y_min = min(all_values)
            self.y_max = max(all_values)
            padding = (self.y_max - self.y_min) * 0.05 if self.y_max != self.y_min else 1.0
            if padding <= 0:
                padding = 1.0
            self.y_min -= padding
            self.y_max += padding
        else:
            self.y_min = 0.0
            self.y_max = 100.0

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            self.chart_rect = QRect(
                self.margin_left,
                self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom,
            )

            self._draw_background(painter)
            self._draw_grid(painter)
            self._draw_axes(painter)
            self._draw_axis_labels(painter)

            if self.driver_throttle_durations:
                self._draw_box_plots(painter)
            else:
                self._draw_no_data_message(painter)

            if self.hover_driver:
                self._draw_tooltip(painter)
        finally:
            # 🔑 關鍵修復：確保 painter 總是被正確結束
            painter.end()

    def _draw_background(self, painter: QPainter):
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        painter.fillRect(self.chart_rect, QColor(255, 255, 255))

    def _draw_grid(self, painter: QPainter):
        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
        num_y_lines = 8
        for i in range(num_y_lines + 1):
            y = self.chart_rect.top() + (self.chart_rect.height() * i / num_y_lines)
            painter.drawLine(self.chart_rect.left(), int(y), self.chart_rect.right(), int(y))

    def _draw_axes(self, painter: QPainter):
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawLine(self.chart_rect.bottomLeft(), self.chart_rect.bottomRight())
        painter.drawLine(self.chart_rect.bottomLeft(), self.chart_rect.topLeft())

    def _draw_axis_labels(self, painter: QPainter):
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(QColor(70, 70, 70)))

        num_y_labels = 8
        for i in range(num_y_labels + 1):
            y_pos = self.chart_rect.top() + (self.chart_rect.height() * i / num_y_labels)
            value = self.y_max - ((self.y_max - self.y_min) * i / num_y_labels)
            # 🔄 百分比模式：顯示百分比符號
            label = f"{value:.1f}%"
            painter.drawText(
                QRect(5, int(y_pos) - 10, self.margin_left - 10, 20),
                Qt.AlignRight | Qt.AlignVCenter,
                label,
            )

        painter.save()
        painter.translate(5, self.chart_rect.center().y())
        painter.rotate(-90)
        title_font = QFont()
        title_font.setPointSize(8)
        painter.setFont(title_font)
        painter.drawText(
            QRect(-120, -10, 240, 20),
            Qt.AlignCenter,
            # 🔄 百分比模式：修改 Y 軸標題
            tr("throttle_box_plot.y_axis_title", "Full Throttle Duration (%)"),
        )
        painter.restore()

    def _draw_box_plots(self, painter: QPainter):
        if not self.driver_throttle_durations:
            return

        drivers = sorted(self.driver_throttle_durations.keys())
        n_drivers = len(drivers)
        if n_drivers == 0:
            return

        box_spacing = self.chart_rect.width() / (n_drivers + 1)
        box_width = min(40, box_spacing * 0.6)

        for idx, driver in enumerate(drivers):
            durations = self.driver_throttle_durations.get(driver)
            if not durations:
                continue
            x_center = self.chart_rect.left() + (idx + 1) * box_spacing
            self._draw_single_box_plot(painter, driver, durations, x_center, box_width)

    def _draw_single_box_plot(
        self,
        painter: QPainter,
        driver: str,
        durations: List[float],
        x_center: float,
        box_width: float,
    ):
        try:
            durations_array = np.array(durations)
            q1 = np.percentile(durations_array, 25)
            median = np.percentile(durations_array, 50)
            q3 = np.percentile(durations_array, 75)
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            whisker_data = durations_array[(durations_array >= lower_bound) & (durations_array <= upper_bound)]
            if len(whisker_data) > 0:
                whisker_min = whisker_data.min()
                whisker_max = whisker_data.max()
            else:
                whisker_min = q1
                whisker_max = q3

            outliers = durations_array[(durations_array < lower_bound) | (durations_array > upper_bound)]

            def duration_to_y(value: float) -> float:
                if self.y_max == self.y_min:
                    return self.chart_rect.center().y()
                ratio = (value - self.y_min) / (self.y_max - self.y_min)
                return self.chart_rect.bottom() - (ratio * self.chart_rect.height())

            team_color = self._driver_color(driver)
            is_hovered = driver == self.hover_driver

            box_rect = QRectF(
                x_center - box_width / 2,
                duration_to_y(q3),
                box_width,
                duration_to_y(q1) - duration_to_y(q3),
            )

            fill_color = team_color if not is_hovered else team_color.darker(110)
            fill_color.setAlpha(180)

            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(Qt.black, 2 if is_hovered else 1.5))
            painter.drawRect(box_rect)

            painter.setPen(QPen(Qt.black, 3))
            painter.drawLine(
                QPoint(int(x_center - box_width / 2), int(duration_to_y(median))),
                QPoint(int(x_center + box_width / 2), int(duration_to_y(median))),
            )

            painter.setPen(QPen(Qt.black, 1.5, Qt.SolidLine))
            painter.drawLine(QPoint(int(x_center), int(duration_to_y(q3))), QPoint(int(x_center), int(duration_to_y(whisker_max))))
            painter.drawLine(QPoint(int(x_center), int(duration_to_y(q1))), QPoint(int(x_center), int(duration_to_y(whisker_min))))

            painter.drawLine(
                QPoint(int(x_center - box_width / 3), int(duration_to_y(whisker_max))),
                QPoint(int(x_center + box_width / 3), int(duration_to_y(whisker_max))),
            )
            painter.drawLine(
                QPoint(int(x_center - box_width / 3), int(duration_to_y(whisker_min))),
                QPoint(int(x_center + box_width / 3), int(duration_to_y(whisker_min))),
            )

            painter.setPen(QPen(Qt.black, 5))
            for outlier in outliers:
                y = duration_to_y(outlier)
                painter.drawPoint(QPoint(int(x_center), int(y)))

            label_font = QFont("Arial", 8)
            painter.setFont(label_font)
            painter.setPen(QPen(Qt.black))
            painter.drawText(
                QRectF(x_center - box_width, self.chart_rect.bottom() + 10, box_width * 2, 20),
                Qt.AlignCenter,
                driver,
            )

        except Exception as exc:
            print(f"[ERROR] [THROTTLE_CHART] 繪製箱型圖失敗: {exc}")
            import traceback

            traceback.print_exc()

    def _draw_no_data_message(self, painter: QPainter):
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(
            self.chart_rect,
            Qt.AlignCenter,
            tr("throttle_box_plot.no_data", "No throttle data available"),
        )

    def _draw_tooltip(self, painter: QPainter):
        if not self.hover_driver or not self.hover_position:
            return

        stats = self.statistics.get(self.hover_driver, {})
        if not stats:
            return

        tooltip_lines = [
            f"{tr('driver', 'Driver')}: {self.hover_driver}",
            # 🔄 百分比模式：統計數據顯示百分比
            f"{tr('throttle_box_plot.stat_min', 'Min')}: {stats.get('min', 0):.1f}%",
            f"{tr('throttle_box_plot.stat_q1', 'Q1')}: {stats.get('q1', 0):.1f}%",
            f"{tr('throttle_box_plot.stat_median', 'Median')}: {stats.get('median', 0):.1f}%",
            f"{tr('throttle_box_plot.stat_q3', 'Q3')}: {stats.get('q3', 0):.1f}%",
            f"{tr('throttle_box_plot.stat_max', 'Max')}: {stats.get('max', 0):.1f}%",
            f"{tr('throttle_box_plot.stat_mean', 'Mean')}: {stats.get('mean', 0):.1f}%",
            f"{tr('throttle_box_plot.stat_count', 'Samples')}: {stats.get('count', 0)}",
        ]
        tooltip_text = "\n".join(tooltip_lines)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont("Arial", 9)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        text_width = max(metrics.width(line) for line in tooltip_lines) + 16
        text_height = (metrics.height() * len(tooltip_lines)) + 12

        x = self.hover_position.x() + 12
        y = self.hover_position.y() - text_height - 12
        if x + text_width > self.width():
            x = self.hover_position.x() - text_width - 12
        if y < 0:
            y = self.hover_position.y() + 12

        # 使用 QRectF 而不是 QRect 以支援 addRoundedRect
        tooltip_rect = QRectF(float(x), float(y), float(text_width), float(text_height))
        path = QPainterPath()
        path.addRoundedRect(tooltip_rect, 8, 8)

        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawPath(path)

        painter.setPen(QPen(QColor(30, 30, 30)))
        painter.drawText(tooltip_rect, Qt.AlignLeft | Qt.AlignVCenter, tooltip_text)
        painter.restore()

    def mouseMoveEvent(self, event: QMouseEvent):
        position = event.pos()
        previous_driver = self.hover_driver

        hovered_driver = self._detect_hovered_driver(position)
        if hovered_driver != previous_driver:
            self.hover_driver = hovered_driver
            self.hover_position = position if hovered_driver else None
            self.update()
        else:
            self.hover_position = position if hovered_driver else None

    def leaveEvent(self, event):
        self.hover_driver = None
        self.hover_position = None
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return

        driver = self._detect_hovered_driver(event.pos())
        if driver:
            self.chart_clicked.emit(driver)

    def _detect_hovered_driver(self, position: QPoint) -> Optional[str]:
        if not self.driver_throttle_durations:
            return None

        drivers = sorted(self.driver_throttle_durations.keys())
        if not drivers:
            return None

        box_spacing = self.chart_rect.width() / (len(drivers) + 1)
        box_width = min(40, box_spacing * 0.6)

        for idx, driver in enumerate(drivers):
            x_center = self.chart_rect.left() + (idx + 1) * box_spacing
            rect = QRectF(
                x_center - box_width / 2,
                self.chart_rect.top(),
                box_width,
                self.chart_rect.height(),
            )
            if rect.contains(position):
                return driver
        return None

    def export_chart(self, file_path: str) -> bool:
        try:
            export_image = QImage(self.size(), QImage.Format_ARGB32)
            export_image.fill(Qt.transparent)

            painter = QPainterForExport(export_image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            self.paint(painter)
            painter.end()

            if export_image.save(file_path):
                return True

            raise RuntimeError("Failed to save image")
        except Exception as exc:
            print(f"[ERROR] [THROTTLE_CHART] 匯出圖表失敗: {exc}")
            QMessageBox.critical(
                self,
                tr("throttle_box_plot.export_failed_title", "Export Failed"),
                tr(
                    "throttle_box_plot.export_failed_body",
                    "Unable to export chart. Please try another file name or location.",
                ),
            )
            return False
