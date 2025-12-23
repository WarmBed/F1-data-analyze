#!/usr/bin/env python3
"""
Traffic Timeline DEMO (Pure PyQt5 QPainter Style)
==================================================

獨立 DEMO：用純 PyQt5 QPainter 繪製 Tire Strategy 風格的 traffic 時間線視覺化。

執行方式：
    python demo_traffic_timeline.py

預設載入：json/live_timing_traffic_distance_2025_Abu_Dhabi_R.json

Author: F1T Team
Date: 2025-12-23
Version: 2.0.0 - Pure QPainter Implementation
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 確保專案根目錄在 Python path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QRect, QPoint, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QFontMetrics,
    QMouseEvent, QPainterPath, QLinearGradient
)

# 嘗試載入專案的 color_palette_provider
try:
    from modules.gui.themes import color_palette_provider
    HAS_PALETTE = True
except ImportError:
    HAS_PALETTE = False

# F1 Team Colors (2024-2025) - Fallback
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Red Bull": "#3671C6",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Kick Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
    "Haas": "#B6BABD",
}

# Status Colors (Dark Theme)
STATUS_COLORS = {
    "clean": QColor("#4CAF50"),      # Green
    "traffic": QColor("#FFD700"),    # Yellow/Gold
    "excluded": QColor("#555555"),   # Gray
    "no_data": QColor("#2a2a2a"),    # Dark gray
}


class TrafficTimelineChartWidget(QWidget):
    """Traffic Timeline 純 PyQt5 QPainter 圖表組件"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data
        self._data: Dict[str, Any] = {}
        self._drivers_data: List[Dict[str, Any]] = []
        self._max_lap: int = 0
        self._metadata: Dict[str, Any] = {}

        # Layout margins
        self.margin_left = 120
        self.margin_right = 30
        self.margin_top = 60
        self.margin_bottom = 50

        # Cell dimensions
        self.cell_width = 12
        self.cell_height = 22
        self.cell_gap = 2

        # Interaction
        self.hover_driver: Optional[str] = None
        self.hover_lap: Optional[int] = None
        self.hover_position: Optional[QPoint] = None

        self.setMouseTracking(True)
        self.setMinimumSize(400, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def load_from_file(self, file_path: Path) -> bool:
        try:
            if not file_path.exists():
                return False

            with file_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            self._parse_data(payload)
            self._update_size()
            self.update()
            return True

        except Exception as e:
            print(f"[ERROR] Load failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _parse_data(self, root: Dict[str, Any]):
        data = root.get("data") or {}
        self._metadata = data.get("metadata") or {}
        drivers = data.get("drivers") or {}

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
        """Update widget size based on data"""
        if not self._drivers_data or self._max_lap == 0:
            return

        width = self.margin_left + self._max_lap * (self.cell_width + self.cell_gap) + self.margin_right
        height = self.margin_top + len(self._drivers_data) * (self.cell_height + self.cell_gap) + self.margin_bottom
        self.setMinimumSize(max(800, width), max(400, height))

    def _get_team_color(self, team: str, driver: str = "") -> QColor:
        """Get team color from palette or fallback"""
        if HAS_PALETTE and driver:
            try:
                color = color_palette_provider.get_driver_color(driver, format="qcolor")
                if isinstance(color, QColor):
                    return QColor(color)
            except Exception:
                pass

        hex_color = TEAM_COLORS.get(team, "#888888")
        return QColor(hex_color)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            self._draw_background(painter)
            self._draw_title(painter)

            if self._drivers_data and self._max_lap > 0:
                self._draw_lap_axis(painter)
                self._draw_timeline(painter)
                self._draw_legend(painter)

                if self.hover_driver and self.hover_position:
                    self._draw_tooltip(painter)
            else:
                self._draw_no_data(painter)
        finally:
            painter.end()

    def _draw_background(self, painter: QPainter):
        """Draw dark background with gradient"""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#1e1e1e"))
        gradient.setColorAt(1, QColor("#141414"))
        painter.fillRect(self.rect(), gradient)

    def _draw_title(self, painter: QPainter):
        """Draw title and metadata"""
        # Title
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor("#FFFFFF")))

        year = self._metadata.get("year", "")
        race = self._metadata.get("race", "")
        session = self._metadata.get("session", "")

        title = f"Traffic Timeline - {year} {race} {session}"
        painter.drawText(QRect(self.margin_left, 10, self.width() - self.margin_left - self.margin_right, 30),
                         Qt.AlignLeft | Qt.AlignVCenter, title)

        # Subtitle
        subtitle_font = QFont("Segoe UI", 9)
        painter.setFont(subtitle_font)
        painter.setPen(QPen(QColor("#888888")))
        subtitle = f"{len(self._drivers_data)} drivers | {self._max_lap} laps"
        painter.drawText(QRect(self.margin_left, 32, self.width() - self.margin_left - self.margin_right, 20),
                         Qt.AlignLeft | Qt.AlignVCenter, subtitle)

    def _draw_lap_axis(self, painter: QPainter):
        """Draw lap number axis"""
        axis_font = QFont("Segoe UI", 8)
        painter.setFont(axis_font)
        painter.setPen(QPen(QColor("#666666")))

        # Draw lap numbers (every 5 laps)
        for lap in range(1, self._max_lap + 1):
            if lap == 1 or lap % 5 == 0 or lap == self._max_lap:
                x = self.margin_left + (lap - 1) * (self.cell_width + self.cell_gap) + self.cell_width // 2
                y = self.margin_top - 5

                painter.drawText(QRect(x - 15, y - 15, 30, 15),
                                 Qt.AlignCenter, str(lap))

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
        time_ratio = driver_data["time_in_traffic_ratio"]

        # Get team color
        team_color = self._get_team_color(team, driver_tla)
        is_hovered_row = self.hover_driver == driver_tla

        # ===== Draw driver label with team color background =====
        label_font = QFont("Segoe UI", 9, QFont.Bold if is_hovered_row else QFont.Normal)
        painter.setFont(label_font)
        fm = QFontMetrics(label_font)

        # Driver label text
        label_text = f"{driver_tla}"
        stats_text = f"({laps_in_traffic}/{laps_analyzed})"

        # Background for driver label
        label_rect = QRectF(8, y, self.margin_left - 16, self.cell_height)

        # Draw rounded background
        bg_color = QColor(team_color)
        bg_color.setAlpha(180 if is_hovered_row else 140)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))

        path = QPainterPath()
        path.addRoundedRect(label_rect, 4, 4)
        painter.drawPath(path)

        # Calculate text color based on luminance
        luminance = 0.299 * team_color.red() + 0.587 * team_color.green() + 0.114 * team_color.blue()
        text_color = QColor("#000000") if luminance > 128 else QColor("#FFFFFF")

        painter.setPen(text_color)
        painter.drawText(QRect(12, y, 40, self.cell_height),
                         Qt.AlignLeft | Qt.AlignVCenter, label_text)

        # Draw stats in lighter color
        stats_color = QColor(text_color)
        stats_color.setAlpha(180)
        painter.setPen(stats_color)
        stats_font = QFont("Segoe UI", 8)
        painter.setFont(stats_font)
        painter.drawText(QRect(50, y, self.margin_left - 60, self.cell_height),
                         Qt.AlignLeft | Qt.AlignVCenter, stats_text)

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

            # Draw cell with rounded corners
            cell_rect = QRectF(x, y, self.cell_width, self.cell_height)

            # Brighten if hovered
            if is_hovered_cell:
                cell_color = cell_color.lighter(130)

            painter.setPen(QPen(QColor("#333333"), 0.5))
            painter.setBrush(QBrush(cell_color))

            path = QPainterPath()
            path.addRoundedRect(cell_rect, 2, 2)
            painter.drawPath(path)

    def _draw_legend(self, painter: QPainter):
        """Draw legend at bottom"""
        legend_y = self.height() - 30
        legend_x = self.margin_left

        legend_items = [
            ("Clean Lap", STATUS_COLORS["clean"]),
            ("In Traffic", STATUS_COLORS["traffic"]),
            ("SC/VSC Excluded", STATUS_COLORS["excluded"]),
            ("No Data / DNF", STATUS_COLORS["no_data"]),
        ]

        legend_font = QFont("Segoe UI", 9)
        painter.setFont(legend_font)

        for label, color in legend_items:
            # Color box
            box_rect = QRectF(legend_x, legend_y, 14, 14)
            painter.setPen(QPen(QColor("#444444"), 1))
            painter.setBrush(QBrush(color))
            path = QPainterPath()
            path.addRoundedRect(box_rect, 2, 2)
            painter.drawPath(path)

            # Label
            painter.setPen(QPen(QColor("#CCCCCC")))
            painter.drawText(QRect(int(legend_x + 20), int(legend_y - 2), 120, 20),
                             Qt.AlignLeft | Qt.AlignVCenter, label)

            legend_x += 130

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
            f"Driver: {self.hover_driver}",
            f"Team: {driver_data['team']}",
        ]

        if self.hover_lap:
            state = driver_data["lap_states"].get(self.hover_lap, -1)
            state_text = {0: "Clean Lap", 1: "In Traffic", 2: "SC/VSC Excluded", -1: "No Data"}
            lines.append(f"Lap {self.hover_lap}: {state_text.get(state, 'Unknown')}")

        lines.append(f"Traffic Laps: {driver_data['laps_in_traffic']}/{driver_data['laps_analyzed']}")
        lines.append(f"Traffic Ratio: {driver_data['time_in_traffic_ratio']*100:.1f}%")

        # Calculate tooltip size
        tooltip_font = QFont("Segoe UI", 9)
        painter.setFont(tooltip_font)
        fm = QFontMetrics(tooltip_font)

        max_width = max(fm.horizontalAdvance(line) for line in lines) + 20
        total_height = len(lines) * fm.height() + 16

        # Position tooltip
        x = self.hover_position.x() + 15
        y = self.hover_position.y() - total_height - 10

        if x + max_width > self.width():
            x = self.hover_position.x() - max_width - 15
        if y < 0:
            y = self.hover_position.y() + 20

        # Draw tooltip background
        tooltip_rect = QRectF(x, y, max_width, total_height)
        painter.setPen(QPen(QColor("#444444"), 1))
        bg_color = QColor("#2a2a2a")
        bg_color.setAlpha(245)
        painter.setBrush(QBrush(bg_color))

        path = QPainterPath()
        path.addRoundedRect(tooltip_rect, 6, 6)
        painter.drawPath(path)

        # Draw tooltip text
        painter.setPen(QPen(QColor("#EEEEEE")))
        text_y = y + 10
        for line in lines:
            painter.drawText(QRect(int(x + 10), int(text_y), int(max_width - 20), fm.height()),
                             Qt.AlignLeft | Qt.AlignVCenter, line)
            text_y += fm.height()

    def _draw_no_data(self, painter: QPainter):
        """Draw no data message"""
        painter.setPen(QPen(QColor("#666666")))
        font = QFont("Segoe UI", 12, QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "No traffic data loaded")

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


class DemoTimelineWindow(QMainWindow):
    """Traffic Timeline DEMO 主視窗"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traffic Timeline DEMO (F127) - Pure PyQt5 Style")
        self.setMinimumSize(1200, 700)

        # 中央 Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for timeline
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666666;
            }
            QScrollBar:horizontal {
                background: #2a2a2a;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #555555;
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #666666;
            }
        """)

        # Timeline Widget
        self._widget = TrafficTimelineChartWidget()
        scroll.setWidget(self._widget)
        layout.addWidget(scroll)

        # 設置深色背景
        self.setStyleSheet("QMainWindow { background-color: #1e1e1e; }")

        # 載入預設 JSON
        self._load_default_json()

    def _load_default_json(self):
        default_file = PROJECT_ROOT / "json" / "live_timing_traffic_distance_2025_Abu_Dhabi_R.json"
        if default_file.exists():
            self._widget.load_from_file(default_file)
            print(f"[DEMO] Loaded: {default_file}")
        else:
            print(f"[DEMO] File not found: {default_file}")
            print("[DEMO] Run CLI first: python f1_analysis_modular_main.py -f 127 -y 2025 -r Abu_Dhabi -s R")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set dark palette
    from PyQt5.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1e1e1e"))
    palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Base, QColor("#252525"))
    palette.setColor(QPalette.AlternateBase, QColor("#2a2a2a"))
    palette.setColor(QPalette.Text, QColor("#FFFFFF"))
    palette.setColor(QPalette.Button, QColor("#333333"))
    palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
    app.setPalette(palette)

    window = DemoTimelineWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
