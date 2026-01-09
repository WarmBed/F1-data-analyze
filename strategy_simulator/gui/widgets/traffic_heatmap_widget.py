#!/usr/bin/env python3
"""
TrafficHeatmapWidget - 完整賽事 Traffic 熱力圖組件

功能：
- 使用 PyQt5 QPainter 繪製熱力圖（類似主 GUI Traffic Timeline）
- 顯示所有車手每一圈的 traffic 狀態
- 綠色=Clean（無阻擋）、橙色=Traffic（gap < 1.5s）、灰色=SC/VSC
- 支援滑鼠懸停顯示詳細資訊
- 支援圖表匯出

Author: F1T Team
Date: 2025-10-11
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QRect, QPoint, QRectF
from PyQt5.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
    QFont,
    QFontMetrics,
    QPainterPath,
)

from core.logger import get_logger

logger = get_logger("strategy_simulator.traffic_heatmap", component="gui")


# 狀態顏色定義
STATUS_COLORS = {
    "clean": QColor("#4CAF50"),      # 綠色 - 無阻擋
    "traffic": QColor("#FF9800"),    # 橙色 - 受阻擋 (gap < 1.5s)
    "sc_vsc": QColor("#9E9E9E"),     # 灰色 - SC/VSC
    "no_data": QColor("#E0E0E0"),    # 淺灰 - 無數據
}


class TrafficHeatmapWidget(QWidget):
    """完整賽事 Traffic 熱力圖組件（純 PyQt5 QPainter 實現）"""

    DEFAULT_COLOR = QColor(128, 128, 128)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 數據
        self._drivers_data: List[Dict[str, Any]] = []
        self._max_lap: int = 0
        self._race_info: str = ""

        # 佈局邊距
        self.margin_left = 100
        self.margin_right = 20
        self.margin_top = 25
        self.margin_bottom = 40

        # Cell 尺寸（動態計算）
        self.cell_width = 10
        self.cell_height = 18
        self.cell_gap = 1

        # 圖表區域
        self.chart_rect = QRect()

        # 互動
        self.hover_driver: Optional[str] = None
        self.hover_lap: Optional[int] = None
        self.hover_position: Optional[QPoint] = None

        self.setMouseTracking(True)
        self.setMinimumSize(600, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        logger.info("[TRAFFIC_HEATMAP] Widget initialized")

    def update_data(self, drivers_data: List[Dict[str, Any]], max_lap: int, race_info: str = ""):
        """
        更新熱力圖數據
        
        Args:
            drivers_data: 車手數據列表，格式：
                [
                    {
                        "driver_code": "VER",
                        "final_position": 1,
                        "lap_states": {1: 0, 2: 1, 3: 2, ...},  # lap -> state (0=clean, 1=traffic, 2=sc_vsc, -1=no_data)
                        "traffic_stats": {
                            "blocked_laps": 5,
                            "clean_laps": 50,
                            "sc_vsc_laps": 3
                        }
                    },
                    ...
                ]
            max_lap: 最大圈數
            race_info: 賽事資訊（如 "2025 Japan R"）
        """
        try:
            if not drivers_data:
                logger.warning("[TRAFFIC_HEATMAP] Empty drivers data")
                return

            self._drivers_data = drivers_data
            self._max_lap = max_lap
            self._race_info = race_info

            # 按最終位置排序（P1 在最上方）
            self._drivers_data.sort(key=lambda x: x.get("final_position", 99))

            self._update_size()
            logger.info(f"[TRAFFIC_HEATMAP] Data updated: {len(drivers_data)} drivers, {max_lap} laps")
            self.update()

        except Exception as exc:
            logger.exception("[TRAFFIC_HEATMAP] Failed to update data")

    def _update_size(self):
        """根據數據更新組件最小尺寸"""
        if not self._drivers_data or self._max_lap == 0:
            return

        min_width = max(600, self.margin_left + self._max_lap * 8 + self.margin_right)
        min_height = max(300, self.margin_top + len(self._drivers_data) * 16 + self.margin_bottom)
        self.setMinimumSize(min_width, min_height)

    def _calculate_cell_dimensions(self):
        """動態計算 cell 尺寸以填滿可用空間"""
        if not self._drivers_data or self._max_lap == 0:
            return
        
        available_width = self.chart_rect.width()
        available_height = self.chart_rect.height() - 30  # 減去 legend 高度
        
        # 根據圈數和車手數量計算 cell 大小
        self.cell_width = max(6, (available_width - self._max_lap * self.cell_gap) // self._max_lap)
        num_drivers = len(self._drivers_data)
        self.cell_height = max(12, (available_height - num_drivers * self.cell_gap) // num_drivers)
        
        # 限制最大尺寸
        self.cell_width = min(self.cell_width, 20)
        self.cell_height = min(self.cell_height, 28)

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
            
            self._calculate_cell_dimensions()

            self._draw_background(painter)

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
        """繪製背景"""
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        painter.fillRect(self.chart_rect, QColor(255, 255, 255))

    def _draw_lap_axis(self, painter: QPainter):
        """繪製頂部圈數軸"""
        axis_font = QFont()
        axis_font.setPointSize(7)
        painter.setFont(axis_font)
        painter.setPen(QPen(QColor(100, 100, 100)))

        # 每 5 圈顯示一次圈數
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
        """繪製所有車手的時間線"""
        for idx, driver_data in enumerate(self._drivers_data):
            y = self.margin_top + idx * (self.cell_height + self.cell_gap)
            self._draw_driver_row(painter, driver_data, y, idx)

    def _draw_driver_row(self, painter: QPainter, driver_data: Dict, y: int, idx: int):
        """繪製單個車手的時間線行"""
        driver_code = driver_data.get("driver_code", "???")
        final_pos = driver_data.get("final_position", 0)
        lap_states = driver_data.get("lap_states", {})
        traffic_stats = driver_data.get("traffic_stats", {})

        blocked_laps = traffic_stats.get("blocked_laps", 0)
        clean_laps = traffic_stats.get("clean_laps", 0)
        sc_vsc_laps = traffic_stats.get("sc_vsc_laps", 0)
        total_analyzed = blocked_laps + clean_laps + sc_vsc_laps

        is_hovered_row = self.hover_driver == driver_code

        # ===== 繪製車手標籤 =====
        label_font = QFont()
        label_font.setPointSize(8)
        label_font.setBold(is_hovered_row)
        painter.setFont(label_font)
        fm = QFontMetrics(label_font)

        # 標籤文字（包含統計）
        label_text = f"P{final_pos} {driver_code} ({blocked_laps}/{total_analyzed})"

        # 標籤背景
        label_width = fm.horizontalAdvance(label_text) + 12
        label_rect = QRectF(5, y, min(label_width, self.margin_left - 10), self.cell_height)

        # 根據最終位置決定背景顏色
        if final_pos <= 3:
            bg_color = QColor("#FFD700") if final_pos == 1 else QColor("#C0C0C0") if final_pos == 2 else QColor("#CD7F32")
        else:
            bg_color = QColor("#B0B0B0")
        
        bg_color.setAlpha(180 if is_hovered_row else 140)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))

        path = QPainterPath()
        path.addRoundedRect(label_rect, 3, 3)
        painter.drawPath(path)

        # 計算文字顏色
        luminance = 0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()
        text_color = QColor(0, 0, 0) if luminance > 128 else QColor(255, 255, 255)

        painter.setPen(text_color)
        painter.drawText(
            QRect(8, y, int(self.margin_left - 15), self.cell_height),
            Qt.AlignLeft | Qt.AlignVCenter,
            label_text
        )

        # ===== 繪製圈數 cells =====
        for lap in range(1, self._max_lap + 1):
            x = self.margin_left + (lap - 1) * (self.cell_width + self.cell_gap)

            # 獲取狀態
            state = lap_states.get(lap, -1)  # -1 = 無數據

            # 決定 cell 顏色
            if state == 0:
                cell_color = STATUS_COLORS["clean"]
            elif state == 1:
                cell_color = STATUS_COLORS["traffic"]
            elif state == 2:
                cell_color = STATUS_COLORS["sc_vsc"]
            else:
                cell_color = STATUS_COLORS["no_data"]

            # 檢查是否懸停
            is_hovered_cell = (self.hover_driver == driver_code and self.hover_lap == lap)

            if is_hovered_cell:
                cell_color = cell_color.lighter(120)

            # 繪製 cell
            cell_rect = QRectF(x, y, self.cell_width, self.cell_height)

            painter.setPen(QPen(QColor(200, 200, 200), 0.5))
            painter.setBrush(QBrush(cell_color))

            path = QPainterPath()
            path.addRoundedRect(cell_rect, 2, 2)
            painter.drawPath(path)

    def _draw_legend(self, painter: QPainter):
        """繪製底部圖例"""
        legend_y = self.height() - 25
        legend_x = self.margin_left

        legend_items = [
            ("Clean Lap", STATUS_COLORS["clean"]),
            ("In Traffic (<1.5s)", STATUS_COLORS["traffic"]),
            ("SC/VSC", STATUS_COLORS["sc_vsc"]),
            ("No Data", STATUS_COLORS["no_data"]),
        ]

        legend_font = QFont()
        legend_font.setPointSize(8)
        painter.setFont(legend_font)

        for label, color in legend_items:
            # 顏色方塊
            box_rect = QRectF(legend_x, legend_y, 12, 12)
            painter.setPen(QPen(QColor(180, 180, 180), 1))
            painter.setBrush(QBrush(color))
            path = QPainterPath()
            path.addRoundedRect(box_rect, 2, 2)
            painter.drawPath(path)

            # 標籤
            painter.setPen(QPen(QColor(80, 80, 80)))
            fm = QFontMetrics(legend_font)
            label_width = fm.horizontalAdvance(label)
            painter.drawText(
                QRect(int(legend_x + 16), int(legend_y - 1), label_width + 10, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                label
            )

            legend_x += label_width + 40

    def _draw_tooltip(self, painter: QPainter):
        """繪製懸停提示"""
        if not self.hover_driver or not self.hover_position:
            return

        # 查找車手數據
        driver_data = next((d for d in self._drivers_data if d.get("driver_code") == self.hover_driver), None)
        if not driver_data:
            return

        lap_states = driver_data.get("lap_states", {})
        state = lap_states.get(self.hover_lap, -1) if self.hover_lap else -1

        # 狀態描述
        state_text = {
            0: "Clean Lap",
            1: "In Traffic (gap < 1.5s)",
            2: "SC/VSC",
            -1: "No Data"
        }.get(state, "Unknown")

        # 構建提示文字
        lines = [
            f"Driver: {self.hover_driver}",
            f"Lap: {self.hover_lap}",
            f"Status: {state_text}",
            f"Final Position: P{driver_data.get('final_position', '?')}"
        ]

        # 繪製提示框
        tooltip_font = QFont()
        tooltip_font.setPointSize(8)
        painter.setFont(tooltip_font)
        fm = QFontMetrics(tooltip_font)

        max_width = max(fm.horizontalAdvance(line) for line in lines) + 16
        tooltip_height = len(lines) * 16 + 8

        # 計算位置
        tooltip_x = self.hover_position.x() + 10
        tooltip_y = self.hover_position.y() + 10

        # 防止超出邊界
        if tooltip_x + max_width > self.width():
            tooltip_x = self.hover_position.x() - max_width - 10
        if tooltip_y + tooltip_height > self.height():
            tooltip_y = self.hover_position.y() - tooltip_height - 10

        tooltip_rect = QRectF(tooltip_x, tooltip_y, max_width, tooltip_height)

        # 繪製背景
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(QColor(255, 255, 220, 230)))
        path = QPainterPath()
        path.addRoundedRect(tooltip_rect, 4, 4)
        painter.drawPath(path)

        # 繪製文字
        painter.setPen(QPen(QColor(30, 30, 30)))
        text_y = tooltip_y + 12
        for line in lines:
            painter.drawText(
                QRect(int(tooltip_x + 8), int(text_y), max_width - 16, 16),
                Qt.AlignLeft | Qt.AlignVCenter,
                line
            )
            text_y += 16

    def _draw_no_data_message(self, painter: QPainter):
        """繪製無數據訊息"""
        painter.setPen(QPen(QColor(150, 150, 150)))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(
            self.chart_rect,
            Qt.AlignCenter,
            "No traffic data available"
        )

    def mouseMoveEvent(self, event):
        """處理滑鼠移動事件"""
        pos = event.pos()

        if not self.chart_rect.contains(pos) or not self._drivers_data:
            if self.hover_driver or self.hover_lap:
                self.hover_driver = None
                self.hover_lap = None
                self.hover_position = None
                self.update()
            return

        # 計算懸停的車手和圈數
        relative_x = pos.x() - self.margin_left
        relative_y = pos.y() - self.margin_top

        lap_index = relative_x // (self.cell_width + self.cell_gap)
        driver_index = relative_y // (self.cell_height + self.cell_gap)

        hover_lap = lap_index + 1 if 0 <= lap_index < self._max_lap else None
        hover_driver = self._drivers_data[driver_index].get("driver_code") if 0 <= driver_index < len(self._drivers_data) else None

        if hover_lap != self.hover_lap or hover_driver != self.hover_driver:
            self.hover_lap = hover_lap
            self.hover_driver = hover_driver
            self.hover_position = pos
            self.update()

    def leaveEvent(self, event):
        """處理滑鼠離開事件"""
        if self.hover_driver or self.hover_lap:
            self.hover_driver = None
            self.hover_lap = None
            self.hover_position = None
            self.update()
