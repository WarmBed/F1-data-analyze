#!/usr/bin/env python3
"""
PoleDefenseChartWidget - 桿位防守時間軸格子圖 (純 PyQt5 實現，白色風格)

功能：
- 使用 PyQt5 QPainter 繪製時間軸格子圖
- 白色風格主題，與 TrafficTimelineChartWidget 一致
- 每列為一場比賽，每行為一位車手
- 顯示桿位防守結果：成功保持P1 / 失去P1 / 非桿位發車
- 應用車隊配色方案 (使用 color_palette_provider)
- 按防守成功率排序

格式說明：
- 成功守住P1: 綠色背景 + P1 文字
- 失去P1: 紅色背景 + 顯示 Lap2 的位置 (如 P2)
- 非桿位發車: 淺灰色背景 + - 符號

作者: F1T Team
日期: 2025-12-23
版本: 2.0.0
"""

from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QSizePolicy
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter,
    QPen,
    QColor,
    QBrush,
    QFont,
    QFontMetrics,
    QMouseEvent,
    QLinearGradient,
)

from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.themes import color_palette_provider

logger = get_logger(__name__)


# 狀態顏色定義 (白色風格)
STATUS_COLORS = {
    "defended": QColor("#4CAF50"),     # 綠色 - 成功守住 P1
    "lost": QColor("#F44336"),         # 紅色 - 失去 P1
    "not_pole": QColor("#E0E0E0"),     # 淺灰色 - 非桿位發車
    "grid_line": QColor("#BDBDBD"),    # 格線顏色
    "header_bg": QColor("#F5F5F5"),    # 標題列背景
    "text_dark": QColor("#212121"),    # 深色文字
    "text_light": QColor("#FFFFFF"),   # 白色文字
}


class PoleDefenseChartWidget(QWidget):
    """桿位防守時間軸格子圖 (純 PyQt5 QPainter 實現，白色風格)"""

    DEFAULT_COLOR = QColor(128, 128, 128)
    chart_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 數據存儲
        self.driver_pole_data: Dict[str, Dict[str, Any]] = {}
        self.sorted_drivers: List[str] = []
        self.race_list: List[str] = []
        self.current_year: int = 2025

        # 圖表尺寸
        self.margin_left = 80       # 車手名稱區域
        self.margin_right = 100     # 統計區域
        self.margin_top = 50        # 標題列
        self.margin_bottom = 50     # 圖例區域
        
        self.cell_width = 45        # 每個格子的寬度
        self.cell_height = 26       # 每個格子的高度
        self.header_height = 35     # 標題列高度
        
        self.chart_rect = QRect()

        # 懸停狀態
        self.hover_cell: Optional[Tuple[str, str]] = None  # (driver, race)
        self.hover_position: Optional[QPoint] = None

        self.setMouseTracking(True)
        self.setMinimumSize(800, 400)
        
        # 設置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        logger.info("[POLE_DEFENSE_CHART] Widget initialized (White theme)")

    def update_data(self, data: Dict[str, Any]) -> None:
        """更新圖表數據並重新繪製"""
        try:
            logger.info("[POLE_DEFENSE_CHART] ========== update_data ==========")
            
            if not data or not isinstance(data, dict):
                logger.warning("[POLE_DEFENSE_CHART] Invalid data format")
                self._clear_data()
                return

            # 處理可能的雙層嵌套格式
            api_data = data
            if "data" in data and isinstance(data.get("data"), dict):
                api_data = data["data"]
                logger.info("[POLE_DEFENSE_CHART] Unwrapped first layer")
                
            # 再檢查一次是否有雙層嵌套
            if "data" in api_data and isinstance(api_data.get("data"), dict):
                api_data = api_data["data"]
                logger.info("[POLE_DEFENSE_CHART] Unwrapped second layer")

            logger.info(f"[POLE_DEFENSE_CHART] Data keys: {list(api_data.keys())}")

            self.current_year = api_data.get("year", 2025)
            
            # 提取 p1 桿位數據
            p1_unchanged = api_data.get("p1_lap2_position_unchanged", {})
            p1_changed = api_data.get("p1_lap2_position_changed", {})
            
            unchanged_races = p1_unchanged.get("races", [])
            changed_races = p1_changed.get("races", [])
            
            logger.info(f"[POLE_DEFENSE_CHART] p1_unchanged count: {len(unchanged_races)}, p1_changed count: {len(changed_races)}")
            
            # Debug: 打印第一筆數據看結構
            if unchanged_races:
                logger.info(f"[POLE_DEFENSE_CHART] Sample unchanged race: {unchanged_races[0]}")
            if changed_races:
                logger.info(f"[POLE_DEFENSE_CHART] Sample changed race: {changed_races[0]}")

            # 建立車手桿位數據 (注意：使用 pole_driver 而不是 driver)
            self.driver_pole_data = self._build_driver_pole_data(unchanged_races, changed_races)
            
            if not self.driver_pole_data:
                logger.warning("[POLE_DEFENSE_CHART] No pole defense data found")
                self._clear_data()
                return

            # 提取所有比賽列表並排序（按照比賽回合）
            self.race_list = self._build_race_list(unchanged_races, changed_races)
            
            # 按防守成功率排序車手（高到低）
            self.sorted_drivers = self._sort_drivers_by_success_rate()
            
            logger.info(f"[POLE_DEFENSE_CHART] Processed {len(self.sorted_drivers)} drivers, {len(self.race_list)} races")

            self.update()

        except Exception as e:
            logger.exception(f"[POLE_DEFENSE_CHART] Failed to update data: {e}")
            self._clear_data()

    def _build_driver_pole_data(self, unchanged_races: List[Dict], changed_races: List[Dict]) -> Dict[str, Dict]:
        """建立車手桿位數據"""
        driver_data = {}
        
        # 處理成功防守的比賽 (使用 pole_driver 欄位)
        for race in unchanged_races:
            driver = race.get("pole_driver", "")  # 修正：使用 pole_driver
            race_name = race.get("race", "")
            if not driver or not race_name:
                continue
                
            if driver not in driver_data:
                driver_data[driver] = {
                    "poles": 0,
                    "defended": 0,
                    "lost": 0,
                    "races": {}
                }
            
            driver_data[driver]["poles"] += 1
            driver_data[driver]["defended"] += 1
            driver_data[driver]["races"][race_name] = {
                "result": "defended",
                "lap2_position": 1,
                "round": race.get("round", 0)
            }
        
        # 處理失去 P1 的比賽 (使用 pole_driver 欄位)
        for race in changed_races:
            driver = race.get("pole_driver", "")  # 修正：使用 pole_driver
            race_name = race.get("race", "")
            lap2_pos = race.get("lap2_position", 2)
            if not driver or not race_name:
                continue
                
            if driver not in driver_data:
                driver_data[driver] = {
                    "poles": 0,
                    "defended": 0,
                    "lost": 0,
                    "races": {}
                }
            
            driver_data[driver]["poles"] += 1
            driver_data[driver]["lost"] += 1
            driver_data[driver]["races"][race_name] = {
                "result": "lost",
                "lap2_position": lap2_pos,
                "round": race.get("round", 0)
            }
        
        # 計算成功率
        for driver, stats in driver_data.items():
            if stats["poles"] > 0:
                stats["success_rate"] = (stats["defended"] / stats["poles"]) * 100
            else:
                stats["success_rate"] = 0.0
        
        return driver_data

    def _build_race_list(self, unchanged_races: List[Dict], changed_races: List[Dict]) -> List[str]:
        """建立比賽列表，按回合排序"""
        race_rounds = {}
        
        for race in unchanged_races + changed_races:
            race_name = race.get("race", "")
            race_round = race.get("round", 0)
            if race_name and race_name not in race_rounds:
                race_rounds[race_name] = race_round
        
        # 按回合排序
        sorted_races = sorted(race_rounds.keys(), key=lambda r: race_rounds.get(r, 0))
        return sorted_races

    def _sort_drivers_by_success_rate(self) -> List[str]:
        """按防守成功率排序車手（高到低）"""
        return sorted(
            self.driver_pole_data.keys(),
            key=lambda d: (
                self.driver_pole_data[d].get("success_rate", 0),
                self.driver_pole_data[d].get("poles", 0)
            ),
            reverse=True
        )

    def _clear_data(self) -> None:
        """清空數據"""
        self.driver_pole_data = {}
        self.sorted_drivers = []
        self.race_list = []
        self.update()

    def clear_data(self) -> None:
        """公開方法：清空數據"""
        self._clear_data()

    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            # 更新圖表區域
            self.chart_rect = QRect(
                self.margin_left,
                self.margin_top + self.header_height,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom - self.header_height
            )
            
            # 動態計算 cell 大小
            self._calculate_cell_dimensions()
            
            # 白色背景
            self._draw_background(painter)
            
            if not self.sorted_drivers or not self.race_list:
                self._draw_no_data(painter)
            else:
                # 繪製標題列（比賽名稱）
                self._draw_header_row(painter)
                
                # 繪製車手名稱列
                self._draw_driver_column(painter)
                
                # 繪製數據格子
                self._draw_data_cells(painter)
                
                # 繪製統計列
                self._draw_stats_column(painter)
                
                # 繪製懸停提示
                if self.hover_cell and self.hover_position:
                    self._draw_tooltip(painter)
                
                # 繪製圖例
                self._draw_legend(painter)
        finally:
            painter.end()

    def _calculate_cell_dimensions(self):
        """動態計算 cell 尺寸"""
        if not self.race_list or not self.sorted_drivers:
            return
        
        # 計算可用區域
        available_width = self.chart_rect.width()
        available_height = self.chart_rect.height()
        
        # 寬度：根據比賽數量
        self.cell_width = max(35, min(55, (available_width - 10) // max(1, len(self.race_list))))
        
        # 高度：根據車手數量
        self.cell_height = max(20, min(32, (available_height - 10) // max(1, len(self.sorted_drivers))))

    def _draw_background(self, painter: QPainter):
        """繪製白色背景"""
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        painter.fillRect(self.chart_rect, QColor(255, 255, 255))

    def _draw_no_data(self, painter: QPainter):
        """繪製無數據提示"""
        painter.setPen(QColor(100, 100, 100))
        font = QFont("Segoe UI", 12)
        painter.setFont(font)
        text = tr("no_pole_defense_data", "No Pole Defense Data Available")
        painter.drawText(self.rect(), Qt.AlignCenter, text)

    def _draw_header_row(self, painter: QPainter):
        """繪製標題列（比賽名稱）"""
        header_y = self.margin_top
        
        # 標題列背景
        painter.fillRect(
            self.margin_left, header_y,
            len(self.race_list) * self.cell_width,
            self.header_height,
            STATUS_COLORS["header_bg"]
        )
        
        # 比賽名稱（縮寫）
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.setPen(STATUS_COLORS["text_dark"])
        
        for i, race in enumerate(self.race_list):
            x = self.margin_left + i * self.cell_width
            abbrev = self._get_race_abbreviation(race)
            rect = QRect(x, header_y, self.cell_width, self.header_height)
            painter.drawText(rect, Qt.AlignCenter, abbrev)

    def _get_race_abbreviation(self, race_name: str) -> str:
        """獲取比賽名稱縮寫"""
        abbreviations = {
            "Bahrain": "BAH", "Saudi Arabia": "SAU", "Australia": "AUS",
            "Japan": "JPN", "China": "CHN", "Miami": "MIA",
            "Emilia Romagna": "IMO", "Monaco": "MON", "Canada": "CAN",
            "Spain": "ESP", "Austria": "AUT", "United Kingdom": "GBR",
            "Hungary": "HUN", "Belgium": "BEL", "Netherlands": "NED",
            "Italy": "ITA", "Azerbaijan": "AZE", "Singapore": "SIN",
            "United States": "USA", "Mexico": "MEX", "Brazil": "BRA",
            "Las Vegas": "LVS", "Qatar": "QAT", "Abu Dhabi": "ABU",
            "São Paulo": "SAO",
        }
        
        for key, abbrev in abbreviations.items():
            if key.lower() in race_name.lower():
                return abbrev
        
        return race_name[:3].upper()

    def _draw_driver_column(self, painter: QPainter):
        """繪製車手名稱列 (帶車隊顏色背景)"""
        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)
        
        start_y = self.margin_top + self.header_height
        
        for i, driver in enumerate(self.sorted_drivers):
            y = start_y + i * self.cell_height
            
            # 獲取車隊顏色
            team_color = self._get_driver_color(driver)
            
            # 繪製車手名稱背景 (整個背景填充車隊顏色，如 ideal_lap_table)
            driver_rect = QRect(5, y + 1, self.margin_left - 10, self.cell_height - 2)
            painter.fillRect(driver_rect, team_color)
            
            # 根據背景色亮度決定文字顏色
            luminance = (0.299 * team_color.red() + 0.587 * team_color.green() + 0.114 * team_color.blue())
            text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
            
            # 車手名稱
            painter.setPen(text_color)
            text_rect = QRect(10, y, self.margin_left - 20, self.cell_height)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, driver)

    def _get_driver_color(self, driver: str) -> QColor:
        """獲取車手的車隊顏色 (使用 color_palette_provider)"""
        try:
            # 使用正確的調用方式，返回 QColor 格式
            color = color_palette_provider.get_driver_color(driver, format="qcolor", fallback=True)
            if color and isinstance(color, QColor):
                return color
        except Exception:
            pass
        return self.DEFAULT_COLOR

    def _draw_data_cells(self, painter: QPainter):
        """繪製數據格子"""
        start_y = self.margin_top + self.header_height
        font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(font)
        
        for i, driver in enumerate(self.sorted_drivers):
            y = start_y + i * self.cell_height
            driver_races = self.driver_pole_data.get(driver, {}).get("races", {})
            
            for j, race in enumerate(self.race_list):
                x = self.margin_left + j * self.cell_width
                cell_rect = QRect(x + 1, y + 1, self.cell_width - 2, self.cell_height - 2)
                
                race_data = driver_races.get(race)
                
                if race_data:
                    result = race_data.get("result", "")
                    lap2_pos = race_data.get("lap2_position", 1)
                    
                    if result == "defended":
                        # 成功防守 - 綠色背景
                        painter.fillRect(cell_rect, STATUS_COLORS["defended"])
                        painter.setPen(STATUS_COLORS["text_light"])
                        painter.drawText(cell_rect, Qt.AlignCenter, "P1")
                    else:
                        # 失去 P1 - 紅色背景
                        painter.fillRect(cell_rect, STATUS_COLORS["lost"])
                        painter.setPen(STATUS_COLORS["text_light"])
                        painter.drawText(cell_rect, Qt.AlignCenter, f"P{lap2_pos}")
                else:
                    # 非桿位發車 - 淺灰色背景
                    painter.fillRect(cell_rect, STATUS_COLORS["not_pole"])
                    painter.setPen(QColor(150, 150, 150))
                    painter.drawText(cell_rect, Qt.AlignCenter, "-")
                
                # 繪製格線
                painter.setPen(QPen(STATUS_COLORS["grid_line"], 1))
                painter.drawRect(cell_rect)
        
        # 繪製懸停高亮
        if self.hover_cell:
            driver, race = self.hover_cell
            try:
                driver_idx = self.sorted_drivers.index(driver)
                race_idx = self.race_list.index(race)
                hover_x = self.margin_left + race_idx * self.cell_width
                hover_y = start_y + driver_idx * self.cell_height
                hover_rect = QRect(hover_x, hover_y, self.cell_width, self.cell_height)
                painter.setPen(QPen(QColor(33, 150, 243), 2))  # 藍色邊框
                painter.drawRect(hover_rect)
            except ValueError:
                pass

    def _draw_stats_column(self, painter: QPainter):
        """繪製統計列"""
        start_y = self.margin_top + self.header_height
        stats_x = self.margin_left + len(self.race_list) * self.cell_width + 10
        
        # 標題
        header_font = QFont("Segoe UI", 8, QFont.Bold)
        painter.setFont(header_font)
        painter.setPen(STATUS_COLORS["text_dark"])
        
        painter.drawText(stats_x, self.margin_top + 12, tr("poles", "Poles"))
        painter.drawText(stats_x + 45, self.margin_top + 12, tr("rate", "Rate"))
        
        # 數據
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        for i, driver in enumerate(self.sorted_drivers):
            y = start_y + i * self.cell_height + self.cell_height - 6
            stats = self.driver_pole_data.get(driver, {})
            
            poles = stats.get("poles", 0)
            success_rate = stats.get("success_rate", 0)
            
            # 桿位數
            painter.setPen(STATUS_COLORS["text_dark"])
            painter.drawText(stats_x, y, str(poles))
            
            # 成功率 (顏色編碼)
            if success_rate >= 80:
                rate_color = QColor("#4CAF50")  # 綠色
            elif success_rate >= 50:
                rate_color = QColor("#FF9800")  # 橙色
            else:
                rate_color = QColor("#F44336")  # 紅色
            
            painter.setPen(rate_color)
            rate_text = f"{success_rate:.0f}%"
            painter.drawText(stats_x + 45, y, rate_text)

    def _draw_legend(self, painter: QPainter):
        """繪製圖例"""
        legend_y = self.height() - 30
        legend_x = self.margin_left
        
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        # 成功防守
        painter.fillRect(legend_x, legend_y, 14, 14, STATUS_COLORS["defended"])
        painter.setPen(QPen(STATUS_COLORS["grid_line"], 1))
        painter.drawRect(legend_x, legend_y, 14, 14)
        painter.setPen(STATUS_COLORS["text_dark"])
        painter.drawText(legend_x + 20, legend_y + 11, tr("defended_p1", "Defended P1"))
        
        # 失去 P1
        legend_x += 120
        painter.fillRect(legend_x, legend_y, 14, 14, STATUS_COLORS["lost"])
        painter.setPen(QPen(STATUS_COLORS["grid_line"], 1))
        painter.drawRect(legend_x, legend_y, 14, 14)
        painter.setPen(STATUS_COLORS["text_dark"])
        painter.drawText(legend_x + 20, legend_y + 11, tr("lost_p1", "Lost P1"))
        
        # 非桿位
        legend_x += 100
        painter.fillRect(legend_x, legend_y, 14, 14, STATUS_COLORS["not_pole"])
        painter.setPen(QPen(STATUS_COLORS["grid_line"], 1))
        painter.drawRect(legend_x, legend_y, 14, 14)
        painter.setPen(STATUS_COLORS["text_dark"])
        painter.drawText(legend_x + 20, legend_y + 11, tr("not_on_pole", "Not on Pole"))

    def _draw_tooltip(self, painter: QPainter):
        """繪製懸停提示"""
        if not self.hover_cell or not self.hover_position:
            return
        
        driver, race = self.hover_cell
        driver_data = self.driver_pole_data.get(driver, {})
        race_data = driver_data.get("races", {}).get(race)
        
        if not race_data:
            return
        
        # 構建提示文字
        result = race_data.get("result", "")
        lap2_pos = race_data.get("lap2_position", 1)
        
        if result == "defended":
            status = tr("kept_p1_at_lap2", "Kept P1 at Lap 2")
        else:
            status = tr("dropped_to_position", "Dropped to P{pos} at Lap 2").format(pos=lap2_pos)
        
        tooltip_text = f"{driver} - {race}\n{status}"
        
        # 繪製提示框
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        lines = tooltip_text.split("\n")
        max_width = max(fm.horizontalAdvance(line) for line in lines) + 16
        tooltip_height = len(lines) * fm.height() + 12
        
        tooltip_x = min(self.hover_position.x() + 15, self.width() - max_width - 10)
        tooltip_y = min(self.hover_position.y() + 15, self.height() - tooltip_height - 10)
        
        # 背景 (白色半透明)
        painter.fillRect(tooltip_x, tooltip_y, max_width, tooltip_height, QColor(255, 255, 255, 245))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(tooltip_x, tooltip_y, max_width, tooltip_height)
        
        # 文字
        painter.setPen(STATUS_COLORS["text_dark"])
        text_y = tooltip_y + fm.ascent() + 6
        for line in lines:
            painter.drawText(tooltip_x + 8, text_y, line)
            text_y += fm.height()

    def mouseMoveEvent(self, event: QMouseEvent):
        """處理滑鼠移動事件"""
        pos = event.pos()
        self.hover_position = pos
        
        # 檢查是否在數據區域內
        start_y = self.margin_top + self.header_height
        
        # 計算位置
        col = (pos.x() - self.margin_left) // self.cell_width
        row = (pos.y() - start_y) // self.cell_height
        
        if 0 <= col < len(self.race_list) and 0 <= row < len(self.sorted_drivers):
            new_hover = (self.sorted_drivers[row], self.race_list[col])
            if new_hover != self.hover_cell:
                self.hover_cell = new_hover
                self.update()
        else:
            if self.hover_cell is not None:
                self.hover_cell = None
                self.update()

    def leaveEvent(self, event):
        """處理滑鼠離開事件"""
        self.hover_cell = None
        self.hover_position = None
        self.update()

    def reset_view(self) -> None:
        """重置視圖"""
        self.update()

    def sizeHint(self):
        """建議尺寸"""
        from PyQt5.QtCore import QSize
        width = self.margin_left + len(self.race_list) * self.cell_width + self.margin_right
        height = self.margin_top + self.header_height + len(self.sorted_drivers) * self.cell_height + self.margin_bottom
        return QSize(max(800, width), max(400, height))
