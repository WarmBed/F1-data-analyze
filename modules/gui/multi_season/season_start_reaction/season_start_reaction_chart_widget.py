#!/usr/bin/env python3
"""
SeasonStartReactionChartWidget - 年度起跑反應 0-50km/h 箱型圖 (純 PyQt5 實現)

功能：
- 使用 PyQt5 QPainter 繪製箱型圖 + 散點圖
- 顯示所有車手的 0-50km/h 加速時間分布
- 應用車隊配色方案 (使用 color_palette_provider)
- 顯示統計資訊（中位數、Q1、Q3、鬚線）
- 滑鼠懸停顯示詳細資訊
- 支援多國語言（i18n）

作者: F1T Team
日期: 2025-12-22
版本: 2.0.0
"""

from typing import Dict, List, Any, Optional
import numpy as np
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QCursor,
)

from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.themes import color_palette_provider

logger = get_logger(__name__)


class SeasonStartReactionChartWidget(QWidget):
    """年度起跑反應 0-50km/h 箱型圖 (純 PyQt5 QPainter 實現)"""

    DEFAULT_COLOR = QColor(128, 128, 128)
    chart_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 數據存儲
        self.driver_t50_data: Dict[str, Dict[str, Any]] = {}
        self.sorted_drivers: List[str] = []
        self.current_year: int = 2025

        # 圖表邊距
        self.margin_left = 70
        self.margin_right = 30
        self.margin_top = 30
        self.margin_bottom = 80
        self.chart_rect = QRect()

        # 懸停狀態
        self.hover_driver: Optional[str] = None
        self.hover_position: Optional[QPoint] = None

        # Y 軸範圍
        self.y_min = 2.0
        self.y_max = 4.0
        
        # 自定義 Y 軸範圍
        self._custom_y_min: Optional[float] = None
        self._custom_y_max: Optional[float] = None
        self._use_custom_y_range: bool = False
        
        # 隱藏的車手
        self.hidden_drivers: set = set()

        self.setMouseTracking(True)
        self.setMinimumSize(600, 400)

        logger.info("[SEASON_START_REACTION_CHART] Widget initialized")

    def update_data(self, data: Dict[str, Any]) -> None:
        """更新圖表數據並重新繪製"""
        try:
            logger.info("[SEASON_START_REACTION_CHART] ========== update_data ==========")
            
            if not data or not isinstance(data, dict):
                logger.warning("[SEASON_START_REACTION_CHART] Invalid data format")
                self._clear_data()
                return

            # 處理可能的雙層嵌套格式
            api_data = data
            if "data" in data and isinstance(data.get("data"), dict):
                api_data = data["data"]
                logger.info("[SEASON_START_REACTION_CHART] Unwrapped first layer")
                
            # 再檢查一次是否有雙層嵌套
            if "data" in api_data and isinstance(api_data.get("data"), dict):
                api_data = api_data["data"]
                logger.info("[SEASON_START_REACTION_CHART] Unwrapped second layer")

            logger.info(f"[SEASON_START_REACTION_CHART] Data keys: {list(api_data.keys())}")

            self.current_year = api_data.get("year", 2025)
            t50_dist = api_data.get("t50_distribution", {})
            drivers_data = t50_dist.get("drivers", {})

            if not drivers_data:
                logger.warning("[SEASON_START_REACTION_CHART] No driver data found")
                self._clear_data()
                return

            # 存儲數據
            self.driver_t50_data = drivers_data
            logger.info(f"[SEASON_START_REACTION_CHART] Loaded {len(drivers_data)} drivers")

            # 按中位數排序（由快到慢）
            self.sorted_drivers = sorted(
                drivers_data.keys(),
                key=lambda d: drivers_data[d].get("median", 999)
            )

            # 確保調色板已載入
            self._ensure_palette_loaded()

            # 計算 Y 軸範圍
            self._calculate_y_range()

            logger.info(f"[SEASON_START_REACTION_CHART] Update complete: {len(self.sorted_drivers)} drivers, Y range: {self.y_min:.2f} - {self.y_max:.2f}")
            self.update()

        except Exception as e:
            logger.exception(f"[SEASON_START_REACTION_CHART] Update failed: {e}")
            self._clear_data()

    def _clear_data(self) -> None:
        """清除數據"""
        self.driver_t50_data = {}
        self.sorted_drivers = []
        self.update()

    def clear_data(self) -> None:
        """公開的清除數據方法"""
        self._clear_data()

    def _ensure_palette_loaded(self) -> None:
        """確保調色板已載入"""
        try:
            color_palette_provider.ensure_loaded(year=self.current_year)
        except Exception:
            pass

    def _driver_color(self, driver: str) -> QColor:
        """獲取車手顏色"""
        try:
            color = color_palette_provider.get_driver_color(driver, format="qcolor")
            if isinstance(color, QColor):
                return QColor(color)
        except Exception:
            pass
        return QColor(self.DEFAULT_COLOR)

    def _calculate_y_range(self) -> None:
        """計算 Y 軸範圍"""
        # 如果使用自定義範圍，直接使用
        if self._use_custom_y_range and self._custom_y_min is not None and self._custom_y_max is not None:
            self.y_min = self._custom_y_min
            self.y_max = self._custom_y_max
            return
            
        if not self.driver_t50_data:
            self.y_min = 2.0
            self.y_max = 4.0
            return

        all_values: List[float] = []
        for driver, stats in self.driver_t50_data.items():
            # 過濾隱藏的車手
            if driver in self.hidden_drivers:
                continue
            races = stats.get("races", [])
            for race_data in races:
                t50 = race_data.get("t50")
                if t50 is not None:
                    all_values.append(t50)

        if all_values:
            self.y_min = max(1.8, min(all_values) - 0.2)
            self.y_max = min(5.0, max(all_values) + 0.2)
        else:
            self.y_min = 2.0
            self.y_max = 4.0

    def paintEvent(self, event) -> None:
        """繪製圖表"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # 計算圖表區域
            self.chart_rect = QRect(
                self.margin_left,
                self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )

            # 繪製背景
            self._draw_background(painter)
            
            # 繪製網格
            self._draw_grid(painter)
            
            # 繪製座標軸
            self._draw_axes(painter)

            # 繪製箱型圖
            if self.sorted_drivers:
                self._draw_box_plots(painter)
            else:
                self._draw_no_data_message(painter)

            # 繪製懸停提示
            if self.hover_driver and self.hover_position:
                self._draw_tooltip(painter)

        finally:
            painter.end()

    def _draw_background(self, painter: QPainter) -> None:
        """繪製背景（與 throttle_box_plot 一致）"""
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        painter.fillRect(self.chart_rect, QColor(255, 255, 255))

    def _draw_grid(self, painter: QPainter) -> None:
        """繪製網格線"""
        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DashLine))
        num_y_lines = 8
        for i in range(num_y_lines + 1):
            y = self.chart_rect.top() + (self.chart_rect.height() * i / num_y_lines)
            painter.drawLine(self.chart_rect.left(), int(y), self.chart_rect.right(), int(y))

    def _draw_axes(self, painter: QPainter) -> None:
        """繪製座標軸"""
        # 軸線
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.drawLine(self.chart_rect.bottomLeft(), self.chart_rect.bottomRight())
        painter.drawLine(self.chart_rect.bottomLeft(), self.chart_rect.topLeft())

        # Y 軸刻度標籤
        font = QFont("Microsoft JhengHei", 9)
        painter.setFont(font)
        painter.setPen(QPen(QColor(70, 70, 70)))

        num_y_labels = 8
        for i in range(num_y_labels + 1):
            y_pos = self.chart_rect.top() + (self.chart_rect.height() * i / num_y_labels)
            value = self.y_max - ((self.y_max - self.y_min) * i / num_y_labels)
            label = f"{value:.2f}s"
            painter.drawText(
                QRect(5, int(y_pos) - 10, self.margin_left - 10, 20),
                Qt.AlignRight | Qt.AlignVCenter,
                label,
            )

        # Y 軸標籤
        painter.save()
        painter.translate(15, self.chart_rect.center().y())
        painter.rotate(-90)
        y_label = tr("time_seconds", "Time (seconds)")
        fm = QFontMetrics(font)
        label_width = fm.horizontalAdvance(y_label)
        painter.drawText(-label_width // 2, 0, y_label)
        painter.restore()

        # X 軸標籤
        x_label = tr("driver", "Driver")
        fm = QFontMetrics(font)
        label_width = fm.horizontalAdvance(x_label)
        painter.drawText(
            self.chart_rect.center().x() - label_width // 2,
            self.height() - 10,
            x_label
        )

    def _draw_title(self, painter: QPainter) -> None:
        """繪製標題"""
        title_font = QFont("Microsoft JhengHei", 14, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(0, 0, 0))

        title = tr("season_start_reaction_title", "0-50 km/h Time Distribution") + f" ({self.current_year} {tr('season', 'Season')})"
        
        fm = QFontMetrics(title_font)
        title_width = fm.horizontalAdvance(title)
        title_x = (self.width() - title_width) // 2
        title_y = 35

        painter.drawText(title_x, title_y, title)

    def _draw_no_data_message(self, painter: QPainter) -> None:
        """繪製無數據訊息"""
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        font = QFont("Microsoft JhengHei", 12, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            self.chart_rect,
            Qt.AlignCenter,
            tr("no_data_available", "No data available"),
        )

    def _draw_box_plots(self, painter: QPainter) -> None:
        """繪製所有車手的箱型圖"""
        # 過濾隱藏的車手
        visible_drivers = [d for d in self.sorted_drivers if d not in self.hidden_drivers]
        
        if not visible_drivers:
            self._draw_no_data_message(painter)
            return
        
        num_drivers = len(visible_drivers)
        box_width = max(20, min(50, (self.chart_rect.width() - 20) // num_drivers - 10))
        spacing = (self.chart_rect.width() - num_drivers * box_width) / (num_drivers + 1)
        
        # 收集車手位置資訊，用於後續繪製標籤
        driver_positions = []

        # 設定裁剪區域，確保超出 Y 軸範圍的數據不顯示
        painter.save()
        painter.setClipRect(self.chart_rect)

        for i, driver in enumerate(visible_drivers):
            stats = self.driver_t50_data.get(driver, {})
            if not stats:
                continue

            x_center = self.chart_rect.left() + spacing * (i + 1) + box_width * i + box_width // 2
            driver_positions.append((driver, x_center, box_width))
            self._draw_single_box_plot_content(painter, driver, stats, x_center, box_width)
        
        # 恢復裁剪區域
        painter.restore()
        
        # 在裁剪區域外繪製車手標籤
        for driver, x_center, bw in driver_positions:
            team_color = self._driver_color(driver)
            is_hovered = driver == self.hover_driver
            self._draw_driver_label(painter, driver, x_center, team_color, is_hovered, bw)

    def _draw_single_box_plot_content(self, painter: QPainter, driver: str, stats: Dict[str, Any], x_center: float, box_width: int) -> None:
        """繪製單個車手的箱型圖內容（不含標籤）"""
        try:
            median = stats.get("median", 0)
            q1 = stats.get("q1", 0)
            q3 = stats.get("q3", 0)
            min_val = stats.get("min", 0)
            max_val = stats.get("max", 0)
            races = stats.get("races", [])

            # 轉換為 Y 座標
            y_median = self._value_to_y(median)
            y_q1 = self._value_to_y(q1)
            y_q3 = self._value_to_y(q3)
            y_min = self._value_to_y(min_val)
            y_max = self._value_to_y(max_val)

            # 獲取車手顏色
            team_color = self._driver_color(driver)
            is_hovered = driver == self.hover_driver

            # ========== 1. 繪製箱體 (Q1 到 Q3) - 半透明填充 ==========
            box_rect = QRectF(
                x_center - box_width / 2,
                y_q3,
                box_width,
                y_q1 - y_q3,
            )

            fill_color = QColor(team_color)
            fill_color.setAlpha(100 if not is_hovered else 140)
            
            border_color = QColor(team_color)
            border_color.setAlpha(255)

            painter.setBrush(QBrush(fill_color))
            painter.setPen(QPen(border_color, 2 if is_hovered else 1.5))
            painter.drawRect(box_rect)

            # ========== 2. 繪製鬚線 ==========
            whisker_pen = QPen(border_color, 1.5, Qt.SolidLine)
            painter.setPen(whisker_pen)
            
            # 上鬚線
            painter.drawLine(
                QPoint(int(x_center), int(y_q3)),
                QPoint(int(x_center), int(y_max))
            )
            painter.drawLine(
                QPoint(int(x_center - box_width / 4), int(y_max)),
                QPoint(int(x_center + box_width / 4), int(y_max))
            )
            
            # 下鬚線
            painter.drawLine(
                QPoint(int(x_center), int(y_q1)),
                QPoint(int(x_center), int(y_min))
            )
            painter.drawLine(
                QPoint(int(x_center - box_width / 4), int(y_min)),
                QPoint(int(x_center + box_width / 4), int(y_min))
            )

            # ========== 3. 繪製中位數線 ==========
            median_color = QColor(team_color).darker(130)
            painter.setPen(QPen(median_color, 2.5))
            painter.drawLine(
                QPoint(int(x_center - box_width / 2), int(y_median)),
                QPoint(int(x_center + box_width / 2), int(y_median)),
            )

            # ========== 4. 繪製散點圖 ==========
            if races:
                np.random.seed(hash(driver) % (2**31))
                jitter_range = box_width * 0.35
                
                scatter_color = QColor(team_color)
                scatter_color.setAlpha(200)
                
                painter.setPen(QPen(border_color, 0.5))
                painter.setBrush(QBrush(scatter_color))
                
                scatter_radius = 4
                
                for race_data in races:
                    t50 = race_data.get("t50")
                    if t50 is not None:
                        jitter_x = np.random.uniform(-jitter_range, jitter_range)
                        x_pos = x_center + jitter_x
                        y_pos = self._value_to_y(t50)
                        
                        painter.drawEllipse(
                            QPoint(int(x_pos), int(y_pos)),
                            scatter_radius, scatter_radius
                        )

        except Exception as exc:
            logger.exception(f"[SEASON_START_REACTION_CHART] Draw box plot failed for {driver}")

    def _draw_driver_label(self, painter: QPainter, driver: str, x_center: float, color: QColor, is_hovered: bool, box_width: int) -> None:
        """繪製車手標籤"""
        label_font = QFont("Arial", 9, QFont.Bold if is_hovered else QFont.Normal)
        painter.setFont(label_font)
        fm = QFontMetrics(label_font)
        label_width = fm.horizontalAdvance(driver)
        label_height = fm.height()

        label_x = x_center - label_width // 2
        label_y = self.chart_rect.bottom() + 15

        # 背景矩形
        padding = 3
        bg_rect = QRectF(
            label_x - padding,
            label_y - label_height + 2,
            label_width + padding * 2,
            label_height + padding
        )

        # 繪製背景
        painter.setPen(Qt.NoPen)
        bg_color = QColor(color)
        bg_color.setAlpha(200)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(bg_rect, 3, 3)

        # 繪製文字
        luminance = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
        text_color = QColor(0, 0, 0) if luminance > 128 else QColor(255, 255, 255)
        painter.setPen(text_color)
        painter.drawText(int(label_x), int(label_y), driver)

    def _draw_tooltip(self, painter: QPainter) -> None:
        """繪製懸停提示"""
        if not self.hover_driver or self.hover_driver not in self.driver_t50_data:
            return

        stats = self.driver_t50_data[self.hover_driver]
        
        lines = [
            f"{self.hover_driver}",
            f"{tr('median', 'Median')}: {stats.get('median', 0):.3f}s",
            f"{tr('average', 'Average')}: {stats.get('mean', 0):.3f}s",
            f"{tr('min', 'Min')}: {stats.get('min', 0):.3f}s",
            f"{tr('max', 'Max')}: {stats.get('max', 0):.3f}s",
            f"{tr('race_count', 'Races')}: {stats.get('race_count', 0)}",
        ]

        tooltip_font = QFont("Microsoft JhengHei", 10)
        painter.setFont(tooltip_font)
        fm = QFontMetrics(tooltip_font)

        max_width = max(fm.horizontalAdvance(line) for line in lines)
        line_height = fm.height()
        padding = 8
        tooltip_width = max_width + padding * 2
        tooltip_height = len(lines) * line_height + padding * 2

        tooltip_x = self.hover_position.x() + 15
        tooltip_y = self.hover_position.y() - tooltip_height // 2

        if tooltip_x + tooltip_width > self.width():
            tooltip_x = self.hover_position.x() - tooltip_width - 15
        if tooltip_y < 0:
            tooltip_y = 0
        if tooltip_y + tooltip_height > self.height():
            tooltip_y = self.height() - tooltip_height

        # 繪製背景
        tooltip_rect = QRectF(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QBrush(QColor(40, 40, 40, 230)))
        painter.drawRoundedRect(tooltip_rect, 5, 5)

        # 繪製文字
        for i, line in enumerate(lines):
            text_y = tooltip_y + padding + (i + 1) * line_height - 3
            if i == 0:
                bold_font = QFont("Microsoft JhengHei", 10, QFont.Bold)
                painter.setFont(bold_font)
                color = self._driver_color(self.hover_driver)
                painter.setPen(color)
            else:
                painter.setFont(tooltip_font)
                painter.setPen(QColor(255, 255, 255))
            painter.drawText(int(tooltip_x + padding), int(text_y), line)

    def _value_to_y(self, value: float) -> float:
        """將數值轉換為 Y 座標"""
        if self.y_max == self.y_min:
            return float(self.chart_rect.center().y())
        
        ratio = (value - self.y_min) / (self.y_max - self.y_min)
        return self.chart_rect.bottom() - ratio * self.chart_rect.height()

    def _get_driver_at_position(self, pos: QPoint) -> Optional[str]:
        """根據位置獲取車手"""
        if not self.sorted_drivers or not self.chart_rect.contains(pos):
            return None

        # 使用可見車手列表
        visible_drivers = [d for d in self.sorted_drivers if d not in self.hidden_drivers]
        if not visible_drivers:
            return None
            
        num_drivers = len(visible_drivers)
        box_width = max(20, min(50, (self.chart_rect.width() - 20) // num_drivers - 10))
        spacing = (self.chart_rect.width() - num_drivers * box_width) / (num_drivers + 1)

        for i, driver in enumerate(visible_drivers):
            x_center = self.chart_rect.left() + spacing * (i + 1) + box_width * i + box_width // 2
            if abs(pos.x() - x_center) <= box_width:
                return driver

        return None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """滑鼠移動事件"""
        driver = self._get_driver_at_position(event.pos())
        
        if driver != self.hover_driver:
            self.hover_driver = driver
            self.hover_position = event.pos() if driver else None
            self.update()
        elif driver:
            self.hover_position = event.pos()
            self.update()

    def leaveEvent(self, event) -> None:
        """滑鼠離開事件"""
        self.hover_driver = None
        self.hover_position = None
        self.update()

    def _is_on_y_axis(self, pos: QPoint) -> bool:
        """檢查滑鼠位置是否在 Y 軸區域"""
        y_axis_rect = QRect(
            0,
            self.margin_top,
            self.margin_left + 10,
            self.height() - self.margin_top - self.margin_bottom
        )
        return y_axis_rect.contains(pos)

    def contextMenuEvent(self, event) -> None:
        """右鍵選單事件"""
        pos = event.pos()
        
        # 檢查是否在 Y 軸區域
        if self._is_on_y_axis(pos):
            self._show_y_axis_menu(event)
            return
        
        # 檢查是否在車手區域
        driver = self._get_driver_at_position(pos)
        if driver and driver not in self.hidden_drivers:
            self._show_driver_menu(driver, event)
            return

    def _show_driver_menu(self, driver: str, event) -> None:
        """顯示車手右鍵選單"""
        menu = QMenu(self)
        
        # 隱藏車手選項
        hide_action = QAction(f"{tr('hide', 'Hide')} {driver}", self)
        hide_action.triggered.connect(lambda: self._hide_driver(driver))
        menu.addAction(hide_action)
        
        # 如果有隱藏的車手，顯示「顯示全部」選項
        if self.hidden_drivers:
            menu.addSeparator()
            show_all_action = QAction(tr("show_all_drivers", "Show All Drivers"), self)
            show_all_action.triggered.connect(self.show_all_drivers)
            menu.addAction(show_all_action)
        
        menu.exec_(event.globalPos())

    def _show_y_axis_menu(self, event) -> None:
        """顯示 Y 軸右鍵選單"""
        menu = QMenu(self)
        
        # 調整 Y 軸範圍選項
        adjust_y_action = QAction(tr("adjust_y_axis_range", "Adjust Y Axis Range..."), self)
        adjust_y_action.triggered.connect(self._show_y_axis_dialog)
        menu.addAction(adjust_y_action)
        
        # 如果當前使用自定義範圍，顯示重置選項
        if self._use_custom_y_range:
            menu.addSeparator()
            reset_y_action = QAction(tr("reset_y_axis_range", "Reset Y Axis to Auto"), self)
            reset_y_action.triggered.connect(self.reset_y_axis_range)
            menu.addAction(reset_y_action)
        
        menu.exec_(event.globalPos())

    def _show_y_axis_dialog(self) -> None:
        """顯示 Y 軸範圍調整對話框"""
        current_min = self.y_min
        current_max = self.y_max
        
        # 詢問最小值
        min_val, ok1 = QInputDialog.getDouble(
            self,
            tr("set_y_axis_min", "Set Y Axis Minimum"),
            tr("enter_min_value", "Enter minimum value (seconds):"),
            current_min,
            0.0,
            10.0,
            2
        )
        
        if not ok1:
            return
        
        # 詢問最大值
        max_val, ok2 = QInputDialog.getDouble(
            self,
            tr("set_y_axis_max", "Set Y Axis Maximum"),
            tr("enter_max_value", "Enter maximum value (seconds):"),
            current_max,
            min_val + 0.1,
            10.0,
            2
        )
        
        if not ok2:
            return
        
        # 驗證範圍
        if max_val <= min_val:
            QMessageBox.warning(
                self,
                tr("invalid_range", "Invalid Range"),
                tr("max_must_be_greater", "Maximum value must be greater than minimum value.")
            )
            return
        
        # 設定自定義範圍
        self.set_custom_y_range(min_val, max_val)

    def set_custom_y_range(self, y_min: float, y_max: float) -> None:
        """設定自定義 Y 軸範圍"""
        self._custom_y_min = y_min
        self._custom_y_max = y_max
        self._use_custom_y_range = True
        
        self._calculate_y_range()
        self.update()
        
        logger.debug(f"[SEASON_START_REACTION_CHART] Custom Y range set: {y_min:.2f} - {y_max:.2f}")

    def reset_y_axis_range(self) -> None:
        """重置 Y 軸為自動範圍"""
        self._custom_y_min = None
        self._custom_y_max = None
        self._use_custom_y_range = False
        
        self._calculate_y_range()
        self.update()
        
        logger.debug("[SEASON_START_REACTION_CHART] Y axis range reset to auto")

    def _hide_driver(self, driver: str) -> None:
        """隱藏指定車手"""
        self.hidden_drivers.add(driver)
        self._calculate_y_range()
        self.update()
        
        logger.debug(f"[SEASON_START_REACTION_CHART] Driver hidden: {driver}")

    def show_all_drivers(self) -> None:
        """顯示所有車手（清除隱藏列表）"""
        self.hidden_drivers.clear()
        self._calculate_y_range()
        self.update()
        
        logger.debug("[SEASON_START_REACTION_CHART] All drivers shown")

    def reset_view(self) -> None:
        """重置圖表視圖 - 供 Show All Data 按鈕使用"""
        # 清除隱藏的車手
        self.hidden_drivers.clear()
        
        # 重置 Y 軸為自動範圍
        self._custom_y_min = None
        self._custom_y_max = None
        self._use_custom_y_range = False
        
        # 重新計算 Y 軸範圍
        self._calculate_y_range()
        self.update()
        
        logger.debug("[SEASON_START_REACTION_CHART] View reset (Show All Data)")
